"""Tester för utils.lagrum.

Täcker registerinläsning/-validering av data/lagrum.json,
extract_lagrum-parsning av olika citatformer ("36 § AvtL",
"3 kap. 1 § skadeståndslagen"), normalisering till kanonisk form och
verify_lagrum-klassificering i matched/missing/hallucinated.
"""

from __future__ import annotations

import pytest

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

def test_register_laddas_med_21_lagar():
    """Antalet har vuxit med de moduler som tillkommit efter granskningen.

    18 -> 20: GFL och LFF med Personrätt och Allmän förmögenhetsrätt.
    20 -> 21: PreskL med Fordringsrätt. Testet är ett skydd mot att lagar
    tappas bort vid redigering av lagrum.json.
    """
    reg = lagrum_register()
    assert len(reg) == 21


def test_register_innehaller_forvantade_forkortningar():
    fk = giltiga_forkortningar()
    for forkortning in ("AvtL", "SkL", "ÄktB", "ÄB", "KöpL", "LAS", "GFL", "LFF", "PreskL"):
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


# --- Omvänd ordning (FÖRK först) --------------------------------------------

def test_extrahera_omvand_enkel_paragraf():
    # Modellen skriver ofta förkortningen först: "AvtL 18 §".
    (ref,) = extrahera_lagrum("Detta regleras i AvtL 18 §.")
    assert ref.forkortning == "AvtL"
    assert ref.paragraf == "18"
    assert ref.kapitel is None


def test_extrahera_omvand_intervall():
    (ref,) = extrahera_lagrum("Ogiltighet enligt AvtL 28–30 §§.")
    assert ref.forkortning == "AvtL"
    assert ref.paragraf == "28"
    assert ref.paragraf_till == "30"


def test_extrahera_omvand_kapitelform():
    (ref,) = extrahera_lagrum("Principalansvaret i SkL 3 kap. 1 §.")
    assert ref.forkortning == "SkL"
    assert ref.kapitel == "3"
    assert ref.paragraf == "1"


def test_extrahera_omvand_ignorerar_okand_forkortning():
    # "Bestämmelsen" är ett versalinlett vanligt ord, inte en känd lag.
    # Utan registerspärr skulle detta felaktigt bli en träff.
    assert extrahera_lagrum("Bestämmelsen 5 § är tydlig.") == ()


def test_extrahera_omvand_ignorerar_vanligt_versalord():
    assert extrahera_lagrum("Paragrafen 5 § reglerar detta.") == ()


def test_extrahera_blandad_ordning_i_samma_text():
    refs = extrahera_lagrum("Jämför 1 § AvtL med AvtL 36 §.")
    assert len(refs) == 2
    assert [r.paragraf for r in refs] == ["1", "36"]


# --- Skiftlägesokänslig förkortning ------------------------------------------

def test_extrahera_gemener_normaliseras_till_kanoniskt_skiftlage():
    (ref,) = extrahera_lagrum("36 § avtl")
    assert ref.forkortning == "AvtL"


def test_extrahera_versaler_normaliseras_till_kanoniskt_skiftlage():
    (ref,) = extrahera_lagrum("3 kap. 1 § SKL")
    assert ref.forkortning == "SkL"


def test_extrahera_omvand_gemener_normaliseras():
    (ref,) = extrahera_lagrum("skl 3 kap. 1 §")
    assert ref.forkortning == "SkL"


def test_validera_gement_okant_ord_ar_ej_validerbart():
    # "xyz" är gement och motsvarar ingen registrerad lag i något skiftläge,
    # så det tolkas inte alls som ett lagrum (samma som "Pizzalagen" hade
    # gjort om ordet varit versalinlett hade det däremot gett OKAND_LAG,
    # se test_verify_lagrum_markerar_pahittad_lag).
    assert validera_lagrum("5 § xyz") == STATUS_EJ_VALIDERBAR


@pytest.mark.parametrize(
    "text",
    ["36 § avtl", "36 § AVTL", "36 § AvTl", "avtl 36 §", "AVTL 36 §"],
)
def test_validera_verifierad_oavsett_skiftlage(text):
    assert validera_lagrum(text) == STATUS_VERIFIERAD


def test_validera_omvand_verifierad():
    assert validera_lagrum("AvtL 36 §") == STATUS_VERIFIERAD


def test_validera_omvand_okand_paragraf_pa_kand_lag():
    # Känd lag i omvänd ordning men paragraf utanför kursavsnitt ska flaggas.
    assert validera_lagrum("AvtL 999 §") == STATUS_OKAND_PARAGRAF


def test_verify_lagrum_fangar_omvand_ordning():
    (traff,) = verify_lagrum("Enligt AvtL 36 § är avtalsvillkoret oskäligt.")
    assert traff.status == STATUS_VERIFIERAD
    assert traff.url == "https://lagen.nu/1915:218#P36"


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


@pytest.mark.parametrize(
    "ref",
    [
        "12 kap. 4 § AvtL",
        "99 kap. 1 § AvtL",
        "3 kap. 36 § AvtL",
        "7 kap. 2 § KöpL",
    ],
)
def test_validera_avvisar_kapitel_pa_lag_utan_kapitel(ref):
    """En lag utan kapitelindelning får aldrig verifieras med ett kapitel.

    Kapitelledet ignorerades tidigare helt när lagen saknade kapitel, så
    "99 kap. 1 § AvtL" verifierades på styrkan av att AvtL har en 1 §. Ett
    påhittat kapitel gick därmed igenom garden och renderades som ett
    grönt, klickbart chip. Observerat när tutorn granskade ett studentsvar
    som citerade "12 kap. 4 § AvtL".
    """
    assert validera_lagrum(ref) == STATUS_OKAND_PARAGRAF


def test_validera_slapper_fortfarande_igenom_ratt_kapitellag():
    """Regressionsvakt: skärpningen får inte träffa kapitelindelade lagar."""
    assert validera_lagrum("2 kap. 1 § SkL") == STATUS_VERIFIERAD
    assert validera_lagrum("3 kap. 1 § SkL") == STATUS_VERIFIERAD
    assert validera_lagrum("36 § AvtL") == STATUS_VERIFIERAD


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


def test_inget_kursavsnitt_ar_overifierat():
    """Slutgrind: allt som visas för studenten ska vara genomgånget.

    Flaggan betyder enligt registrets egen beskrivning paragrafgränser som
    ännu inte kontrollerats mot författningen. Sådant får inte renderas som
    ett påstående i lagkortet. Kontrollen är automatiserad sedan
    data/lagstruktur/ finns; se utils.kursavsnitt_kontroll.
    """
    from utils.lagrum import lagrum_register

    oflaggade = [
        f"{lag.forkortning}: {a.beskrivning}"
        for lag in lagrum_register().values()
        for a in lag.kursavsnitt
        if a.verifiera
    ]
    assert oflaggade == [], "\n".join(oflaggade)


# --- Aliasfält på Lag ---------------------------------------------------


def test_validera_ra_lag_las_alias_falt():
    from utils.lagrum import _validera_ra_lag

    rad = {
        "forkortning": "TestL",
        "namn": "Testlag",
        "sfs": "2026:1",
        "kapitelindelad": False,
        "lagen_nu_bas_url": "https://lagen.nu/2026:1",
        "aliaser": ["testlagen", "TL"],
        "kursavsnitt": [],
    }
    lag = _validera_ra_lag(rad)
    assert lag.aliaser == ("testlagen", "TL")


def test_validera_ra_lag_alias_falt_default_tomt():
    from utils.lagrum import _validera_ra_lag

    rad = {
        "forkortning": "TestL",
        "namn": "Testlag",
        "sfs": "2026:1",
        "kapitelindelad": False,
        "lagen_nu_bas_url": "https://lagen.nu/2026:1",
        "kursavsnitt": [],
    }
    lag = _validera_ra_lag(rad)
    assert lag.aliaser == ()


# --- _bygg_alias_karta --------------------------------------------------

def test_bygg_alias_karta_loser_alias_till_forkortning():
    from utils.lagrum import Lag, _bygg_alias_karta

    register = {
        "AvtL": Lag(
            forkortning="AvtL",
            namn="Testnamn",
            sfs="1915:218",
            kapitelindelad=False,
            lagen_nu_bas_url="https://lagen.nu/1915:218",
            kursavsnitt=(),
            aliaser=("avtalslagen",),
        ),
    }
    karta = _bygg_alias_karta(register)
    assert karta["avtalslagen"] == "AvtL"
    assert karta["avtl"] == "AvtL"


def test_bygg_alias_karta_kastar_vid_kolliderande_alias():
    from utils.lagrum import Lag, _bygg_alias_karta

    register = {
        "AvtL": Lag(
            forkortning="AvtL",
            namn="Testnamn A",
            sfs="1915:218",
            kapitelindelad=False,
            lagen_nu_bas_url="https://lagen.nu/1915:218",
            kursavsnitt=(),
            aliaser=("dubbel",),
        ),
        "SkL": Lag(
            forkortning="SkL",
            namn="Testnamn B",
            sfs="1972:207",
            kapitelindelad=True,
            lagen_nu_bas_url="https://lagen.nu/1972:207",
            kursavsnitt=(),
            aliaser=("dubbel",),
        ),
    }
    with pytest.raises(ValueError, match="dubbel"):
        _bygg_alias_karta(register)


# --- Alias: fulla lagnamn och alternativa förkortningar mot riktiga registret

@pytest.mark.parametrize(
    "text,forkortning",
    [
        ("36 § avtalslagen", "AvtL"),
        ("avtalslagen 36 §", "AvtL"),
        ("1 kap. 1 § brottsbalken", "BrB"),
        ("brottsbalken 1 kap. 1 §", "BrB"),
        ("3 § köplagen", "KöpL"),
        ("3 kap. 1 § KKL", "KKöpL"),
        ("10 § PreskrL", "PreskL"),
    ],
)
def test_extrahera_kant_alias_normaliseras_till_forkortning(text, forkortning):
    (ref,) = extrahera_lagrum(text)
    assert ref.forkortning == forkortning


@pytest.mark.parametrize(
    "text",
    ["36 § AVTALSLAGEN", "36 § Avtalslagen", "avtalslagen 36 §"],
)
def test_extrahera_alias_skiftlagesokansligt(text):
    (ref,) = extrahera_lagrum(text)
    assert ref.forkortning == "AvtL"


def test_validera_verifierad_med_fullt_lagnamn():
    assert validera_lagrum("36 § avtalslagen") == STATUS_VERIFIERAD


def test_validera_verifierad_med_alternativ_forkortning():
    assert validera_lagrum("3 kap. 1 § KKL") == STATUS_VERIFIERAD


def test_lagen_nu_url_med_fullt_lagnamn_ar_samma_som_forkortning():
    assert lagen_nu_url("36 § avtalslagen") == lagen_nu_url("36 § AvtL")
