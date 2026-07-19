"""Tester för utils/texter.py: central texthjälp för användarsynliga strängar."""

from __future__ import annotations

from utils.texter import antal_med_enhet


def test_antal_med_enhet_singular():
    assert (
        antal_med_enhet(1, "genomfört rättsfall", "genomförda rättsfall")
        == "1 genomfört rättsfall"
    )


def test_antal_med_enhet_plural():
    assert (
        antal_med_enhet(3, "genomfört rättsfall", "genomförda rättsfall")
        == "3 genomförda rättsfall"
    )


def test_antal_med_enhet_noll_ar_plural():
    assert (
        antal_med_enhet(0, "genomfört rättsfall", "genomförda rättsfall")
        == "0 genomförda rättsfall"
    )


def test_antal_med_enhet_negativt_ger_fel():
    import pytest

    with pytest.raises(ValueError):
        antal_med_enhet(-1, "fall", "fall")
