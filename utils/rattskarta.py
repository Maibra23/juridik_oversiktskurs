"""Rättskartan: doktrinär, rekursiv karta över det svenska rättssystemet.

Läser data/rattssystem.json som ett rekursivt träd av *grenar*. Trädet följer
rättens systematik: offentlig rätt och civilrätt, där civilrätten delas i
förmögenhetsrätt (obligationsrätt/sakrätt), familjerätt, associationsrätt och
fastighetsrätt. Varje gren har antingen undergrenar eller lagar (löv).

Modulen driver både appens taxonomigraf/rättskartesida (utils.rattssystem_graf,
utils.taxonomi_ui) och Obsidian-exportens rättskarta, så att de två vyerna aldrig
kan glida isär.

Grundningsprincipen gäller: varje lag i data/rattssystem.json måste finnas i
lagrumsregistret (data/lagrum.json), annars vägrar inläsningen. Namn och SFS
hämtas alltid ur registret och dupliceras aldrig i kartdatat. Ren modul utan
Streamlit-beroende.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Iterator

from utils.lagrum import lagrum_register

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "rattssystem.json"

# Callouttyper som Obsidian färgkodar olika; kartdatat får bara använda dessa.
_TILLATNA_FARGER = frozenset(
    {"note", "abstract", "info", "todo", "tip", "success", "question",
     "warning", "failure", "danger", "bug", "example", "quote"}
)

_DISCLAIMER = (
    "Kartan är studieunderlag från ett övningsverktyg och utgör inte "
    "juridisk rådgivning."
)


# --- Datamodell (immutabel, rekursiv) ----------------------------------------

@dataclass(frozen=True)
class LagPost:
    """En lag i kartan: kursens förkortning plus kartans pedagogiska texter.

    ``ar_referens`` skiljer kurslagar (de 21 i lagrumsregistret, som rättningen
    graderar) från referenslagar: kartnoder som ger överblick över svensk rätt
    men står utanför kursen. En referenslag bär sitt ``namn`` och ``sfs`` inline
    (den finns inte i registret att hämta dem ur) och rättningen ser den aldrig.
    """

    forkortning: str
    beskrivning: str
    nar: str
    relaterade: tuple[str, ...]
    ar_referens: bool = False
    namn: str | None = None
    sfs: str | None = None
    # Färdig klicklänk för referenslagar. Lagen.nu för svenska SFS, men EU-rätt
    # ligger på EUR-Lex, så länken kan sättas explicit i stället för via SFS.
    url: str | None = None


@dataclass(frozen=True)
class Gren:
    """En nod i rättssystemsträdet.

    En gren har ANTINGEN undergrenar (``grenar``) ELLER lagar (``lagar``, ett
    löv). ``farg`` ärvs från toppgrenen och färgkodar hela grenen. ``toppgren``
    är id:t på den toppgren (offentlig_ratt/civilratt) noden hör till, vilket
    driver appens färgläggning.
    """

    id: str
    namn: str
    beskrivning: str
    nar: str
    farg: str
    toppgren: str
    grenar: tuple["Gren", ...] = ()
    lagar: tuple[LagPost, ...] = field(default_factory=tuple)

    @property
    def ar_lov(self) -> bool:
        """True om grenen bär lagar i stället för undergrenar."""
        return not self.grenar


# --- Inläsning med grundningsvalidering ---------------------------------------

def _bygg_referenslag(rad: dict) -> LagPost:
    """Bygg en referenslag: kartnod utanför kursregistret, med inline namn/SFS.

    Ingen registerspärr (referenslagen finns per definition inte i registret),
    men namn och SFS är obligatoriska eftersom de driver etikett och lagen.nu-
    länk som annars hade hämtats ur registret.
    """
    for falt in ("forkortning", "namn", "beskrivning"):
        if not str(rad.get(falt, "")).strip():
            raise ValueError(
                f"Referenslagen saknar obligatoriskt fält {falt!r}: {rad!r}"
            )
    sfs = str(rad.get("sfs", "")).strip()
    url = str(rad.get("url", "")).strip()
    if not sfs and not url:
        raise ValueError(
            f"Referenslagen {rad['forkortning']!r} behöver antingen 'sfs' "
            "(lagen.nu) eller en explicit 'url'."
        )
    return LagPost(
        forkortning=str(rad["forkortning"]),
        beskrivning=str(rad["beskrivning"]),
        nar=str(rad.get("nar", "")),
        relaterade=(),
        ar_referens=True,
        namn=str(rad["namn"]),
        sfs=sfs or None,
        url=url or f"https://lagen.nu/{sfs}",
    )


def _bygg_lagpost(rad: dict) -> LagPost:
    if rad.get("referens"):
        return _bygg_referenslag(rad)
    lag = LagPost(
        forkortning=str(rad["forkortning"]),
        beskrivning=str(rad["beskrivning"]),
        nar=str(rad["nar"]),
        relaterade=tuple(str(r) for r in rad.get("relaterade", ())),
    )
    register = lagrum_register()
    if lag.forkortning not in register:
        raise ValueError(
            f"Rättskartan nämner {lag.forkortning!r} som inte finns i "
            "lagrumsregistret. Kartan får aldrig peka på okända lagar."
        )
    for rel in lag.relaterade:
        if rel not in register:
            raise ValueError(
                f"{lag.forkortning} relaterar till okänd lag {rel!r}."
            )
    return lag


def _bygg_gren(rad: dict, farg: str, toppgren: str) -> Gren:
    """Bygg en gren rekursivt och ärv färg och toppgren nedåt."""
    har_grenar = "grenar" in rad
    har_lagar = "lagar" in rad
    if har_grenar == har_lagar:
        raise ValueError(
            f"Grenen {rad.get('id')!r} måste ha antingen 'grenar' eller 'lagar', "
            "inte båda och inte ingetdera."
        )
    grenar = tuple(
        _bygg_gren(barn, farg, toppgren) for barn in rad.get("grenar", ())
    )
    lagar = tuple(_bygg_lagpost(lag) for lag in rad.get("lagar", ()))
    return Gren(
        id=str(rad["id"]),
        namn=str(rad["namn"]),
        beskrivning=str(rad["beskrivning"]),
        nar=str(rad.get("nar", "")),
        farg=farg,
        toppgren=toppgren,
        grenar=grenar,
        lagar=lagar,
    )


@lru_cache(maxsize=1)
def ladda_rattssystem() -> tuple[Gren, ...]:
    """Läs, validera och cachea rättssystemsträdet. Fail fast vid fel data.

    Returnerar toppgrenarna (offentlig rätt, civilrätt) i dispositionsordning.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Hittar inte rättssystemdatat: {DATA_PATH}")
    rad = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    toppgrenar = rad.get("grenar")
    if not toppgrenar:
        raise ValueError("data/rattssystem.json saknar nyckeln 'grenar'.")

    grenar: list[Gren] = []
    for topp in toppgrenar:
        farg = str(topp["farg"])
        if farg not in _TILLATNA_FARGER:
            raise ValueError(
                f"Toppgrenen {topp['namn']!r} har okänd callout-färg {farg!r}. "
                f"Tillåtna: {sorted(_TILLATNA_FARGER)}"
            )
        grenar.append(_bygg_gren(topp, farg, str(topp["id"])))

    _validera_unika_id(grenar)
    return tuple(grenar)


def _validera_unika_id(grenar: tuple[Gren, ...] | list[Gren]) -> None:
    """Fail fast om samma gren-id förekommer flera gånger i trädet."""
    sedda: set[str] = set()
    for gren in _alla_grenar(grenar):
        if gren.id in sedda:
            raise ValueError(f"Dubblerat gren-id i rättssystemet: {gren.id!r}")
        sedda.add(gren.id)


def _alla_grenar(grenar: tuple[Gren, ...] | list[Gren]) -> Iterator[Gren]:
    """Gå igenom trädet i förhandsordning och ge varje gren."""
    for gren in grenar:
        yield gren
        yield from _alla_grenar(gren.grenar)


def toppgrenar() -> tuple[Gren, ...]:
    """Rättssystemets toppgrenar (offentlig rätt, civilrätt)."""
    return ladda_rattssystem()


def delomraden() -> tuple[Gren, ...]:
    """Alla löv-grenar (de som bär lagar), i trädets ordning.

    Det här är nivån som data/nyckelbegrepp.json knyter begrepp till, så id:na
    är stabila delar av kontraktet mot begreppsdatat.
    """
    return tuple(gren for gren in _alla_grenar(ladda_rattssystem()) if gren.ar_lov)


def delomraden_med_vag() -> tuple[tuple[tuple[str, ...], Gren], ...]:
    """Alla löv-grenar med sin brödsmula (namnen på grenarna ovanför).

    Ger t.ex. (("Civilrätt", "Förmögenhetsrätt", "Obligationsrätt"), <köp-lövet>)
    så att sidan kan visa var i doktrinen ett delområde hör hemma.
    """
    ut: list[tuple[tuple[str, ...], Gren]] = []

    def _walk(gren: Gren, vag: tuple[str, ...]) -> None:
        if gren.ar_lov:
            ut.append((vag, gren))
        else:
            for barn in gren.grenar:
                _walk(barn, vag + (gren.namn,))

    for topp in ladda_rattssystem():
        _walk(topp, ())
    return tuple(ut)


def hitta_gren(gren_id: str) -> Gren | None:
    """Slå upp en gren på id, eller None om den saknas."""
    for gren in _alla_grenar(ladda_rattssystem()):
        if gren.id == gren_id:
            return gren
    return None


def _lagindex() -> dict[str, tuple[LagPost, Gren]]:
    """Index förkortning -> (lagpost, löv-gren) för notbyggarna.

    Referenslagar utelämnas: de står utanför kursregistret och saknar
    kursavsnitt, så de får ingen egen Obsidian-not — de finns bara som
    överblick på kartan.
    """
    index: dict[str, tuple[LagPost, Gren]] = {}
    for lov in delomraden():
        for lag in lov.lagar:
            if lag.ar_referens:
                continue
            index.setdefault(lag.forkortning, (lag, lov))
    return index


# --- Notbyggare (Obsidian-export) --------------------------------------------

def _frontmatter(rader: dict[str, str], taggar: tuple[str, ...]) -> str:
    ut = ["---"]
    ut += [f'{nyckel}: "{varde}"' for nyckel, varde in rader.items()]
    ut.append("taggar:")
    ut.extend(f"  - {t}" for t in taggar)
    ut.append("---")
    return "\n".join(ut)


def _lagrad(lag: LagPost, inryck: str = "", med_nar: bool = False) -> str:
    """En listrad för en lag i en not.

    Kurslagar wikilänkas till sin egen not ([[AvtL]]). Referenslagar saknar not
    (de står utanför kursen) och länkas i stället direkt till lagen.nu, så att
    valvet aldrig får en bruten wikilänk.
    """
    if lag.ar_referens:
        return (
            f"{inryck}- {lag.forkortning} "
            f"([{lag.namn}]({lag.url})): {lag.beskrivning}"
        )
    rad = f"{inryck}- [[{lag.forkortning}]]: {lag.beskrivning}"
    if med_nar and lag.nar:
        rad += f" *När:* {lag.nar}"
    return rad


def lagnot(forkortning: str) -> str:
    """Bygg noten för en lag: vad den täcker, när den övervägs, relaterat.

    KeyError om lagen inte finns i kartan (och därmed i registret).
    """
    lag, lov = _lagindex()[forkortning]
    register = lagrum_register()
    info = register[forkortning]

    frontmatter = _frontmatter(
        {
            "lag": info.namn,
            "sfs": info.sfs,
            "område": lov.namn,
            "beskrivning": lag.beskrivning,
        },
        taggar=("juridik/lag", f"juridik/omrade/{lov.id}"),
    )

    rader = [
        frontmatter,
        "",
        f"# {forkortning}: {info.namn}",
        "",
        f"> [!{lov.farg}] I korthet",
        f"> {lag.beskrivning}",
        "",
        "## När ska lagen övervägas?",
        "",
        lag.nar,
        "",
    ]
    if lag.relaterade:
        rader += ["## Relaterade lagar", ""]
        for rel in lag.relaterade:
            rel_info = register[rel]
            rader.append(f"- [[{rel}]]: {rel_info.namn}")
        rader.append("")
    toppnamn = _toppnamn(lov.toppgren)
    rader += [
        "## Läs lagen",
        "",
        f"[Öppna {forkortning} på lagen.nu](https://lagen.nu/{info.sfs})",
        "",
        f"Del av [[{toppnamn}#{lov.namn}|{lov.namn}]] · tillbaka till "
        "[[Rättskartan]].",
        "",
        "---",
        "",
        _DISCLAIMER,
        "",
    ]
    return "\n".join(rader)


def _toppnamn(toppgren_id: str) -> str:
    """Namnet på en toppgren, för deep-länkar in i dess note."""
    for topp in ladda_rattssystem():
        if topp.id == toppgren_id:
            return topp.namn
    return toppgren_id


def _gren_rubriker(gren: Gren, niva: int, rader: list[str]) -> None:
    """Rendera en gren och dess undergrenar som rubriker i en områdesnot."""
    prefix = "#" * min(niva, 6)
    rader += [f"{prefix} {gren.namn}", "", gren.beskrivning, ""]
    if gren.nar:
        rader += [f"**När:** {gren.nar}", ""]
    if gren.ar_lov:
        if gren.lagar:
            for lag in gren.lagar:
                rader.append(_lagrad(lag))
        else:
            rader.append("*Inga lagar ur kursens lagrumslista i denna gren.*")
        rader.append("")
    else:
        for barn in gren.grenar:
            _gren_rubriker(barn, niva + 1, rader)


def omradesnot(gren: Gren) -> str:
    """Bygg noten för en toppgren med hela dess subträd som rubriker."""
    frontmatter = _frontmatter(
        {"område": gren.namn, "beskrivning": gren.beskrivning},
        taggar=("juridik/omrade", f"juridik/omrade/{gren.id}"),
    )
    rader = [
        frontmatter,
        "",
        f"# {gren.namn}",
        "",
        gren.beskrivning,
        "",
    ]
    if gren.nar:
        rader += [f"**När hamnar ett fall här?** {gren.nar}", ""]
    for barn in gren.grenar:
        _gren_rubriker(barn, 2, rader)
    rader += ["---", "", "Tillbaka till [[Rättskartan]].", "", _DISCLAIMER, ""]
    return "\n".join(rader)


# Snabbguide fall -> lag på kartsidan. Deterministisk och grundad: endast
# förkortningar ur registret (valideras i testerna via kartans lagindex).
_FALLTYPSGUIDE: tuple[tuple[str, str], ...] = (
    ("Privatperson har köpt en felaktig vara av ett företag", "[[KKöpL]]"),
    ("Köp mellan företag eller mellan privatpersoner", "[[KöpL]]"),
    ("Oklart om ett bindande avtal alls har ingåtts", "[[AvtL]]"),
    ("Person eller egendom har skadats utan avtalsband", "[[SkL]]"),
    ("Någon har sagts upp eller avskedats", "[[LAS]]"),
    ("Skilsmässa eller separation: vad ska delas?", "[[ÄktB]] eller [[SamboL]]"),
    ("Dödsfall: vem ärver och vad säger testamentet?", "[[ÄB]]"),
    ("Misstanke om brott", "[[BrB]]"),
    ("Dom finns men gäldenären betalar inte", "[[UB]]"),
    ("Företaget kan inte betala sina skulder", "[[KonkL]]"),
    ("Vem svarar för bolagets skulder?", "[[ABL]] eller [[HBL]]"),
    ("Köp eller fel som rör en fastighet", "[[JB]]"),
    ("Ett skuldebrev har överlåtits", "[[SkbrL]]"),
    ("Vilseledande reklam eller aggressiva säljmetoder", "[[MFL]]"),
    ("En omyndig har ingått ett avtal", "[[FB]]"),
    ("Hur och var prövas tvisten?", "[[RB]]"),
)


# Sökord per falltyp. Situationstexterna är skrivna som meningar ("Någon har
# sagts upp eller avskedats"), medan studenten söker på grundformen
# ("uppsagd", "arv", "konkurs"). Ren delsträngsmatchning missar därför de
# mest naturliga sökningarna, och därför bär varje rad sina egna sökord.
# Vault-markdownen använder _FALLTYPSGUIDE direkt och påverkas inte.
_SOKORD: dict[str, str] = {
    "Privatperson har köpt en felaktig vara av ett företag":
        "konsument konsumentköp fel reklamation garanti retur vara handla",
    "Köp mellan företag eller mellan privatpersoner":
        "köp köplag näringsidkare begagnat blocket handel avtal vara",
    "Oklart om ett bindande avtal alls har ingåtts":
        "avtal anbud accept offert bindande överenskommelse muntligt",
    "Person eller egendom har skadats utan avtalsband":
        "skada skadestånd skadad olycka vårdslös oaktsam ersättning",
    "Någon har sagts upp eller avskedats":
        "uppsagd uppsägning avsked avskedad sparken anställning arbete "
        "arbetsbrist turordning jobb",
    "Skilsmässa eller separation: vad ska delas?":
        "skilsmässa separation bodelning gift sambo makar delning "
        "giftorätt äktenskap",
    "Dödsfall: vem ärver och vad säger testamentet?":
        "arv ärva arvinge dödsfall testamente laglott bröstarvinge "
        "kvarlåtenskap död",
    "Misstanke om brott": "brott straff åtal misstänkt stöld misshandel "
        "bedrägeri uppsåt polis brottslig",
    "Dom finns men gäldenären betalar inte":
        "utmätning kronofogden verkställighet indrivning skuld obetald "
        "exekutionstitel betalningsföreläggande",
    "Företaget kan inte betala sina skulder":
        "konkurs obestånd insolvent betalningsoförmåga återvinning "
        "skulder likvidation",
    "Vem svarar för bolagets skulder?":
        "bolag aktiebolag handelsbolag ansvar personligt betalningsansvar "
        "ägare styrelse företagsform",
    "Köp eller fel som rör en fastighet":
        "fastighet hus tomt husköp dolt fel besiktning undersökningsplikt "
        "tillbehör mark villa",
    "Ett skuldebrev har överlåtits":
        "skuldebrev fordran överlåtelse denuntiation löpande enkelt "
        "lån kredit invändning",
    "Vilseledande reklam eller aggressiva säljmetoder":
        "reklam marknadsföring vilseledande säljmetod telefonförsäljning "
        "konsumentskydd",
    "En omyndig har ingått ett avtal":
        "omyndig underårig barn minderårig ålder förmyndare "
        "rättshandlingsförmåga god man förvaltare",
    "Hur och var prövas tvisten?":
        "domstol tingsrätt process rättegång tvistemål brottmål forum "
        "bevisning rättegångskostnad stämning",
}


def falltypsguide() -> tuple[tuple[str, str, str], ...]:
    """Falltypsguiden som (situation, lag, sökord) utan wikilänkhakar.

    Publik ingång för appens Rättskarta-sida, så att den slipper importera
    den privata konstanten. Markdownbyggarna använder _FALLTYPSGUIDE direkt
    eftersom de vill ha wikilänkarna kvar.
    """
    return tuple(
        (
            situation,
            lag.replace("[[", "").replace("]]", ""),
            _SOKORD.get(situation, ""),
        )
        for situation, lag in _FALLTYPSGUIDE
    )


def _tradgren(gren: Gren, toppnamn: str | None = None, niva: int = 0) -> list[str]:
    """Rendera en gren rekursivt som hopfällbar, färgkodad callout.

    Callout-nivån (antal '>') följer djupet i trädet. Löv listar sina lagar.
    Toppgrenen länkar till sin egen note; undergrenar deep-länkar in i
    toppgrenens note via en rubrik (den enda note som faktiskt genereras).
    """
    if toppnamn is None:
        toppnamn = gren.namn
        lank = f"[[{gren.namn}]]"
    else:
        lank = f"[[{toppnamn}#{gren.namn}|{gren.namn}]]"

    inryck = "> " * (niva + 1)
    rader = [
        f"{inryck}[!{gren.farg}]- **{lank}**: {gren.beskrivning}",
    ]
    if gren.nar:
        rader.append(f"{inryck}*När:* {gren.nar}")
    if gren.ar_lov:
        if gren.lagar:
            rader.append(inryck.rstrip())
            for lag in gren.lagar:
                rader.append(_lagrad(lag, inryck, med_nar=True))
    else:
        for barn in gren.grenar:
            rader.extend(_tradgren(barn, toppnamn, niva + 1))
    return rader


def rattskarta_not() -> str:
    """Bygg kartsidan: översikt, hopfällbart färgkodat träd och falltypsguide."""
    frontmatter = _frontmatter(
        {
            "titel": "Rättskartan",
            "beskrivning": "Klickbar karta över det svenska rättssystemet",
        },
        taggar=("juridik", "juridik/rattskarta"),
    )
    rader = [
        frontmatter,
        "",
        "# Rättskartan: det svenska rättssystemet",
        "",
        "Svensk rätt delas i **offentlig rätt** (förhållandet mellan enskilda och "
        "det allmänna, däribland straffrätten och processrätten) och **civilrätt** "
        "(förhållanden mellan enskilda). Civilrätten delas i sin tur i "
        "förmögenhetsrätt (obligationsrätt och sakrätt), familjerätt, "
        "associationsrätt och fastighetsrätt. Kartan nedan visar hur grenarna "
        "hänger ihop, vilka lagar som bär varje gren och när de ska övervägas.",
        "",
        "> [!question]- Så använder du kartan",
        "> - **Fäll ut** en gren genom att klicka på pilen i rutans vänsterkant.",
        "> - **Klicka** på en länk för att öppna områdes- eller lagnoten.",
        "> - **Hovra** över en länk för en förhandsvisning. Aktivera "
        "kärnpluginen *Sidförhandsvisning* (Page preview) i Obsidian.",
        "> - **Färgerna** skiljer huvudgrenarna åt: blå = civilrätt, grå = "
        "offentlig rätt.",
        "> - Grafvyn (Ctrl/Cmd + G) visar samma karta som nätverk, tillsammans "
        "med dina egna rättsfallsnoter.",
        "",
        "## Kartan",
        "",
    ]

    for gren in ladda_rattssystem():
        rader.extend(_tradgren(gren))
        rader.append("")

    rader += [
        "## Vilken lag gäller för mitt fall?",
        "",
        "| Situationen | Börja här |",
        "| --- | --- |",
    ]
    rader += [f"| {situation} | {lag} |" for situation, lag in _FALLTYPSGUIDE]
    rader += [
        "",
        "Fler än en lag kan vara tillämplig samtidigt. Ett avskedande kan "
        "t.ex. väcka både [[LAS]]-frågor och skadeståndsfrågor enligt [[SkL]]. "
        "Följ länkarna *Relaterade lagar* i varje lagnot för att se kopplingarna.",
        "",
        "---",
        "",
        _DISCLAIMER,
        "",
    ]
    return "\n".join(rader)


# --- Filpaket för valvbyggaren -----------------------------------------------

def rattskarta_filer() -> dict[str, str]:
    """Alla kartfiler som {sökväg i valvet: markdown}."""
    filer: dict[str, str] = {"Juridik/Rättskartan.md": rattskarta_not()}
    for gren in ladda_rattssystem():
        filer[f"Juridik/Rättssystemet/{gren.namn}.md"] = omradesnot(gren)
    for forkortning in _lagindex():
        filer[f"Juridik/Lagar/{forkortning}.md"] = lagnot(forkortning)
    return filer
