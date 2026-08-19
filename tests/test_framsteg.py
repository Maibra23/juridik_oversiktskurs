"""Test för utils.framsteg: vilka övningsmoduler studenten har börjat på.

Funktionen är ren och tar böckerna som argument, så den kan testas utan
Streamlit-runtime. Wrappern som läser session_state testas inte här.
"""

from __future__ import annotations

from utils.framsteg import pabborjade_ur_bocker


def test_tom_bok_ger_tom_mangd():
    assert pabborjade_ur_bocker({}, {}) == frozenset()


def test_quizresultat_raknas_som_paborjad():
    assert pabborjade_ur_bocker({"Avtalsrätt": (2, 3)}, {}) == frozenset({"Avtalsrätt"})


def test_genomfort_case_raknas_som_paborjad():
    assert pabborjade_ur_bocker({}, {"Personrätt": ("p-1",)}) == frozenset({"Personrätt"})


def test_bada_kallorna_slas_samman():
    resultat = pabborjade_ur_bocker(
        {"Avtalsrätt": (1, 1)}, {"Personrätt": ("p-1",)}
    )
    assert resultat == frozenset({"Avtalsrätt", "Personrätt"})


def test_tomma_poster_raknas_inte():
    """En modul med noll besvarade frågor och noll fall är inte påbörjad."""
    assert pabborjade_ur_bocker({"Avtalsrätt": (0, 0)}, {"Personrätt": ()}) == frozenset()
