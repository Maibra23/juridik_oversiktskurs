"""Global sida: Kunskapsutmaning.

Studenten testar sin förmåga på ett färskt, fiktivt rättsfall som genereras av
LLM vid knapptryck. Fallet grundas mot appens lagrumsregister innan det visas
(utils.generator). Påhittade paragrafer släpps aldrig igenom, och vid problem
faller vi tillbaka på ett kuraterat fall. Själva övningen (RNTS-formulär, tutor
och facit) återanvänder exakt samma flöde som modulsidorna.
"""

from __future__ import annotations

import dataclasses

import streamlit as st

from utils.generator import generera_case, valj_slumpmodul
from utils.modulvy import rendera_case_ovning, svarighetsvaljare
from utils.scenarier import ladda_modul, lista_moduler
from utils.ui import (
    footer_note,
    hero,
    render_info,
    render_varning,
    section_heading,
)

st.html(
    hero(
        eyebrow="TESTA DIG SJÄLV",
        title="Kunskapsutmaning",
        lead=(
            "Generera ett helt nytt, fiktivt rättsfall och pröva din juridiska "
            "metod. Varje lagrum i facit kontrolleras mot appens lagrumsregister "
            "innan fallet visas. Du testas aldrig på en påhittad paragraf."
        ),
    )
)

@st.cache_data(show_spinner=False)
def _visningsnamn() -> dict[str, str]:
    """Karta från filnamn (stem) till modulens visningsnamn."""
    namn: dict[str, str] = {}
    for stem in lista_moduler():
        try:
            namn[stem] = ladda_modul(stem).modul
        except Exception:  # noqa: BLE001 (hoppa över trasig fil, visa stem)
            namn[stem] = stem
    return namn

visningsnamn = _visningsnamn()
moduler = list(visningsnamn)

st.html(section_heading("VÄLJ", "Vad vill du öva på?"))

kol_val, kol_slump = st.columns([3, 1], vertical_alignment="bottom")
with kol_val:
    vald_stem = st.selectbox(
        "Rättsområde",
        options=moduler,
        format_func=lambda s: visningsnamn.get(s, s),
        key="utmaning_val",
    )
with kol_slump:
    overraska = st.button("Överraska mig", width="stretch")

# Svårigheten väljs alltid av studenten. Överraska mig slumpar bara modulen,
# inte nivån: studenten behåller kontrollen över hur svårt fallet blir.
niva = svarighetsvaljare("utmaning_niva")

generera = st.button("Generera nytt rättsfall", type="primary")

if generera or overraska:
    stem = valj_slumpmodul() if overraska else vald_stem
    with st.spinner("Genererar ett nytt rättsfall och kontrollerar lagrummen …"):
        resultat = generera_case(stem, svarighetsgrad=niva)
    # Unik id per generering så RNTS-formuläret alltid börjar tomt.
    raknare = st.session_state.get("utmaning_raknare", 0) + 1
    st.session_state["utmaning_raknare"] = raknare
    case = dataclasses.replace(resultat.case, id=f"utmaning-{raknare}")
    st.session_state["utmaning_case"] = case
    st.session_state["utmaning_modul"] = visningsnamn.get(stem, stem)
    st.session_state["utmaning_kalla"] = resultat.kalla
    st.session_state["utmaning_notis"] = resultat.notis

case = st.session_state.get("utmaning_case")
if case is None:
    render_info(
        "Välj ett rättsområde och tryck på **Generera nytt rättsfall**. Du kan "
        "också låta slumpen välja med **Överraska mig**."
    )
else:
    notis = st.session_state.get("utmaning_notis")
    if notis:
        render_varning(notis)
    elif st.session_state.get("utmaning_kalla") == "genererad":
        st.success(
            "Nytt rättsfall genererat och grundat mot appens lagrum. "
            "Skriv din RNTS-analys och be tutorn granska den."
        )
    st.divider()
    rendera_case_ovning(st.session_state["utmaning_modul"], case)

st.html(footer_note())
