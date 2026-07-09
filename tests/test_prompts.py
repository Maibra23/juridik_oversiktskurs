"""Tester för utils.prompts.

Täcker att varje promptbyggare returnerar (system, user), att
RNTS-strukturen och förbudet mot påhittade lagrum finns i systemprompten,
att LAGRUMSVITLISTAN injiceras i användarprompten och att endast
scenariots relevanta lagar tas med i den fokuserade vitlistan.
"""

from __future__ import annotations

from utils.prompts import (
    MAX_SVARSLANGD_ORD,
    RNTS_RUBRIKER,
    SYSTEM_PROMPT_BASE,
    build_case_prompt,
    build_quiz_prompt,
    vitlista_block,
)
from utils.scenarier import ladda_modul


def test_systemprompt_kraver_rnts_rubriker():
    for rubrik in RNTS_RUBRIKER:
        assert rubrik in SYSTEM_PROMPT_BASE


def test_systemprompt_forbjuder_pahitt():
    assert "ALDRIG" in SYSTEM_PROMPT_BASE
    assert "jag är osäker på exakt lagrum" in SYSTEM_PROMPT_BASE


def test_systemprompt_anger_lagrumsformat_och_langd():
    assert "N § FÖRK" in SYSTEM_PROMPT_BASE
    assert "N kap. M § FÖRK" in SYSTEM_PROMPT_BASE
    assert str(MAX_SVARSLANGD_ORD) in SYSTEM_PROMPT_BASE


def test_systemprompt_instruerar_granskning_ej_omskrivning():
    # Tutorn ska bedöma studentens svar, inte skriva om lösningen.
    assert "steg för steg" in SYSTEM_PROMPT_BASE
    assert "INTE om hela lösningen" in SYSTEM_PROMPT_BASE


def test_vitlista_hel_innehaller_kanda_lagar():
    block = vitlista_block()
    assert "AvtL" in block
    assert "LAGRUMSVITLISTA" in block


def test_vitlista_fokuserad_utesluter_orelevanta_lagar():
    block = vitlista_block(["AvtL"])
    assert "AvtL" in block
    assert "SkL" not in block


def test_vitlista_okand_forkortning_faller_tillbaka_pa_hela():
    # En okänd förkortning ska inte ge en tom vitlista.
    block = vitlista_block(["FINNSINTE"])
    assert "AvtL" in block


def test_build_case_prompt_injicerar_scenario_och_vitlista():
    modul = ladda_modul("avtalsratt")
    case = modul.case[0]
    system, user = build_case_prompt(
        case,
        {"rattsfragan": "Har avtal slutits?", "norm": "4 § AvtL",
         "tillampning": "Sen accept", "slutsats": "Nej"},
    )
    assert system == SYSTEM_PROMPT_BASE
    assert case.scenariotext[:40] in user
    assert "LAGRUMSVITLISTA" in user
    assert "AvtL" in user
    # Studentens svar ska finnas med.
    assert "Sen accept" in user


def test_build_case_prompt_tomt_svar_hanteras():
    modul = ladda_modul("avtalsratt")
    case = modul.case[0]
    _, user = build_case_prompt(case, {})
    assert "(tomt)" in user


def test_build_quiz_prompt_markerar_valt_alternativ():
    modul = ladda_modul("avtalsratt")
    fraga = modul.flervalsfragor[0]
    valt = fraga.alternativ[1]
    system, user = build_quiz_prompt(fraga, valt)
    assert system == SYSTEM_PROMPT_BASE
    assert fraga.fraga[:30] in user
    assert valt.text in user
    assert "→" in user
    assert "LAGRUMSVITLISTA" in user
