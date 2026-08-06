"""Test för utils.rnts: RNTS-stegen och vilken aktivitet som tränar vilket steg.

Ren data utan Streamlit-beroende, så avbildningen kan testas direkt.
"""

from __future__ import annotations

import pytest

from utils.rnts import AKTIVITETSSTEG, RNTS_STEG, tranar_etikett


def test_rnts_steg_har_de_fyra_i_ratt_ordning():
    assert RNTS_STEG == ("Rättsfrågan", "Norm", "Tillämpning", "Slutsats")


def test_varje_aktivitet_tranar_minst_ett_steg():
    assert AKTIVITETSSTEG
    for aktivitet, steg in AKTIVITETSSTEG.items():
        assert steg, f"{aktivitet} tränar inga steg"


def test_alla_angivna_steg_finns_i_rnts_steg():
    """Vakt mot stavfel: ett okänt stegnamn ska inte kunna smyga in."""
    for aktivitet, steg in AKTIVITETSSTEG.items():
        for s in steg:
            assert s in RNTS_STEG, f"{aktivitet} anger okänt steg {s!r}"


def test_lagrumsjakt_tranar_norm():
    assert AKTIVITETSSTEG["lagrumsjakt"] == ("Norm",)


def test_rattsfall_tranar_alla_fyra():
    assert AKTIVITETSSTEG["rattsfall"] == RNTS_STEG


def test_tranar_etikett_ar_versal_och_kommaseparerad():
    assert tranar_etikett("lagrumsjakt") == "TRÄNAR: NORM"
    assert tranar_etikett("quiz") == "TRÄNAR: NORM, TILLÄMPNING"


def test_tranar_etikett_okand_aktivitet_ger_valueerror():
    with pytest.raises(ValueError, match="Okänd aktivitet"):
        tranar_etikett("finns-inte")
