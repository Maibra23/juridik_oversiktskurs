"""Tester för läsningen av lagstrukturen (utils.lagstruktur).

Strukturen är appens enda källa till lagens egen disposition. Den valideras
strikt vid inläsning: hellre ett tydligt fel vid uppstart än ett halvt
kapitel i lagkortet. Det skiljer modulen från utils.lagtext, som får
degradera tyst när en paragraf saknas -- en tom lucka är ofarlig, men en
trasig struktur blir ett felaktigt påstående om hur lagen är uppbyggd.
"""

from __future__ import annotations

import pytest

from utils.lagrum import lagrum_register
from utils.lagstruktur import (
    DATA_DIR,
    _bygg_struktur,
    antal_kapitel,
    kapitelrubrik,
    ladda_lagstruktur,
    paragrafnycklar,
)


@pytest.fixture(scope="module")
def strukturer():
    return ladda_lagstruktur()


def test_alla_lagar_i_registret_har_en_strukturfil(strukturer):
    saknas = sorted(set(lagrum_register()) - set(strukturer))
    assert saknas == [], f"Saknar strukturfil för: {saknas}"


def test_ingen_lag_saknar_bada_rubriknivaerna(strukturer):
    tomma = [f for f, s in strukturer.items() if not s.kapitel and not s.moment]
    assert tomma == []


def test_moment_pekar_alltid_pa_ett_existerande_kapitel(strukturer):
    for forkortning, struktur in strukturer.items():
        nummer = {k.nummer for k in struktur.kapitel}
        for moment in struktur.moment:
            if moment.kapitel is not None:
                assert moment.kapitel in nummer, (
                    f"{forkortning}: momentet {moment.rubrik!r} pekar på "
                    f"kapitel {moment.kapitel} som inte finns"
                )


def test_paragrafnycklarna_har_samma_form_som_lagtextkorpusen(strukturer):
    for forkortning, struktur in strukturer.items():
        for kapitel in struktur.kapitel:
            for nyckel in kapitel.paragrafer:
                delar = nyckel.split(":")
                assert all(d.isdigit() for d in delar), f"{forkortning}: {nyckel}"
                assert len(delar) <= 2


def test_kapitellosa_lagar_har_platta_nycklar(strukturer):
    """AvtL och SkbrL har kapitelrubriker men löpande numrering.

    Nyckelns form följer registrets kapitelindelad-flagga, inte källans
    ankare. Annars går strukturen inte att foga ihop med korpusen.
    """
    register = lagrum_register()
    for forkortning, struktur in strukturer.items():
        if register[forkortning].kapitelindelad:
            continue
        platta = [
            nyckel
            for post in (*struktur.kapitel, *struktur.moment)
            for nyckel in post.paragrafer
            if ":" in nyckel
        ]
        assert platta == [], f"{forkortning} har kapitelnycklar: {platta[:5]}"


def test_strukturen_ar_immutabel(strukturer):
    struktur = strukturer["KKöpL"]
    assert isinstance(struktur.kapitel, tuple)
    with pytest.raises(Exception):
        struktur.kapitel = ()


def test_kapitelrubrik_slar_upp_pa_nummer():
    assert kapitelrubrik("KKöpL", "3") == "Näringsidkarens dröjsmål"


def test_kapitelrubrik_ger_none_for_okant_kapitel():
    assert kapitelrubrik("KKöpL", "99") is None


def test_kapitelrubrik_ger_none_for_okand_lag():
    assert kapitelrubrik("Påhittad", "1") is None


def test_antal_kapitel_raknar_hela_lagen():
    """Hela lagen, inte kursens del: KKöpL har nio kapitel."""
    assert antal_kapitel("KKöpL") == 9


def test_antal_kapitel_ar_noll_for_kapitellos_lag():
    assert antal_kapitel("PreskL") == 0


def test_paragrafnycklar_samlar_bade_kapitel_och_moment():
    nycklar = paragrafnycklar("KKöpL")
    assert "3:1" in nycklar
    assert "99:1" not in nycklar


def test_trasig_fil_kastar_vid_inlasning():
    """Fail fast: hellre ett fel vid uppstart än ett halvt kapitel i vyn."""
    rad = {"forkortning": "X", "namn": "X", "sfs": "1:1", "kapitel": "inte en lista"}
    with pytest.raises(ValueError):
        _bygg_struktur(rad)


def test_fil_utan_rubriknivaer_kastar():
    rad = {
        "forkortning": "X",
        "namn": "X",
        "sfs": "1:1",
        "kalla": "",
        "kallnamn": "",
        "hamtad": "",
        "licens": "",
        "kapitel": [],
        "moment": [],
    }
    with pytest.raises(ValueError):
        _bygg_struktur(rad)


def test_moment_mot_okant_kapitel_kastar():
    rad = {
        "forkortning": "X",
        "namn": "X",
        "sfs": "1:1",
        "kapitel": [{"nummer": "1", "rubrik": "Ett", "paragrafer": ["1:1"]}],
        "moment": [{"rubrik": "Spöke", "kapitel": "9", "paragrafer": ["9:1"]}],
    }
    with pytest.raises(ValueError, match="9"):
        _bygg_struktur(rad)


def test_datakatalogen_ar_committad():
    assert DATA_DIR.exists()
    assert len(list(DATA_DIR.glob("*.json"))) == 21
