"""Tester för kraftvyns rendering (utils.kraftgraf_ui).

Kraftvyn byter layout och kringutrustning mot den hierarkiska vyn, men ärver
designsystemets färgkontrakt oförändrat: guld betyder lag, aldrig struktur, och
varje toppgren behåller sin egen färg (design_system.md avsnitt 1). Testerna
vaktar just det, plus att sidopanelens innehåll escapas och att inga tal eller
färger dubbleras mellan Python och JavaScript.
"""

from __future__ import annotations

import json

import pytest

from utils.kraftgraf import STORLEK_MAX, STORLEK_MIN, hullgrupper
from utils.kraftgraf_ui import (
    _JS_FIL,
    HULL_ETIKETTOPACITET,
    HULL_FYLLOPACITET,
    HULL_KANTOPACITET,
    HULL_UTVIDGNING,
    bygg_kraft_html,
    hullgrupper_for_js,
    kraft_noder,
    kraftkonfig,
    sidopanel_html,
)
from utils.rattssystem_graf import (
    GRUPP_GREN,
    GRUPP_LAG,
    GRUPP_REFERENS,
    GRUPP_ROT,
    bygg_taxonomigraf,
)
from utils.taxonomi_ui import (
    _LAGFARG,
    _REFERENSFARG,
    BAKGRUNDSOPACITET,
    GRENFARGER,
)


@pytest.fixture(scope="module")
def graf():
    return bygg_taxonomigraf()


@pytest.fixture(scope="module")
def noder(graf):
    return kraft_noder(graf)


@pytest.fixture(scope="module")
def html(graf):
    return bygg_kraft_html(graf)


# --- Färgkontraktet ärvs oförändrat -----------------------------------------


def test_kurslagar_ar_paragrafguld(graf, noder):
    guld = {
        n["color"]["background"]
        for n, kalla in zip(noder, graf["noder"])
        if kalla["grupp"] == GRUPP_LAG
    }
    assert guld == {_LAGFARG["bg"]}


def test_referenslagar_ar_blek_guld(graf, noder):
    blek = {
        n["color"]["background"]
        for n, kalla in zip(noder, graf["noder"])
        if kalla["grupp"] == GRUPP_REFERENS
    }
    assert blek == {_REFERENSFARG["bg"]}


def test_strukturnoder_anvander_aldrig_guld(graf, noder):
    for nod, kalla in zip(noder, graf["noder"]):
        if kalla["grupp"] in (GRUPP_GREN, GRUPP_ROT):
            assert nod["color"]["background"] != _LAGFARG["bg"]
            assert nod["color"]["background"] != _REFERENSFARG["bg"]


def test_grenarna_behaller_sin_toppgrensfarg(graf, noder):
    for nod, kalla in zip(noder, graf["noder"]):
        if kalla["grupp"] == GRUPP_GREN:
            assert nod["color"]["background"] == GRENFARGER[kalla["toppgren"]]["bg"]


def test_holjena_far_sin_toppgrens_farg(graf):
    for grupp in hullgrupper_for_js(graf):
        assert grupp["farg"] == GRENFARGER[grupp["id"]]["bg"]


def test_inget_holje_ar_guld(graf):
    fargar = {g["farg"] for g in hullgrupper_for_js(graf)}
    assert _LAGFARG["bg"] not in fargar


# --- Nodstorlek efter grad, inte djup ---------------------------------------


def test_storlekarna_kommer_ur_gradskalan(noder):
    assert all(STORLEK_MIN <= n["size"] <= STORLEK_MAX for n in noder)


def test_roten_ar_storre_an_ett_lov(graf, noder):
    per_id = {n["id"]: n for n in noder}
    lov = next(kalla["id"] for kalla in graf["noder"] if kalla["grupp"] == GRUPP_LAG)
    assert per_id["rot"]["size"] > per_id[lov]["size"]


def test_alla_noder_ar_prickar(noder):
    """Kraftvyns form är pricken, som i graphifys egen vy: boxar med långa
    svenska etiketter täcker varandra så fort fysiken får placera dem."""
    assert {n["shape"] for n in noder} == {"dot"}


# --- Klickbarhet ------------------------------------------------------------


def test_lagnoder_bar_sin_url(graf, noder):
    for nod, kalla in zip(noder, graf["noder"]):
        if kalla["grupp"] in (GRUPP_LAG, GRUPP_REFERENS):
            assert nod["url"].startswith("http")


def test_strukturnoder_har_tom_url(graf, noder):
    for nod, kalla in zip(noder, graf["noder"]):
        if kalla["grupp"] in (GRUPP_GREN, GRUPP_ROT):
            assert nod["url"] == ""


# --- Höljesdatat till JavaScripten ------------------------------------------


def test_holjesdatat_bar_noderna(graf):
    ur_datalagret = {g.id: set(g.nod_id) for g in hullgrupper(graf)}
    for grupp in hullgrupper_for_js(graf):
        assert set(grupp["nod_id"]) == ur_datalagret[grupp["id"]]


def test_holjesdatat_ar_giltig_json(graf, html):
    """Höljena bäddas in som JSON-literal och måste gå att tolka."""
    bit = json.dumps(hullgrupper_for_js(graf), ensure_ascii=False)
    assert json.loads(bit)
    assert "JOK_HULLGRUPPER" in html


# --- Konfigurationen --------------------------------------------------------


def test_konfigurationen_baddas_in(html):
    assert "JOK_KRAFTKONFIG" in html


def test_konfigurationen_bar_alla_varden():
    konfig = kraftkonfig()
    assert konfig["hullUtvidgning"] == HULL_UTVIDGNING
    assert konfig["hullFyllopacitet"] == HULL_FYLLOPACITET
    assert konfig["hullKantopacitet"] == HULL_KANTOPACITET
    assert konfig["hullEtikettopacitet"] == HULL_ETIKETTOPACITET
    assert konfig["bakgrundsopacitet"] == BAKGRUNDSOPACITET


def test_inga_magiska_tal_i_konfigurationen():
    """Varje värde ska komma från en namngiven konstant, inte skrivas två gånger."""
    assert set(kraftkonfig()) == {
        "fysik",
        "hullUtvidgning",
        "hullFyllopacitet",
        "hullKantopacitet",
        "hullEtikettopacitet",
        "hullKantbredd",
        "hullEtikettfont",
        "hullEtikettlyft",
        "bakgrundsopacitet",
        "fokusSkala",
        "animeringMs",
        "kantfarg",
        "sokMaxTraffar",
    }


def test_javascripten_laser_bara_konfigurerade_varden():
    """Varje konfignyckel JS:en läser ska finnas i kraftkonfig()."""
    import re

    from utils.taxonomi_ui import _las_js

    lasta = set(re.findall(r"\bkonfig\.([a-zA-Z]+)", _las_js(_JS_FIL)))
    assert lasta <= set(kraftkonfig())


def test_fysiken_ar_forceatlas2_som_i_graphify():
    """Layouten är graphifys: forceAtlas2Based som fryser efter stabilisering."""
    fysik = kraftkonfig()["fysik"]
    assert fysik["solver"] == "forceAtlas2Based"
    assert fysik["stabiliseringsIterationer"] > 0


# --- JavaScript som egen fil ------------------------------------------------


def test_js_filen_finns():
    """Kraftvyns JS ligger i samma katalog som trädvyns, utils/static/."""
    from utils.taxonomi_ui import _JS_KATALOG

    assert (_JS_KATALOG / _JS_FIL).is_file()


def test_js_baddas_in_i_html(html):
    from utils.taxonomi_ui import _las_js

    assert _las_js(_JS_FIL).strip() in html


def test_fallback_utan_internet(html):
    """Utan vis-network ska rutan säga det, inte stå tom."""
    assert "Kunde inte ladda grafbiblioteket" in html


def test_script_taggar_escapas_i_json(graf):
    """Ingen av kraftvyns nyttolaster får kunna stänga sin script-tagg.

    Mallen har egna riktiga </script>-taggar, så det är JSON-bitarna som
    granskas, inte hela dokumentet.
    """
    from utils.kraftgraf_ui import _json_for_html

    for nyttolast in (kraft_noder(graf), hullgrupper_for_js(graf), kraftkonfig()):
        assert "</script" not in _json_for_html(nyttolast)

    giftig = _json_for_html([{"label": "</script><script>alert(1)</script>"}])
    assert "</script>" not in giftig
    assert "<\\/script>" in giftig
    assert json.loads(giftig.replace("<\\/", "</"))[0]["label"].startswith("</script>")


# --- Sidopanelen ------------------------------------------------------------


def test_sidopanelen_har_sokruta(graf):
    assert 'id="jok-kraft-sok"' in sidopanel_html(graf)


def test_sidopanelen_har_en_kryssruta_per_toppgren(graf):
    panel = sidopanel_html(graf)
    for grupp in hullgrupper(graf):
        assert f'value="{grupp.id}"' in panel


def test_sidopanelen_visar_statistiken(graf):
    from utils.kraftgraf import grafstatistik

    panel = sidopanel_html(graf)
    stat = grafstatistik(graf)
    assert str(stat.kurslagar) in panel
    assert str(stat.referenslagar) in panel


def test_sidopanelens_etiketter_escapas(graf):
    """Etiketterna kommer ur data/rattssystem.json och får inte tolkas som HTML."""
    panel = sidopanel_html(graf)
    assert "<script" not in panel


def test_infopanelen_finns_for_vald_nod(graf):
    assert 'id="jok-kraft-info"' in sidopanel_html(graf)


# --- Kartans egen återställning ---------------------------------------------


def test_aterstallknappen_finns(html):
    assert 'id="jok-kraft-aterstall"' in html


def test_aterstallknappen_ar_dold_tills_vis_laddat(html):
    knapp = html[html.index('id="jok-kraft-aterstall"') :]
    assert "hidden" in knapp[: knapp.index(">")]


def test_grafinstansen_exponeras_for_verifiering(html):
    assert "window.jokKraftgraf" in html
