"""Tester för utils.lagrum.

Täcker registerinläsning/-validering av data/lagrum.json,
extract_lagrum-parsning av olika citatformer ("36 § AvtL",
"3 kap. 1 § skadeståndslagen"), normalisering till kanonisk form och
verify_lagrum-klassificering i matched/missing/hallucinated.
"""

from __future__ import annotations

from utils.lagrum import (
    STATUS_EJ_VALIDERBAR,
    STATUS_OKAND_LAG,
    STATUS_OKAND_PARAGRAF,
    STATUS_VERIFIERAD,
    Lagrumsref,
    extrahera_lagrum,
    giltiga_forkortningar,
    lagen_nu_url,
    lagrum_register,
    validera_lagrum,
    verify_lagrum,
)


# --- Register ---------------------------------------------------------------

def test_register_laddas_med_18_lagar():
    reg = lagrum_register()
    assert len(reg) == 18


def test_register_innehaller_forvantade_forkortningar():
    fk = giltiga_forkortningar()
    for forkortning in ("AvtL", "SkL", "ÄktB", "ÄB", "KöpL", "LAS"):
        assert forkortning in fk


# --- Extrahering ------------------------------------------------------------

def test_extrahera_enkel_paragraf():
    (ref,) = extrahera_lagrum("Se 36 § AvtL för oskälighet.")
    assert ref.forkortning == "AvtL"
    assert ref.paragraf == "36"
    assert ref.kapitel is None
    assert ref.paragraf_till is None


def test_extrahera_kapitelform_med_punkt():
    (ref,) = extrahera_lagrum("Principalansvaret regleras i 3 kap. 1 § SkL.")
    assert ref.forkortning == "SkL"
    assert ref.kapitel == "3"
    assert ref.paragraf == "1"


def test_extrahera_kapitelform_utan_punkt():
    (ref,) = extrahera_lagrum("Giftorättsgods enligt 7 kap 1 § ÄktB.")
    assert ref.kapitel == "7"
    assert ref.paragraf == "1"
    assert ref.forkortning == "ÄktB"


def test_extrahera_intervall():
    (ref,) = extrahera_lagrum("Ogiltighet enligt 28 till 30 §§ AvtL.")
    assert ref.paragraf == "28"
    assert ref.paragraf_till == "30"
    assert ref.forkortning == "AvtL"


def test_extrahera_flera_referenser():
    refs = extrahera_lagrum("Jämför 1 § AvtL och 3 kap. 1 § SkL i detta fall.")
    assert len(refs) == 2
    assert {r.forkortning for r in refs} == {"AvtL", "SkL"}


def test_extrahera_ignorerar_text_utan_lagrum():
    assert extrahera_lagrum("Detta är en vanlig mening utan hänvisning.") == ()


def test_extrahera_fangar_inte_nja():
    # NJA-referenser är rättsfall, inte lagrum, och ska inte extraheras.
    assert extrahera_lagrum("Se NJA 2015 s. 1040.") == ()


# --- Validering -------------------------------------------------------------

def test_validera_verifierad_paragraflag():
    assert validera_lagrum("36 § AvtL") == STATUS_VERIFIERAD


def test_validera_verifierad_kapitellag():
    assert validera_lagrum("3 kap. 1 § SkL") == STATUS_VERIFIERAD


def test_validera_okand_paragraf_utanfor_kursavsnitt():
    # AvtL finns, men 999 § ingår inte i något kursavsnitt.
    assert validera_lagrum("999 § AvtL") == STATUS_OKAND_PARAGRAF


def test_validera_okand_lag_pahittad_forkortning():
    assert validera_lagrum("5 § XYZ") == STATUS_OKAND_LAG


def test_validera_kapitellag_utan_kapitel_ger_okand_paragraf():
    # ÄB är kapitelindelad; en referens utan kapitel kan inte verifieras.
    assert validera_lagrum("1 § ÄB") == STATUS_OKAND_PARAGRAF


def test_validera_accepterar_lagrumsref_objekt():
    ref = Lagrumsref(forkortning="AvtL", paragraf="36")
    assert validera_lagrum(ref) == STATUS_VERIFIERAD


# --- lagen.nu-URL -----------------------------------------------------------

def test_lagen_nu_url_paragraflag():
    assert lagen_nu_url("36 § AvtL") == "https://lagen.nu/1915:218#P36"


def test_lagen_nu_url_kapitellag():
    assert lagen_nu_url("3 kap. 1 § SkL") == "https://lagen.nu/1972:207#K3P1"


def test_lagen_nu_url_okand_lag_ar_none():
    assert lagen_nu_url("5 § XYZ") is None


# --- verify_lagrum (helhetsrapport) -----------------------------------------

def test_verify_lagrum_markerar_nja_som_ej_validerbar():
    (traff,) = verify_lagrum("Jämför resonemanget i NJA 2015 s. 1040.")
    assert traff.status == STATUS_EJ_VALIDERBAR


def test_verify_lagrum_markerar_pahittad_lag():
    (traff,) = verify_lagrum("Enligt 5 § Pizzalagen gäller ångerrätt.")
    assert traff.status == STATUS_OKAND_LAG


def test_verify_lagrum_blandad_text():
    text = (
        "Anbud regleras i 1 § AvtL. Oskälighet i 36 § AvtL. "
        "Jämför NJA 2015 s. 1040. En påhittad 5 § Pizzalagen finns inte."
    )
    traffar = verify_lagrum(text)
    statusar = [t.status for t in traffar]
    assert statusar.count(STATUS_VERIFIERAD) == 2
    assert STATUS_EJ_VALIDERBAR in statusar
    assert STATUS_OKAND_LAG in statusar


def test_verify_lagrum_verifierad_traff_har_url_och_beskrivning():
    (traff,) = verify_lagrum("Se 36 § AvtL.")
    assert traff.status == STATUS_VERIFIERAD
    assert traff.url == "https://lagen.nu/1915:218#P36"
    assert traff.beskrivning is not None
