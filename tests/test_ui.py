"""Tester för designsystemets rena HTML-komponenter i utils/ui.py.

Testar de komponenter som returnerar HTML-strängar utan Streamlit-anrop:
RNTS-steppern (render_rnts_steg), scenariokortet (render_case) och
lagrumschipen. Rendering till skärm (st.html) testas inte här utan i
röktesterna som importerar sidorna i bare mode.
"""

from __future__ import annotations

import re

import pytest

import utils.css
from utils.ui import (
    RNTS_STATUS_BEHOVER_MER,
    RNTS_STATUS_EJ_PABORJAD,
    RNTS_STATUS_GODKAND,
    RNTS_STATUS_PAGAR,
    render_case,
    render_kort,
    render_lagrum_chip,
    render_rnts_steg,
)

# --- render_rnts_steg ---------------------------------------------------------

def test_rnts_steg_innehaller_alla_etiketter():
    html_ut = render_rnts_steg(
        (
            ("Rättsfrågan", RNTS_STATUS_GODKAND),
            ("Norm", RNTS_STATUS_PAGAR),
            ("Tillämpning", RNTS_STATUS_EJ_PABORJAD),
            ("Slutsats", RNTS_STATUS_EJ_PABORJAD),
        )
    )
    for etikett in ("Rättsfrågan", "Norm", "Tillämpning", "Slutsats"):
        assert etikett in html_ut


def test_rnts_steg_statusklasser_syns_i_html():
    html_ut = render_rnts_steg(
        (
            ("Rättsfrågan", RNTS_STATUS_GODKAND),
            ("Norm", RNTS_STATUS_BEHOVER_MER),
            ("Tillämpning", RNTS_STATUS_PAGAR),
            ("Slutsats", RNTS_STATUS_EJ_PABORJAD),
        )
    )
    assert RNTS_STATUS_GODKAND in html_ut
    assert RNTS_STATUS_BEHOVER_MER in html_ut
    assert RNTS_STATUS_PAGAR in html_ut
    assert RNTS_STATUS_EJ_PABORJAD in html_ut


def test_rnts_steg_okand_status_ger_fel():
    with pytest.raises(ValueError):
        render_rnts_steg((("Norm", "felaktig-status"),))


def test_rnts_steg_escapar_html():
    html_ut = render_rnts_steg((("<script>", RNTS_STATUS_PAGAR),))
    assert "<script>" not in html_ut
    assert "&lt;script&gt;" in html_ut


# --- render_case --------------------------------------------------------------

def test_render_case_innehaller_rubrik_meta_och_text():
    html_ut = render_case(
        rubrik="Målaren och rutan",
        metadata="Svårighetsgrad: grund · ca 12 min",
        scenariotext="Erik ställer en färgburk på en stege.",
    )
    assert "Målaren och rutan" in html_ut
    assert "ca 12 min" in html_ut
    assert "färgburk" in html_ut
    assert "jok-case" in html_ut


def test_render_case_escapar_html():
    html_ut = render_case(rubrik="<b>x</b>", metadata="", scenariotext="<i>y</i>")
    assert "<b>" not in html_ut
    assert "<i>" not in html_ut


# --- Befintliga komponenter (regression) ---------------------------------------

def test_render_kort_escapar_innehall():
    html_ut = render_kort("Titel", "<script>alert(1)</script>")
    assert "<script>" not in html_ut


def test_render_lagrum_chip_verifierad_med_url():
    html_ut = render_lagrum_chip("36 § AvtL", url="https://lagen.nu/1915:218#P36")
    assert "jok-chip" in html_ut
    assert "ovarifierad" not in html_ut
    assert "lagen.nu" in html_ut


def test_render_lagrum_chip_ovarifierad():
    html_ut = render_lagrum_chip("99 § PåhittL", verifierad=False)
    assert "ovarifierad" in html_ut
    assert "Ej verifierad" in html_ut


# --- Tutortext: markdown från modellen renderas, aldrig råa asterisker ---------

def test_tutortext_fetstil_blir_strong_utan_asterisker():
    from utils.ui import _tutortext_html

    html_ut, _ = _tutortext_html("Detta är **viktigt** att förstå.")
    assert "<strong>viktigt</strong>" in html_ut
    assert "**" not in html_ut


def test_tutortext_kursiv_blir_em():
    from utils.ui import _tutortext_html

    html_ut, _ = _tutortext_html("Frågan är *om avtal slutits* här.")
    assert "<em>om avtal slutits</em>" in html_ut
    assert "*om avtal slutits*" not in html_ut


def test_tutortext_rnts_rubrik_far_stilklass():
    from utils.ui import _tutortext_html

    svar = "**1. Rättsfrågan**\nHar ett bindande avtal slutits?"
    html_ut, _ = _tutortext_html(svar)
    assert "rnts-rubrik" in html_ut
    assert "**" not in html_ut


def test_tutortext_hashtag_rubrik_renderas_som_rubrik():
    from utils.ui import _tutortext_html

    html_ut, _ = _tutortext_html("### Norm\nRätt lagrum är 1 § AvtL.")
    assert "###" not in html_ut
    assert "rnts-rubrik" in html_ut


def test_tutortext_lagrum_i_fetstil_blir_chip():
    from utils.ui import _tutortext_html

    html_ut, _ = _tutortext_html("Se **36 § AvtL** om oskälighet.")
    assert "jok-chip" in html_ut
    assert "lagen.nu" in html_ut
    assert "**" not in html_ut


def test_tutortext_escapar_html_fran_modellen():
    from utils.ui import _tutortext_html

    html_ut, _ = _tutortext_html("Farligt <script>alert(1)</script> svar.")
    assert "<script>" not in html_ut


# --- Lagkortets kursavsnitt --------------------------------------------------


def _grupp(kapitel, rubrik, spann, avsnittsrubrik, url="https://lagen.nu/1:1"):
    from utils.lagkort_avsnitt import Avsnittsrad, Kapitelgrupp

    return Kapitelgrupp(kapitel, rubrik, (Avsnittsrad(spann, avsnittsrubrik, url),))


def test_lagkortet_renderar_kursavsnitt_med_kapitelrubrik():
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="KKöpL",
        namn="Konsumentköplag",
        sfs="2022:260",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/2022:260",
        kursavsnitt=(
            _grupp(
                "3",
                "Näringsidkarens dröjsmål",
                "1–6 §§",
                "Påföljder vid säljarens dröjsmål",
                "https://lagen.nu/2022:260#K3P1",
            ),
        ),
        tackning="kursen täcker 6 av lagens 9 kapitel",
    )
    assert "3 kap. Näringsidkarens dröjsmål" in html
    assert "1–6 §§" in html
    assert "Påföljder vid säljarens dröjsmål" in html
    assert "kursen täcker 6 av lagens 9 kapitel" in html


def test_lagkortet_utan_kursavsnitt_ser_ut_som_forr():
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="X",
        namn="X",
        sfs="1:1",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/1:1",
    )
    assert "KURSAVSNITT" not in html


def test_lagkortet_escapar_avsnittsrubriker():
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="X",
        namn="X",
        sfs="1:1",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/1:1",
        kursavsnitt=(_grupp(None, "", "1 §", "<script>alert(1)</script>"),),
    )
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_kapitellos_grupp_renderar_ingen_kapitelrubrik():
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="KöpL",
        namn="Köplag",
        sfs="1990:931",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/1990:931",
        kursavsnitt=(
            _grupp(
                None,
                "",
                "22–29 §§",
                "Påföljder vid säljarens dröjsmål",
                "https://lagen.nu/1990:931#P22",
            ),
        ),
    )
    assert "kap." not in html
    assert "22–29 §§" in html


def test_avsnittsspannet_lankar_till_lagen_nu():
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="AvtL",
        namn="Avtalslagen",
        sfs="1915:218",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/1915:218",
        kursavsnitt=(
            _grupp(None, "", "10–27 §§", "Fullmakt", "https://lagen.nu/1915:218#P10"),
        ),
    )
    assert 'href="https://lagen.nu/1915:218#P10"' in html
    assert 'target="_blank"' in html


def test_lagkortet_sager_att_urvalet_foljer_kursen():
    """Utan noten läses listan som om lagen tog slut där."""
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="X",
        namn="X",
        sfs="1:1",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/1:1",
        kursavsnitt=(_grupp(None, "", "1 §", "Något"),),
    )
    assert "Urvalet följer kursen, inte hela lagen." in html


def test_avsnittsrubrik_som_upprepar_kapitelrubriken_utelamnas():
    """BrB 3 kap. heter "Om brott mot liv och hälsa" och avsnittet likaså.

    Att skriva ut båda ger en synlig dubblering i kortet; spannet räcker.
    """
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="BrB",
        namn="Brottsbalk",
        sfs="1962:700",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/1962:700",
        kursavsnitt=(
            _grupp(
                "3",
                "Om brott mot liv och hälsa",
                "1–12 §§",
                "Om brott mot liv och hälsa",
            ),
        ),
    )
    assert html.count("Om brott mot liv och hälsa") == 1
    assert "1–12 §§" in html


def test_avsnittsrubrik_som_skiljer_sig_star_kvar():
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="BrB",
        namn="Brottsbalk",
        sfs="1962:700",
        beskrivning="B",
        nar="N",
        url="https://lagen.nu/1962:700",
        kursavsnitt=(
            _grupp(
                "24",
                "Om allmänna grunder för ansvarsfrihet",
                "1–9 §§",
                "Ansvarsfrihetsgrunder (nöd, nödvärn, samtycke)",
            ),
        ),
    )
    assert "Om allmänna grunder för ansvarsfrihet" in html
    assert "Ansvarsfrihetsgrunder (nöd, nödvärn, samtycke)" in html


# --- Design-tokens: typskala och spacingskala (design_system.md 2.1, 2.2) ------

def _css() -> str:
    """Plocka ut CSS-mallen ur utils.css utan att köra Streamlit.

    CSS_MALL flyttades ut ur inject_css() till en egen modul (se
    utils/css.py) för att hålla utils/ui.py under radtaket, så källan läses
    härifrån i stället för från inject_css.
    """
    import inspect
    return inspect.getsource(utils.css)


def test_alla_tokens_ar_deklarerade():
    css = _css()
    for token in ("--t-hero", "--t-h2", "--t-h3", "--t-brod", "--t-ui",
                  "--t-etikett", "--s1", "--s2", "--s3", "--s4", "--s5",
                  "--s6", "--s7"):
        assert f"{token}:" in css, f"token {token} saknas i :root"


def test_inga_hardkodade_typstorlekar():
    """font-size ska referera en token, aldrig ett px-tal.

    Tokendeklarationerna i :root skrivs som `--t-hero: 28px`, inte som
    `font-size:`, så de matchas inte av mönstret och behöver inget undantag.
    """
    hardkodade = re.findall(r"font-size:\s*(\d+)px", _css())
    assert not hardkodade, f"hårdkodade typstorlekar kvar: {sorted(set(hardkodade))}"
