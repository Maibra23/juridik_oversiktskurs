"""Ingångspunkt och router för Juridikverkstan.

Ansvarar för:
- st.set_page_config (måste köras först av alla Streamlit-anrop)
- sidregistret nedan, som ger sidorna deras namn i sidopanelen
- gemensam CSS och sidopanel för samtliga sidor via utils.ui

Varför sidorna ligger i sidor/ och INTE i pages/: en mapp som heter exakt
pages/ aktiverar Streamlits äldre automatiska sidnavigering. Den härleder
etiketter ur ASCII-filnamnen ("Avtalsratt", "Kop och konsumentratt") och
listar även ingångsskriptet som "streamlit app". Ännu värre serveras varje
pages/-fil på sin egen URL och renderas då fristående, utan att den här
routern (och därmed CSS:en och den svenska sidopanelen) körs. Genom att
lägga sidorna i sidor/ finns ingen automatisk navigering: alla vägar går
genom detta skript, och st.navigation ger korrekta svenska titlar.

Ingen affärslogik här: sidinnehållet ligger i sidor/ och all LLM-,
lagrumslogik och scenariologik i utils/.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Juridikverkstan",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None},
)

from utils.navigation import registrera_besok  # noqa: E402
from utils.ui import inject_css, render_sidebar  # noqa: E402

# Titeln är etiketten i webbläsarfliken. Sökvägen måste matcha filnamnet i
# sidor/ exakt. Ordningen här saknar betydelse för sidopanelen: den ritas av
# utils.ui.render_sidopanel ur navigeringsträdet i utils.navigation.
SIDOR = [
    st.Page("sidor/0_Hem.py", title="Hem", default=True),
    st.Page("sidor/1_Juridisk_metod.py", title="Juridisk metod"),
    st.Page("sidor/16_Rattskartan.py", title="Rättskartan"),
    st.Page("sidor/12_Personratt.py", title="Personrätt"),
    st.Page("sidor/13_Allman_formogenhetsratt.py", title="Allmän förmögenhetsrätt"),
    st.Page("sidor/2_Avtalsratt.py", title="Avtalsrätt"),
    st.Page("sidor/3_Kop_och_konsumentratt.py", title="Köprätt och konsumenträtt"),
    st.Page("sidor/4_Skadestandsratt.py", title="Skadeståndsrätt"),
    st.Page("sidor/5_Arbetsratt.py", title="Arbetsrätt"),
    st.Page("sidor/6_Associationsratt.py", title="Associationsrätt"),
    st.Page("sidor/7_Familje_och_arvsratt.py", title="Familjerätt och successionsrätt"),
    st.Page("sidor/8_Straff_och_processratt.py", title="Straffrätt och processrätt"),
    st.Page("sidor/14_Fastighetsratt.py", title="Fastighetsrätt"),
    st.Page("sidor/15_Fordringsratt.py", title="Fordringsrätt"),
    st.Page("sidor/9_Kunskapstest.py", title="Kunskapstest"),
    st.Page("sidor/10_Kunskapskarta.py", title="Kunskapskarta"),
    st.Page("sidor/11_Kunskapsutmaning.py", title="Kunskapsutmaning"),
]

inject_css()
# position="hidden": Streamlits egen platta sidlista ritas inte, så att den
# inte konkurrerar med det hierarkiska trädet i sidopanelen.
aktiv_sida = st.navigation(SIDOR, position="hidden")
st.session_state["_jok_aktiv_sida"] = aktiv_sida.title
registrera_besok(st.session_state, aktiv_sida.title)
render_sidebar()
aktiv_sida.run()
