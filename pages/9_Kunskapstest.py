"""Modulsida: Kunskapstest.

Ansvarar för quizflödet över samtliga juridikmoduler. Frågor hämtas från
deterministisk data i data/scenarier och varje fråga kvalitetskontrolleras:
citerade lagrum måste finnas i lagrumsregistret. Sidan sammanställer även
studentens resultat per modul från session_state.

Det blandade slumptestet över alla moduler byggs ut i Dag 3; här visas
en resultatöversikt och en genväg tillbaka till respektive modul.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Kunskapstest · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.quiz import alla_resultat  # noqa: E402
from utils.scenarier import ladda_modul, lista_moduler  # noqa: E402
from utils.ui import (  # noqa: E402
    footer_note,
    hero,
    inject_css,
    render_sidebar,
    section_heading,
)

inject_css()
render_sidebar("kunskapstest")

st.html(
    hero(
        eyebrow="KUNSKAPSTEST",
        title="Dina resultat per modul",
        lead=(
            "Här samlas resultaten från de quizfrågor du besvarat i modulerna. "
            "Öppna en modul för att öva vidare – varje quiz rättas deterministiskt "
            "och varje lagrum verifieras mot kursens lagrumslista."
        ),
    )
)

resultat = alla_resultat()

st.html(section_heading("RESULTAT", "Besvarade quizfrågor"))
if not resultat:
    st.info(
        "Du har inte besvarat några quizfrågor ännu. Gå till en modul och börja "
        "öva – dina resultat visas här."
    )
else:
    for modul, (ratt, besvarade) in sorted(resultat.items()):
        andel = f"{ratt}/{besvarade}"
        st.markdown(f"**{modul}** — {andel} rätt")


st.html(section_heading("MODULER", "Öva vidare"))
for namn in lista_moduler():
    try:
        modul = ladda_modul(namn)
    except Exception:
        continue
    antal = len(modul.flervalsfragor)
    if antal:
        st.markdown(f"- **{modul.modul}** · {antal} quizfrågor")

st.html(footer_note())
