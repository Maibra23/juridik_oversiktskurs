"""Modulsida: Familjerätt och arvsrätt.

Ansvarar för övningar om äktenskapsbalken, sambolagen (2003:376) och
ärvdabalken: bodelning, giftorättsgods, arvsordning och testamente.
Scenarier hämtas från data/scenarier/ och tutorns lagrumshänvisningar
verifieras mot lagrumsregistret.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Familje- och successionsrätt · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.modulvy import rendera_modulsida  # noqa: E402

rendera_modulsida(
    "familje_och_arvsratt",
    "Familje- och successionsrätt",
    "KAP. 18–21 · FAMILJ OCH ARV",
)
