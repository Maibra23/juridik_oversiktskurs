"""Obsidianexport: studentens analyser blir ett sammanlänkat kunskapsvalv.

Bygger en nedladdningsbar Obsidian-vault (zip) av studentens genomförda
RNTS-analyser. Varje lagrum blir en egen not så att Obsidians backlinks binder
ihop alla rättsfall där lagrummet tillämpats, och en repetitionssektion i
formatet ``fråga :: svar`` matar pluginen Spaced Repetition.

Modulen är ren (inget Streamlit-beroende i rapportbyggarna) och återanvänder
utils.lagrum för all kanonisering, verifiering och lagen.nu-länkning — ingen
regex eller URL-logik återuppfinns här. Endast session-state-hjälparna längst
ned kräver en Streamlit-kontext.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from io import BytesIO
from typing import Iterable, Mapping
from zipfile import ZipFile

from utils.lagrum import (
    LAGRUM_PATTERN,
    STATUS_VERIFIERAD,
    Lagrumsref,
    extrahera_lagrum,
    lagen_nu_url,
    lagrum_register,
    validera_lagrum,
)
from utils.scenarier import Case

DISCLAIMER = (
    "Detta valv är studieunderlag från ett övningsverktyg och utgör inte "
    "juridisk rådgivning. Alla scenarier är fiktiva."
)

# Obsidian förbjuder dessa tecken i notnamn. Paragraftecknet § och å/ä/ö är
# tillåtna och måste behållas — de är länknyckeln.
_FORBJUDNA_TECKEN = '*"\\/<>:|?#^[]'


# --- Datamodell -------------------------------------------------------------

@dataclass(frozen=True)
class CaseAnalys:
    """En genomförd rättsfallsanalys som ska exporteras till valvet."""

    modul: str
    case: Case
    svar: Mapping[str, str]


# --- Kanonisering och länkning ----------------------------------------------

def notnamn(text: str) -> str:
    """Sanera ett notnamn från Obsidians förbjudna filnamnstecken."""
    return "".join(c for c in text if c not in _FORBJUDNA_TECKEN).strip()


def _kanonisk_lagrum(ref: Lagrumsref) -> str:
    """Kanonisk visningsform för ett lagrum, delad av filnamn och wikilänk."""
    if ref.kapitel:
        return f"{ref.kapitel} kap. {ref.paragraf} § {ref.forkortning}"
    return f"{ref.paragraf} § {ref.forkortning}"


def _ref_fran_match(m: "object") -> Lagrumsref:
    return Lagrumsref(
        forkortning=m.group("forkortning"),  # type: ignore[attr-defined]
        paragraf=m.group("paragraf"),  # type: ignore[attr-defined]
        kapitel=m.group("kapitel"),  # type: ignore[attr-defined]
        paragraf_till=m.group("paragraf_till"),  # type: ignore[attr-defined]
        ra=m.group(0).strip(),  # type: ignore[attr-defined]
    )


def _wikilanka_text(text: str) -> str:
    """Skriv om varje lagrum i texten till en Obsidian-wikilänk [[kanonisk]]."""
    return LAGRUM_PATTERN.sub(
        lambda m: f"[[{_kanonisk_lagrum(_ref_fran_match(m))}]]", text or ""
    )


def _kanoniska_lagrum(text: str) -> tuple[str, ...]:
    """Alla lagrum i texten på kanonisk form, i ordning och utan dubbletter."""
    sedda: dict[str, None] = {}
    for m in LAGRUM_PATTERN.finditer(text or ""):
        sedda.setdefault(_kanonisk_lagrum(_ref_fran_match(m)), None)
    return tuple(sedda)


# --- Notbyggare (rena) ------------------------------------------------------

def _frontmatter(rader: Mapping[str, str], taggar: tuple[str, ...]) -> str:
    """Bygg ett YAML-frontmatterblock."""
    ut = ["---"]
    for nyckel, varde in rader.items():
        ut.append(f'{nyckel}: "{varde}"')
    ut.append("taggar:")
    ut.extend(f"  - {t}" for t in taggar)
    ut.append("---")
    return "\n".join(ut)


def lagrumsnot(ref: str) -> str:
    """Bygg en lagrumsnot med frontmatter, status och lagen.nu-länk."""
    traffar = extrahera_lagrum(ref)
    parsad = traffar[0] if traffar else None
    titel = _kanonisk_lagrum(parsad) if parsad else notnamn(ref)

    status = validera_lagrum(ref)
    url = lagen_nu_url(ref)
    lag = lagrum_register().get(parsad.forkortning) if parsad else None

    frontmatter = _frontmatter(
        {
            "lag": lag.namn if lag else "Okänd lag",
            "sfs": lag.sfs if lag else "",
            "status": status,
        },
        taggar=("juridik/lagrum",),
    )

    kropp = [frontmatter, "", f"# {titel}", ""]
    if status == STATUS_VERIFIERAD and url:
        kropp.append(f"Verifierat mot kursens lagrumsregister ({status}).")
        kropp.append("")
        kropp.append(f"[Öppna på lagen.nu]({url})")
    else:
        kropp.append(
            f"⚠️ Kunde inte verifieras mot kursens lagrumsregister (status {status}). "
            "Kontrollera lagrummet själv innan du litar på det."
        )
    kropp += ["", "---", "", DISCLAIMER, ""]
    return "\n".join(kropp)


def _rattsfall_kropp(analys: CaseAnalys) -> str:
    """Rå markdown (plain lagrum) för en rättsfallsnot, utan frontmatter."""
    case = analys.case
    facit = case.facit
    svar = analys.svar

    rader = [
        f"# {case.rubrik}",
        "",
        f"*Modul: {analys.modul} · svårighetsgrad: {case.svarighetsgrad}*",
        "",
        "## Scenario",
        "",
        case.scenariotext,
        "",
        "## Min RNTS-analys",
        "",
        f"**Rättsfrågan:** {svar.get('rattsfragan', '')}",
        "",
        f"**Norm:** {svar.get('norm', '')}",
        "",
        f"**Tillämpning:** {svar.get('tillampning', '')}",
        "",
        f"**Slutsats:** {svar.get('slutsats', '')}",
        "",
        "## Facit",
        "",
        f"**Rättsfrågan:** {facit.rattsfraga}",
        "",
        "**Tillämpliga lagrum:**",
    ]
    rader += [f"- {ref}" for ref in facit.lagrum]
    rader += ["", "**Tillämpning:**"]
    rader += [f"- {punkt}" for punkt in facit.tillampningspunkter]
    rader += [
        "",
        f"**Slutsats:** {facit.slutsats}",
        "",
        "## Repetition",
        "",
        "> [!note] Spaced Repetition",
        "",
        f"{facit.rattsfraga} :: {facit.slutsats} ({', '.join(facit.lagrum)})",
        "",
    ]
    return "\n".join(rader)


def rattsfallsnot(analys: CaseAnalys) -> str:
    """Bygg en rättsfallsnot: studentens RNTS-svar och facit med wikilänkar."""
    frontmatter = _frontmatter(
        {
            "modul": analys.modul,
            "case_id": analys.case.id,
            "svårighetsgrad": analys.case.svarighetsgrad,
        },
        taggar=("juridik/rattsfall",),
    )
    return frontmatter + "\n\n" + _wikilanka_text(_rattsfall_kropp(analys))


def _lagrum_i_analys(analys: CaseAnalys) -> tuple[str, ...]:
    """Kanoniska lagrum som förekommer i en analys (samma som wikilänkas)."""
    return _kanoniska_lagrum(_rattsfall_kropp(analys))


def modulnot(
    modul: str,
    rattsfall: tuple[str, ...],
    lagrum: tuple[str, ...],
) -> str:
    """Bygg en MOC-not (map of content) för en modul."""
    frontmatter = _frontmatter({"modul": modul}, taggar=("juridik/modul",))
    rader = [frontmatter, "", f"# {modul}", "", "## Rättsfall", ""]
    rader += [f"- [[{notnamn(r)}]]" for r in rattsfall] or ["Inga rättsfall ännu."]
    rader += ["", "## Lagrum", ""]
    rader += [f"- [[{notnamn(ref)}]]" for ref in lagrum] or ["Inga lagrum ännu."]
    rader += [""]
    return "\n".join(rader)


def _startnot(moduler: tuple[str, ...]) -> str:
    """Bygg valvets startnot (MOC över moduler och rättskartan)."""
    frontmatter = _frontmatter({"titel": "Juridik"}, taggar=("juridik",))
    rader = [
        frontmatter,
        "",
        "# Juridik – mitt kunskapsvalv",
        "",
        f"Exporterat {date.today().isoformat()} från Juridisk översiktskurs.",
        "",
        "## Rättskartan",
        "",
        "Börja i [[Rättskartan]] – en klickbar, hopfällbar karta över det "
        "svenska rättssystemet som visar vilka lagar som hör till vilket "
        "område och när de ska övervägas.",
        "",
        "## Moduler",
        "",
    ]
    rader += [f"- [[{notnamn(m)}]]" for m in moduler] or ["Inga moduler ännu."]
    rader += ["", "---", "", DISCLAIMER, ""]
    return "\n".join(rader)


# --- Valvbyggare ------------------------------------------------------------

def bygg_valv(poster: Iterable[CaseAnalys]) -> bytes:
    """Bygg en Obsidian-vault som zip-bytes av genomförda analyser.

    Struktur: ``Juridik/Start.md``, ``Juridik/Moduler/<modul>.md``,
    ``Juridik/Rattsfall/<rubrik>.md`` och ``Juridik/Lagrum/<lagrum>.md``.
    Lagrumsnoter skapas endast för lagrum som faktiskt refereras i fallen.
    """
    poster = tuple(poster)

    # Samla moduler, rättsfall per modul och lagrum per modul (i ordning).
    moduler: dict[str, None] = {}
    rattsfall_per_modul: dict[str, dict[str, None]] = {}
    lagrum_per_modul: dict[str, dict[str, None]] = {}
    alla_lagrum: dict[str, None] = {}

    filer: dict[str, str] = {}

    for analys in poster:
        modul = analys.modul
        moduler.setdefault(modul, None)
        rattsfall_per_modul.setdefault(modul, {})
        lagrum_per_modul.setdefault(modul, {})

        rubrik = analys.case.rubrik
        rattsfall_per_modul[modul].setdefault(rubrik, None)
        filer[f"Juridik/Rattsfall/{notnamn(rubrik)}.md"] = rattsfallsnot(analys)

        for ref in _lagrum_i_analys(analys):
            lagrum_per_modul[modul].setdefault(ref, None)
            alla_lagrum.setdefault(ref, None)

    for modul in moduler:
        filer[f"Juridik/Moduler/{notnamn(modul)}.md"] = modulnot(
            modul,
            tuple(rattsfall_per_modul[modul]),
            tuple(lagrum_per_modul[modul]),
        )

    for ref in alla_lagrum:
        filer[f"Juridik/Lagrum/{notnamn(ref)}.md"] = lagrumsnot(ref)

    # Rättskartan följer alltid med: karta, områdesnoter och lagnoter.
    from utils.rattskarta import rattskarta_filer

    filer.update(rattskarta_filer())
    filer["Juridik/Start.md"] = _startnot(tuple(moduler))

    buffert = BytesIO()
    with ZipFile(buffert, "w") as z:
        for namn, innehall in sorted(filer.items()):
            z.writestr(namn, innehall)
    return buffert.getvalue()


# --- Session-state-spårning -------------------------------------------------

_ANALYS_NYCKEL = "obsidian_analyser"


def registrera_case_analys(modul: str, case: Case, svar: Mapping[str, str]) -> None:
    """Lagra en genomförd RNTS-analys för Obsidianexport i session_state."""
    import streamlit as st

    try:
        bok = st.session_state.setdefault(_ANALYS_NYCKEL, {})
    except Exception:
        return
    # Immutabel kopia av svaren så senare redigeringar inte muterar posten.
    bok[(modul, case.id)] = CaseAnalys(modul=modul, case=case, svar=dict(svar))


def hamta_case_analyser() -> tuple[CaseAnalys, ...]:
    """Alla registrerade analyser som en immutabel tuple för valvbyggaren."""
    import streamlit as st

    try:
        bok = st.session_state.get(_ANALYS_NYCKEL, {})
    except Exception:
        return ()
    return tuple(bok.values())
