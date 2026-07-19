"""Tester för designsystemets rena HTML-komponenter i utils/ui.py.

Testar de komponenter som returnerar HTML-strängar utan Streamlit-anrop:
RNTS-steppern (render_rnts_steg), scenariokortet (render_case) och
lagrumschipen. Rendering till skärm (st.html) testas inte här utan i
röktesterna som importerar sidorna i bare mode.
"""

from __future__ import annotations

import pytest

from utils.ui import (
    RNTS_STATUS_EJ_PABORJAD,
    RNTS_STATUS_GODKAND,
    RNTS_STATUS_PAGAR,
    RNTS_STATUS_BEHOVER_MER,
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
