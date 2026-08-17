"""Tester för kraftgrafens datalager (utils.kraftgraf).

Kraftvyn ritar samma taxonomi som den hierarkiska vyn, men låter en
fysiksimulering placera noderna och ringar in varje toppgren med ett hölje.
Det här lagret räknar ut allt som inte är rendering: nodernas grad, deras
storlek, vilka noder som hör till vilket hölje och kartans statistik.

Rent Python utan Streamlit och utan färger — färgsättningen hör till
utils.kraftgraf_ui, som äger designsystemets palett.
"""

from __future__ import annotations

import pytest

from utils.kraftgraf import (
    STORLEK_MAX,
    STORLEK_MIN,
    grafstatistik,
    hullgrupper,
    nodgrader,
    nodstorlek,
)
from utils.rattssystem_graf import (
    GRUPP_LAG,
    GRUPP_REFERENS,
    ROT_ID,
    bygg_taxonomigraf,
)


@pytest.fixture(scope="module")
def graf():
    return bygg_taxonomigraf()


# --- Nodernas grad ----------------------------------------------------------


def test_varje_nod_far_en_grad(graf):
    grader = nodgrader(graf)
    assert set(grader) == {n["id"] for n in graf["noder"]}


def test_lovnoder_har_grad_ett(graf):
    """En lag är ett löv: enda kanten är den upp till sin gren."""
    grader = nodgrader(graf)
    lagnoder = [
        n["id"] for n in graf["noder"] if n["grupp"] in (GRUPP_LAG, GRUPP_REFERENS)
    ]
    assert lagnoder
    assert all(grader[nid] == 1 for nid in lagnoder)


def test_roten_har_grad_lika_med_antalet_toppgrenar(graf):
    grader = nodgrader(graf)
    toppgrenar = [n for n in graf["noder"] if n.get("foralder") == ROT_ID]
    assert grader[ROT_ID] == len(toppgrenar)


def test_gradsumman_ar_dubbla_antalet_kanter(graf):
    """Handskakningslemmat: varje kant bidrar med ett till två noder."""
    grader = nodgrader(graf)
    assert sum(grader.values()) == 2 * len(graf["kanter"])


# --- Nodstorlek -------------------------------------------------------------


def test_minsta_graden_ger_minsta_storleken():
    assert nodstorlek(1, 12) == STORLEK_MIN


def test_hogsta_graden_ger_storsta_storleken():
    assert nodstorlek(12, 12) == STORLEK_MAX


def test_storleken_vaxer_monotont_med_graden():
    storlekar = [nodstorlek(grad, 12) for grad in range(1, 13)]
    assert storlekar == sorted(storlekar)


def test_storleken_haller_sig_inom_skalan():
    assert all(STORLEK_MIN <= nodstorlek(g, 12) <= STORLEK_MAX for g in range(1, 13))


def test_ensam_nod_kraschar_inte():
    """Maxgrad 1 ger en division med noll om skalan inte skyddas."""
    assert nodstorlek(1, 1) == STORLEK_MIN


# --- Höljen per toppgren ----------------------------------------------------


def test_ett_holje_per_toppgren(graf):
    grupper = hullgrupper(graf)
    toppgrenar = {n["toppgren"] for n in graf["noder"] if n.get("toppgren")}
    assert {g.id for g in grupper} == toppgrenar


def test_holjena_tacker_alla_noder_utom_roten(graf):
    grupper = hullgrupper(graf)
    i_holje = {nid for g in grupper for nid in g.nod_id}
    alla = {n["id"] for n in graf["noder"]}
    assert i_holje == alla - {ROT_ID}


def test_holjena_overlappar_inte(graf):
    """En nod ärver exakt en toppgren, så höljena är disjunkta."""
    grupper = hullgrupper(graf)
    sedda: set[str] = set()
    for grupp in grupper:
        assert not (sedda & set(grupp.nod_id))
        sedda |= set(grupp.nod_id)


def test_holjet_bar_toppgrenens_namn(graf):
    grupper = hullgrupper(graf)
    etiketter = {g.id: g.etikett for g in grupper}
    assert etiketter["civilratt"] == "Civilrätt"
    assert etiketter["offentlig_ratt"] == "Offentlig rätt"


def test_holjena_foljer_datats_ordning(graf):
    """Legenden och höljena ska räknas upp i samma ordning som kartan."""
    from utils.rattssystem_graf import taxonomi

    ordning = [g.id for g in taxonomi()]
    grupper = [g.id for g in hullgrupper(graf)]
    assert grupper == [gid for gid in ordning if gid in set(grupper)]


def test_ren_kursvy_ger_bara_kvarvarande_toppgrenar():
    """Utan referenslagar städas EU-rätten bort och får inget hölje."""
    grupper = hullgrupper(bygg_taxonomigraf(inkludera_referens=False))
    assert "internationell_ratt" not in {g.id for g in grupper}


# --- Statistik --------------------------------------------------------------


def test_statistiken_raknar_noderna(graf):
    stat = grafstatistik(graf)
    assert stat.noder == len(graf["noder"])


def test_statistiken_skiljer_kurslag_fran_referenslag(graf):
    stat = grafstatistik(graf)
    kurs = sum(1 for n in graf["noder"] if n["grupp"] == GRUPP_LAG)
    referens = sum(1 for n in graf["noder"] if n["grupp"] == GRUPP_REFERENS)
    assert (stat.kurslagar, stat.referenslagar) == (kurs, referens)


def test_statistikens_delar_summerar_till_helheten(graf):
    stat = grafstatistik(graf)
    assert stat.grenar + stat.kurslagar + stat.referenslagar + 1 == stat.noder


def test_djupet_ar_den_djupaste_nivan(graf):
    stat = grafstatistik(graf)
    assert stat.djup == max(n.get("niva", 0) for n in graf["noder"])


# --- Startpositioner --------------------------------------------------------


def test_varje_nod_far_en_startposition(graf):
    from utils.kraftgraf import startpositioner

    pos = startpositioner(graf)
    assert set(pos) == {n["id"] for n in graf["noder"]}


def test_roten_startar_i_origo(graf):
    from utils.kraftgraf import startpositioner

    assert startpositioner(graf)[ROT_ID] == (0, 0)


def test_radien_vaxer_med_nivan(graf):
    """Djupare noder startar längre ut från sin egen grens mittpunkt."""
    from utils.kraftgraf import startpositioner

    pos = startpositioner(graf)
    for grupp in hullgrupper(graf):
        punkter = [pos[nid] for nid in grupp.nod_id]
        mx = sum(x for x, _ in punkter) / len(punkter)
        my = sum(y for _, y in punkter) / len(punkter)
        per_niva: dict[int, list[float]] = {}
        nivaer = {n["id"]: n["niva"] for n in graf["noder"]}
        for nid in grupp.nod_id:
            x, y = pos[nid]
            per_niva.setdefault(nivaer[nid], []).append(
                ((x - mx) ** 2 + (y - my) ** 2) ** 0.5
            )
        medel = [sum(v) / len(v) for _, v in sorted(per_niva.items())]
        assert medel == sorted(medel), grupp.id


def test_grenarna_startar_langre_ifran_varandra_an_de_ar_breda(graf):
    """Invarianten som gör att höljena går att rita utan att de skär varandra.

    Två grenar vars mittpunkter ligger närmare varandra än deras egna radier
    får överlappande skivor, och därmed konvexa höljen som växer in i varandra.
    """
    from utils.kraftgraf import startpositioner

    pos = startpositioner(graf)
    mitt = {}
    radie = {}
    for grupp in hullgrupper(graf):
        punkter = [pos[nid] for nid in grupp.nod_id]
        mx = sum(x for x, _ in punkter) / len(punkter)
        my = sum(y for _, y in punkter) / len(punkter)
        mitt[grupp.id] = (mx, my)
        radie[grupp.id] = max(
            ((x - mx) ** 2 + (y - my) ** 2) ** 0.5 for x, y in punkter
        )

    idn = list(mitt)
    for i, a in enumerate(idn):
        for b in idn[i + 1 :]:
            avstand = (
                (mitt[a][0] - mitt[b][0]) ** 2 + (mitt[a][1] - mitt[b][1]) ** 2
            ) ** 0.5
            assert avstand > radie[a] + radie[b], f"{a} och {b} startar ovanpå varandra"


def test_toppgrenarna_startar_i_skilda_vadrar(graf):
    """Varje toppgren får sin egen sektor, annars växer höljena in i varandra."""
    import math

    from utils.kraftgraf import startpositioner

    pos = startpositioner(graf)
    vinklar = {}
    for grupp in hullgrupper(graf):
        punkter = [pos[nid] for nid in grupp.nod_id]
        vinklar[grupp.id] = math.atan2(
            sum(y for _, y in punkter) / len(punkter),
            sum(x for x, _ in punkter) / len(punkter),
        )
    varden = list(vinklar.values())
    assert len(varden) > 1
    for i, a in enumerate(varden):
        for b in varden[i + 1 :]:
            skillnad = abs(math.atan2(math.sin(a - b), math.cos(a - b)))
            assert skillnad > 0.5


def test_positionerna_ar_deterministiska(graf):
    from utils.kraftgraf import startpositioner

    assert startpositioner(graf) == startpositioner(graf)
