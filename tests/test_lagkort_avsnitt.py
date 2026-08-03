"""Tester för grupperingen av kursavsnitt inför lagkortet.

Registret bär avsnitten platt medan lagen är indelad i kapitel. Modulen slår
ihop de två så att vyn slipper veta något om lagstrukturen.
"""

from __future__ import annotations

from utils.lagkort_avsnitt import (
    formatera_spann,
    gruppera_kursavsnitt,
    tackningstext,
)
from utils.lagrum import lagrum_register


def test_ett_enda_paragrafnummer_far_enkelt_paragraftecken():
    """36 §, aldrig 36 §§. Pluralfel i lagrum läser studenten som slarv."""
    assert formatera_spann(36, 36) == "36 §"


def test_intervall_far_dubbelt_paragraftecken():
    assert formatera_spann(1, 9) == "1–9 §§"


def test_intervall_anvander_tankstreck_inte_bindestreck():
    assert "–" in formatera_spann(1, 9)
    assert "-" not in formatera_spann(1, 9)


def test_kapitelindelad_lag_grupperas_under_sina_kapitel():
    grupper = gruppera_kursavsnitt(lagrum_register()["KKöpL"])
    assert all(g.kapitel is not None for g in grupper)
    assert all(g.rubrik for g in grupper)


def test_kapitelrubriken_kommer_ur_lagens_egen_struktur():
    grupper = gruppera_kursavsnitt(lagrum_register()["KKöpL"])
    tredje = next(g for g in grupper if g.kapitel == "3")
    assert tredje.rubrik == "Näringsidkarens dröjsmål"


def test_kapitellos_lag_ger_en_enda_ogrupperad_grupp():
    lag = lagrum_register()["KöpL"]
    grupper = gruppera_kursavsnitt(lag)
    assert len(grupper) == 1
    assert grupper[0].kapitel is None
    assert grupper[0].rubrik == ""
    assert len(grupper[0].avsnitt) == len(lag.kursavsnitt)


def test_avsnitten_behaller_registrets_ordning():
    lag = lagrum_register()["KöpL"]
    rubriker = [rad.rubrik for rad in gruppera_kursavsnitt(lag)[0].avsnitt]
    assert rubriker == [a.beskrivning for a in lag.kursavsnitt]


def test_avsnittsraden_bar_spann_rubrik_och_lank():
    grupper = gruppera_kursavsnitt(lagrum_register()["AvtL"])
    rad = grupper[0].avsnitt[0]
    assert rad.spann.endswith("§") or rad.spann.endswith("§§")
    assert rad.rubrik
    assert rad.url.startswith("https://lagen.nu/")


def test_lag_utan_kursavsnitt_ger_inga_grupper():
    from utils.lagrum import Lag

    tom = Lag(
        forkortning="X",
        namn="X",
        sfs="1:1",
        kapitelindelad=False,
        lagen_nu_bas_url="https://lagen.nu/1:1",
        kursavsnitt=(),
    )
    assert gruppera_kursavsnitt(tom) == ()


def test_tackningstext_for_kapitelindelad_lag():
    text = tackningstext(lagrum_register()["KKöpL"])
    assert "av lagens" in text
    assert "kapitel" in text


def test_tackningstext_raknar_mot_hela_lagen():
    """KKöpL har nio kapitel; kursen berör sex av dem."""
    assert tackningstext(lagrum_register()["KKöpL"]) == (
        "kursen täcker 6 av lagens 9 kapitel"
    )


def test_tackningstext_ar_tom_for_kapitellos_lag():
    """Utan kapitel finns inget att räkna, och raden ska då utebli helt."""
    assert tackningstext(lagrum_register()["KöpL"]) == ""


def test_grupperna_ar_immutabla():
    grupp = gruppera_kursavsnitt(lagrum_register()["KKöpL"])[0]
    assert isinstance(grupp.avsnitt, tuple)


def test_alla_lagar_i_registret_kan_grupperas():
    """Regression: ingen lag får krascha grupperingen."""
    for forkortning, lag in lagrum_register().items():
        grupper = gruppera_kursavsnitt(lag)
        antal = sum(len(g.avsnitt) for g in grupper)
        assert antal == len(lag.kursavsnitt), forkortning
