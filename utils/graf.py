"""Kunskapsgraf: genomförda rättsfall och deras lagrum som nod/kant-data.

Ren Python utan Streamlit. Omvandlar registrerade rättsfallsanalyser
(``CaseAnalys`` från utils.obsidian) till en graf
``{"noder": [...], "kanter": [...]}`` där varje lagrum binder ihop de rättsfall
som tillämpat det — samma lagrum-till-rättsfall-länkar som Obsidianexporten
räknar fram (lagrummen extraheras med utils.obsidian så graf och valv aldrig
divergerar). Deterministisk, inget LLM, så den fungerar även när budgettaket
är nått.
"""

from __future__ import annotations

from typing import Iterable, TypedDict

# _lagrum_i_analys återanvänds (obsidian.py lämnas orörd) så att grafen visar
# exakt samma lagrum som valvet wikilänkar.
from utils.obsidian import CaseAnalys
from utils.obsidian import _lagrum_i_analys as lagrum_i_analys

# Nodgrupper (styr färg och form i graf_ui, följer designsystemets palett).
GRUPP_MODUL = "modul"
GRUPP_RATTSFALL = "rattsfall"
GRUPP_LAGRUM = "lagrum"


class Nod(TypedDict):
    id: str
    label: str
    grupp: str


class Kant(TypedDict):
    fran: str
    till: str


class Graf(TypedDict):
    noder: list[Nod]
    kanter: list[Kant]


def _modul_id(modul: str) -> str:
    return f"modul::{modul}"


def _case_id(analys: CaseAnalys) -> str:
    return f"case::{analys.modul}::{analys.case.id}"


def _lagrum_id(ref: str) -> str:
    return f"lagrum::{ref}"


def bygg_graf(poster: Iterable[CaseAnalys]) -> Graf:
    """Bygg nod/kant-data av genomförda analyser.

    Varje modul, rättsfall och lagrum blir en unik nod (dedupliceras på id).
    Kanter går modul → rättsfall och rättsfall → lagrum. Ett lagrum som
    förekommer i flera rättsfall blir därför en enda nod med kanter från alla
    fall — det är den delningen som gör grafen pedagogiskt värdefull.
    """
    noder: dict[str, Nod] = {}
    kanter: list[Kant] = []
    sedda_kanter: set[tuple[str, str]] = set()

    def lagg_nod(nid: str, label: str, grupp: str) -> None:
        noder.setdefault(nid, {"id": nid, "label": label, "grupp": grupp})

    def lagg_kant(fran: str, till: str) -> None:
        if (fran, till) not in sedda_kanter:
            sedda_kanter.add((fran, till))
            kanter.append({"fran": fran, "till": till})

    for analys in poster:
        mid = _modul_id(analys.modul)
        cid = _case_id(analys)
        lagg_nod(mid, analys.modul, GRUPP_MODUL)
        lagg_nod(cid, analys.case.rubrik, GRUPP_RATTSFALL)
        lagg_kant(mid, cid)

        for ref in lagrum_i_analys(analys):
            lid = _lagrum_id(ref)
            lagg_nod(lid, ref, GRUPP_LAGRUM)
            lagg_kant(cid, lid)

    return {"noder": list(noder.values()), "kanter": kanter}
