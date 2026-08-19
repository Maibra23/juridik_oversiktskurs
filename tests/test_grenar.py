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


def test_toppgrenar_i_ordning():
    """Tre toppområden: de två klassiska plus internationell rätt/EU-rätt.

    Internationell rätt & EU-rätt är ett rent överblicksområde (referens- och
    pekarnoder, ingen registerlag) som sätts sist eftersom svensk rätt verkar
    *inom* det snarare än att det är en gren av den inhemska systematiken.
    """
    grenar = toppgrenar()
    assert [g.id for g in grenar] == [
        "offentlig_ratt",
        "civilratt",
        "internationell_ratt",
    ]


def test_toppgrenarna_bar_ratt_farg():
    farger = {g.id: g.farg for g in ladda_rattssystem()}
    assert farger["offentlig_ratt"] == "quote"
    assert farger["civilratt"] == "info"
    assert farger["internationell_ratt"] == "success"


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


def test_speciell_avtalsratt_ordnad_i_tre_transaktionsfamiljer():
    """Axis 1: speciell avtalsrätt grupperas efter vad avtalet gör med saken.

    Överlåtelse (äganderätten övergår), upplåtelse (nyttjande upplåts) och
    prestation (någon presterar). Leaf-id:na är oförändrade, bara föräldern
    byts, så begreppslänkarna i nyckelbegrepp.json består.
    """
    speciell = hitta_gren("speciell_avtalsratt")
    assert speciell is not None
    familj_ider = [b.id for b in speciell.grenar]
    assert familj_ider == [
        "overlatelseavtal",
        "upplatelseavtal",
        "prestationsavtal",
    ]


def test_avtalstyper_ligger_i_ratt_transaktionsfamilj():
    forvantat = {
        "overlatelseavtal": {"kop_och_konsumentratt", "kop_av_fast_egendom"},
        "upplatelseavtal": {"hyra_av_fast_egendom", "leasing", "licensavtal"},
        "prestationsavtal": {"transportavtal", "arbetsratt", "forsakringsavtal"},
    }
    for familj_id, barn in forvantat.items():
        familj = hitta_gren(familj_id)
        assert familj is not None, f"Transaktionsfamiljen {familj_id} saknas"
        assert {b.id for b in familj.grenar} == barn, (
            f"{familj_id} har fel avtalstyper"
        )


def test_speciell_avtalsratt_paminner_om_parterna():
    """Axis 2 som kompakt hint: kartan nudgar användaren att fråga vilka

    parterna är, eftersom samma avtalstyp routas till olika lag beroende på om
    det är B2B, B2C eller privat. Ingen egen nod, bara text på grenen.
    """
    speciell = hitta_gren("speciell_avtalsratt")
    assert speciell is not None
    text = f"{speciell.beskrivning} {speciell.nar}".lower()
    assert "part" in text and ("konsument" in text or "b2b" in text), (
        "Partsöverlägget (vem avtalar?) saknas i speciell avtalsrätt"
    )


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
