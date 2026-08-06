"""Tester för startsidans tomma tillstånd (sidor/0_Hem.py, Task 8).

Löftet är att en förstagångsbesökare möts av exakt en handling: CTA-knappen,
och inga nedladdningsknappar för en rapport som ännu är tom.

Testet kör inte `AppTest.from_file` direkt på `sidor/0_Hem.py`. Den varianten
saknar den sidkontext ett multipage-bygge ger, och `st.page_link` i
sidopanelen kastar då `KeyError: 'url_pathname'` (dokumenterat i
tests/test_rattskartan_sida.py, som drabbas av samma sak för Rättskartan).
I stället körs `streamlit_app.py` — ingångspunkten som registrerar sidorna
och ger den kontexten. Det visade sig fungera utan någon work-around: körd
headless (`python3 -m pytest` och fristående via `python3 -c`) uppstod
aldrig `KeyError`, sannolikt för att `st.navigation` i `streamlit_app.py`
ger `st.page_link` de sidobjekt den behöver, till skillnad från när en
undersida körs som huvudskript utan den registreringen.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import utils.obsidian

APP = str(Path(__file__).resolve().parent.parent / "streamlit_app.py")


@pytest.fixture
def tom_app() -> AppTest:
    """Kör appen med helt tom session_state (en förstagångsbesökare)."""
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    return at


def test_tomt_tillstand_har_exakt_en_knapp(tom_app: AppTest):
    """CTA:n är den enda handlingen en förstagångsbesökare ska mötas av."""
    assert not tom_app.exception, [str(e.value) for e in tom_app.exception]
    etiketter = [b.label for b in tom_app.button]
    assert len(etiketter) == 1, (
        f"tomt tillstånd ska ha exakt en knapp, har {etiketter}"
    )


def test_tomt_tillstand_har_noll_nedladdningar(tom_app: AppTest):
    """Inga nedladdningsknappar för en rapport eller ett valv som är tomt."""
    assert len(tom_app.get("download_button")) == 0


def test_bygg_valv_anropas_inte_i_tomt_lage(monkeypatch: pytest.MonkeyPatch):
    """`_render_export` (och därmed `bygg_valv`) får inte köras i tomt läge.

    Poängen med det tidiga returnet i `_render_framsteg` är att sidan inte
    ska bygga en rapport ingen bett om. En spion som failar testet om
    `bygg_valv` anropas bevisar det direkt, i stället för att bara lita på
    att knappen den producerar råkar utebli.
    """

    def _forbjudet_anrop(*args, **kwargs):
        raise AssertionError(
            "bygg_valv anropades trots tomt tillstånd — startsidan ska inte "
            "bygga en rapport av innehåll som inte finns."
        )

    monkeypatch.setattr(utils.obsidian, "bygg_valv", _forbjudet_anrop)
    monkeypatch.setattr(utils.obsidian, "hamta_case_analyser", _forbjudet_anrop)

    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]


def test_export_nas_nar_studenten_gjort_nagot(tom_app: AppTest):
    """Så snart något finns att exportera ska valvet och rapporterna synas."""
    tom_app.session_state["quiz_resultat"] = {"Juridisk metod": {"q1": True}}
    tom_app.run()

    etiketter = [b.label for b in tom_app.get("download_button")]
    assert "Ladda ner Obsidianvalv med Rättskartan (zip)" in etiketter
    assert "Rapport (Markdown)" in etiketter
    assert "Rapport (Excel)" in etiketter
