"""Tester för lagtextkorpusen (utils.lagtext).

Korpusen är appens svar på den enskilt största felkällan i tutorn: modellen
vet vilka lagrum som gäller men inte vad de säger. Mätt mot Qwen3-8B gav det
påståenden som att "36 § AvtL reglerar avtals ingående" (det är
generalklausulen om jämkning) och påhittade termer som "proxim
meningskausalitet".

Den bärande regeln i testerna nedan: modulen får aldrig gissa. Saknas en
paragraf i korpusen ska den säga det med None, så att prompten hellre
utelämnar lagtexten än hittar på den.
"""

from __future__ import annotations

import pytest

from utils.lagtext import (
    hamta_paragraftext,
    har_lagtext,
    ladda_lagtext,
    lagtext_block,
)


@pytest.fixture(scope="module")
def korpus():
    return ladda_lagtext()


# --- Korpusens integritet ---------------------------------------------------


def test_korpusen_innehaller_appens_lagar(korpus):
    """Varje lag i registret ska ha en fil i korpusen."""
    from utils.lagrum import lagrum_register

    saknas = sorted(set(lagrum_register()) - set(korpus))
    assert not saknas, f"lagar utan lagtext: {saknas}"


def test_varje_lag_har_paragrafer(korpus):
    for forkortning, lag in korpus.items():
        assert lag.paragrafer, f"{forkortning} har inga paragrafer"


def test_korpusen_anger_kalla_och_hamtningsdatum(korpus):
    """Spårbarhet: en läsare ska kunna se var texten kommer ifrån och när."""
    for forkortning, lag in korpus.items():
        assert lag.kalla.startswith("https://"), forkortning
        assert lag.hamtad, forkortning


# --- Uppslagning ------------------------------------------------------------


def test_hamtar_text_for_oindelad_lag():
    """4 § AvtL är appens skolexempel på sen accept."""
    text = hamta_paragraftext("4 § AvtL")
    assert text is not None
    assert "för sent" in text
    assert "nytt anbud" in text


def test_hamtar_text_for_kapitelindelad_lag():
    """2 kap. 1 § SkL är culparegeln."""
    text = hamta_paragraftext("2 kap. 1 § SkL")
    assert text is not None
    assert "vårdslöshet" in text
    assert "ersätta skadan" in text


def test_ratt_paragraf_hamtas_inte_grannen():
    """Uppslagningen får inte glida en paragraf fel."""
    fyra = hamta_paragraftext("4 § AvtL")
    fem = hamta_paragraftext("5 § AvtL")
    assert fyra != fem


def test_36_paragrafen_ar_jamkning_inte_avtals_ingaende():
    """Regressionsvakt mot det verkliga felet tutorn gjorde.

    Modellen påstod att 36 § AvtL reglerar avtals ingående. Med lagtexten i
    prompten går det inte längre att tro: paragrafen handlar om oskäliga
    avtalsvillkor och jämkning.
    """
    text = hamta_paragraftext("36 § AvtL")
    assert text is not None
    assert "oskäl" in text.lower() or "jämka" in text.lower()


# --- Vägran att gissa -------------------------------------------------------


def test_okand_paragraf_ger_none():
    """En paragraf utanför lagavsnitten finns inte i korpusen."""
    assert hamta_paragraftext("999 § AvtL") is None


def test_pahittat_lagrum_ger_none():
    """Det påhittade lagrummet ur sessionens fälla."""
    assert hamta_paragraftext("87 § AvtL") is None
    assert hamta_paragraftext("12 kap. 4 § AvtL") is None


def test_okand_lag_ger_none():
    assert hamta_paragraftext("5 § XYZ") is None


def test_skrap_ger_none_utan_att_krascha():
    for skrap in ("", "   ", "inte ett lagrum", "§§§"):
        assert hamta_paragraftext(skrap) is None


def test_har_lagtext_speglar_hamtningen():
    assert har_lagtext("4 § AvtL") is True
    assert har_lagtext("87 § AvtL") is False


# --- Promptblocket ----------------------------------------------------------


def test_lagtext_block_innehaller_texten():
    block = lagtext_block(["4 § AvtL", "1 § AvtL"])
    assert "4 § AvtL" in block
    assert "nytt anbud" in block


def test_lagtext_block_hoppar_over_saknade_lagrum():
    """Ett påhittat lagrum ska inte ge en tom eller påhittad rad."""
    block = lagtext_block(["4 § AvtL", "87 § AvtL"])
    assert "4 § AvtL" in block
    assert "87 §" not in block


def test_lagtext_block_utan_traffar_ar_tomt():
    """Inget block alls hellre än en rubrik utan innehåll."""
    assert lagtext_block(["87 § AvtL"]) == ""
    assert lagtext_block([]) == ""


def test_lagtext_block_tar_bort_dubbletter():
    block = lagtext_block(["4 § AvtL", "4 § AvtL"])
    assert block.count("Antagande svar") == 1


def test_lagtext_block_sager_att_texten_ar_ordagrann():
    """Prompten måste veta att detta är källtext, inte en parafras."""
    block = lagtext_block(["4 § AvtL"])
    assert "ordagrann" in block.lower() or "ordagrant" in block.lower()
