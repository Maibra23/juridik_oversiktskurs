"""Tester för begreppsbanken (data/nyckelbegrepp.json, utils.nyckelbegrepp).

Vaktar den deterministiska kärnan i fliken Nyckelbegrepp:
- att varje begrepp har alla fyra obligatoriska fälten ifyllda,
- att varje lagrum i filen verifieras mot lagrumsregistret,
- att varje begrepp hör till ett delområde som finns i rättssystemkartan,
- att korslänkar (se_aven) och modulsidor pekar på något som existerar.
"""

from __future__ import annotations

import json

import pytest

from utils.lagrum import STATUS_VERIFIERAD, validera_lagrum
from utils.nyckelbegrepp import (
    DATA_PATH,
    OBLIGATORISKA_FALT,
    Begrepp,
    _bygg_begrepp,
    begrepp_per_omrade,
    hamta_begrepp,
    ladda_begrepp,
    sok_begrepp,
)
from utils.navigation import sida_finns


@pytest.fixture(scope="module")
def begrepp() -> tuple[Begrepp, ...]:
    return ladda_begrepp()


# --- De fyra fasta fälten ---------------------------------------------------


def test_varje_begrepp_har_alla_fyra_falten(begrepp):
    """Definition, förklaring, exempel och igenkänning måste alla vara ifyllda."""
    assert begrepp
    for b in begrepp:
        for falt in OBLIGATORISKA_FALT:
            varde = getattr(b, falt)
            assert varde and varde.strip(), f"{b.id} saknar {falt}"


def test_falten_har_verkligt_innehall(begrepp):
    """Fälten ska vara skrivna, inte platshållare på ett par ord."""
    for b in begrepp:
        assert len(b.definition) >= 40, f"{b.id}: definitionen är för kort"
        assert len(b.forklaring) >= 80, f"{b.id}: förklaringen är för kort"
        assert len(b.exempel) >= 60, f"{b.id}: exemplet är för kort"
        assert len(b.igenkanning) >= 60, f"{b.id}: igenkänningen är för kort"


def test_saknat_falt_ger_tydligt_fel():
    """Fail fast: ett begrepp utan alla fyra fält får aldrig läsas in."""
    rad = {
        "id": "trasigt",
        "term": "Trasigt",
        "omrade_id": "avtalsratt",
        "definition": "En definition.",
        "forklaring": "En förklaring.",
        "exempel": "Ett exempel.",
        # igenkanning saknas
    }
    with pytest.raises(ValueError, match="igenkanning"):
        _bygg_begrepp(rad, {"avtalsratt"})


# --- Grundning mot lagrumsregistret -----------------------------------------


def test_varje_lagrum_i_filen_ar_verifierat(begrepp):
    """Begreppsbanken får aldrig innehålla ett ogrundat lagrum."""
    refs = [(b.id, ref) for b in begrepp for ref in b.lagrum]
    assert refs, "Minst några begrepp ska bära lagrum"
    for bid, ref in refs:
        assert validera_lagrum(ref) == STATUS_VERIFIERAD, f"{bid}: {ref}"


def test_ogrundat_lagrum_ger_tydligt_fel():
    rad = {
        "id": "trasigt",
        "term": "Trasigt",
        "omrade_id": "avtalsratt",
        "definition": "En definition som är tillräckligt lång för att duga.",
        "forklaring": "En förklaring.",
        "exempel": "Ett exempel.",
        "igenkanning": "Signalord.",
        "lagrum": ["999 § AvtL"],
    }
    with pytest.raises(ValueError, match="verifieras"):
        _bygg_begrepp(rad, {"avtalsratt"})


def test_lagrumsformat_har_paragrafnumret_forst(begrepp):
    """Samma format som tutorn tvingas använda: "36 § AvtL", aldrig omvänt."""
    for b in begrepp:
        for ref in b.lagrum:
            assert "§" in ref, f"{b.id}: {ref!r} saknar paragraftecken"
            assert not ref.split()[0].isalpha(), (
                f"{b.id}: {ref!r} verkar ha förkortningen först"
            )


# --- Koppling till kartan och modulerna -------------------------------------


def test_varje_begrepp_hor_till_ett_verkligt_delomrade(begrepp):
    from utils.rattskarta import ladda_rattssystem

    giltiga = {
        under.id
        for omrade in ladda_rattssystem()
        for under in omrade.underomraden
    }
    for b in begrepp:
        assert b.omrade_id in giltiga, f"{b.id}: okänt delområde {b.omrade_id}"


def test_modulsidor_finns_pa_disk(begrepp):
    """En begreppslänk får aldrig peka på en sida som inte är byggd."""
    for b in begrepp:
        if b.modul_sida:
            assert sida_finns(b.modul_sida), f"{b.id}: {b.modul_sida} saknas"


def test_korslankar_pekar_pa_befintliga_begrepp(begrepp):
    ider = {b.id for b in begrepp}
    for b in begrepp:
        for ref in b.se_aven:
            assert ref in ider, f"{b.id}: se_aven pekar på okänt begrepp {ref!r}"


def test_inga_dubblerade_id(begrepp):
    ider = [b.id for b in begrepp]
    assert len(ider) == len(set(ider))


# --- Täckning och uppslag ---------------------------------------------------


def test_alla_byggda_rattsomraden_har_begrepp():
    """Varje delområde med egna lagar ska ha minst tre begrepp.

    Undantag: delområden helt utan lagar i kursens register (statsrätt och
    förvaltningsrätt) kan inte bära lagrumsgrundade begrepp.
    """
    from utils.rattskarta import ladda_rattssystem

    per_omrade = begrepp_per_omrade()
    for omrade in ladda_rattssystem():
        for under in omrade.underomraden:
            if not under.lagar:
                continue
            traffar = per_omrade.get(under.id, ())
            assert len(traffar) >= 3, (
                f"{under.id} har bara {len(traffar)} begrepp"
            )


def test_hamta_och_sok(begrepp):
    b = hamta_begrepp("behorighet-och-befogenhet")
    assert b is not None
    assert b.term.startswith("Behörighet")
    assert b.skillnaden, "Kontrastpar ska ha en skillnadsrad"

    assert hamta_begrepp("finns-inte") is None
    assert sok_begrepp("befogenhet")
    assert sok_begrepp("") == begrepp
    assert not sok_begrepp("kvantfysik")


def test_sok_traffar_pa_lagrum():
    traffar = sok_begrepp("36 § AvtL")
    assert any(b.id == "jamkning-av-oskaliga-villkor" for b in traffar)


# --- Filens form ------------------------------------------------------------


def test_json_ar_valformad_och_har_schemaversion():
    rad = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assert rad["schema_version"] == 1
    assert isinstance(rad["begrepp"], list)
