"""Tester för renderingen av taxonomigrafen (utils.taxonomi_ui).

Vaktar det som gör grafen användbar och designsystemsenlig:
- att lagnoder är klickbara och bär rätt lagen.nu-URL,
- att strukturnoder inte är klickbara,
- att guld används för lagar och aldrig för strukturnivåerna,
- att färglegenden ritas som riktiga färgrutor, inte som prosa.
"""

from __future__ import annotations

import json

import pytest

from utils.lagrum import lagrum_register
from utils.rattssystem_graf import GRUPP_LAG, bygg_taxonomigraf
from utils.taxonomi_ui import (
    _LAGFARG,
    BAKGRUNDSOPACITET,
    FOKUS_ANIMERING_MS,
    GRENFARGER,
    KEDJEBREDD,
    KEDJEFARG,
    MAX_FOKUS_SKALA,
    MIN_SKALA_FAKTOR,
    _vis_noder,
    bygg_html,
    farglegend_html,
)


@pytest.fixture(scope="module")
def graf():
    return bygg_taxonomigraf()


@pytest.fixture(scope="module")
def html(graf):
    return bygg_html(graf)


# --- Klickbarhet ------------------------------------------------------------


def test_klickhanterare_oppnar_ny_flik(html):
    assert "network.on(\"click\"" in html
    assert "window.open(nod.url" in html
    assert '"_blank"' in html
    assert "noopener,noreferrer" in html


def test_lagnoder_bar_sin_lagen_nu_url(graf, html):
    """Varje lags URL ska finnas i den inbäddade JSON-datan."""
    register = lagrum_register()
    for nod in graf["noder"]:
        if nod["grupp"] == GRUPP_LAG:
            assert register[nod["label"]].lagen_nu_bas_url in html


def test_strukturnoder_har_tom_url(graf):
    """Endast lagnoder är klickbara; övriga får tom url och blir inerta."""
    for vis_nod, kall_nod in zip(_vis_noder(graf), graf["noder"]):
        if kall_nod["grupp"] == GRUPP_LAG:
            assert vis_nod["url"], f"{kall_nod['label']} borde vara klickbar"
        else:
            assert vis_nod["url"] == "", f"{kall_nod['label']} borde vara inert"


def test_markoren_signalerar_klickbarhet(html):
    assert "hoverNode" in html
    assert "pointer" in html


# --- Färgsättning -----------------------------------------------------------


def test_lagnoder_ar_paragrafguld(graf):
    """Guld betyder alltid lag eller lagrum (design_system.md avsnitt 1)."""
    for vis_nod, kall_nod in zip(_vis_noder(graf), graf["noder"]):
        if kall_nod["grupp"] == GRUPP_LAG:
            assert vis_nod["color"]["background"] == _LAGFARG["bg"] == "#B8860B"


def test_strukturnoder_anvander_aldrig_guld(graf):
    """Navigeringsnivåerna får inte konkurrera med lagrumsguldet."""
    guld = {"#B8860B", "#8A6608"}
    for vis_nod, kall_nod in zip(_vis_noder(graf), graf["noder"]):
        if kall_nod["grupp"] != GRUPP_LAG:
            assert vis_nod["color"]["background"] not in guld
            assert vis_nod["color"]["border"] not in guld


def test_varje_toppgren_har_egen_farg():
    farger = [f["bg"] for f in GRENFARGER.values()]
    assert len(farger) == 2
    assert len(set(farger)) == 2, "Toppgrenarna måste gå att skilja åt"


def test_offentlig_och_civil_far_olika_farg(graf):
    """Strukturnoder ska färgas efter sin toppgren, inte efter djup."""
    from utils.rattssystem_graf import GRUPP_GREN

    farg_for = {}
    for vis_nod, kall_nod in zip(_vis_noder(graf), graf["noder"]):
        tg = kall_nod.get("toppgren")
        if kall_nod["grupp"] == GRUPP_GREN and tg in GRENFARGER:
            farg_for[tg] = vis_nod["color"]["background"]
    assert farg_for["offentlig_ratt"] != farg_for["civilratt"]
    assert "#B8860B" not in farg_for.values()  # aldrig lagrumsguld


def test_noderna_ar_giltig_json(graf, html):
    """JSON-blocket ska gå att parsa, annars ritas inget alls."""
    start = html.index("const noder = ") + len("const noder = ")
    slut = html.index(";\n", start)
    noder = json.loads(html[start:slut])
    assert len(noder) == len(graf["noder"])


# --- Färglegend -------------------------------------------------------------


def test_legenden_ritar_fargrutor_inte_prosa():
    legend = farglegend_html()
    assert legend.count("jok-swatch") == 4  # rot + två toppgrenar + lag
    for farg in GRENFARGER.values():
        assert farg["bg"] in legend
    assert _LAGFARG["bg"] in legend


def test_legenden_forklarar_att_lagar_ar_klickbara():
    assert "lagen.nu" in farglegend_html()


# --- Robusthet --------------------------------------------------------------


def test_fallback_utan_internet(html):
    """Utan CDN ska komponenten säga till och peka på områdesträdet."""
    assert "Kunde inte ladda grafbiblioteket" in html
    assert "Områdesträdet nedanför fungerar ändå" in html


def test_script_taggar_escapas_i_json():
    """En etikett med </script> får aldrig kunna stänga script-taggen."""
    from utils.taxonomi_ui import _json_for_html

    ut = _json_for_html([{"label": "</script><script>alert(1)</script>"}])
    assert "</script>" not in ut
    assert "<\\/script>" in ut
    # Datat ska fortfarande gå att parsa tillbaka i webbläsaren.
    assert json.loads(ut.replace("<\\/", "</"))[0]["label"].startswith("</script>")


# --- Konfiguration ----------------------------------------------------------


def test_vis_noder_bar_foralder(graf):
    """Utan foralder kan JS:en inte bygga sin föräldrakarta."""
    for vis_nod, kall_nod in zip(_vis_noder(graf), graf["noder"]):
        assert vis_nod["foralder"] == kall_nod["foralder"]


def test_konfigurationen_baddas_in(html):
    assert "JOK_GRAFKONFIG" in html


def test_konfigurationen_bar_alla_varden():
    from utils.taxonomi_ui import grafkonfig

    konfig = grafkonfig()
    assert konfig["bakgrundsopacitet"] == BAKGRUNDSOPACITET
    assert konfig["minSkalaFaktor"] == MIN_SKALA_FAKTOR
    assert konfig["maxFokusSkala"] == MAX_FOKUS_SKALA
    assert konfig["animeringMs"] == FOKUS_ANIMERING_MS
    assert konfig["kedjefarg"] == KEDJEFARG
    assert konfig["kedjebredd"] == KEDJEBREDD


def test_inga_magiska_tal_i_konfigurationen():
    """Varje värde ska komma från en namngiven konstant, inte skrivas två gånger."""
    from utils.taxonomi_ui import grafkonfig

    assert set(grafkonfig()) == {
        "bakgrundsopacitet",
        "minSkalaFaktor",
        "maxFokusSkala",
        "animeringMs",
        "kedjefarg",
        "kedjebredd",
        "kantfarg",
    }


# --- JavaScript som egen fil ------------------------------------------------


def test_js_filen_finns():
    from utils.taxonomi_ui import _JS_KATALOG

    assert (_JS_KATALOG / "taxonomigraf.js").is_file()


def test_js_baddas_in_i_html(html):
    """Innehållet ska ligga i svaret, inte länkas — iframen är sandboxad."""
    from utils.taxonomi_ui import _las_js

    assert _las_js("taxonomigraf.js").strip() in html


def test_saknad_js_fil_ger_tydligt_fel():
    from utils.taxonomi_ui import _las_js

    with pytest.raises(FileNotFoundError, match="Grafens JavaScript saknas"):
        _las_js("finns_inte.js")


def test_logikfilen_baddas_in_fore_dom_filen(html):
    """DOM-lagret anropar beraknaSkikt, så logiken måste komma först."""
    from utils.taxonomi_ui import _las_js

    logik = _las_js("taxonomigraf_logik.js").strip()
    dom = _las_js("taxonomigraf.js").strip()
    assert logik in html and dom in html
    assert html.index(logik) < html.index(dom)


# --- Kartans egen återställning ---------------------------------------------


def test_overlayknappen_finns_i_grafen(html):
    assert "jok-aterstall-vy" in html
    assert "Återställ vyn" in html


def test_overlayknappen_ligger_inuti_grafcontainern(html):
    """Knappen ska följa med grafens ram, inte flyta ovanpå sidan."""
    assert html.index('id="taxonomigraf"') < html.index("jok-aterstall-vy")


def test_overlayknappen_ar_dold_tills_vis_laddat(html):
    """I CDN-fallbacken får ingen knapp stå kvar och lova interaktivitet."""
    knapp_start = html.index("jok-aterstall-vy")
    assert "hidden" in html[knapp_start : knapp_start + 200]
