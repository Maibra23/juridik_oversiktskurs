"""Deterministisk rättning av quiz och lagrumsjakt.

All rättning här är deterministisk och kräver ALDRIG LLM: flervalsfrågor
rättas mot facit i scenariodata, lagrumsjakt rättas genom att parsa
studentens svar med utils.lagrum och jämföra mot facit-lagrummet.

Modulen delas i två lager:
- Rena rättningsfunktioner (ratta_flervalsfraga, ratta_lagrumsjakt) utan
  Streamlit-beroende, fullt enhetstestbara.
- Session-state-hjälpare (registrera_mc_svar, modulresultat) som lagrar
  poäng per modul för resultatpanelen och exporten (Dag 3).
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.lagrum import (
    STATUS_EJ_VALIDERBAR,
    Lagrumsref,
    extrahera_lagrum,
    validera_lagrum,
)
from utils.scenarier import Flervalsfraga, Lagrumsjakt

# --- Resultatmodeller (immutabla) -------------------------------------------


@dataclass(frozen=True)
class MCResultat:
    """Resultatet av att rätta en flervalsfråga."""

    korrekt: bool
    valt_index: int
    ratt_index: int
    forklaring: str


@dataclass(frozen=True)
class LagrumsjaktResultat:
    """Resultatet av att rätta en lagrumsjakt."""

    korrekt: bool
    status: str
    traffade: tuple[str, ...]
    saknade: tuple[str, ...]
    facit: tuple[str, ...]


# --- Rena rättningsfunktioner -----------------------------------------------


def ratt_alternativ_index(fraga: Flervalsfraga) -> int:
    """Index för det korrekta alternativet. Kräver exakt ett rätt svar."""
    ratta = [i for i, a in enumerate(fraga.alternativ) if a.korrekt]
    if len(ratta) != 1:
        raise ValueError(
            f"Fråga {fraga.id!r} måste ha exakt ett rätt alternativ, har {len(ratta)}."
        )
    return ratta[0]


def ratta_flervalsfraga(fraga: Flervalsfraga, valt_index: int) -> MCResultat:
    """Rätta ett flervalssvar deterministiskt mot facit."""
    if not 0 <= valt_index < len(fraga.alternativ):
        raise ValueError(
            f"valt_index {valt_index} utanför intervallet för fråga {fraga.id!r}."
        )
    ratt_index = ratt_alternativ_index(fraga)
    valt = fraga.alternativ[valt_index]
    return MCResultat(
        korrekt=(valt_index == ratt_index),
        valt_index=valt_index,
        ratt_index=ratt_index,
        forklaring=valt.forklaring,
    )


def _nyckel(ref: Lagrumsref) -> tuple[str, str | None, str]:
    """Kanonisk jämförelsenyckel (förkortning, kapitel, paragraf)."""
    return (ref.forkortning, ref.kapitel, ref.paragraf)


def _nycklar_ur(text: str) -> set[tuple[str, str | None, str]]:
    """Kanoniska nycklar för alla lagrum i en text."""
    return {_nyckel(ref) for ref in extrahera_lagrum(text)}


def ratta_lagrumsjakt(jakt: Lagrumsjakt, studentens_svar: str) -> LagrumsjaktResultat:
    """Rätta en lagrumsjakt deterministiskt: parsa svaret och jämför med facit.

    Korrekt = varje facit-lagrum återfinns i studentens svar (ordningsoberoende).
    ``status`` speglar valideringen av studentens svar mot registret så att UI:t
    kan visa grönt/gult utan att avslöja facit.
    """
    student_nycklar = _nycklar_ur(studentens_svar or "")

    traffade: list[str] = []
    saknade: list[str] = []
    for ref in jakt.facit_lagrum:
        facit_nycklar = _nycklar_ur(ref)
        if facit_nycklar and facit_nycklar <= student_nycklar:
            traffade.append(ref)
        else:
            saknade.append(ref)

    korrekt = not saknade and bool(jakt.facit_lagrum)

    # Statusen beskriver studentens första lagrum (om något): verifierbart,
    # okänd paragraf/lag eller inget giltigt lagrum alls.
    if not student_nycklar:
        status = STATUS_EJ_VALIDERBAR
    else:
        forsta = extrahera_lagrum(studentens_svar)[0]
        status = validera_lagrum(forsta)

    return LagrumsjaktResultat(
        korrekt=korrekt,
        status=status,
        traffade=tuple(traffade),
        saknade=tuple(saknade),
        facit=tuple(jakt.facit_lagrum),
    )


# --- Session-state-hjälpare -------------------------------------------------


def _resultatbok() -> dict:
    """Hämta (eller skapa) quizresultatboken i session_state."""
    import streamlit as st

    return st.session_state.setdefault("quiz_resultat", {})


def registrera_mc_svar(modul: str, fraga_id: str, korrekt: bool) -> None:
    """Lagra utfallet av en besvarad flervalsfråga per modul och fråga."""
    try:
        bok = _resultatbok()
    except Exception:
        return
    modulbok = bok.setdefault(modul, {})
    modulbok[fraga_id] = bool(korrekt)


def modulresultat(modul: str) -> tuple[int, int]:
    """Returnera (antal_ratt, antal_besvarade) för en modul."""
    try:
        bok = _resultatbok()
    except Exception:
        return (0, 0)
    modulbok = bok.get(modul, {})
    ratt = sum(1 for v in modulbok.values() if v)
    return (ratt, len(modulbok))


def alla_resultat() -> dict[str, tuple[int, int]]:
    """Sammanställ (rätt, besvarade) för varje modul med registrerade svar."""
    try:
        bok = _resultatbok()
    except Exception:
        return {}
    return {modul: modulresultat(modul) for modul in bok}
