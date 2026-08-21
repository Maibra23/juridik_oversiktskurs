"""Tester för utils.svarighetsgrad (kanoniskt svårighetsbegrepp).

Ren logik, ingen Streamlit och ingen LLM. Täcker normalisering av äldre och
okända värden, etikettuppslag och att varje nivå har en distinkt instruktion.
"""

from __future__ import annotations

import pytest

from utils.svarighetsgrad import (
    NYCKLAR,
    STANDARDNIVA,
    SVARIGHETSNIVAER,
    etikett_for,
    forvantan_for,
    instruktion_for,
    normalisera,
)


def test_standardniva_ar_grund():
    assert STANDARDNIVA == "grund"


def test_nycklar_matchar_nivalistan():
    assert NYCKLAR == tuple(nyckel for nyckel, _ in SVARIGHETSNIVAER)
    assert NYCKLAR == ("grund", "medel", "avancerad")


@pytest.mark.parametrize(
    "indata,forvantat",
    [
        ("grund", "grund"),
        ("medel", "medel"),
        ("avancerad", "avancerad"),
        ("Avancerad", "avancerad"),   # skiftlägesokänsligt
        ("  medel  ", "medel"),        # trimmas
        ("svar", "avancerad"),          # felstavat kuraterat värde
        ("svår", "avancerad"),          # äldre stavning
        ("SVÅR", "avancerad"),
        ("", "grund"),                  # tomt -> standard
        (None, "grund"),                # None -> standard
        ("nonsens", "grund"),           # okänt -> standard
    ],
)
def test_normalisera(indata, forvantat):
    assert normalisera(indata) == forvantat


def test_etikett_for_kanda_nycklar():
    assert etikett_for("grund") == "Grund"
    assert etikett_for("medel") == "Medel"
    assert etikett_for("avancerad") == "Avancerad"


def test_etikett_for_okand_faller_till_standard():
    assert etikett_for("nonsens") == etikett_for(STANDARDNIVA)


def test_instruktion_ar_distinkt_och_icke_tom_per_niva():
    texter = {nyckel: instruktion_for(nyckel) for nyckel in NYCKLAR}
    for text in texter.values():
        assert text.strip()
    assert len(set(texter.values())) == len(NYCKLAR)


def test_instruktion_for_okand_niva_normaliseras():
    assert instruktion_for("nonsens") == instruktion_for(STANDARDNIVA)


# --- Bedömningsnivå (forvantan_for) -----------------------------------------


def test_forvantan_ar_distinkt_och_icke_tom_per_niva():
    texter = [forvantan_for(n) for n in NYCKLAR]
    assert all(t.strip() for t in texter)
    assert len(set(texter)) == len(NYCKLAR)


def test_forvantan_for_okand_niva_normaliseras():
    assert forvantan_for("nonsens") == forvantan_for(STANDARDNIVA)
    assert forvantan_for(None) == forvantan_for(STANDARDNIVA)


def test_forvantan_namnger_sin_egen_niva():
    for nyckel in NYCKLAR:
        assert nyckel.upper() in forvantan_for(nyckel)


def test_forvantan_skiljer_sig_fran_genereringsinstruktionen():
    """De besvarar olika frågor: hur svår uppgiften är, hur hårt den bedöms."""
    for nyckel in NYCKLAR:
        assert forvantan_for(nyckel) != instruktion_for(nyckel)
