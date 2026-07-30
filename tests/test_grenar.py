"""Tester för rättssystemets doktrinära trädstruktur.

Ersätter de gamla avdelningstesterna. Vaktar att trädet följer rättens
systematik: två toppgrenar (offentlig rätt, civilrätt), straffrätt och
processrätt under offentlig rätt, och köp-/arbetsrätt som speciell avtalsrätt
under obligationsrätt under förmögenhetsrätt. Vaktar också det hårda kontraktet
mot begreppsdatat: de 14 delområdes-id:na måste finnas kvar.
"""

from __future__ import annotations

from utils.rattskarta import (
    delomraden,
    hitta_gren,
    ladda_rattssystem,
    toppgrenar,
)

# Delområdes-id som data/nyckelbegrepp.json knyter begrepp till. Får aldrig
# försvinna ur trädet utan att begreppsdatat migreras samtidigt.
BEGREPP_DELOMRADEN = {
    "avtalsratt",
    "kop_och_konsumentratt",
    "skadestandsratt",
    "arbetsratt",
    "fastighetsratt",
    "associationsratt",
    "fordringsratt",
    "personratt",
    "makar_och_sambor",
    "foraldrar_och_barn",
    "arv_och_testamente",
    "brott_och_ansvar",
    "rattegangen",
    "verkstallighet_och_obestand",
}


def test_tva_toppgrenar_i_ordning():
    grenar = toppgrenar()
    assert [g.id for g in grenar] == ["offentlig_ratt", "civilratt"]


def test_toppgrenarna_bar_ratt_farg():
    farger = {g.id: g.farg for g in ladda_rattssystem()}
    assert farger["offentlig_ratt"] == "quote"
    assert farger["civilratt"] == "info"


def test_toppgren_arvs_nedat_pa_varje_gren():
    for topp in ladda_rattssystem():
        _kontrollera_toppgren(topp, topp.id)


def _kontrollera_toppgren(gren, forvantad):
    assert gren.toppgren == forvantad, f"{gren.id} har fel toppgren"
    for barn in gren.grenar:
        _kontrollera_toppgren(barn, forvantad)


def test_alla_begreppsdelomraden_finns_kvar():
    lov_ider = {lov.id for lov in delomraden()}
    saknade = BEGREPP_DELOMRADEN - lov_ider
    assert not saknade, f"Delområden som begrepp pekar på saknas: {saknade}"


def test_straffratt_och_process_ligger_under_offentlig_ratt():
    for lov_id in ("brott_och_ansvar", "rattegangen", "verkstallighet_och_obestand"):
        gren = hitta_gren(lov_id)
        assert gren is not None and gren.toppgren == "offentlig_ratt", (
            f"{lov_id} ska ligga under offentlig rätt"
        )


def test_kop_och_arbetsratt_ar_speciell_avtalsratt():
    speciell = hitta_gren("speciell_avtalsratt")
    assert speciell is not None
    barn_ider = {b.id for b in speciell.grenar}
    assert {"kop_och_konsumentratt", "arbetsratt"} <= barn_ider


def test_obligationsratt_och_sakratt_ligger_under_formogenhetsratt():
    formogenhet = hitta_gren("formogenhetsratt")
    assert formogenhet is not None
    barn_ider = {b.id for b in formogenhet.grenar}
    assert {"obligationsratt", "sakratt"} <= barn_ider


def test_varje_gren_har_antingen_undergrenar_eller_lagar():
    for topp in ladda_rattssystem():
        _kontrollera_form(topp)


def _kontrollera_form(gren):
    if gren.ar_lov:
        assert not gren.grenar, f"{gren.id} är löv men har undergrenar"
    else:
        assert not gren.lagar, f"{gren.id} är gren men bär lagar direkt"
        for barn in gren.grenar:
            _kontrollera_form(barn)


def test_juridisk_metod_finns_inte_i_tradet():
    assert hitta_gren("juridisk_metod") is None
    assert hitta_gren("avd1_introduktion") is None
