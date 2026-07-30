"""Renderingstester för sidan Rättskartan (sidor/16_Rattskartan.py).

Sidans hela löfte är att den är *deterministisk*: alla tre flikarna ska vara
fulla på dag noll, utan LLM, utan token och utan genomförda rättsfall. Övriga
tester vaktar datalagret var för sig. De här kör hela sidan och vaktar löftet
i sin helhet, så att en framtida ändring inte smyger in ett LLM-anrop eller en
session_state-läsning i renderingsvägen.

Två saker stubbas, och bara två:

- ``st.page_link`` kastar ``KeyError: 'url_pathname'`` under AppTest, som
  saknar den sidkontext ett multipage-appbygge ger. Det är en begränsning i
  testverktyget, inte ett fel i sidan: samma anrop fungerar i appen och
  används redan i sidor/0_Hem.py och utils/ui.py.
- ``utils.llm.cached_chat`` ersätts med en spion som failar testet om den
  anropas. Sidan får rendera 52 tutorknappar, men inte röra modellen förrän
  någon faktiskt trycker på en.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

SIDA = str(Path(__file__).resolve().parent.parent / "sidor" / "16_Rattskartan.py")


@pytest.fixture
def sida(monkeypatch):
    """Kör Rättskartan med tom session_state, utan token och utan LLM."""
    import streamlit as st

    import utils.llm

    # Ingen token: sidan ska inte ens vara frestad att nå en modell.
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("HUGGINGFACEHUB_API_TOKEN", raising=False)

    def _forbjudet_llm_anrop(*args, **kwargs):
        raise AssertionError(
            "Rättskartan anropade LLM:en vid rendering. Sidan ska vara helt "
            "deterministisk tills studenten trycker på \"Förklara djupare\"."
        )

    monkeypatch.setattr(utils.llm, "cached_chat", _forbjudet_llm_anrop)
    monkeypatch.setattr(st, "page_link", lambda *a, **k: None)

    at = AppTest.from_file(SIDA, default_timeout=120)
    at.run()
    return at


def test_sidan_renderar_utan_fel_med_tom_session_state(sida):
    """Grundlöftet: inget krav på tidigare arbete, inget krav på token."""
    assert not sida.exception, [str(e.value) for e in sida.exception]


def test_sidan_ror_inte_llm_vid_rendering(sida):
    """Spionen i fixturen failar om modellen anropas. Detta befäster det."""
    assert not sida.exception


def test_alla_tre_flikarna_har_innehall(sida):
    """Systemet, Falltypsguide och Nyckelbegrepp ska alla vara fulla."""
    # Flik 1: ett områdesträd av expanders (avdelningar + delområden).
    assert len(sida.expander) > 5

    # Flik 2: falltypsguiden som tabell.
    assert len(sida.dataframe) == 1

    # Flik 3: sök, områdesfilter och ett tutorupplägg per begrepp.
    assert len(sida.text_input) == 2  # falltypssök + begreppssök
    assert len(sida.selectbox) == 1  # områdesfilter
    assert len(sida.button) > 0  # "Förklara djupare" per begrepp


def test_varje_begrepp_far_sin_egen_tutorknapp(sida):
    """Knappnycklarna måste vara unika, annars kraschar Streamlit i appen."""
    from utils.nyckelbegrepp import ladda_begrepp

    nycklar = [k.key for k in sida.button if k.key]
    assert len(nycklar) == len(set(nycklar)), "dubblerade knappnycklar"
    # En nycklad tutorknapp per begrepp. Återställningsknappen överst saknar
    # nyckel och räknas därför inte in här.
    assert len(nycklar) == len(ladda_begrepp())


def test_sidan_anvander_inga_raa_statuskomponenter(sida):
    """Designsystemet: statusrutor går genom render_*, aldrig st.success m.fl."""
    assert not sida.success
    assert not sida.warning
    assert not sida.error
    assert not sida.info
