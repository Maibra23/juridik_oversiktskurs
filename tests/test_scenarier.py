"""Tester för utils.scenarier.

Täcker inläsning av basscenarier, strukturvalidering, att varje lagrum i
Avtalsrätt-modulen verifieras mot data/lagrum.json och att varje
flervalsfråga har exakt ett rätt svar.
"""

from __future__ import annotations

import pytest

from utils.scenarier import (
    Modulscenarier,
    alla_lagrum,
    fragor_utan_exakt_ett_ratt,
    ladda_modul,
    lista_moduler,
    ogiltiga_lagrum,
)


@pytest.fixture(scope="module")
def avtalsratt() -> Modulscenarier:
    return ladda_modul("avtalsratt")


# --- Inläsning och struktur -------------------------------------------------

def test_avtalsratt_laddas(avtalsratt):
    assert avtalsratt.modul == "Avtalsrätt"


def test_avtalsratt_har_forvantat_antal_ovningar(avtalsratt):
    assert len(avtalsratt.case) == 2
    assert len(avtalsratt.flervalsfragor) == 8
    assert len(avtalsratt.lagrumsjakt) == 4


def test_varje_case_har_rnts_facit(avtalsratt):
    for c in avtalsratt.case:
        assert c.facit.rattsfraga
        assert c.facit.lagrum
        assert c.facit.tillampningspunkter
        assert c.facit.slutsats


def test_lista_moduler_innehaller_avtalsratt():
    assert "avtalsratt" in lista_moduler()


# --- Hallucinationsskydd: lagrum måste verifieras ---------------------------

def test_alla_lagrum_i_avtalsratt_ar_verifierade(avtalsratt):
    # Kärnan i Dag 1: avtalsrättsdata inläst OCH validerad mot lagrum.json.
    problem = ogiltiga_lagrum(avtalsratt)
    assert problem == (), f"Overifierade lagrum: {problem}"


def test_alla_lagrum_tillhor_avtalslagen(avtalsratt):
    # Alla referenser i modulen ska peka på AvtL i denna modul.
    for ref in alla_lagrum(avtalsratt):
        assert ref.endswith("AvtL"), ref


# --- Quizintegritet ---------------------------------------------------------

def test_varje_flervalsfraga_har_exakt_ett_ratt(avtalsratt):
    assert fragor_utan_exakt_ett_ratt(avtalsratt) == ()


def test_varje_alternativ_har_forklaring(avtalsratt):
    for q in avtalsratt.flervalsfragor:
        for a in q.alternativ:
            assert a.forklaring, f"Alternativ utan förklaring i {q.id}"
