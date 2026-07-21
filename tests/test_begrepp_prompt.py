"""Tester för build_begrepp_prompt (utils.prompts).

Vaktar att begreppsfördjupningen injicerar begreppets verifierade grunddata
och upprepar källreglerna, så att LLM-lagret kompletterar begreppsbanken i
stället för att ersätta den.
"""

from __future__ import annotations

import pytest

from utils.nyckelbegrepp import hamta_begrepp
from utils.prompts import (
    LAS_FORDJUPNING,
    LAS_OVNING,
    MAX_BEGREPPSSVAR_ORD,
    SYSTEM_PROMPT_BASE,
    SYSTEM_PROMPT_BEGREPP,
    build_begrepp_prompt,
)


@pytest.fixture(scope="module")
def begrepp():
    b = hamta_begrepp("behorighet-och-befogenhet")
    assert b is not None
    return b


def test_begreppsprompten_ar_inte_fallgranskningens(begrepp):
    """Begreppsfördjupningen har en egen systemprompt, inte fallgranskningens.

    Fallprompten kräver RNTS-rubriker och förutsätter ett bifogat studentsvar.
    Ingetdera stämmer för en begreppsförklaring.
    """
    system, _user = build_begrepp_prompt(begrepp)
    assert system == SYSTEM_PROMPT_BEGREPP
    assert system != SYSTEM_PROMPT_BASE


def test_begreppsprompten_delar_kallreglerna(begrepp):
    """Det som skyddar studenten mot påhittade lagrum måste vara identiskt.

    Rollen, förbudet mot påhitt och lagrumsformatet är samma text som i
    fallgranskningen: de är själva grunden för att verify_lagrum ska kunna
    göra sitt jobb, och får aldrig glida isär mellan de två prompterna.
    """
    system, _user = build_begrepp_prompt(begrepp)
    for regel in (
        "30 års erfarenhet",
        "ALDRIG hitta på lagar, paragrafer, kapitel eller rättsfall",
        "jag är osäker på exakt lagrum",
        "LAGRUMSVITLISTAN",
        "36 § AvtL",
        "N kap. M § FÖRK",
        "svenska juridisk facksvenska",
    ):
        assert regel in system, f"{regel!r} saknas i begreppsprompten"
        assert regel in SYSTEM_PROMPT_BASE, f"{regel!r} saknas i basprompten"


def test_begreppsprompten_kraver_inte_rnts(begrepp):
    """Ingen motsägelse: systemprompten får inte kräva rubriker som uppdraget förbjuder."""
    system, user = build_begrepp_prompt(begrepp)
    assert "STRUKTUR (obligatorisk)" not in system
    assert "Bygg alltid svaret med exakt dessa fyra rubriker" not in system
    # Och uppdraget behöver då inte längre säga emot systemprompten.
    assert "Använd inte RNTS-rubrikerna" not in user


def test_begreppsprompten_forutsatter_inget_studentsvar(begrepp):
    """TUTORROLL-blocket bifogar ett studentsvar som inte finns här."""
    system, _user = build_begrepp_prompt(begrepp)
    assert "Studentens eget svar bifogas" not in system
    assert "Studentens eget svar bifogas" in SYSTEM_PROMPT_BASE


def test_begreppsprompten_anger_sin_egen_langdgrans(begrepp):
    """Begreppssvar är kortare än fallgranskningar."""
    system, _user = build_begrepp_prompt(begrepp)
    assert str(MAX_BEGREPPSSVAR_ORD) in system


def test_grunddatan_injiceras_i_prompten(begrepp):
    """Alla fyra fälten ska med, annars kan modellen motsäga dem."""
    _system, user = build_begrepp_prompt(begrepp)
    assert begrepp.term in user
    assert begrepp.definition in user
    assert begrepp.forklaring in user
    assert begrepp.exempel in user
    assert begrepp.igenkanning in user


def test_begreppets_lagrum_finns_med(begrepp):
    _system, user = build_begrepp_prompt(begrepp)
    for ref in begrepp.lagrum:
        assert ref in user


def test_kallreglerna_upprepas(begrepp):
    """Prompten ska nämna vitlistan, förbudet mot påhitt och formatkravet."""
    _system, user = build_begrepp_prompt(begrepp)
    assert "LAGRUMSVITLISTA" in user
    assert "ENDAST" in user
    assert "ALDRIG hitta på" in user
    assert "Motsäg aldrig grunddatan" in user


def test_vitlistan_begransas_till_begreppets_lagar(begrepp):
    """Fokuserad vitlista: AvtL ska med, orelaterade lagar inte."""
    _system, user = build_begrepp_prompt(begrepp)
    vitlista = user.split("BEGREPPETS GRUNDDATA")[0]
    assert "AvtL" in vitlista
    assert "ÄktB" not in vitlista
    assert "BrB" not in vitlista


def test_langdgrans_anges(begrepp):
    _system, user = build_begrepp_prompt(begrepp)
    assert str(MAX_BEGREPPSSVAR_ORD) in user


def test_fordjupning_och_ovning_ger_olika_uppdrag(begrepp):
    _s1, fordjupning = build_begrepp_prompt(begrepp, las=LAS_FORDJUPNING)
    _s2, ovning = build_begrepp_prompt(begrepp, las=LAS_OVNING)

    assert fordjupning != ovning
    assert "Fördjupa förklaringen" in fordjupning
    assert "övningsscenario" in ovning
    assert "Rättsfrågan att besvara" in ovning
    # Övningen får aldrig innehålla lösningen.
    assert "Ge INTE lösningen" in ovning


def test_fungerar_med_dict_som_begrepp():
    """Byggaren ska klara både dataklass och dict, som övriga byggare."""
    _system, user = build_begrepp_prompt(
        {
            "term": "Testbegrepp",
            "definition": "En definition.",
            "forklaring": "En förklaring.",
            "exempel": "Ett exempel.",
            "igenkanning": "Signalord.",
            "lagrum": ["36 § AvtL"],
        }
    )
    assert "Testbegrepp" in user
    assert "36 § AvtL" in user


def test_begrepp_utan_lagrum_ger_hel_vitlista():
    """Utan egna lagrum faller vi tillbaka på registret, aldrig på en tom lista."""
    _system, user = build_begrepp_prompt(
        {
            "term": "Utan lagrum",
            "definition": "En definition.",
            "forklaring": "En förklaring.",
            "exempel": "Ett exempel.",
            "igenkanning": "Signalord.",
            "lagrum": [],
        }
    )
    assert "LAGRUMSVITLISTA" in user
    assert "(inga angivna)" in user
