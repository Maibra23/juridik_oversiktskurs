"""Tester för taxonomigrafen över svensk rätt (utils.rattssystem_graf).

Vaktar tre saker:
- att alla fyra avdelningar ur bokens disposition finns med,
- att grafen är ett strikt träd utan dubblett-id:n,
- att varje lagnod har en giltig lagen.nu-URL ur registret,

samt att grafen och Obsidianexportens rättskarta aldrig glider isär: båda
ska täcka exakt samma lagar.
"""

from __future__ import annotations

import pytest

from utils.lagrum import lagrum_register
from utils.rattssystem_graf import (
    GRUPP_AVDELNING,
    GRUPP_LAG,
    GRUPP_OMRADE,
    GRUPP_ROT,
    GRUPP_UNDEROMRADE,
    ROT_ID,
    bygg_taxonomigraf,
    taxonomi,
)


@pytest.fixture(scope="module")
def graf():
    return bygg_taxonomigraf()


# --- Struktur ---------------------------------------------------------------


def test_alla_fyra_avdelningar_finns_som_noder(graf):
    """Bokens fyra avdelningar ska alla vara egna noder, även tomma AVD I."""
    avdelningsnoder = [n for n in graf["noder"] if n["grupp"] == GRUPP_AVDELNING]
    assert len(avdelningsnoder) == 4
    from utils.rattskarta import ladda_avdelningar

    assert {n["label"] for n in avdelningsnoder} == {
        a.label for a in ladda_avdelningar()
    }


def test_avd1_tas_med_trots_att_den_saknar_rattsomraden():
    """AVD I har inga områden i datat men ska ändå synas, med en modullänk."""
    avd1 = next(a for a in taxonomi() if a.id == "avd1_introduktion")
    assert avd1.omraden == ()
    assert avd1.sida == "pages/1_Juridisk_metod.py"


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


def test_avdelning_arvs_nedat(graf):
    """Alla noder utom roten bär ett avdelnings-id som styr färgen."""
    for nod in graf["noder"]:
        if nod["id"] == ROT_ID:
            continue
        assert nod["avdelning"], f"{nod['id']} saknar avdelning"


# --- Lagnoder ---------------------------------------------------------------


def test_varje_lagnod_har_giltig_lagen_nu_url(graf):
    """Lagnoder ska ha en URL ur registret, aldrig en konstruerad."""
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
    """Strukturnoder får aldrig url: de ska vara inerta vid klick."""
    for nod in graf["noder"]:
        if nod["grupp"] != GRUPP_LAG:
            assert "url" not in nod, f"{nod['id']} borde inte vara klickbar"


def test_alla_registrets_lagar_finns_i_grafen(graf):
    lagnoder = {n["forkortning"] for n in graf["noder"] if n["grupp"] == GRUPP_LAG}
    assert lagnoder == set(lagrum_register())


def test_grafen_och_rattskartan_tacker_samma_lagar(graf):
    """App och Obsidianvalv får aldrig glida isär om vilka lagar som ingår."""
    from utils.rattskarta import _lagindex

    lagnoder = {n["forkortning"] for n in graf["noder"] if n["grupp"] == GRUPP_LAG}
    assert lagnoder == set(_lagindex())


def test_lagnoder_bar_sin_forkortning_som_eget_falt(graf):
    """Förkortningen läses ur ett fält, aldrig ur nod-id:t eller etiketten.

    Id:t är skopat efter förälder (se testet nedan) och går därför inte att
    tolka som en förkortning.
    """
    for nod in graf["noder"]:
        if nod["grupp"] == GRUPP_LAG:
            assert nod["forkortning"]
            assert nod["label"] == nod["forkortning"]


def test_samma_lag_i_tva_delomraden_ger_tva_distinkta_noder():
    """En lag kan höra till flera delområden utan att grafen kraschar.

    lag_id() skopades tidigare bara på förkortningen. En lag som lades under
    två delområden gav då två noder med samma id, vilket får vis.DataSet att
    kasta i webbläsaren och bryter trädinvarianten. Noden ska i stället
    dupliceras per förälder: att AvtL bär både avtalsrätt och allmän
    förmögenhetsrätt är sant och ska synas på båda ställena.
    """
    from utils.rattssystem_graf import lag_id

    a = lag_id("avtalsratt", "AvtL")
    b = lag_id("allman_formogenhetsratt", "AvtL")
    assert a != b, "lagnod-id måste vara skopat efter delområde"
    assert "AvtL" in a and "AvtL" in b
    assert "avtalsratt" in a and "allman_formogenhetsratt" in b


# --- Taxonomiträdet ---------------------------------------------------------


def test_taxonomin_har_alla_omraden_och_underomraden(graf):
    omraden = [n for n in graf["noder"] if n["grupp"] == GRUPP_OMRADE]
    underomraden = [n for n in graf["noder"] if n["grupp"] == GRUPP_UNDEROMRADE]
    assert len(omraden) == 5
    assert len(underomraden) == 16


def test_taxonomin_hamtar_lagnamn_ur_registret():
    """Namn och SFS dupliceras aldrig i kartdatat utan kommer ur registret."""
    from utils.rattssystem_graf import alla_lagar

    register = lagrum_register()
    lagar = list(alla_lagar())
    assert lagar
    for lag in lagar:
        assert lag.namn == register[lag.forkortning].namn
        assert lag.sfs == register[lag.forkortning].sfs


@pytest.mark.parametrize(
    ("trasig_nyckel", "vantat_fel"),
    [
        ("okand", "okänd avdelning"),
        ("saknas", "saknar nyckeln 'avdelning'"),
    ],
)
def test_omrade_utan_giltig_avdelning_ger_tydligt_fel(
    monkeypatch, tmp_path, trasig_nyckel, vantat_fel
):
    """Fail fast: ett område utanför dispositionen får inte tappas tyst.

    Valideringen bor numera i utils.rattskarta.ladda_rattssystem, som är den
    enda som läser datat. Cacherna måste tömmas både före och efter, annars
    läcker den trasiga kartan in i efterföljande tester.
    """
    import json

    from utils.rattskarta import DATA_PATH, ladda_avdelningar, ladda_rattssystem

    rad = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if trasig_nyckel == "okand":
        rad["omraden"][0]["avdelning"] = "avd_finns_inte"
    else:
        del rad["omraden"][0]["avdelning"]

    trasig = tmp_path / "rattssystem.json"
    trasig.write_text(json.dumps(rad, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setattr("utils.rattskarta.DATA_PATH", trasig)
    ladda_rattssystem.cache_clear()
    ladda_avdelningar.cache_clear()
    try:
        with pytest.raises(ValueError, match=vantat_fel):
            ladda_rattssystem()
    finally:
        ladda_rattssystem.cache_clear()
        ladda_avdelningar.cache_clear()


# --- Falltypsguidens sökbarhet ----------------------------------------------


def test_falltypsguiden_har_sokord_for_varje_rad():
    """Varje falltyp ska bära sökord, annars blir tabellen osökbar."""
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
    """De ord en student faktiskt söker på måste hitta rätt rad.

    Situationstexterna är böjda meningar ("sagts upp"), så ren
    delsträngsmatchning räcker inte.
    """
    from utils.rattskarta import falltypsguide

    traffar = [
        s
        for s, lag, sokord in falltypsguide()
        if fras in s.lower() or fras in lag.lower() or fras in sokord
    ]
    assert traffar, f"Sökningen {fras!r} gav inga träffar i falltypsguiden"


def test_falltypsguiden_paverkar_inte_vaultens_markdown():
    """Sökorden är ett apptillägg och får aldrig läcka in i valvet."""
    from utils.rattskarta import rattskarta_not

    not_md = rattskarta_not()
    assert "kronofogden utmätning" not in not_md.lower()
    assert "| Situationen | Börja här |" in not_md
