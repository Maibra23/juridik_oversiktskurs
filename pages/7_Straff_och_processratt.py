"""Modulsida: Straffrätt och processrätt.

Ansvarar för övningar om brottsbegreppet enligt brottsbalken (1962:700)
och rättegångens gång enligt rättegångsbalken (1942:740): rekvisit,
uppsåt/oaktsamhet, tvistemål och brottmål. Tutorförklaringar genereras
on demand med lagrumsverifiering.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Straff- och processrätt · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.modulvy import rendera_modulsida  # noqa: E402

rendera_modulsida(
    "straff_och_processratt", "Straff- och processrätt", "KAP. 22 · STRAFFRÄTT"
)
