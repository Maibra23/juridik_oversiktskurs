"""Global sida: Kunskapskarta.

Visar en interaktiv kunskapsgraf över de rättsfall studenten genomfört den här
sessionen och de lagrum de bygger på. Lagrum som återkommer i flera fall blir
gemensamma noder, så grafen synliggör hur samma paragraf tillämpas i olika
situationer, samma sammanlänkning som Obsidianexporten ger men live i appen.

Datat kommer från session_state (utils.obsidian.hamta_case_analyser) och byggs
deterministiskt utan LLM. Kartan växer allteftersom studenten fyller i fler
RNTS-analyser.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Kunskapskarta · Juridisk översiktskurs",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.graf import bygg_graf  # noqa: E402
from utils.graf_ui import render_kunskapsgraf  # noqa: E402
from utils.obsidian import hamta_case_analyser  # noqa: E402
from utils.texter import antal_med_enhet  # noqa: E402
from utils.ui import (  # noqa: E402
    footer_note,
    hero,
    inject_css,
    render_info,
    render_sidebar,
    section_heading,
)

inject_css()
render_sidebar("kunskapskarta")

st.html(
    hero(
        eyebrow="KUNSKAPSKARTA",
        title="Så hänger dina rättsfall ihop",
        lead=(
            "Varje rättsfall du fyllt i en RNTS-analys för visas här tillsammans "
            "med de lagrum det bygger på. Lagrum som återkommer i flera fall blir "
            "gemensamma noder. Dra i grafen och se hur paragraferna binder ihop "
            "situationerna."
        ),
    )
)

analyser = hamta_case_analyser()

st.html(section_heading("KARTA", "Rättsfall och lagrum"))
if not analyser:
    render_info(
        "Du har inte genomfört några rättsfall ännu. Öppna en modul, fyll i hela "
        "RNTS-analysen för ett rättsfall, så dyker det upp här tillsammans med sina "
        "lagrum. Kartan växer för varje fall du arbetar igenom."
    )
else:
    graf = bygg_graf(analyser)
    antal_lagrum = sum(1 for n in graf["noder"] if n["grupp"] == "lagrum")
    st.caption(
        antal_med_enhet(len(analyser), "genomfört rättsfall", "genomförda rättsfall")
        + f" · {antal_lagrum} lagrum. Guld = lagrum, blå = rättsfall, mörkblå = modul."
    )
    render_kunskapsgraf(graf)

st.html(footer_note())
