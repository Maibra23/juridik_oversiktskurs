"""Tester för utils.quiz rättningslogik.

Täcker deterministisk rättning av flervalsfrågor (rätt/fel, förklaring,
gränsvärden) och lagrumsjakt (exakt träff, kapitelindelat lagrum,
saknat lagrum, fel lagrum och tomt svar). Ingen LLM inblandad.
"""

from __future__ import annotations

import pytest

from utils.lagrum import (
    STATUS_EJ_VALIDERBAR,
    STATUS_VERIFIERAD,
)
from utils.quiz import (
    ratt_alternativ_index,
    ratta_flervalsfraga,
    ratta_lagrumsjakt,
)
from utils.scenarier import Alternativ, Flervalsfraga, Lagrumsjakt, ladda_modul


def _fraga() -> Flervalsfraga:
    return Flervalsfraga(
        id="q1",
        fraga="Vad gäller?",
        alternativ=(
            Alternativ(text="Rätt", korrekt=True, forklaring="Detta stämmer.", lagrum="1 § AvtL"),
            Alternativ(text="Fel", korrekt=False, forklaring="Detta är fel.", lagrum="7 § AvtL"),
            Alternativ(text="Också fel", korrekt=False, forklaring="Nej.", lagrum=None),
        ),
    )


def test_ratt_svar_ger_korrekt():
    res = ratta_flervalsfraga(_fraga(), 0)
    assert res.korrekt is True
    assert res.ratt_index == 0
    assert res.forklaring == "Detta stämmer."


def test_fel_svar_ger_ratt_index_och_forklaring():
    res = ratta_flervalsfraga(_fraga(), 1)
    assert res.korrekt is False
    assert res.ratt_index == 0
    assert res.forklaring == "Detta är fel."


def test_valt_index_utanfor_intervall_kastar():
    with pytest.raises(ValueError):
        ratta_flervalsfraga(_fraga(), 5)


def test_fraga_utan_exakt_ett_ratt_kastar():
    trasig = Flervalsfraga(
        id="q2",
        fraga="?",
        alternativ=(
            Alternativ(text="a", korrekt=True, forklaring=""),
            Alternativ(text="b", korrekt=True, forklaring=""),
        ),
    )
    with pytest.raises(ValueError):
        ratt_alternativ_index(trasig)


def test_lagrumsjakt_exakt_traff():
    jakt = Lagrumsjakt(id="lj1", situation="?", facit_lagrum=("4 § AvtL",))
    res = ratta_lagrumsjakt(jakt, "Jag tror det är 4 § AvtL.")
    assert res.korrekt is True
    assert res.status == STATUS_VERIFIERAD
    assert res.saknade == ()


def test_lagrumsjakt_kapitelindelat():
    jakt = Lagrumsjakt(id="lj2", situation="?", facit_lagrum=("2 kap. 1 § SkL",))
    res = ratta_lagrumsjakt(jakt, "Det är 2 kap. 1 § SkL som gäller.")
    assert res.korrekt is True
    assert res.status == STATUS_VERIFIERAD


def test_lagrumsjakt_fel_paragraf():
    jakt = Lagrumsjakt(id="lj3", situation="?", facit_lagrum=("4 § AvtL",))
    res = ratta_lagrumsjakt(jakt, "1 § AvtL")
    assert res.korrekt is False
    assert "4 § AvtL" in res.saknade


def test_lagrumsjakt_tomt_svar():
    jakt = Lagrumsjakt(id="lj4", situation="?", facit_lagrum=("4 § AvtL",))
    res = ratta_lagrumsjakt(jakt, "")
    assert res.korrekt is False
    assert res.status == STATUS_EJ_VALIDERBAR


def test_lagrumsjakt_flera_facit_delvis():
    jakt = Lagrumsjakt(id="lj5", situation="?", facit_lagrum=("10 § AvtL", "11 § AvtL"))
    res = ratta_lagrumsjakt(jakt, "10 § AvtL")
    assert res.korrekt is False
    assert "11 § AvtL" in res.saknade
    assert "10 § AvtL" in res.traffade


def test_avtalsratt_alla_mc_har_exakt_ett_ratt():
    modul = ladda_modul("avtalsratt")
    for fraga in modul.flervalsfragor:
        # Kastar om någon fråga saknar exakt ett rätt svar.
        idx = ratt_alternativ_index(fraga)
        assert 0 <= idx < len(fraga.alternativ)
