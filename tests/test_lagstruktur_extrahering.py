"""Tester för strukturparsern (utils.lagstruktur_extrahering).

Fixturerna är sparad HTML från Riksdagens öppna data, en per källform:
KKöpL har både kapitel- och momentrubriker, AvtL har bara kapitelrubriker
(med löpande paragrafnumrering), PreskL har bara momentrubriker. Parsern
får aldrig anta en form; den läser de nivåer som finns.

Testerna går aldrig mot nätet. Källan ändras när lagarna ändras, och ett
test som beror på det är inte ett test utan en väderleksrapport.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.lagstruktur_extrahering import (
    extrahera_struktur,
    paragrafnyckel,
    rensa_html,
)

FIXTURER = Path(__file__).parent / "fixtures"


def _las(namn: str) -> str:
    return (FIXTURER / namn).read_text(encoding="utf-8")


# kapitelindelad-flaggan speglar lagrumsregistret: KKöpL är kapitelindelad,
# AvtL och PreskL har löpande paragrafnumrering.
@pytest.fixture(scope="module")
def kkopl():
    return extrahera_struktur(_las("kkopl-2022-260.html"), kapitelindelad=True)


@pytest.fixture(scope="module")
def avtl():
    return extrahera_struktur(_las("avtl-1915-218.html"), kapitelindelad=False)


@pytest.fixture(scope="module")
def preskl():
    return extrahera_struktur(_las("preskl-1981-130.html"), kapitelindelad=False)


def test_rensa_html_tar_bort_taggar_och_normaliserar():
    assert rensa_html("<em>3 kap.</em>  Om\n fullmakt") == "3 kap. Om fullmakt"


def test_paragrafnyckel_kapitelindelad():
    assert paragrafnyckel("K3P2") == "3:2"


def test_paragrafnyckel_oindelad():
    assert paragrafnyckel("P12") == "12"


def test_paragrafnyckel_avvisar_bokstavsparagraf():
    """Kursavsnitten refererar bara hela paragrafnummer, aldrig "1 a §"."""
    assert paragrafnyckel("K4P1a") is None


def test_paragrafnyckel_slapper_kapitlet_for_lopande_numrering():
    """Källan märker AvtL:s paragrafer K2P10 fast numreringen löper 1-41.

    Registret säger kapitelindelad: false och korpusen nycklar dem platt.
    Läser vi kapitlet ur ankaret ändå går strukturen inte att foga ihop med
    dem, och varje AvtL-avsnitt skulle se överskjutande ut i kontrollen.
    """
    assert paragrafnyckel("K2P10", kapitelindelad=False) == "10"
    assert paragrafnyckel("K2P10", kapitelindelad=True) == "2:10"


def test_kkopl_ger_bade_kapitel_och_moment(kkopl):
    kapitel, moment = kkopl
    assert kapitel, "KKöpL ska ge kapitel"
    assert moment, "KKöpL ska ge moment"


def test_kkopl_kapitelrubrik_ar_uppdelad_i_nummer_och_text(kkopl):
    kapitel, _ = kkopl
    tredje = next(k for k in kapitel if k["nummer"] == "3")
    assert tredje["rubrik"] == "Näringsidkarens dröjsmål"


def test_kkopl_moment_arver_sitt_kapitel(kkopl):
    _, moment = kkopl
    pafoljder = next(m for m in moment if m["rubrik"] == "Påföljder vid dröjsmål")
    assert pafoljder["kapitel"] == "3"
    assert all(p.startswith("3:") for p in pafoljder["paragrafer"])


def test_kkopl_kapitel_bar_sina_paragrafer_i_ordning(kkopl):
    kapitel, _ = kkopl
    forsta = next(k for k in kapitel if k["nummer"] == "1")
    assert forsta["paragrafer"][:3] == ["1:1", "1:2", "1:3"]


def test_avtl_ger_kapitel_utan_moment(avtl):
    kapitel, moment = avtl
    assert [k["rubrik"] for k in kapitel] == [
        "Om slutande av avtal",
        "Om fullmakt",
        "Om rättshandlingars ogiltighet",
        "Allmänna bestämmelser",
    ]
    assert moment == []


def test_avtl_har_platta_paragrafnycklar(avtl):
    """AvtL har kapitelrubriker men löpande numrering: "10", inte "2:10"."""
    kapitel, _ = avtl
    fullmakt = next(k for k in kapitel if k["rubrik"] == "Om fullmakt")
    assert "10" in fullmakt["paragrafer"]
    assert not any(":" in p for p in fullmakt["paragrafer"])


def test_avtl_grupperar_fortfarande_under_sina_kapitel(avtl):
    """Platta nycklar får inte kosta kapitelindelningen i kartan."""
    kapitel, _ = avtl
    fullmakt = next(k for k in kapitel if k["rubrik"] == "Om fullmakt")
    assert fullmakt["nummer"] == "2"
    assert fullmakt["paragrafer"][0] == "10"


def test_preskl_ger_moment_utan_kapitel(preskl):
    kapitel, moment = preskl
    assert kapitel == []
    assert "Preskriptionstid" in [m["rubrik"] for m in moment]
    assert all(m["kapitel"] is None for m in moment)


def test_innehallsforteckning_blir_inte_ett_kapitel(kkopl):
    """h3-bruset "Innehåll:" och "Övergångsbestämmelser" ska filtreras bort."""
    kapitel, _ = kkopl
    rubriker = [k["rubrik"] for k in kapitel]
    assert "Innehåll:" not in rubriker
    assert "Övergångsbestämmelser" not in rubriker


def test_rubriker_utan_paragrafer_utelamnas(preskl):
    """En rubrik som inte äger någon paragraf är en mellanrubrik, inte ett moment."""
    _, moment = preskl
    assert all(m["paragrafer"] for m in moment)


def test_paragrafer_forekommer_bara_en_gang_per_rubrik(kkopl):
    kapitel, moment = kkopl
    for post in [*kapitel, *moment]:
        assert len(post["paragrafer"]) == len(set(post["paragrafer"]))
