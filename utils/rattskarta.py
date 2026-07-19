"""Rättskartan: Obsidiankarta över det svenska rättssystemet.

Bygger en hierarkisk, hopfällbar och klickbar trädvy av rättssystemet som
huvudsida i det exporterade Obsidianvalvet, plus en not per rättsområde och
en not per lag. Trädet renderas med Obsidians callouts (färgkodade per
område, hopfällbara med "-") och wikilänkar (klickbara, med förhandsvisning
vid hovring via kärnpluginen Page preview).

Grundningsprincipen gäller även här: varje lag i data/rattssystem.json måste
finnas i lagrumsregistret (data/lagrum.json), annars vägrar inläsningen.
Namn och SFS-nummer hämtas alltid ur registret – de dupliceras aldrig i
kartdatat. Ren modul utan Streamlit-beroende.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

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


# --- Datamodell (immutabel) ---------------------------------------------------

@dataclass(frozen=True)
class LagPost:
    """En lag i kartan: kursens förkortning plus kartans pedagogiska texter."""

    forkortning: str
    beskrivning: str
    nar: str
    relaterade: tuple[str, ...]


@dataclass(frozen=True)
class Underomrade:
    """Ett underområde (t.ex. Avtalsrätt) med sina lagar."""

    id: str
    namn: str
    beskrivning: str
    nar: str
    lagar: tuple[LagPost, ...]


@dataclass(frozen=True)
class Omrade:
    """Ett toppområde (t.ex. Civilrätt) med callout-färg och underområden."""

    id: str
    namn: str
    farg: str
    beskrivning: str
    nar: str
    underomraden: tuple[Underomrade, ...]


# --- Inläsning med grundningsvalidering ----------------------------------------

def _bygg_lagpost(rad: dict) -> LagPost:
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
            "lagrumsregistret – kartan får aldrig peka på okända lagar."
        )
    for rel in lag.relaterade:
        if rel not in register:
            raise ValueError(
                f"{lag.forkortning} relaterar till okänd lag {rel!r}."
            )
    return lag


@lru_cache(maxsize=1)
def ladda_rattssystem() -> tuple[Omrade, ...]:
    """Läs, validera och cachea rättssystemkartan. Fail fast vid fel data."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Hittar inte rättssystemdatat: {DATA_PATH}")
    rad = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    omraden = []
    for o in rad.get("omraden", ()):
        farg = str(o["farg"])
        if farg not in _TILLATNA_FARGER:
            raise ValueError(
                f"Området {o['namn']!r} har okänd callout-färg {farg!r}. "
                f"Tillåtna: {sorted(_TILLATNA_FARGER)}"
            )
        omraden.append(
            Omrade(
                id=str(o["id"]),
                namn=str(o["namn"]),
                farg=farg,
                beskrivning=str(o["beskrivning"]),
                nar=str(o["nar"]),
                underomraden=tuple(
                    Underomrade(
                        id=str(u["id"]),
                        namn=str(u["namn"]),
                        beskrivning=str(u["beskrivning"]),
                        nar=str(u["nar"]),
                        lagar=tuple(_bygg_lagpost(lag) for lag in u.get("lagar", ())),
                    )
                    for u in o.get("underomraden", ())
                ),
            )
        )
    if not omraden:
        raise ValueError("Rättssystemdatat innehåller inga områden.")
    return tuple(omraden)


def _lagindex() -> dict[str, tuple[LagPost, Omrade, Underomrade]]:
    """Index förkortning -> (lagpost, område, underområde) för notbyggarna."""
    index: dict[str, tuple[LagPost, Omrade, Underomrade]] = {}
    for omrade in ladda_rattssystem():
        for under in omrade.underomraden:
            for lag in under.lagar:
                index.setdefault(lag.forkortning, (lag, omrade, under))
    return index


# --- Notbyggare -----------------------------------------------------------------

def _frontmatter(rader: dict[str, str], taggar: tuple[str, ...]) -> str:
    ut = ["---"]
    ut += [f'{nyckel}: "{varde}"' for nyckel, varde in rader.items()]
    ut.append("taggar:")
    ut.extend(f"  - {t}" for t in taggar)
    ut.append("---")
    return "\n".join(ut)


def lagnot(forkortning: str) -> str:
    """Bygg noten för en lag: vad den täcker, när den övervägs, relaterat.

    KeyError om lagen inte finns i kartan (och därmed i registret).
    """
    lag, omrade, under = _lagindex()[forkortning]
    register = lagrum_register()
    info = register[forkortning]

    frontmatter = _frontmatter(
        {
            "lag": info.namn,
            "sfs": info.sfs,
            "område": f"{omrade.namn} · {under.namn}",
            "beskrivning": lag.beskrivning,
        },
        taggar=("juridik/lag", f"juridik/omrade/{omrade.id}"),
    )

    rader = [
        frontmatter,
        "",
        f"# {forkortning} – {info.namn}",
        "",
        f"> [!{omrade.farg}] I korthet",
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
            rader.append(f"- [[{rel}]] – {rel_info.namn}")
        rader.append("")
    rader += [
        "## Läs lagen",
        "",
        f"[Öppna {forkortning} på lagen.nu](https://lagen.nu/{info.sfs})",
        "",
        f"Del av [[{omrade.namn}#{under.namn}|{under.namn}]] "
        f"i [[{omrade.namn}]] · tillbaka till [[Rättskartan]].",
        "",
        "---",
        "",
        _DISCLAIMER,
        "",
    ]
    return "\n".join(rader)


def omradesnot(omrade: Omrade) -> str:
    """Bygg noten för ett rättsområde med underområdena som rubriker.

    Rubrikerna gör att kartan kan djuplänka med [[Område#Underområde]].
    """
    frontmatter = _frontmatter(
        {"område": omrade.namn, "beskrivning": omrade.beskrivning},
        taggar=("juridik/omrade", f"juridik/omrade/{omrade.id}"),
    )
    rader = [
        frontmatter,
        "",
        f"# {omrade.namn}",
        "",
        omrade.beskrivning,
        "",
        f"**När hamnar ett fall här?** {omrade.nar}",
        "",
    ]
    for under in omrade.underomraden:
        rader += [
            f"## {under.namn}",
            "",
            under.beskrivning,
            "",
            f"**När:** {under.nar}",
            "",
        ]
        if under.lagar:
            for lag in under.lagar:
                rader.append(f"- [[{lag.forkortning}]] – {lag.beskrivning}")
        else:
            rader.append("*Inga lagar ur kursens lagrumslista i detta underområde.*")
        rader.append("")
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
    ("Skilsmässa eller separation – vad ska delas?", "[[ÄktB]] eller [[SamboL]]"),
    ("Dödsfall – vem ärver och vad säger testamentet?", "[[ÄB]]"),
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


def _tradgren(omrade: Omrade) -> list[str]:
    """Rendera ett toppområde som hopfällbar, färgkodad callout-gren."""
    rader = [
        f"> [!{omrade.farg}]- **[[{omrade.namn}]]** — {omrade.beskrivning}",
        f"> *När:* {omrade.nar}",
        ">",
    ]
    for under in omrade.underomraden:
        lank = f"[[{omrade.namn}#{under.namn}|{under.namn}]]"
        rader.append(f"> > [!{omrade.farg}]- **{lank}** — {under.beskrivning}")
        rader.append(f"> > *När:* {under.nar}")
        if under.lagar:
            rader.append("> >")
            for lag in under.lagar:
                rader.append(
                    f"> > - [[{lag.forkortning}]] — {lag.beskrivning} "
                    f"*När:* {lag.nar}"
                )
        rader.append(">")
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
        "# Rättskartan – det svenska rättssystemet",
        "",
        "Svensk rätt delas traditionellt i **civilrätt** (förhållanden mellan "
        "enskilda) och **offentlig rätt** (förhållandet mellan enskilda och det "
        "allmänna, däribland straffrätten). Process- och exekutionsrätten styr "
        "hur anspråken prövas och tvingas igenom. Kartan nedan visar hur "
        "områdena hänger ihop, vilka lagar som bär varje område och när de ska "
        "övervägas i ett fall.",
        "",
        "> [!question]- Så använder du kartan",
        "> - **Fäll ut** en gren genom att klicka på pilen i rutans vänsterkant.",
        "> - **Klicka** på en länk för att öppna områdes- eller lagnoten.",
        "> - **Hovra** över en länk för en förhandsvisning – aktivera "
        "kärnpluginen *Sidförhandsvisning* (Page preview) i Obsidian.",
        "> - **Färgerna** skiljer områdena åt: blå = civilrätt, turkos = familj "
        "och arv, orange = straffrätt, lila = process och exekution, grå = "
        "offentlig rätt i övrigt.",
        "> - Grafvyn (Ctrl/Cmd + G) visar samma karta som nätverk, tillsammans "
        "med dina egna rättsfallsnoter.",
        "",
        "## Kartan",
        "",
    ]
    for omrade in ladda_rattssystem():
        rader += _tradgren(omrade)
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
        "Fler än en lag kan vara tillämplig samtidigt – ett avskedande kan "
        "t.ex. väcka både [[LAS]]-frågor och skadeståndsfrågor enligt [[SkL]]. "
        "Följ länkarna *Relaterade lagar* i varje lagnot för att se kopplingarna.",
        "",
        "---",
        "",
        _DISCLAIMER,
        "",
    ]
    return "\n".join(rader)


# --- Filpaket för valvbyggaren ---------------------------------------------------

def rattskarta_filer() -> dict[str, str]:
    """Alla kartfiler som {sökväg i valvet: markdown}."""
    filer: dict[str, str] = {"Juridik/Rättskartan.md": rattskarta_not()}
    for omrade in ladda_rattssystem():
        filer[f"Juridik/Rättssystemet/{omrade.namn}.md"] = omradesnot(omrade)
    for forkortning in _lagindex():
        filer[f"Juridik/Lagar/{forkortning}.md"] = lagnot(forkortning)
    return filer
