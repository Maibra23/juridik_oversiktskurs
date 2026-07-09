"""Modulsida: Skadeståndsrätt.

Ansvarar för övningar om utomobligatoriskt skadestånd enligt
skadeståndslagen (1972:207): culparegeln, person- och sakskada, ren
förmögenhetsskada samt principalansvar. Tutorförklaringar genereras on
demand och citerade lagrum verifieras mot registret.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Skadeståndsrätt · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.modulvy import rendera_modulsida  # noqa: E402

rendera_modulsida("skadestandsratt", "Skadeståndsrätt", "KAP. 10 · SKADESTÅNDSRÄTT")
