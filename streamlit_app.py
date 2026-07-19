"""Startsida för Juridisk översiktskurs.

Ingångspunkt för Streamlit-multipage-appen. Ansvarar för:
- st.set_page_config (måste köras först av alla Streamlit-anrop)
- Hjärtat på landningssidan: hero-block, modulkarta och arbetsgång
- Navigering till modulsidorna i pages/ via st.page_link
- Injektion av gemensam CSS och rendering av sidopanelen via utils.ui

Ingen affärslogik här: all LLM-, lagrums- och scenariologik ligger i utils/.
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

from utils.export import (  # noqa: E402
    bygg_excel_rapport,
    bygg_markdown_rapport,
    genomforda_case,
)
from utils.obsidian import bygg_valv, hamta_case_analyser  # noqa: E402
from utils.quiz import alla_resultat  # noqa: E402
from utils.texter import antal_med_enhet  # noqa: E402
from utils.ui import (  # noqa: E402
    footer_note,
    hero,
    inject_css,
    module_map,
    pipeline_steps,
    render_info,
    render_sidebar,
    section_heading,
    summary_box,
)

inject_css()
render_sidebar("hem")

# Paretourvalet: åtta P0-moduler (PRD avsnitt 5.1) och sidfilerna de länkar
# till. Ordningen speglar bokens kapitelföljd.
MODULER = [
    {
        "roll": "Grund",
        "titel": "Juridisk metod",
        "tag": "Kap. 1",
        "beskrivning": "Rättskälleläran, lagtolkning och RNTS-strukturen. "
        "Grunden som allt annat vilar på.",
        "sida": "pages/1_Juridisk_metod.py",
    },
    {
        "roll": "Avtal",
        "titel": "Avtalsrätt",
        "tag": "Kap. 7",
        "beskrivning": "Anbud och accept, fullmakt (behörighet mot befogenhet), "
        "ogiltighet och 36 § AvtL.",
        "sida": "pages/2_Avtalsratt.py",
    },
    {
        "roll": "Köp",
        "titel": "Köp- och konsumenträtt",
        "tag": "Kap. 8",
        "beskrivning": "KöpL mot KKöpL, dröjsmål, fel, påföljder och reklamation.",
        "sida": "pages/3_Kop_och_konsumentratt.py",
    },
    {
        "roll": "Skadestånd",
        "titel": "Skadeståndsrätt",
        "tag": "Kap. 10",
        "beskrivning": "Culparegeln, adekvat kausalitet, principalansvar och "
        "ren förmögenhetsskada.",
        "sida": "pages/4_Skadestandsratt.py",
    },
    {
        "roll": "Arbete",
        "titel": "Arbetsrätt",
        "tag": "Kap. 11",
        "beskrivning": "Anställningsformer, uppsägning mot avsked (LAS) och "
        "diskriminering.",
        "sida": "pages/5_Arbetsratt.py",
    },
    {
        "roll": "Bolag",
        "titel": "Associationsrätt",
        "tag": "Kap. 12",
        "beskrivning": "Bolagsformerna, personligt ansvar i handelsbolag mot "
        "aktiebolag och aktiebolagets organisation.",
        "sida": "pages/6_Associationsratt.py",
    },
    {
        "roll": "Familj & arv",
        "titel": "Familje- och successionsrätt",
        "tag": "Kap. 18–21",
        "beskrivning": "Giftorättsgods mot enskild egendom, bodelning, "
        "arvsordning, laglott, testamente och särkullbarn.",
        "sida": "pages/7_Familje_och_arvsratt.py",
    },
    {
        "roll": "Straff & process",
        "titel": "Straff- och processrätt",
        "tag": "Kap. 22",
        "beskrivning": "Brottsbegreppets objektiva och subjektiva sida, uppsåt "
        "mot oaktsamhet och ansvarsfrihetsgrunder.",
        "sida": "pages/8_Straff_och_processratt.py",
    },
    {
        "roll": "Pröva",
        "titel": "Kunskapstest",
        "tag": "Alla moduler",
        "beskrivning": "Samlad resultatöversikt över dina quiz per modul, med "
        "genvägar vidare till modulernas övningar.",
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
                "Kursboken är bred, men tentan mäter förmågan att tillämpa "
                "juridisk metod på konkreta fall. Här övar du fallbaserat: "
                "identifiera rättsfrågan, hitta rätt lagrum, tillämpa normen "
                "och dra en slutsats — med en tutor som granskar ditt eget "
                "resonemang och kvalitetssäkrar varje lagrum."
            ),
        )
    )

    # Disclaimer högt upp: appen ger inte juridisk rådgivning (PRD 4).
    render_info(
        "Detta är ett studieverktyg, inte juridisk rådgivning. Använd inte "
        "appen för verkliga rättsliga beslut och mata inte in personuppgifter."
    )

    st.html(
        section_heading("PARETOURVALET", "Åtta moduler som ger 80 % av tentanyttan")
    )
    st.html(
        summary_box(
            "Kursen har 22 kapitel, men fallfrågorna återkommer inom ett fåtal "
            "områden. Vi tränar de åtta där juridisk metod ger mest utdelning: "
            "från avtal och köp till skadestånd, familj och arv, arbetsrätt och "
            "straffrätt — allt med samma RNTS-struktur så att metoden blir vana."
        )
    )
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

    with st.expander("Om appen och metoden", expanded=False):
        st.markdown(
            """
            **RNTS** står för Rättsfrågan, Norm, Tillämpning, Slutsats — den
            struktur som juridisk metod bygger på. Tutorn förklarar dina egna
            svar steg för steg i stället för att lösa fallet åt dig.

            **Hallucinationsskydd:** varje lagrum i ett tutorsvar kontrolleras
            mot kursens lagrumslista. Verifierade lagrum blir klickbara länkar
            till lagen.nu; övriga markeras med en varning så att du kan
            kontrollera dem själv.

            Alla scenarier är fiktiva. Appen ger ingen juridisk rådgivning.
            """
        )

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

    # Obsidianvalvet är värdefullt redan utan analyser: Rättskartan – en
    # klickbar, hopfällbar karta över rättssystemet – följer alltid med.
    st.download_button(
        "Ladda ner Obsidianvalv med Rättskartan (zip)",
        data=bygg_valv(hamta_case_analyser()),
        file_name="juridik_valv.zip",
        mime="application/zip",
    )
    st.info(
        "Packa upp zipen och öppna mappen **Juridik** som ett valv i Obsidian. "
        "**Rättskartan** ger en hopfällbar, klickbar karta över hela "
        "rättssystemet med en not per lag: vad den täcker, när den ska "
        "övervägas och hur den hänger ihop med andra lagar. Varje genomförd "
        "RNTS-analys blir dessutom en egen not — grafvyn och backlinks visar "
        "alla rättsfall där ett lagrum tillämpats. Repetitionsavsnitten "
        "fungerar med pluginen Spaced Repetition."
    )


def resultat_till_svar() -> dict[str, dict[str, bool]]:
    """Hämta rå quizresultatbok ur session_state för rapportbyggarna."""
    try:
        return dict(st.session_state.get("quiz_resultat", {}))
    except Exception:
        return {}


render_landing()
