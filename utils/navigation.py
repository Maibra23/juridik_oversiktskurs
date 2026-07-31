"""Navigeringsträdet: appens sidor ordnade efter svensk rätts systematik.

Sidopanelen speglar bokens disposition (Persson m.fl., Svensk juridik) i
stället för en platt lista av filer: offentlig rätt, civilrätt med
förmögenhetsrättens undergrenar, och straff- och processrätt.

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
from typing import Iterator, Union

ROT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Modul:
    """Ett löv i trädet: en modulsida, byggd eller planerad.

    ``sida`` är sökvägen relativt projektroten, t.ex. "sidor/2_Avtalsratt.py".
    None betyder att modulen är planerad men ännu inte byggd.
    """

    namn: str
    sida: str | None = None

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


# Trädet följer bokens avdelningar. Kapitelhänvisningarna i kommentarerna
# avser Persson m.fl., Svensk juridik.
NAV_TRAD: tuple[Grupp, ...] = (
    Grupp(
        "START OCH METOD",
        (
            Modul("Hem", "sidor/0_Hem.py"),
            Modul("Juridisk metod", "sidor/1_Juridisk_metod.py"),  # kap 1
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
            Grupp(
                "Personrätt",
                (Modul("Personrätt", "sidor/12_Personratt.py"),),  # kap 5
            ),
            Grupp(
                "Förmögenhetsrätt",
                (
                    Modul(
                        "Allmän förmögenhetsrätt",
                        "sidor/13_Allman_formogenhetsratt.py",
                    ),  # kap 6
                    Grupp(
                        "Kontraktsrätt",
                        (
                            Modul("Avtalsrätt", "sidor/2_Avtalsratt.py"),  # kap 7
                            Modul(
                                "Köp- och konsumenträtt",
                                "sidor/3_Kop_och_konsumentratt.py",
                            ),  # kap 8
                            Modul(
                                "Fastighetsrätt", "sidor/14_Fastighetsratt.py"
                            ),  # kap 9
                        ),
                    ),
                    Grupp(
                        "Ersättningsrätt",
                        (
                            Modul(
                                "Skadeståndsrätt", "sidor/4_Skadestandsratt.py"
                            ),  # kap 10
                        ),
                    ),
                    Grupp(
                        "Näringsrätt",
                        (
                            Modul("Arbetsrätt", "sidor/5_Arbetsratt.py"),  # kap 11
                            Modul(
                                "Associationsrätt", "sidor/6_Associationsratt.py"
                            ),  # kap 12
                        ),
                    ),
                    Grupp(
                        "Kredit- och obeståndsrätt",
                        (
                            Modul(
                                "Fordringsrätt", "sidor/15_Fordringsratt.py"
                            ),
                        ),  # kap 15-17
                    ),
                ),
            ),
            Grupp(
                "Familjerätt",
                (
                    Modul(
                        "Familje- och successionsrätt",
                        "sidor/7_Familje_och_arvsratt.py",
                    ),  # kap 18-21
                ),
            ),
        ),
    ),
    Grupp(
        "STRAFF- OCH PROCESSRÄTT",
        (
            Modul(
                "Straff- och processrätt", "sidor/8_Straff_och_processratt.py"
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
