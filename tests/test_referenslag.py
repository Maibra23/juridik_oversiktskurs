"""Tester för referenslag: kartnoder som ger överblick men står utanför kursen.

En referenslag syns och är klickbar (lagen.nu-länk) på Rättskartan men ingår
INTE i det graderade kursregistret: den får inte finnas i lagrum_register(),
och rättningen (validera_lagrum/quiz/lagrumsjakt) ska aldrig se den. Det är den
gränsen som håller kartans bredd skild från kursens djup.
"""

from __future__ import annotations

import pytest

from utils.rattskarta import _bygg_lagpost


def test_referenslag_byggs_utan_registerkrav():
    """RF finns inte i kursregistret men ska ändå gå att bygga som referens."""
    post = _bygg_lagpost(
        {
            "forkortning": "RF",
            "namn": "Regeringsformen",
            "sfs": "1974:152",
            "beskrivning": "Statsskicket och de grundläggande fri- och rättigheterna.",
            "referens": True,
        }
    )
    assert post.ar_referens is True
    assert post.forkortning == "RF"
    assert post.namn == "Regeringsformen"
    assert post.sfs == "1974:152"


def test_referenslag_kraver_namn_och_sfs():
    """Utan namn/SFS går ingen lagen.nu-länk att bygga — då ska bygget faila."""
    with pytest.raises(ValueError):
        _bygg_lagpost({"forkortning": "RF", "beskrivning": "x", "referens": True})


def test_kurslag_kraver_fortfarande_registermedlemskap():
    """Grundningsprincipen står kvar för icke-referenslagar: okänd lag = fel."""
    with pytest.raises(ValueError):
        _bygg_lagpost({"forkortning": "RF", "beskrivning": "x", "nar": "y"})


def test_referenslag_lacker_inte_in_i_kursregistret():
    """Registret ska förbli exakt kursens 21 lagar även med referensnoder i trädet."""
    from utils.lagrum import giltiga_forkortningar

    assert len(giltiga_forkortningar()) == 21
    assert "RF" not in giltiga_forkortningar()


def test_referensnoder_ar_klickbara_lagen_nu_lankar():
    from utils.rattssystem_graf import GRUPP_REFERENS, bygg_taxonomigraf

    graf = bygg_taxonomigraf()
    referens = [n for n in graf["noder"] if n["grupp"] == GRUPP_REFERENS]
    assert referens, "Inga referensnoder i grafen"
    rf = next((n for n in referens if n.get("forkortning") == "RF"), None)
    assert rf is not None, "Regeringsformen saknas som referensnod"
    assert rf["url"] == "https://lagen.nu/1974:152"
    assert "utanför kursen" in rf["titel"].lower()


def test_referenslag_ar_inte_verifierbara_i_rattningen():
    """En referenslag ska aldrig kunna bli VERIFIERAD i en lagrumsjakt."""
    from utils.lagrum import STATUS_VERIFIERAD, extrahera_lagrum, validera_lagrum

    refs = extrahera_lagrum("regeringsformen 2 §")
    # Antingen ingen träff alls, eller en träff som inte är verifierad.
    if refs:
        assert validera_lagrum(refs[0]) != STATUS_VERIFIERAD
