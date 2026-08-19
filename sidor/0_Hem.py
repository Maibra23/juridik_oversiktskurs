"""Startsida: hero-block, en enda call-to-action och framsteg.

Registreras som standardsida i sidregistret i streamlit_app.py. CSS och
sidopanel injiceras centralt av ingångspunkten, inte här.

Modullistan visas inte här: sidopanelen (utils.navigation.NAV_TRAD) är
appens enda navigering. Startsidan gör i stället det sidopanelen inte kan
visa var du är i appen och ge dig ett enda tydligt nästa steg, så att
de två aldrig konkurrerar om att vara "kartan över appen".

Ingen affärslogik: all LLM-, lagrumslogik och scenariologik ligger i utils/.
"""

from __future__ import annotations

import streamlit as st

from utils.export import (
    bygg_excel_rapport,
    bygg_markdown_rapport,
    genomforda_case,
)
from utils.framsteg import pabborjade_moduler
from utils.navigation import SENAST_BESOKT_NYCKEL, cta_mal, sida_for_namn
from utils.obsidian import bygg_valv, hamta_case_analyser
from utils.quiz import alla_resultat
from utils.texter import antal_med_enhet
from utils.ui import footer_note, hero, section_heading


def render_landing() -> None:
    """Rendera hela landningssidan."""
    st.html(
        hero(
            eyebrow="JURIDIKVERKSTAN",
            title="Träna att tänka juridiskt, inte att läsa passivt",
            lead=(
                "Öva fallbaserat: identifiera rättsfrågan, hitta rätt lagrum, "
                "tillämpa normen och dra en slutsats."
            ),
        )
    )

    # Disclaimer högt upp: appen ger inte juridisk rådgivning (PRD 4). Den
    # fullständiga texten står i footer_note(); kravet var synlighet, inte
    # dominans, så här räcker en caption.
    st.caption(
        "Studieverktyg, inte juridisk rådgivning. Mata inte in personuppgifter."
    )

    _render_cta()
    _render_framsteg()

    st.html(footer_note())


def _render_cta() -> None:
    """Startsidans enda call-to-action: ett kort som svarar på vad och varför.

    Modulerna nås i övrigt uteslutande via sidopanelen: en andra länklista
    här skulle bara upprepa den, i en annan ordning, med olika omfattning.
    """
    try:
        senast = st.session_state.get(SENAST_BESOKT_NYCKEL)
    except Exception:
        senast = None
    mal = cta_mal(senast, pabborjade_moduler())

    st.html(
        section_heading(
            "NÄSTA STEG",
            "Fortsätt där du var" if mal.ateruppta else "Kom igång",
        )
    )
    if mal.skal:
        st.caption(mal.skal)
    prefix = "Fortsätt" if mal.ateruppta else "Börja med"
    if st.button(f"{prefix}: {mal.titel} →", type="primary"):
        st.switch_page(mal.sida)

    # Den sekundära vägen: har studenten en pågående modul som inte är målet,
    # ska den vara nåbar utan att konkurrera med den primära knappen.
    if not mal.ateruppta and senast and senast != mal.titel:
        sida = sida_for_namn(senast)
        if sida:
            st.page_link(sida, label=f"Fortsätt där du var: {senast}")


def _render_framsteg() -> None:
    """Framstegssektion: tre tal, en ärlig rad om sessionen, och exporten.

    Tomt tillstånd visar ingenting alls utom en mening: en förstagångsbesökare
    ska mötas av exakt en handling, inte av nedladdningsknappar för en rapport
    som ännu är tom.
    """
    resultat = alla_resultat()
    case_bok = genomforda_case()

    if not resultat and not case_bok:
        st.caption(
            "När du börjat öva visas dina framsteg här."
        )
        return

    st.html(section_heading("FRAMSTEG", "Så här långt"))

    moduler = len(pabborjade_moduler())
    fall = sum(len(ids) for ids in case_bok.values())
    ratt = sum(r for r, _b in resultat.values())
    besvarade = sum(b for _r, b in resultat.values())

    delar = [
        antal_med_enhet(moduler, "modul påbörjad", "moduler påbörjade"),
        antal_med_enhet(fall, "rättsfall genomfört", "rättsfall genomförda"),
    ]
    if besvarade:
        delar.append(f"{ratt}/{besvarade} rätt på quiz")
    st.markdown(": ".join(delar))

    st.caption(
        "Framstegen gäller den här sessionen. Stänger du fliken är de borta. "
        "ladda ner dem nedan för att behålla dem."
    )
    _render_export(case_bok)


def _render_export(case_bok: dict[str, tuple[str, ...]]) -> None:
    """Exportknapparna: valvet primärt, rapporterna sekundära.

    Obsidianvalvet ligger först och får mest vikt eftersom det är den
    pedagogiskt intressanta exporten: Rättskartan följer alltid med, varje
    RNTS-analys blir en egen not, och noterna binds ihop av sina lagrum. Det
    är appens enda väg till repetition över tid.
    """
    st.html(section_heading("TA MED DIG", "Läs om det du gjort i morgon"))
    st.download_button(
        "Ladda ner Obsidianvalv med Rättskartan (zip)",
        data=bygg_valv(hamta_case_analyser()),
        file_name="juridik_valv.zip",
        mime="application/zip",
        type="primary",
    )
    st.caption(
        "Packa upp zipen och öppna mappen Juridik som ett valv i Obsidian. "
        "Rättskartan är en klickbar karta över rättssystemet, och varje "
        "genomförd RNTS-analys blir en egen not."
    )

    kol_md, kol_xlsx = st.columns(2)
    with kol_md:
        st.download_button(
            "Rapport (Markdown)",
            data=bygg_markdown_rapport(resultat_till_svar(), case_bok),
            file_name="studierapport.md",
            mime="text/markdown",
        )
    with kol_xlsx:
        st.download_button(
            "Rapport (Excel)",
            data=bygg_excel_rapport(resultat_till_svar(), case_bok),
            file_name="studierapport.xlsx",
            mime="application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet",
        )


def resultat_till_svar() -> dict[str, dict[str, bool]]:
    """Hämta rå quizresultatbok ur session_state för rapportbyggarna."""
    try:
        return dict(st.session_state.get("quiz_resultat", {}))
    except Exception:
        return {}


render_landing()
