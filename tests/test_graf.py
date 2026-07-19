"""Tester för kunskapsgrafen: nod/kant-data och HTML-serialisering.

Testar de rena funktionerna i utils.graf och utils.graf_ui utan Streamlit.
Kärnpoängen som verifieras: ett lagrum som förekommer i flera rättsfall blir
en enda nod med kanter från alla fall (det är den delningen grafen finns för),
samt att grafens lagrum matchar det Obsidianexporten wikilänkar.
"""

from __future__ import annotations

from utils.graf import (
    GRUPP_LAGRUM,
    GRUPP_MODUL,
    GRUPP_RATTSFALL,
    bygg_graf,
)
from utils.graf_ui import _bygg_html
from utils.obsidian import CaseAnalys, lagrumsnot  # noqa: F401
from utils.obsidian import _lagrum_i_analys
from utils.scenarier import Case, CaseFacit


def _case(cid: str, rubrik: str, lagrum: tuple[str, ...]) -> Case:
    return Case(
        id=cid,
        rubrik=rubrik,
        svarighetsgrad="grund",
        uppskattad_tid_min=10,
        scenariotext="Ett fiktivt scenario.",
        facit=CaseFacit(
            rattsfraga="En fråga?",
            lagrum=lagrum,
            tillampningspunkter=("Punkt",),
            slutsats="En slutsats.",
        ),
    )


def _svar(norm: str) -> dict[str, str]:
    return {
        "rattsfragan": "r",
        "norm": norm,
        "tillampning": "t",
        "slutsats": "s",
    }


CASE_A = _case("a1", "Anbud och accept", ("1 § AvtL", "6 § AvtL"))
CASE_B = _case("b1", "Oskälighet", ("36 § AvtL", "6 § AvtL"))
ANALYS_A = CaseAnalys("Avtalsrätt", CASE_A, _svar("1 § AvtL"))
ANALYS_B = CaseAnalys("Avtalsrätt", CASE_B, _svar("36 § AvtL"))


def _nod(graf, grupp):
    return [n for n in graf["noder"] if n["grupp"] == grupp]


# --- bygg_graf --------------------------------------------------------------

def test_tom_input_ger_tom_graf():
    graf = bygg_graf([])
    assert graf == {"noder": [], "kanter": []}


def test_graf_har_modul_rattsfall_och_lagrumnoder():
    graf = bygg_graf([ANALYS_A])
    assert len(_nod(graf, GRUPP_MODUL)) == 1
    assert len(_nod(graf, GRUPP_RATTSFALL)) == 1
    labels = {n["label"] for n in _nod(graf, GRUPP_LAGRUM)}
    assert {"1 § AvtL", "6 § AvtL"} <= labels


def test_rattsfall_kopplas_till_sin_modul():
    graf = bygg_graf([ANALYS_A])
    modul_id = next(n["id"] for n in _nod(graf, GRUPP_MODUL))
    case_id = next(n["id"] for n in _nod(graf, GRUPP_RATTSFALL))
    assert {"fran": modul_id, "till": case_id} in graf["kanter"]


def test_delat_lagrum_blir_en_nod_med_kant_fran_bada_fallen():
    graf = bygg_graf([ANALYS_A, ANALYS_B])
    # 6 § AvtL finns i båda fallen -> exakt en lagrumnod.
    delade = [n for n in _nod(graf, GRUPP_LAGRUM) if n["label"] == "6 § AvtL"]
    assert len(delade) == 1
    delad_id = delade[0]["id"]
    kanter_till_delad = [k for k in graf["kanter"] if k["till"] == delad_id]
    assert len(kanter_till_delad) == 2  # ett från vardera rättsfallet


def test_inga_dubblettkanter():
    graf = bygg_graf([ANALYS_A, ANALYS_A])
    par = [(k["fran"], k["till"]) for k in graf["kanter"]]
    assert len(par) == len(set(par))


def test_grafens_lagrum_matchar_obsidianexporten():
    # Grafen ska visa exakt de lagrum valvet wikilänkar för samma analys.
    graf = bygg_graf([ANALYS_A])
    graf_lagrum = {n["label"] for n in _nod(graf, GRUPP_LAGRUM)}
    assert graf_lagrum == set(_lagrum_i_analys(ANALYS_A))


# --- _bygg_html -------------------------------------------------------------

def test_html_bar_med_noder_och_cdn():
    html = _bygg_html(bygg_graf([ANALYS_A]))
    assert "vis-network" in html
    assert "1 § AvtL" in html
    assert "kunskapsgraf" in html


def test_html_serialiserar_giltig_json_utan_script_injektion():
    # Ett elakt label får inte kunna stänga script-taggen.
    case = _case("x", "</script><b>hej", ("1 § AvtL",))
    analys = CaseAnalys("Avtalsrätt", case, _svar("1 § AvtL"))
    html = _bygg_html(bygg_graf([analys]))
    assert "</script><b>" not in html  # neutraliserat till <\/script>
    assert "<\\/script>" in html
