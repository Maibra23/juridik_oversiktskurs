"""Startsida: hero-block, en enda call-to-action, framsteg och arbetsgång.

Registreras som standardsida i sidregistret i streamlit_app.py. CSS och
sidopanel injiceras centralt av ingångspunkten, inte här.

Modullistan visas inte här: sidopanelen (utils.navigation.NAV_TRAD) är
appens enda navigering. Startsidan gör i stället det sidopanelen inte kan
— visa var du är i kursen och ge dig ett enda tydligt nästa steg — så att
de två aldrig konkurrerar om att vara "kartan över kursen".

Ingen affärslogik: all LLM-, lagrums- och scenariologik ligger i utils/.
"""

from __future__ import annotations

import streamlit as st

from utils.export import (
    bygg_excel_rapport,
    bygg_markdown_rapport,
    genomforda_case,
)
from utils.navigation import SENAST_BESOKT_NYCKEL, cta_mal
from utils.obsidian import bygg_valv, hamta_case_analyser
from utils.quiz import alla_resultat
from utils.texter import antal_med_enhet
from utils.ui import (
    footer_note,
    hero,
    pipeline_steps,
    render_info,
    section_heading,
)


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

    _render_cta()
    _render_framsteg()

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

    st.html(footer_note())


def _render_cta() -> None:
    """Startsidans enda call-to-action: fortsätt eller kom igång.

    Modulerna nås i övrigt uteslutande via sidopanelen: en andra länklista
    här skulle bara upprepa den, i en annan ordning, med olika omfattning.
    """
    try:
        senast = st.session_state.get(SENAST_BESOKT_NYCKEL)
    except Exception:
        senast = None
    mal = cta_mal(senast)

    st.html(
        section_heading(
            "NÄSTA STEG",
            "Fortsätt där du var" if mal.ateruppta else "Kom igång",
        )
    )
    prefix = "Fortsätt" if mal.ateruppta else "Börja med"
    if st.button(f"{prefix}: {mal.titel} →", type="primary"):
        st.switch_page(mal.sida)


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
