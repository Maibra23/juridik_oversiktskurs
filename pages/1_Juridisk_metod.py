"""Modulsida: Juridisk metod och rättskällor.

Ansvarar för den interaktiva övningen i rättskälleläran: författningar,
förarbeten, praxis och doktrin samt lagtolkningsmetoder. Sidan samlar
studentens input, anropar tutorn on demand via utils.tutor och verifierar
att förklaringens lagrumshänvisningar finns i utils.lagrum-registret.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Juridisk metod · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.modulvy import rendera_modulsida  # noqa: E402

rendera_modulsida("juridisk_metod", "Juridisk metod", "KAP. 1 · JURIDISK METOD")
