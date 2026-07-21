"""Startsida: hero-block, modulkarta, arbetsgång och framsteg.

Registreras som standardsida i sidregistret i streamlit_app.py. CSS och
sidopanel injiceras centralt av ingångspunkten, inte här.

Ingen affärslogik: all LLM-, lagrums- och scenariologik ligger i utils/.
"""

from __future__ import annotations

import streamlit as st

from utils.export import (
    bygg_excel_rapport,
    bygg_markdown_rapport,
    genomforda_case,
)
from utils.obsidian import bygg_valv, hamta_case_analyser
from utils.quiz import alla_resultat
from utils.texter import antal_med_enhet
from utils.ui import (
    footer_note,
    hero,
    module_map,
    pipeline_steps,
    render_info,
    section_heading,
)

# Paretourvalet: tolv P0-moduler (PRD avsnitt 5.1) och sidfilerna de länkar
# till. Ordningen speglar bokens kapitelföljd.
MODULER = [
    {
        "roll": "Grund",
        "titel": "Juridisk metod",
        "tag": "Kap. 1",
        "beskrivning": "Rättskälleläran, lagtolkning och RNTS-strukturen.",
        "sida": "pages/1_Juridisk_metod.py",
    },
    {
        "roll": "Person",
        "titel": "Personrätt",
        "tag": "Kap. 5",
        "beskrivning": "Rättskapacitet, underårigas avtal och framtidsfullmakt.",
        "sida": "pages/12_Personratt.py",
    },
    {
        "roll": "Egendom",
        "titel": "Allmän förmögenhetsrätt",
        "tag": "Kap. 6",
        "beskrivning": "Äganderättens övergång, godtrosförvärv och lösningsrätt.",
        "sida": "pages/13_Allman_formogenhetsratt.py",
    },
    {
        "roll": "Avtal",
        "titel": "Avtalsrätt",
        "tag": "Kap. 7",
        "beskrivning": "Anbud och accept, fullmakt, ogiltighet och 36 § AvtL.",
        "sida": "pages/2_Avtalsratt.py",
    },
    {
        "roll": "Köp",
        "titel": "Köp- och konsumenträtt",
        "tag": "Kap. 8",
        "beskrivning": "KöpL mot KKöpL, dröjsmål, fel och påföljder.",
        "sida": "pages/3_Kop_och_konsumentratt.py",
    },
    {
        "roll": "Fastighet",
        "titel": "Fastighetsrätt",
        "tag": "Kap. 9",
        "beskrivning": "Tillbehör, formkrav vid köp och undersökningsplikt.",
        "sida": "pages/14_Fastighetsratt.py",
    },
    {
        "roll": "Skadestånd",
        "titel": "Skadeståndsrätt",
        "tag": "Kap. 10",
        "beskrivning": "Culparegeln, adekvat kausalitet och principalansvar.",
        "sida": "pages/4_Skadestandsratt.py",
    },
    {
        "roll": "Arbete",
        "titel": "Arbetsrätt",
        "tag": "Kap. 11",
        "beskrivning": "Anställningsformer, uppsägning mot avsked och diskriminering.",
        "sida": "pages/5_Arbetsratt.py",
    },
    {
        "roll": "Bolag",
        "titel": "Associationsrätt",
        "tag": "Kap. 12",
        "beskrivning": "Bolagsformerna och personligt ansvar i olika bolag.",
        "sida": "pages/6_Associationsratt.py",
    },
    {
        "roll": "Fordringar",
        "titel": "Fordringsrätt",
        "tag": "Kap. 15-17",
        "beskrivning": "Löpande mot enkla skuldebrev, preskription och obestånd.",
        "sida": "pages/15_Fordringsratt.py",
    },
    {
        "roll": "Familj & arv",
        "titel": "Familje- och successionsrätt",
        "tag": "Kap. 18–21",
        "beskrivning": "Bodelning, arvsordning, laglott och testamente.",
        "sida": "pages/7_Familje_och_arvsratt.py",
    },
    {
        "roll": "Straff & process",
        "titel": "Straff- och processrätt",
        "tag": "Kap. 22",
        "beskrivning": "Brottsbegreppet, uppsåt mot oaktsamhet och ansvarsfrihet.",
        "sida": "pages/8_Straff_och_processratt.py",
    },
    {
        "roll": "Pröva",
        "titel": "Kunskapstest",
        "tag": "Alla moduler",
        "beskrivning": "Samlad resultatöversikt över dina quiz per modul.",
        "sida": "pages/9_Kunskapstest.py",
    },
]


def render_landing() -> None:
    """Rendera hela landningssidan."""
    st.html(
        hero(
            eyebrow="JURIDISK ÖVERSIKTSKURS",
            title="Träna att tänka juridiskt, inte att läsa passivt",
            lead=(
                "Öva fallbaserat: identifiera rättsfrågan, hitta rätt lagrum, "
                "tillämpa normen och dra en slutsats."
            ),
        )
    )

    # Disclaimer högt upp: appen ger inte juridisk rådgivning (PRD 4).
    render_info(
        "Ett studieverktyg, inte juridisk rådgivning. Mata inte in personuppgifter."
    )

    st.html(section_heading("MODULER", "Tolv moduler där juridisk metod ger mest"))
    st.html(module_map(MODULER))

    # Riktiga navigeringslänkar under kartan (modulkorten är inte klickbara).
    cols = st.columns(4)
    for i, modul in enumerate(MODULER):
        with cols[i % 4]:
            st.page_link(modul["sida"], label=f'{modul["titel"]} →')

    st.html(section_heading("ARBETSGÅNG", "Så arbetar du i varje modul"))
    st.html(
        pipeline_steps(
            [
                "Läs scenariot",
                "Skriv din RNTS-analys",
                "Be tutorn granska",
                "Öva lagrum och quiz",
            ]
        )
    )

    _render_framsteg()

    st.html(footer_note())


def _render_framsteg() -> None:
    """Framstegssektion: quizresultat och genomförda case, med export."""
    st.html(section_heading("FRAMSTEG", "Dina resultat den här sessionen"))

    resultat = alla_resultat()
    case_bok = genomforda_case()
    if not resultat and not case_bok:
        st.info(
            "Inga resultat ännu. Öppna en modul, besvara quizfrågor eller "
            "fyll i en RNTS-analys så samlas dina framsteg här."
        )
    else:
        for modul, (ratt, besvarade) in sorted(resultat.items()):
            andel = ratt / besvarade if besvarade else 0.0
            st.progress(andel, text=f"{modul}: {ratt}/{besvarade} rätt på quiz")
        for modul, case_ids in sorted(case_bok.items()):
            st.markdown(
                f"- **{modul}**: "
                + antal_med_enhet(
                    len(case_ids), "genomfört rättsfall", "genomförda rättsfall"
                )
            )

        kol_md, kol_xlsx = st.columns(2)
        with kol_md:
            st.download_button(
                "Ladda ner rapport (Markdown)",
                data=bygg_markdown_rapport(resultat_till_svar(), case_bok),
                file_name="studierapport.md",
                mime="text/markdown",
            )
        with kol_xlsx:
            st.download_button(
                "Ladda ner rapport (Excel)",
                data=bygg_excel_rapport(resultat_till_svar(), case_bok),
                file_name="studierapport.xlsx",
                mime="application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet",
            )

    # Obsidianvalvet är värdefullt redan utan analyser: Rättskartan, en
    # klickbar och hopfällbar karta över rättssystemet, följer alltid med.
    st.download_button(
        "Ladda ner Obsidianvalv med Rättskartan (zip)",
        data=bygg_valv(hamta_case_analyser()),
        file_name="juridik_valv.zip",
        mime="application/zip",
    )
    st.info(
        "Packa upp zipen och öppna mappen **Juridik** som ett valv i Obsidian. "
        "**Rättskartan** är en klickbar karta över rättssystemet, och varje "
        "genomförd RNTS-analys blir en egen not."
    )


def resultat_till_svar() -> dict[str, dict[str, bool]]:
    """Hämta rå quizresultatbok ur session_state för rapportbyggarna."""
    try:
        return dict(st.session_state.get("quiz_resultat", {}))
    except Exception:
        return {}


render_landing()
