"""Scenariogenerering och scenariohantering.

Ansvarar för de rättsfallsscenarier som modulsidorna övar på:
- Schemat (immutabla dataklasser) för case, flervalsfrågor och lagrumsjakt
- Inläsning av deterministiska basscenarier från data/scenarier/*.json med
  strikt strukturvalidering (fail fast vid trasig data)
- Validering: varje lagrum i facit, alternativ och lagrumsjakt måste kunna
  verifieras mot utils.lagrum-registret, annars flaggas modulen
- Kontroll att varje flervalsfråga har exakt ett rätt svar

LLM-generering av varierade scenarier och session_state-hantering byggs ut
i Dag 2; denna modul täcker den deterministiska kärnan som Dag 1 kräver.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from utils.lagrum import STATUS_VERIFIERAD, validera_lagrum

SCENARIER_DIR = Path(__file__).resolve().parent.parent / "data" / "scenarier"


# --- Schema (immutabelt) ----------------------------------------------------

@dataclass(frozen=True)
class Alternativ:
    """Ett svarsalternativ i en flervalsfråga."""

    text: str
    korrekt: bool
    forklaring: str
    lagrum: str | None = None


@dataclass(frozen=True)
class Flervalsfraga:
    """En flervalsfråga med deterministiskt facit."""

    id: str
    fraga: str
    alternativ: tuple[Alternativ, ...]


@dataclass(frozen=True)
class CaseFacit:
    """RNTS-facit för ett rättsfall."""

    rattsfraga: str
    lagrum: tuple[str, ...]
    tillampningspunkter: tuple[str, ...]
    slutsats: str


@dataclass(frozen=True)
class Case:
    """Ett rättsfall (scenario i löptext) med RNTS-facit."""

    id: str
    rubrik: str
    svarighetsgrad: str
    uppskattad_tid_min: int
    scenariotext: str
    facit: CaseFacit


@dataclass(frozen=True)
class Lagrumsjakt:
    """En lagrumsjaktfråga: hitta rätt lagrum för en situation."""

    id: str
    situation: str
    facit_lagrum: tuple[str, ...]
    ledtrad: str = ""


@dataclass(frozen=True)
class Modulscenarier:
    """Allt övningsinnehåll för en modul.

    ``ingress`` är en valfri mening om just den här modulen, som modulsidans
    hero visar. Saknas den faller sidan tillbaka på en generell formulering.
    Fältet är valfritt så att befintliga scenariofiler läses oförändrat.
    """

    modul: str
    case: tuple[Case, ...]
    flervalsfragor: tuple[Flervalsfraga, ...]
    lagrumsjakt: tuple[Lagrumsjakt, ...]
    ingress: str = ""


# --- Inläsning --------------------------------------------------------------

def _krav(villkor: bool, meddelande: str) -> None:
    """Fail fast: kasta ValueError om ett strukturkrav inte är uppfyllt."""
    if not villkor:
        raise ValueError(meddelande)


def _bygg_case(rad: dict) -> Case:
    _krav(isinstance(rad, dict), f"Case måste vara ett objekt: {rad!r}")
    facit = rad.get("facit", {})
    _krav(isinstance(facit, dict), f"Case {rad.get('id')!r} saknar facit-objekt.")
    return Case(
        id=str(rad["id"]),
        rubrik=str(rad["rubrik"]),
        svarighetsgrad=str(rad.get("svarighetsgrad", "grund")),
        uppskattad_tid_min=int(rad.get("uppskattad_tid_min", 10)),
        scenariotext=str(rad["scenariotext"]),
        facit=CaseFacit(
            rattsfraga=str(facit["rattsfraga"]),
            lagrum=tuple(str(x) for x in facit.get("lagrum", [])),
            tillampningspunkter=tuple(
                str(x) for x in facit.get("tillampningspunkter", [])
            ),
            slutsats=str(facit["slutsats"]),
        ),
    )


def bygg_case_fran_dict(rad: dict) -> Case:
    """Publik case-byggare med samma strukturvalidering som filinläsningen.

    Används av utils.generator för att coerca ett LLM-genererat JSON-scenario
    till ett Case (och därmed återanvända befintlig validering och fail fast).
    Kastar ValueError/KeyError vid trasig struktur.
    """
    return _bygg_case(rad)


def _bygg_fraga(rad: dict) -> Flervalsfraga:
    _krav(isinstance(rad, dict), f"Fråga måste vara ett objekt: {rad!r}")
    alternativ = tuple(
        Alternativ(
            text=str(a["text"]),
            korrekt=bool(a.get("korrekt", False)),
            forklaring=str(a.get("forklaring", "")),
            lagrum=(str(a["lagrum"]) if a.get("lagrum") else None),
        )
        for a in rad.get("alternativ", [])
    )
    _krav(len(alternativ) >= 2, f"Fråga {rad.get('id')!r} behöver minst två alternativ.")
    return Flervalsfraga(id=str(rad["id"]), fraga=str(rad["fraga"]), alternativ=alternativ)


def _bygg_lagrumsjakt(rad: dict) -> Lagrumsjakt:
    _krav(isinstance(rad, dict), f"Lagrumsjakt måste vara ett objekt: {rad!r}")
    return Lagrumsjakt(
        id=str(rad["id"]),
        situation=str(rad["situation"]),
        facit_lagrum=tuple(str(x) for x in rad.get("facit_lagrum", [])),
        ledtrad=str(rad.get("ledtrad", "")),
    )


def ladda_fil(path: Path) -> Modulscenarier:
    """Läs en scenariofil och bygg en validerad Modulscenarier."""
    _krav(path.exists(), f"Scenariofilen saknas: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    _krav(isinstance(data, dict), f"Scenariofilen {path} måste innehålla ett objekt.")

    ingress = data.get("ingress", "")
    _krav(
        isinstance(ingress, str),
        f"Fältet 'ingress' i {path} måste vara en sträng, inte {type(ingress).__name__}.",
    )

    return Modulscenarier(
        modul=str(data.get("modul", path.stem)),
        case=tuple(_bygg_case(c) for c in data.get("case", [])),
        flervalsfragor=tuple(_bygg_fraga(q) for q in data.get("flervalsfragor", [])),
        lagrumsjakt=tuple(_bygg_lagrumsjakt(lj) for lj in data.get("lagrumsjakt", [])),
        ingress=ingress,
    )


def ladda_modul(namn: str) -> Modulscenarier:
    """Läs en modul via filnamn utan suffix, t.ex. 'avtalsratt'."""
    return ladda_fil(SCENARIER_DIR / f"{namn}.json")


def lista_moduler() -> tuple[str, ...]:
    """Alla scenariofiler i data/scenarier (utan suffix)."""
    return tuple(sorted(p.stem for p in SCENARIER_DIR.glob("*.json")))


# --- Validering -------------------------------------------------------------

def alla_lagrum(modul: Modulscenarier) -> tuple[str, ...]:
    """Samla varje lagrumsreferens i modulen (facit, alternativ, jakt)."""
    refs: list[str] = []
    for c in modul.case:
        refs.extend(c.facit.lagrum)
    for q in modul.flervalsfragor:
        refs.extend(a.lagrum for a in q.alternativ if a.lagrum)
    for lj in modul.lagrumsjakt:
        refs.extend(lj.facit_lagrum)
    return tuple(refs)


def ogiltiga_lagrum(modul: Modulscenarier) -> tuple[tuple[str, str], ...]:
    """Lagrum i modulen som inte verifieras mot registret, med sin status."""
    return tuple(
        (ref, status)
        for ref in alla_lagrum(modul)
        if (status := validera_lagrum(ref)) != STATUS_VERIFIERAD
    )


def fragor_utan_exakt_ett_ratt(modul: Modulscenarier) -> tuple[str, ...]:
    """Id:n för flervalsfrågor som inte har exakt ett rätt alternativ."""
    return tuple(
        q.id
        for q in modul.flervalsfragor
        if sum(1 for a in q.alternativ if a.korrekt) != 1
    )
