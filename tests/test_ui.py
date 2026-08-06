"""Tester för designsystemets rena HTML-komponenter i utils/ui.py.

Testar de komponenter som returnerar HTML-strängar utan Streamlit-anrop:
RNTS-steppern (render_rnts_steg), scenariokortet (render_case) och
lagrumschipen. Rendering till skärm (st.html) testas inte här utan i
röktesterna som importerar sidorna i bare mode — med två undantag:
render_sidopanel testas genom att st.html/st.page_link/st.session_state
monkeypatchas, se avsnittet om aktiv rubrikkedja nedan för varför AppTest
inte kan användas där, och samma mönster används för
utils.modulvy._rendera_rattsfall i avsnittet om TRÄNAR-raden längst ner.
"""

from __future__ import annotations

import contextlib
import re

import pytest

import utils.css
from utils import modulvy
from utils.scenarier import (
    Alternativ,
    Case,
    CaseFacit,
    Flervalsfraga,
    Lagrumsjakt,
    Modulscenarier,
)
from utils.ui import (
    RNTS_STATUS_BEHOVER_MER,
    RNTS_STATUS_EJ_PABORJAD,
    RNTS_STATUS_GODKAND,
    RNTS_STATUS_PAGAR,
    render_case,
    render_kort,
    render_lagrum_chip,
    render_rnts_steg,
    render_sidopanel,
    statusrad,
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


# --- statusrad ------------------------------------------------------------

def test_statusrad_normalfall_ar_kort_och_inte_expanderad():
    text, expandera = statusrad(True, 40, 40, 300, 300)
    assert text == "Tutorn: tillgänglig"
    assert expandera is False


def test_statusrad_expanderar_nar_sessionen_narmar_sig_taket():
    _text, expandera = statusrad(True, 9, 40, 300, 300)
    assert expandera is True


def test_statusrad_expanderar_nar_dagsbudgeten_narmar_sig_taket():
    _text, expandera = statusrad(True, 40, 40, 70, 300)
    assert expandera is True


def test_statusrad_otillganglig_sager_vad_som_anda_fungerar():
    text, expandera = statusrad(False, 40, 40, 300, 300)
    assert "inte tillgänglig" in text
    assert expandera is True


def test_statusrad_tal_noll_tak_utan_division_med_noll():
    text, expandera = statusrad(True, 0, 0, 0, 0)
    assert text
    assert expandera is True


# --- render_sidopanel: aktiv rubrikkedja (design_system.md 4.1) ---------------
#
# Testar kopplingen hela vägen: st.session_state["_jok_aktiv_sida"] ->
# rubrikkedja -> klassen "aktiv" i den HTML render_sidopanel ritar. Utan de
# här testerna kan kopplingen tystna (t.ex. om nyckeln av misstag bar en
# sökväg i stället för ett modulnamn) utan att någon test i sviten märker
# det: rubrikkedja är väl testad i tests/test_navigation.py, men ingenting
# body-testade själva anropskedjan i render_sidopanel förrän nu.


def _sidopanel_html(monkeypatch: pytest.MonkeyPatch, session_state: dict) -> list[str]:
    """Kör render_sidopanel utanför AppTest och samla den ritade HTML:en.

    AppTest kan inte köra den här funktionen: render_sidopanel anropar
    st.page_link för varje modullöv i trädet, och st.page_link kastar
    KeyError: 'url_pathname' under AppTest eftersom testverktyget saknar den
    sidkontext ett riktigt multipage-appbygge ger (samma begränsning som
    tests/test_rattskartan_sida.py dokumenterar för sidor/16_Rattskartan.py,
    som har samma problem med samma anrop). Testet kör i stället funktionen
    direkt och monkeypatchar tre saker på streamlit-modulen: st.html samlar
    varje sträng i en lista i stället för att rita den, st.page_link blir en
    no-op så att modullöven inte kraschar, och st.session_state blir en
    vanlig dict med det värde testet vill undersöka.
    """
    import streamlit as st

    html_rader: list[str] = []
    monkeypatch.setattr(st, "html", lambda s: html_rader.append(s))
    monkeypatch.setattr(st, "page_link", lambda *a, **k: None)
    monkeypatch.setattr(st, "session_state", session_state)

    render_sidopanel()
    return html_rader


def _klass_for(html_rader: list[str], namn: str) -> str:
    """Klassattributet för den rad vars textinnehåll är exakt ``namn``."""
    for rad in html_rader:
        match = re.search(rf'<div class="([^"]*)">{re.escape(namn)}</div>', rad)
        if match:
            return match.group(1)
    raise AssertionError(f"Ingen rad för {namn!r} hittades i {html_rader}")


def test_render_sidopanel_markerar_hela_rubrikkedjan_som_aktiv(monkeypatch):
    """Avtalsrätt öppen: dess tre förfäder (i var sitt <div>) ska bära aktiv."""
    html_rader = _sidopanel_html(monkeypatch, {"_jok_aktiv_sida": "Avtalsrätt"})

    for namn in ("CIVILRÄTT", "Förmögenhetsrätt", "Kontraktsrätt"):
        klass = _klass_for(html_rader, namn)
        assert "aktiv" in klass.split(), f"{namn!r} fick inte klassen aktiv: {klass!r}"


def test_render_sidopanel_grupp_utanfor_kedjan_ar_inte_aktiv(monkeypatch):
    """Grupper som inte omsluter den öppna sidan ska aldrig bära aktiv.

    Utan den här kontrollen skulle testet ovan även godkänna en
    implementation som (felaktigt) sätter aktiv på varje grupp i trädet.
    Personrätt och Ersättningsrätt är särskilt viktiga negativa fall: de
    ligger som syskon till en aktiv gren (Förmögenhetsrätt respektive
    Kontraktsrätt) och skulle avslöja en implementation som markerar en hel
    förälder-nivå i stället för bara de faktiska förfäderna.
    """
    html_rader = _sidopanel_html(monkeypatch, {"_jok_aktiv_sida": "Avtalsrätt"})

    for namn in ("STRAFF- OCH PROCESSRÄTT", "Personrätt", "Ersättningsrätt"):
        klass = _klass_for(html_rader, namn)
        assert "aktiv" not in klass.split(), f"{namn!r} fick oväntat klassen aktiv: {klass!r}"


def test_render_sidopanel_utan_aktiv_sida_har_ingen_aktiv_klass(monkeypatch):
    """Tom session_state (ny session, eller en sida utanför trädet): inget aktiv alls."""
    html_rader = _sidopanel_html(monkeypatch, {})

    assert not any("aktiv" in rad for rad in html_rader), (
        "Ordet 'aktiv' förekom i utdatan trots att ingen sida är öppen."
    )


# --- _rendera_rattsfall: TRÄNAR-raden ligger efter tomhetskontrollen ----------
#
# En modul utan rättsfall ska inte annonsera vad fliken skulle ha tränat: raden
# ska ligga efter `if not modul.case: ... return`, inte före. Alla åtta
# scenariofiler i data/scenarier har rättsfall i dag, så utan det här testet
# kunde asymmetrin ligga vilande utan att något annat i sviten märkte den.

_DUMMY_ALTERNATIV = Alternativ(text="Ja", korrekt=True, forklaring="För att.", lagrum=None)
_DUMMY_FRAGA = Flervalsfraga(id="f1", fraga="Fråga?", alternativ=(_DUMMY_ALTERNATIV,))
_DUMMY_JAKT = Lagrumsjakt(id="j1", situation="En situation.", facit_lagrum=("1 § AvtL",))
_DUMMY_FACIT = CaseFacit(
    rattsfraga="Fråga?",
    lagrum=("1 § AvtL",),
    tillampningspunkter=("Punkt.",),
    slutsats="Svar.",
)
_DUMMY_CASE = Case(
    id="c1",
    rubrik="Rubrik",
    svarighetsgrad="grund",
    uppskattad_tid_min=5,
    scenariotext="Text.",
    facit=_DUMMY_FACIT,
)


def _rattsfall_html(monkeypatch: pytest.MonkeyPatch, modul: Modulscenarier) -> list[str]:
    """Kör _rendera_rattsfall utanför AppTest och samla den ritade HTML:en.

    Samma skäl som _sidopanel_html ovan: AppTest saknar sidkontext för
    st.button/st.selectbox/st.columns. Fliken monkeypatchas i stället direkt
    på streamlit-modulen (st.html samlar HTML-strängarna, st.session_state
    blir en vanlig dict, resten blir no-ops som inte tar någon gren), och
    rendera_case_ovning stubbas ut eftersom testet gäller TRÄNAR-radens
    placering i _rendera_rattsfall, inte hela case-flödet den funktionen
    i sin tur ritar.
    """
    import streamlit as st

    html_rader: list[str] = []
    monkeypatch.setattr(st, "html", lambda s: html_rader.append(s))
    monkeypatch.setattr(st, "info", lambda *a, **k: None)
    monkeypatch.setattr(st, "session_state", {})
    monkeypatch.setattr(st, "segmented_control", lambda *a, **k: None)
    monkeypatch.setattr(
        st,
        "columns",
        lambda spec: tuple(
            contextlib.nullcontext()
            for _ in range(spec if isinstance(spec, int) else len(spec))
        ),
    )
    monkeypatch.setattr(st, "button", lambda *a, **k: False)
    monkeypatch.setattr(st, "selectbox", lambda label, options, **k: options[0])
    monkeypatch.setattr(modulvy, "rendera_case_ovning", lambda *a, **k: None)

    modulvy._rendera_rattsfall("test", modul)
    return html_rader


def test_rattsfall_utan_case_ritar_ingen_tranar_rad(monkeypatch):
    """Tom case-tupel: ingen TRÄNAR-rad, trots innehåll i de andra två flikarna."""
    modul = Modulscenarier(
        modul="test", case=(), flervalsfragor=(_DUMMY_FRAGA,), lagrumsjakt=(_DUMMY_JAKT,)
    )
    html_rader = _rattsfall_html(monkeypatch, modul)

    assert not any("jok-tranar" in rad for rad in html_rader), (
        "TRÄNAR-raden ritades trots att modulen saknar rättsfall att träna på."
    )


def test_rattsfall_med_case_ritar_tranar_rad(monkeypatch):
    """Motsatsen till testet ovan: med ett rättsfall ska raden faktiskt ritas.

    Utan den här kontrollen skulle testet ovan även godkänna en
    implementation som aldrig ritar TRÄNAR-raden alls.
    """
    modul = Modulscenarier(modul="test", case=(_DUMMY_CASE,), flervalsfragor=(), lagrumsjakt=())
    html_rader = _rattsfall_html(monkeypatch, modul)

    assert any("jok-tranar" in rad for rad in html_rader), (
        "TRÄNAR-raden ritades inte trots att modulen har ett rättsfall."
    )
