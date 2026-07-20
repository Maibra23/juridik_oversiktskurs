"""Ingångspunkt och router för Juridisk översiktskurs.

Ansvarar för:
- st.set_page_config (måste köras först av alla Streamlit-anrop)
- sidregistret nedan, som ger sidorna deras namn i sidopanelen
- gemensam CSS och sidopanel för samtliga sidor via utils.ui

Varför ett explicit sidregister: filnamnen i pages/ är ASCII och saknar
å, ä och ö. Streamlits automatiska sidnavigering härleder etiketterna ur
filnamnen och visade därför "Avtalsratt", "Kop och konsumentratt" och
"streamlit app" i sidopanelen. st.navigation låter oss sätta korrekt
svenska titlar oberoende av filnamnen.

Ingen affärslogik här: sidinnehållet ligger i pages/ och all LLM-,
lagrums- och scenariologik i utils/.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None},
)

from utils.ui import inject_css, render_sidebar  # noqa: E402

# Titeln är etiketten i sidopanelen och i webbläsarfliken. Sökvägen måste
# matcha filnamnet i pages/ exakt.
SIDOR = [
    st.Page("pages/0_Hem.py", title="Hem", default=True),
    st.Page("pages/1_Juridisk_metod.py", title="Juridisk metod"),
    st.Page("pages/2_Avtalsratt.py", title="Avtalsrätt"),
    st.Page("pages/3_Kop_och_konsumentratt.py", title="Köp- och konsumenträtt"),
    st.Page("pages/4_Skadestandsratt.py", title="Skadeståndsrätt"),
    st.Page("pages/5_Arbetsratt.py", title="Arbetsrätt"),
    st.Page("pages/6_Associationsratt.py", title="Associationsrätt"),
    st.Page("pages/7_Familje_och_arvsratt.py", title="Familje- och successionsrätt"),
    st.Page("pages/8_Straff_och_processratt.py", title="Straff- och processrätt"),
    st.Page("pages/9_Kunskapstest.py", title="Kunskapstest"),
    st.Page("pages/10_Kunskapskarta.py", title="Kunskapskarta"),
    st.Page("pages/11_Kunskapsutmaning.py", title="Kunskapsutmaning"),
]

inject_css()
aktiv_sida = st.navigation(SIDOR)
render_sidebar()
aktiv_sida.run()
