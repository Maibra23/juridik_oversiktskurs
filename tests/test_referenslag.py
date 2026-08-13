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


def test_referenslag_med_sfs_far_lagen_nu_lank():
    post = _bygg_lagpost(
        {"forkortning": "RF", "namn": "Regeringsformen", "sfs": "1974:152",
         "beskrivning": "x", "referens": True}
    )
    assert post.url == "https://lagen.nu/1974:152"


def test_referenslag_med_explicit_url_behover_ingen_sfs():
    """EU-rätt finns inte på lagen.nu; en explicit url ska räcka."""
    post = _bygg_lagpost(
        {"forkortning": "FEU", "namn": "Fördraget om Europeiska unionen",
         "url": "https://eur-lex.europa.eu/legal-content/SV/TXT/?uri=celex:12016M/TXT",
         "beskrivning": "x", "referens": True}
    )
    assert post.ar_referens is True
    assert post.url.startswith("https://eur-lex.europa.eu/")
    assert post.sfs is None


def test_referenslag_kraver_namn_och_lankkalla():
    """Utan namn, och utan antingen SFS eller url, går ingen länk att bygga."""
    with pytest.raises(ValueError):
        _bygg_lagpost({"forkortning": "RF", "beskrivning": "x", "referens": True})
    with pytest.raises(ValueError):
        _bygg_lagpost(
            {"forkortning": "RF", "namn": "Regeringsformen",
             "beskrivning": "x", "referens": True}
        )


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


def test_toggle_doljer_referenslagar_och_deras_tomma_grenar():
    """Med referens av ska bara kurslagar synas, och grenar utan kurslag städas bort."""
    from utils.rattssystem_graf import (
        GRUPP_LAG,
        GRUPP_REFERENS,
        bygg_taxonomigraf,
    )

    med = bygg_taxonomigraf(inkludera_referens=True)
    utan = bygg_taxonomigraf(inkludera_referens=False)

    assert any(n["grupp"] == GRUPP_REFERENS for n in med["noder"])
    assert not any(n["grupp"] == GRUPP_REFERENS for n in utan["noder"])

    # Kurslagarna är oförändrade oavsett toggle.
    kurs_med = {n["id"] for n in med["noder"] if n["grupp"] == GRUPP_LAG}
    kurs_utan = {n["id"] for n in utan["noder"] if n["grupp"] == GRUPP_LAG}
    assert kurs_med == kurs_utan

    # Rena referensgrenar (statsrätt, skatterätt, EU-rätt) städas bort helt.
    labels_utan = {n["label"] for n in utan["noder"]}
    for borta in ("Statsrätt", "Skatterätt", "Internationell rätt & EU-rätt"):
        assert borta not in labels_utan, f"{borta} borde vara dold utan referens"
    # Grenar med kurslag finns kvar.
    assert "Straffrätt" in labels_utan
    assert "Civilrätt" in labels_utan


def test_eu_ratt_noderna_ar_inte_langre_atervandsgrander():
    """EU-rätt och internationell privaträtt ska bära klickbara referenser."""
    from utils.rattskarta import hitta_gren

    eu = hitta_gren("eu_ratt")
    assert eu is not None and eu.lagar, "EU-rätt saknar referenser"
    assert all(lag.ar_referens for lag in eu.lagar)
    assert all(lag.url.startswith("https://eur-lex.europa.eu/") for lag in eu.lagar)

    ip = hitta_gren("internationell_privatratt")
    assert ip is not None and ip.lagar, "Internationell privaträtt saknar referenser"


def test_referenslag_ar_inte_verifierbara_i_rattningen():
    """En referenslag ska aldrig kunna bli VERIFIERAD i en lagrumsjakt."""
    from utils.lagrum import STATUS_VERIFIERAD, extrahera_lagrum, validera_lagrum

    refs = extrahera_lagrum("regeringsformen 2 §")
    # Antingen ingen träff alls, eller en träff som inte är verifierad.
    if refs:
        assert validera_lagrum(refs[0]) != STATUS_VERIFIERAD
