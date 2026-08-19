"""Navigeringsträdet: appens sidor ordnade efter svensk rätts systematik.

Sidopanelen följer svensk juridisk systematik i stället för en platt
lista av filer: offentlig rätt, civilrätt med
förmögenhetsrättens undergrenar, och straffrätt och processrätt.

Trädet är ren data utan Streamlit-beroende, så att det kan enhetstestas.
utils.ui.render_sidopanel ritar det och streamlit_app.py registrerar samma
sidor i st.navigation.

En ``Modul`` utan ``sida`` är planerad men inte byggd. Den visas gråtonad
med texten "(kommer)" och är aldrig en klickbar länk. tests/test_navigation.py
kontrollerar att varje modul antingen pekar på en befintlig fil i sidor/
eller saknar sida.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, MutableMapping, Union

ROT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Modul:
    """Ett löv i trädet: en modulsida, byggd eller planerad.

    ``sida`` är sökvägen relativt projektroten, t.ex. "sidor/2_Avtalsratt.py".
    None betyder att modulen är planerad men ännu inte byggd.

    ``ovningsmodul`` skiljer appens rättsområden (de som har övningsinnehåll i
    data/scenarier och därmed en plats i kursordningen) från verktygssidor som
    Hem, Rättskartan och Kunskapskarta. Startsidans "nästa steg" rör sig bara
    genom övningsmoduler; tests/test_navigation.py vaktar att mängden är exakt
    densamma som scenariodatans moduler.
    """

    namn: str
    sida: str | None = None
    ovningsmodul: bool = False

    @property
    def planerad(self) -> bool:
        """True om modulen ännu inte har någon sida."""
        return self.sida is None


@dataclass(frozen=True)
class Grupp:
    """En rubriknivå i trädet: kategori, underkategori eller undergren."""

    namn: str
    barn: tuple["Nod", ...]


Nod = Union[Modul, Grupp]


# Trädet följer rättssystemets egen indelning. Kapitelhänvisningarna i
# kommentarerna avser den ordningen.
NAV_TRAD: tuple[Grupp, ...] = (
    Grupp(
        "START OCH METOD",
        (
            Modul("Hem", "sidor/0_Hem.py"),
            Modul(
                "Juridisk metod", "sidor/1_Juridisk_metod.py", ovningsmodul=True
            ),  # kap 1
            Modul("Rättskartan", "sidor/16_Rattskartan.py"),
        ),
    ),
    Grupp(
        "OFFENTLIG RÄTT",
        (
            # Heter Statsrätt även i Rättskartan (data/rattssystem.json).
            # Samma rättsområde får inte bära två namn på samma skärm.
            Modul("Statsrätt"),  # kap 2-3, ej byggd
            Modul("Förvaltningsrätt"),  # kap 4, ej byggd
        ),
    ),
    Grupp(
        "CIVILRÄTT",
        (
            # Gruppen och dess enda modul heter båda "Personrätt". Det är
            # avsiktligt, inte en dubblett: gruppen är en äkta förfader till
            # modulen (rättsområdet innehåller bara ett kapitel i appen), så
            # rubrikkedja("Personrätt") ger korrekt ("CIVILRÄTT", "Personrätt").
            # Ingen namnunikhetsvakt ska "fixa" detta.
            Grupp(
                "Personrätt",
                (
                    Modul(
                        "Personrätt", "sidor/12_Personratt.py", ovningsmodul=True
                    ),  # kap 5
                ),
            ),
            Grupp(
                "Förmögenhetsrätt",
                (
                    Modul(
                        "Allmän förmögenhetsrätt",
                        "sidor/13_Allman_formogenhetsratt.py",
                        ovningsmodul=True,
                    ),  # kap 6
                    Grupp(
                        "Kontraktsrätt",
                        (
                            Modul(
                                "Avtalsrätt", "sidor/2_Avtalsratt.py", ovningsmodul=True
                            ),  # kap 7
                            Modul(
                                "Köprätt och konsumenträtt",
                                "sidor/3_Kop_och_konsumentratt.py",
                                ovningsmodul=True,
                            ),  # kap 8
                            Modul(
                                "Fastighetsrätt",
                                "sidor/14_Fastighetsratt.py",
                                ovningsmodul=True,
                            ),  # kap 9
                        ),
                    ),
                    Grupp(
                        "Ersättningsrätt",
                        (
                            Modul(
                                "Skadeståndsrätt",
                                "sidor/4_Skadestandsratt.py",
                                ovningsmodul=True,
                            ),  # kap 10
                        ),
                    ),
                    Grupp(
                        "Näringsrätt",
                        (
                            Modul(
                                "Arbetsrätt", "sidor/5_Arbetsratt.py", ovningsmodul=True
                            ),  # kap 11
                            Modul(
                                "Associationsrätt",
                                "sidor/6_Associationsratt.py",
                                ovningsmodul=True,
                            ),  # kap 12
                        ),
                    ),
                    Grupp(
                        "Krediträtt och obeståndsrätt",
                        (
                            Modul(
                                "Fordringsrätt",
                                "sidor/15_Fordringsratt.py",
                                ovningsmodul=True,
                            ),
                        ),  # kap 15-17
                    ),
                ),
            ),
            Grupp(
                "Familjerätt",
                (
                    Modul(
                        "Familjerätt och successionsrätt",
                        "sidor/7_Familje_och_arvsratt.py",
                        ovningsmodul=True,
                    ),  # kap 18-21
                ),
            ),
        ),
    ),
    Grupp(
        "STRAFF- OCH PROCESSRÄTT",
        (
            Modul(
                "Straffrätt och processrätt",
                "sidor/8_Straff_och_processratt.py",
                ovningsmodul=True,
            ),  # kap 22
        ),
    ),
    Grupp(
        "TRÄNING",
        (
            Modul("Kunskapstest", "sidor/9_Kunskapstest.py"),
            Modul("Kunskapskarta", "sidor/10_Kunskapskarta.py"),
            Modul("Kunskapsutmaning", "sidor/11_Kunskapsutmaning.py"),
        ),
    ),
)


def alla_moduler(noder: tuple[Nod, ...] = NAV_TRAD) -> Iterator[Modul]:
    """Gå igenom trädet på djupet och ge varje modul (löv) i ordning."""
    for nod in noder:
        if isinstance(nod, Modul):
            yield nod
        else:
            yield from alla_moduler(nod.barn)


def byggda_sidor(noder: tuple[Nod, ...] = NAV_TRAD) -> tuple[str, ...]:
    """Sökvägarna till de moduler som faktiskt har en sida, i trädets ordning."""
    return tuple(m.sida for m in alla_moduler(noder) if m.sida is not None)


def byggda_namn(noder: tuple[Nod, ...] = NAV_TRAD) -> tuple[str, ...]:
    """Namnen på de moduler som har en sida.

    Namnen är avsiktligt identiska med titlarna i st.Page-registret i
    streamlit_app.py, så att den öppna sidan kan kännas igen på sin titel.
    tests/test_navigation.py vaktar att de två listorna hålls i synk.
    """
    return tuple(m.namn for m in alla_moduler(noder) if m.sida is not None)


def sida_finns(sida: str) -> bool:
    """True om sökvägen pekar på en fil som finns i projektet."""
    return (ROT / sida).is_file()


def rubrikkedja(namn: str, noder: tuple[Nod, ...] = NAV_TRAD) -> tuple[str, ...]:
    """Namnen på grupperna som omsluter modulen, yttersta först.

    Sidopanelen använder kedjan för att ge den öppna sidans förfäder full
    bläckvikt, så att studenten hittar sin plats i ett träd som är fyra nivåer
    djupt. Tom tupel om modulnamnet inte finns i trädet.
    """
    for nod in noder:
        if isinstance(nod, Modul):
            continue
        if any(m.namn == namn for m in alla_moduler(nod.barn)):
            return (nod.namn,) + rubrikkedja(namn, nod.barn)
    return ()


def sida_for_namn(namn: str, noder: tuple[Nod, ...] = NAV_TRAD) -> str | None:
    """Sökvägen för en byggd moduls namn, eller None om den saknas eller är planerad."""
    for n, s in zip(byggda_namn(noder), byggda_sidor(noder)):
        if n == namn:
            return s
    return None


def övningsmoduler(noder: tuple[Nod, ...] = NAV_TRAD) -> tuple[Modul, ...]:
    """Appens rättsområdesmoduler i trädets ordning.

    Trädets ordning är appens egen ordning, så den här tupeln ÄR
    kursordningen. Verktygssidor (Hem, Rättskartan, Kunskapstest,
    Kunskapskarta, Kunskapsutmaning) ingår inte.
    """
    return tuple(m for m in alla_moduler(noder) if m.ovningsmodul and m.sida)


def nasta_ovningsmodul(pabborjade: frozenset[str]) -> Modul | None:
    """Första ovningsmodulen studenten ännu inte börjat på, i kursordning.

    None betyder att alla övningsmoduler är påbörjade. Då har startsidan inget
    nytt att föreslå och faller tillbaka på att återuppta.
    """
    for modul in övningsmoduler():
        if modul.namn not in pabborjade:
            return modul
    return None


# --- Startsidans call-to-action ----------------------------------------------
#
# Startsidan visar en enda knapp: fortsätt i senast besökta modul, eller
# börja appens första modul om sessionen är ny. Logiken ligger här (ren
# data/funktioner) i stället för i sidor/0_Hem.py, som enligt modulens egen
# regel inte ska innehålla affärslogik.

SENAST_BESOKT_NYCKEL = "_jok_senast_besokt"
FALLBACK_CTA_TITEL = "Juridisk metod"
FALLBACK_CTA_SIDA = "sidor/1_Juridisk_metod.py"


def registrera_besok(session_state: MutableMapping[str, object], titel: str) -> None:
    """Spara senast besökta modul i sessionen, om besöket inte gäller Hem.

    Hem exkluderas: annars skulle startsidan skriva över sin egen källa till
    "senast besökt" varje gång den visas, och knappen skulle aldrig peka
    någon annanstans än till sig själv.
    """
    if titel != "Hem":
        session_state[SENAST_BESOKT_NYCKEL] = titel


@dataclass(frozen=True)
class CtaMal:
    """Startsidans call-to-action: vart den pekar och varför.

    ``skal`` är en mening som visas i kortet, så att en student som vill något
    annat gör ett informerat val i stället för att känna sig olydig.
    """

    titel: str
    sida: str
    ateruppta: bool
    skal: str = ""


def cta_mal(
    senast_besokt: str | None,
    pabborjade: frozenset[str] = frozenset(),
) -> CtaMal:
    """Bestäm startsidans call-to-action.

    Föredrar **nästa ej påbörjade ovningsmodul i kursordning**, eftersom det är den
    enda av de två signalerna som faktiskt leder studenten framåt: senast
    besökta modul kan vara en modul studenten råkade öppna, och pekar man dit
    varje gång låses studenten fast där. Kursordningen är trädets ordning i
    NAV_TRAD, som följer appens egen ordning.

    Är alla övningsmoduler påbörjade finns inget nytt att föreslå, och vi återupptar
    den senast besökta modulen i stället. Går den inte att slå upp (ny session,
    eller ett sparat namn som inte längre finns efter en ombyggnad av trädet)
    faller vi tillbaka på FALLBACK_CTA_TITEL/-SIDA.
    """
    nasta = nasta_ovningsmodul(pabborjade)
    if nasta is not None and nasta.sida:
        return CtaMal(
            nasta.namn,
            nasta.sida,
            False,
            "Nästa i appen efter det du redan gjort.",
        )

    if senast_besokt:
        sida = sida_for_namn(senast_besokt)
        if sida:
            return CtaMal(
                senast_besokt,
                sida,
                True,
                "Du har varit inne i alla övningsmoduler. Fortsätt där du var.",
            )

    return CtaMal(
        FALLBACK_CTA_TITEL,
        FALLBACK_CTA_SIDA,
        False,
        "Appens första modul. Börja här om du är ny.",
    )
