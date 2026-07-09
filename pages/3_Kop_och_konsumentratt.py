"""Modulsida: Köprätt och konsumenträtt.

Ansvarar för övningar om köplagen (1990:931), konsumentköplagen
(2022:260) och distansavtalslagen. Sidan låter studenten analysera
felansvar, reklamation och påföljder i genererade scenarier, med
lagrumsverifierade tutorförklaringar.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Köp- och konsumenträtt · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.modulvy import rendera_modulsida  # noqa: E402

rendera_modulsida(
    "kop_och_konsumentratt", "Köp- och konsumenträtt", "KAP. 8 · KÖPRÄTT"
)
