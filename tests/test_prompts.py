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
    build_begrepp_prompt,
    build_case_prompt,
    build_generate_prompt,
    build_quiz_prompt,
    vitlista_block,
)
from utils.scenarier import ladda_modul
from utils.svarighetsgrad import instruktion_for


def test_systemprompt_kraver_rnts_rubriker():
    for rubrik in RNTS_RUBRIKER:
        assert rubrik in SYSTEM_PROMPT_BASE


def test_systemprompt_forbjuder_pahitt():
    assert "ALDRIG" in SYSTEM_PROMPT_BASE
    assert "jag är osäker på exakt lagrum" in SYSTEM_PROMPT_BASE


def test_systemprompt_anger_lagrumsformat_och_langd():
    # Konkret exempel på kanonisk ordning och kapitelform ska finnas.
    assert "36 § AvtL" in SYSTEM_PROMPT_BASE
    assert "N kap. M § FÖRK" in SYSTEM_PROMPT_BASE
    assert str(MAX_SVARSLANGD_ORD) in SYSTEM_PROMPT_BASE


def test_systemprompt_forbjuder_omvand_lagrumsordning():
    # Skärpning: modellen ska aldrig skriva förkortningen först ("AvtL 36 §").
    assert "AvtL 36 §" in SYSTEM_PROMPT_BASE  # visas som FEL-exempel
    assert "FEL" in SYSTEM_PROMPT_BASE


def test_systemprompt_expertpersona():
    assert "30 års erfarenhet" in SYSTEM_PROMPT_BASE


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


# --- Facit som sanningsunderlag i fallgranskningen ---------------------------
#
# Utan facit måste modellen härleda svensk rätt ur sina egna vikter. Mätt mot
# Qwen3-8B träffade den då 2 av 9 korrekta lagrum, hänvisade 8 gånger till
# lagrum utanför facit och intygade en gång att ett påhittat "87 § AvtL" var
# rätt norm. Med facit i prompten blev det 9 av 9 och noll påhitt.


def test_case_prompt_injicerar_hela_facit():
    """Lagrum, tillämpningspunkter och slutsats ska alla med, inte bara frågan."""
    modul = ladda_modul("avtalsratt")
    case = modul.case[0]
    _, user = build_case_prompt(case, {"norm": "4 § AvtL"})

    for lagrum in case.facit.lagrum:
        assert lagrum in user, f"{lagrum} saknas i prompten"
    for punkt in case.facit.tillampningspunkter:
        assert punkt[:40] in user, "tillämpningspunkterna saknas"
    assert case.facit.slutsats[:40] in user, "facits slutsats saknas"


def test_case_prompt_forbjuder_ordet_facit_i_svaret():
    """Studenten ska aldrig få veta att en lösningsnyckel finns.

    Observerat i skarpt läge innan förbudet: "Fyll i rättsfrågan enligt facit."
    """
    modul = ladda_modul("avtalsratt")
    _, user = build_case_prompt(modul.case[0], {"norm": "4 § AvtL"})
    lag = user.lower()
    assert "aldrig ordet facit" in lag, "förbudet mot att nämna facit saknas"
    # Underlaget ska finnas med, men bara som modellens egen bedömning.
    assert "eget omdöme" in lag or "din egen bedömning" in lag


def test_case_prompt_kraver_svenska():
    """Svaret ska alltid vara på svenska, oavsett vad studenten skriver."""
    modul = ladda_modul("avtalsratt")
    _, user = build_case_prompt(modul.case[0], {"norm": "The contract is void"})
    assert "svenska" in user.lower()


def test_case_prompt_ber_modellen_peka_ut_fel_lagrum():
    """Kärnan i förbättringen: säg till när studentens lagrum inte är facits."""
    modul = ladda_modul("avtalsratt")
    _, user = build_case_prompt(modul.case[0], {"norm": "36 § AvtL"})
    assert "inte tillämpligt" in user or "inte är tillämpliga" in user


def test_case_prompt_haller_igen_pa_hur_mycket_som_avslojas():
    """Facit får vägleda granskningen, inte serveras som lösning."""
    modul = ladda_modul("avtalsratt")
    _, user = build_case_prompt(modul.case[0], {"norm": "4 § AvtL"})
    assert "inte ut lösningen" in user or "inte lösningen" in user


# --- Lagtext i prompten (fas 2) ---------------------------------------------
#
# Facit säger VILKA lagrum som gäller. Lagtexten säger vad de innehåller.
# Utan den senare gissar modellen, och gissade fel: "36 § AvtL reglerar
# avtals ingående" när paragrafen är generalklausulen om jämkning.


def test_case_prompt_injicerar_lagtext_for_facits_lagrum():
    modul = ladda_modul("avtalsratt")
    case = modul.case[0]
    _, user = build_case_prompt(case, {"norm": "4 § AvtL"})

    assert "LAGTEXT" in user
    # 4 § AvtL handlar om sen accept som nytt anbud.
    assert "nytt anbud" in user


def test_case_prompt_injicerar_lagtext_for_studentens_egna_lagrum():
    """Tutorn ska kunna säga VARFÖR studentens paragraf inte passar.

    Utan textens innehåll kan den bara konstatera att lagrummet saknas i
    facit, vilket är en svagare och mindre lärorik invändning.
    """
    modul = ladda_modul("avtalsratt")
    case = modul.case[0]
    _, user = build_case_prompt(case, {"norm": "Jag tror 36 § AvtL gäller."})

    assert "36 § AvtL" in user
    # 36 § är jämkningsparagrafen, och det ska framgå av texten i prompten.
    assert "oskäl" in user.lower() or "jämka" in user.lower()


def test_case_prompt_utan_lagtext_kraschar_inte():
    """Saknad lagtext ska ge en prompt utan lagtextblock, inte ett fel."""
    _, user = build_case_prompt(
        {
            "scenariotext": "Ett scenario.",
            "facit": {"rattsfraga": "En fråga?", "lagrum": ["87 § AvtL"]},
        },
        {"norm": "87 § AvtL"},
    )
    assert "LAGTEXT" not in user
    assert "En fråga?" in user


def test_begrepp_prompt_injicerar_lagtext():
    """Begreppsfördjupningen saknade helt sanningsunderlag före fas 2."""
    from utils.nyckelbegrepp import hamta_begrepp

    b = hamta_begrepp("behorighet-och-befogenhet")
    _, user = build_begrepp_prompt(b)

    assert "LAGTEXT" in user
    # Begreppet hänger på 10 och 11 §§ AvtL om fullmakt.
    assert "fullmakt" in user.lower()


def test_lagtexten_markeras_som_ordagrann():
    """Modellen måste veta att blocket är källtext, inte en parafras."""
    modul = ladda_modul("avtalsratt")
    _, user = build_case_prompt(modul.case[0], {"norm": "4 § AvtL"})
    assert "ordagrann" in user.lower()
    assert "som inte står i texten" in user


# --- build_generate_prompt: svårighetsgrad ---------------------------------

def test_generate_prompt_injicerar_vald_svarighetsinstruktion():
    """Prompten ska innehålla exakt det block som hör till vald nivå."""
    _, user = build_generate_prompt("avtalsratt", svarighetsgrad="avancerad")
    assert instruktion_for("avancerad") in user


def test_generate_prompt_pinnar_schemafaltet_till_vald_niva():
    """JSON-schemat ska tvinga svarighetsgrad till den valda nivån."""
    _, user = build_generate_prompt("avtalsratt", svarighetsgrad="medel")
    assert '"svarighetsgrad": "medel"' in user
    # Det gamla fria alternativuttrycket ska inte längre ligga kvar.
    assert '"grund" | "medel" | "avancerad"' not in user


def test_generate_prompt_olika_nivaer_ger_olika_instruktion():
    _, grund = build_generate_prompt("avtalsratt", svarighetsgrad="grund")
    _, avancerad = build_generate_prompt("avtalsratt", svarighetsgrad="avancerad")
    assert grund != avancerad
    assert instruktion_for("grund") in grund
    assert instruktion_for("avancerad") in avancerad


def test_generate_prompt_default_ar_grund():
    _, user = build_generate_prompt("avtalsratt")
    assert instruktion_for("grund") in user
    assert '"svarighetsgrad": "grund"' in user


def test_generate_prompt_ogiltig_niva_normaliseras_till_grund():
    _, user = build_generate_prompt("avtalsratt", svarighetsgrad="nonsens")
    assert instruktion_for("grund") in user
    assert '"svarighetsgrad": "grund"' in user


def test_generate_prompt_kraver_korrekt_svensk_sprakkvalitet():
    """Genereringen ska uttryckligen be om korrekt, idiomatisk svenska.

    Scenariotexten grundas inte deterministiskt (bara lagrummen verifieras),
    så språkkvaliteten vilar helt på prompten. Regression: 8B-modellen skrev
    'Ongiltig', 'anlade ett avtal' och 'Penaltiklause'.
    """
    _, user = build_generate_prompt("avtalsratt")
    lag = user.lower()
    assert "språk" in lag
    assert "korrekt" in lag and "svenska" in lag
    assert "korrekturläs" in lag or "stavning" in lag
