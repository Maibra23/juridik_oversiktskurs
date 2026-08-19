"""Tester för grupperingen av lagavsnitt inför lagkortet.

Registret bär avsnitten platt medan lagen är indelad i kapitel. Modulen slår
ihop de två så att vyn slipper veta något om lagstrukturen.
"""

from __future__ import annotations

from utils.lagkort_avsnitt import (
    formatera_spann,
    gruppera_lagavsnitt,
    tackningstext,
)
from utils.lagrum import lagrum_register


def test_ett_enda_paragrafnummer_far_enkelt_paragraftecken():
    """36 §, aldrig 36 §§. Pluralfel i lagrum läser studenten som slarv."""
    assert formatera_spann(36, 36) == "36 §"


def test_intervall_far_dubbelt_paragraftecken():
    assert formatera_spann(1, 9) == "1 till 9 §§"


def test_intervall_skrivs_med_ordet_till_utan_streck():
    """Spannet skrivs ut med "till", inte med streck av något slag.

    Lagrumsparsern (utils.lagrum) tar emot alla tre formerna, så bytet är
    bara en fråga om hur appen själv skriver, inte om vad den förstår.
    """
    spann = formatera_spann(1, 9)
    assert " till " in spann
    assert "-" not in spann
    assert "\u2013" not in spann
    assert "\u2014" not in spann


def test_kapitelindelad_lag_grupperas_under_sina_kapitel():
    grupper = gruppera_lagavsnitt(lagrum_register()["KKöpL"])
    assert all(g.kapitel is not None for g in grupper)
    assert all(g.rubrik for g in grupper)


def test_kapitelrubriken_kommer_ur_lagens_egen_struktur():
    grupper = gruppera_lagavsnitt(lagrum_register()["KKöpL"])
    tredje = next(g for g in grupper if g.kapitel == "3")
    assert tredje.rubrik == "Näringsidkarens dröjsmål"


def test_kapitellos_lag_ger_en_enda_ogrupperad_grupp():
    lag = lagrum_register()["KöpL"]
    grupper = gruppera_lagavsnitt(lag)
    assert len(grupper) == 1
    assert grupper[0].kapitel is None
    assert grupper[0].rubrik == ""
    assert len(grupper[0].avsnitt) == len(lag.lagavsnitt)


def test_kapitlen_kommer_i_lagens_ordning():
    """Registret är redaktionellt sorterat och kan lägga 6 kap. före 3 kap.

    I ett lagkort läser det som ett slarvfel: en student som letar efter
    3 kap. förväntar sig den mellan 2 och 4, precis som i författningen.
    """
    grupper = gruppera_lagavsnitt(lagrum_register()["KKöpL"])
    nummer = [int(g.kapitel) for g in grupper]
    assert nummer == sorted(nummer)


def test_avsnitten_i_en_kapitellos_lag_kommer_i_paragrafordning():
    lag = lagrum_register()["KöpL"]
    forsta = [
        int(rad.spann.split(",")[0].split(" ")[0])
        for rad in gruppera_lagavsnitt(lag)[0].avsnitt
    ]
    assert forsta == sorted(forsta)


def test_avsnitten_gar_inte_forlorade_vid_sortering():
    lag = lagrum_register()["KKöpL"]
    grupper = gruppera_lagavsnitt(lag)
    rubriker = {rad.rubrik for g in grupper for rad in g.avsnitt}
    assert rubriker == {a.beskrivning for a in lag.lagavsnitt}


def test_avsnittsraden_bar_spann_rubrik_och_lank():
    grupper = gruppera_lagavsnitt(lagrum_register()["AvtL"])
    rad = grupper[0].avsnitt[0]
    assert rad.spann.endswith("§") or rad.spann.endswith("§§")
    assert rad.rubrik
    assert rad.url.startswith("https://lagen.nu/")


def test_lag_utan_lagavsnitt_ger_inga_grupper():
    from utils.lagrum import Lag

    tom = Lag(
        forkortning="X",
        namn="X",
        sfs="1:1",
        kapitelindelad=False,
        lagen_nu_bas_url="https://lagen.nu/1:1",
        lagavsnitt=(),
    )
    assert gruppera_lagavsnitt(tom) == ()


def test_tackningstext_for_kapitelindelad_lag():
    text = tackningstext(lagrum_register()["KKöpL"])
    assert "av lagens" in text
    assert "kapitel" in text


def test_tackningstext_raknar_mot_hela_lagen():
    """KKöpL har nio kapitel; appen behandlar sex av dem."""
    assert tackningstext(lagrum_register()["KKöpL"]) == (
        "appen behandlar 6 av lagens 9 kapitel"
    )


def test_tackningstext_ar_tom_for_kapitellos_lag():
    """Utan kapitel finns inget att räkna, och raden ska då utebli helt."""
    assert tackningstext(lagrum_register()["KöpL"]) == ""


def test_grupperna_ar_immutabla():
    grupp = gruppera_lagavsnitt(lagrum_register()["KKöpL"])[0]
    assert isinstance(grupp.avsnitt, tuple)


def test_alla_lagar_i_registret_kan_grupperas():
    """Regression: ingen lag får krascha grupperingen."""
    for forkortning, lag in lagrum_register().items():
        grupper = gruppera_lagavsnitt(lag)
        antal = sum(len(g.avsnitt) for g in grupper)
        assert antal == len(lag.lagavsnitt), forkortning
