"""Modulsida: Arbetsrätt.

Ansvarar för övningar om anställningsskydd (LAS 1982:80),
medbestämmande (MBL 1976:580) och diskrimineringslagen (2008:567).
Studenten analyserar uppsägnings- och förhandlingsscenarier med
lagrumsverifierade förklaringar från tutorn.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Arbetsrätt · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.modulvy import rendera_modulsida  # noqa: E402

rendera_modulsida("arbetsratt", "Arbetsrätt", "KAP. 11 · ARBETSRÄTT")
