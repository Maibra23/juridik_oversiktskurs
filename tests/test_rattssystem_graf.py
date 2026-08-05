"""Tester för taxonomigrafen över svensk rätt (utils.rattssystem_graf).

Vaktar att grafen är ett strikt träd utan dubblett-id:n, att varje lagnod har
en giltig lagen.nu-URL ur registret, att toppgrenen ärvs nedåt och styr färgen,
och att grafen och Obsidianexportens rättskarta aldrig glider isär (samma lagar).
"""

from __future__ import annotations

import pytest

from utils.lagrum import lagrum_register
from utils.rattssystem_graf import (
    GRUPP_GREN,
    GRUPP_LAG,
    GRUPP_ROT,
    ROT_ID,
    bygg_taxonomigraf,
    taxonomi,
)


@pytest.fixture(scope="module")
def graf():
    return bygg_taxonomigraf()


# --- Struktur ---------------------------------------------------------------


def test_tva_toppgrenar_finns_som_noder(graf):
    """Offentlig rätt och civilrätt ska vara de två grennoderna på nivå 1."""
    toppnoder = [
        n for n in graf["noder"] if n["grupp"] == GRUPP_GREN and n["niva"] == 1
    ]
    assert {n["label"] for n in toppnoder} == {"Offentlig rätt", "Civilrätt"}


def test_juridisk_metod_finns_inte_i_grafen(graf):
    labels = {n["label"] for n in graf["noder"]}
    assert "Juridisk metod" not in labels
    assert not any("AVD" in lbl for lbl in labels)


def test_exakt_en_rot(graf):
    rotnoder = [n for n in graf["noder"] if n["grupp"] == GRUPP_ROT]
    assert len(rotnoder) == 1
    assert rotnoder[0]["id"] == ROT_ID


def test_inga_dubblett_id(graf):
    ider = [n["id"] for n in graf["noder"]]
    assert len(ider) == len(set(ider)), "Nod-id:n måste vara unika"


def test_grafen_ar_ett_strikt_trad(graf):
    """Varje nod utom roten har exakt en förälder: kanter == noder - 1."""
    assert len(graf["kanter"]) == len(graf["noder"]) - 1

    foraldrar: dict[str, int] = {}
    for kant in graf["kanter"]:
        foraldrar[kant["till"]] = foraldrar.get(kant["till"], 0) + 1
    assert all(antal == 1 for antal in foraldrar.values())
    assert ROT_ID not in foraldrar


def test_alla_kanter_pekar_pa_befintliga_noder(graf):
    ider = {n["id"] for n in graf["noder"]}
    for kant in graf["kanter"]:
        assert kant["fran"] in ider
        assert kant["till"] in ider


def test_nivaer_okar_nedat(graf):
    """Ett barn ligger alltid exakt en nivå under sin förälder."""
    niva = {n["id"]: n["niva"] for n in graf["noder"]}
    for kant in graf["kanter"]:
        assert niva[kant["till"]] == niva[kant["fran"]] + 1


def test_toppgren_arvs_nedat(graf):
    """Alla noder utom roten bär en toppgren (offentlig/civil) som styr färg."""
    for nod in graf["noder"]:
        if nod["id"] == ROT_ID:
            continue
        assert nod["toppgren"] in {"offentlig_ratt", "civilratt"}, (
            f"{nod['id']} har oväntad toppgren {nod['toppgren']!r}"
        )


def test_djupt_trad_civilratten_ar_djupare_an_offentliga(graf):
    """Doktrinen är ojämnt djup: köprätten ligger flera nivåer ner."""
    niva_for_label = {n["label"]: n["niva"] for n in graf["noder"]}
    # Civilrätt(1) -> Förmögenhetsrätt(2) -> Obligationsrätt(3)
    # -> Speciell avtalsrätt(4) -> Köp- och konsumenträtt(5)
    assert niva_for_label["Köp- och konsumenträtt"] >= 5


# --- Lagnoder ---------------------------------------------------------------


def test_varje_lagnod_har_giltig_lagen_nu_url(graf):
    register = lagrum_register()
    lagnoder = [n for n in graf["noder"] if n["grupp"] == GRUPP_LAG]
    assert lagnoder

    for nod in lagnoder:
        url = nod.get("url", "")
        assert url.startswith("https://lagen.nu/"), f"{nod['label']}: {url!r}"
        forkortning = nod["label"]
        assert forkortning in register
        assert url == register[forkortning].lagen_nu_bas_url


def test_endast_lagnoder_ar_klickbara(graf):
    for nod in graf["noder"]:
        if nod["grupp"] != GRUPP_LAG:
            assert "url" not in nod, f"{nod['id']} borde inte vara klickbar"


def test_alla_registrets_lagar_finns_i_grafen(graf):
    lagnoder = {n["forkortning"] for n in graf["noder"] if n["grupp"] == GRUPP_LAG}
    assert lagnoder == set(lagrum_register())


def test_grafen_och_rattskartan_tacker_samma_lagar(graf):
    from utils.rattskarta import _lagindex

    lagnoder = {n["forkortning"] for n in graf["noder"] if n["grupp"] == GRUPP_LAG}
    assert lagnoder == set(_lagindex())


def test_lagnoder_bar_sin_forkortning_som_eget_falt(graf):
    for nod in graf["noder"]:
        if nod["grupp"] == GRUPP_LAG:
            assert nod["forkortning"]
            assert nod["label"] == nod["forkortning"]


def test_samma_lag_i_tva_grenar_ger_tva_distinkta_noder():
    """lag_id skopas efter gren så samma lag kan förekomma flera gånger."""
    from utils.rattssystem_graf import lag_id

    a = lag_id("avtalsratt", "AvtL")
    b = lag_id("kop_och_konsumentratt", "AvtL")
    assert a != b, "lagnod-id måste vara skopat efter gren"
    assert "AvtL" in a and "AvtL" in b
    assert "avtalsratt" in a and "kop_och_konsumentratt" in b


# --- Taxonomiträdet ---------------------------------------------------------


def test_taxonomin_ger_toppgrenarna():
    grenar = taxonomi()
    assert [g.id for g in grenar] == ["offentlig_ratt", "civilratt"]


def test_nyckelgrenar_finns_som_noder(graf):
    labels = {n["label"] for n in graf["noder"]}
    for vantad in (
        "Förmögenhetsrätt", "Obligationsrätt", "Speciell avtalsrätt", "Sakrätt",
    ):
        assert vantad in labels, f"{vantad} saknas i grafen"


# --- Fail fast i inläsningen ------------------------------------------------


@pytest.mark.parametrize(
    ("mutation", "vantat_fel"),
    [
        ("bade_grenar_och_lagar", "antingen 'grenar' eller 'lagar'"),
        ("okand_farg", "okänd callout-färg"),
    ],
)
def test_trasig_data_ger_tydligt_fel(monkeypatch, tmp_path, mutation, vantat_fel):
    """Fail fast: en tvetydig gren eller okänd färg får inte laddas tyst."""
    import json

    from utils.rattskarta import DATA_PATH, ladda_rattssystem

    rad = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if mutation == "bade_grenar_och_lagar":
        rad["grenar"][0]["lagar"] = []  # har redan 'grenar'
    else:
        rad["grenar"][0]["farg"] = "finns_inte"

    trasig = tmp_path / "rattssystem.json"
    trasig.write_text(json.dumps(rad, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr("utils.rattskarta.DATA_PATH", trasig)
    ladda_rattssystem.cache_clear()
    try:
        with pytest.raises(ValueError, match=vantat_fel):
            ladda_rattssystem()
    finally:
        ladda_rattssystem.cache_clear()


# --- Falltypsguidens sökbarhet ----------------------------------------------


def test_falltypsguiden_har_sokord_for_varje_rad():
    from utils.rattskarta import falltypsguide

    guide = falltypsguide()
    assert len(guide) == 16
    for situation, lag, sokord in guide:
        assert sokord, f"{situation!r} saknar sökord"
        assert lag and "[[" not in lag


@pytest.mark.parametrize(
    "fras",
    [
        "uppsagd", "arv", "konkurs", "skilsmässa", "omyndig", "stöld",
        "reklamation", "kronofogden", "bodelning", "testamente",
        "aktiebolag", "fastighet", "skadestånd", "domstol", "skuldebrev",
    ],
)
def test_naturliga_sokningar_ger_traff(fras):
    from utils.rattskarta import falltypsguide

    traffar = [
        s
        for s, lag, sokord in falltypsguide()
        if fras in s.lower() or fras in lag.lower() or fras in sokord
    ]
    assert traffar, f"Sökningen {fras!r} gav inga träffar i falltypsguiden"


def test_falltypsguiden_paverkar_inte_vaultens_markdown():
    from utils.rattskarta import rattskarta_not

    not_md = rattskarta_not()
    assert "kronofogden utmätning" not in not_md.lower()
    assert "| Situationen | Börja här |" in not_md


# --- Släktskap --------------------------------------------------------------


def test_varje_nods_foralder_matchar_kantlistan(graf):
    """foralder ska vara härledd ur samma träd som kanterna, inte gissad."""
    per_id = {n["id"]: n for n in graf["noder"]}
    for kant in graf["kanter"]:
        barn = per_id[kant["till"]]
        assert barn["foralder"] == kant["fran"], (
            f"{barn['label']} pekar på {barn['foralder']}, "
            f"men kanten kommer från {kant['fran']}"
        )


def test_endast_roten_saknar_foralder(graf):
    """Ett strikt träd har exakt en nod utan förälder."""
    utan = [n["id"] for n in graf["noder"] if not n["foralder"]]
    assert utan == [ROT_ID]


def test_alla_noder_bar_faltet(graf):
    """Saknas fältet på någon nod faller JS-sidans föräldrakarta tyst."""
    for nod in graf["noder"]:
        assert "foralder" in nod, f"{nod['label']} saknar foralder"
