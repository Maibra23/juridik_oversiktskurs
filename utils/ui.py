"""Delade UI-komponenter och tema.

Ansvarar för allt visuellt som delas mellan sidorna:
- inject_css: appens gemensamma stilar (palett ur design_system.md,
  varningsbadge för overifierade lagrum, lagrumschips)
- render_sidebar / render_statuspanel: navigering, modellväljare och
  räknare för återstående LLM-anrop (session + dagsbudget)
- hero, section_heading, summary_box, module_map, pipeline_steps,
  footer_note: HTML-byggstenar för landnings- och modulsidor
- render_session_cap_card / render_daily_cap_card: vänliga svenska
  informationskort när anropsbudgeten är slut
- render_kort, render_lagrum_chip, render_varning, render_info:
  återanvändbara block för scenarier, lagrum och meddelanden

Detta är ett Dag 1-skelett. Den fulla komponentuppsättningen
(render_rnts_steg, render_case, render_tutortext m.fl.) byggs ut i Dag 3.
"""

from __future__ import annotations

import html

import streamlit as st

APP_VERSION = "0.1.0"
APP_UPDATED = "2026-07-08"

# --- Palett (design_system.md avsnitt 1) ------------------------------------
BLACK = "#1A2332"       # Bläck: primär text och rubriker
PARCHMENT = "#FAF7F2"   # Pergament: appbakgrund
PANEL = "#FFFFFF"       # Panel: kortbakgrund
BORDER = "#E5E0D8"      # Kortram
BLUE = "#2C5F8A"        # Myndighetsblå: primär accent
GOLD = "#B8860B"        # Paragrafguld: enbart lagrum
GREEN = "#2E7D4F"       # Godkänd
WARN_FG = "#C9971C"     # Varning, text
WARN_BG = "#FFF8E1"     # Varning, bakgrund
ERROR = "#B3402A"       # Fel


def inject_css() -> None:
    """Injicera appens gemensamma CSS. Anropa direkt efter set_page_config."""
    st.html(
        f"""
        <style>
        :root {{
            --bl: {BLACK}; --perg: {PARCHMENT}; --panel: {PANEL};
            --ram: {BORDER}; --bla: {BLUE}; --guld: {GOLD};
            --gron: {GREEN}; --varn-fg: {WARN_FG}; --varn-bg: {WARN_BG};
            --fel: {ERROR};
        }}
        .jok-hero {{
            max-width: 46rem; margin: 0 0 1.5rem 0;
        }}
        .jok-hero .eyebrow {{
            font-family: "IBM Plex Mono", monospace; font-size: 14px;
            letter-spacing: .12em; color: var(--bla); text-transform: uppercase;
        }}
        .jok-hero h1 {{
            font-family: Georgia, "Source Serif 4", serif; color: var(--bl);
            font-size: 28px; line-height: 1.2; margin: .3rem 0 .6rem 0;
        }}
        .jok-hero p {{
            font-size: 17px; line-height: 1.65; color: var(--bl); margin: 0;
        }}
        .jok-section {{ margin: 1.8rem 0 .6rem 0; }}
        .jok-section .eyebrow {{
            font-family: "IBM Plex Mono", monospace; font-size: 14px;
            letter-spacing: .12em; color: var(--bla); text-transform: uppercase;
        }}
        .jok-section h2 {{
            font-family: Georgia, "Source Serif 4", serif; color: var(--bl);
            font-size: 22px; margin: .2rem 0 0 0;
        }}
        .jok-summary {{
            max-width: 46rem; font-size: 17px; line-height: 1.65;
            color: var(--bl); margin: .5rem 0 1rem 0;
        }}
        .jok-kort {{
            background: var(--panel); border: 1px solid var(--ram);
            border-radius: 12px; padding: 1.1rem 1.3rem; margin: .6rem 0;
            box-shadow: 0 1px 3px rgba(26,35,50,.06);
        }}
        .jok-kort h3 {{
            font-family: Georgia, serif; color: var(--bl); font-size: 18px;
            margin: 0 0 .4rem 0;
        }}
        .jok-modulrutnat {{
            display: grid; grid-template-columns: repeat(2, 1fr);
            gap: .8rem; margin: .6rem 0 1rem 0;
        }}
        @media (max-width: 640px) {{
            .jok-modulrutnat {{ grid-template-columns: 1fr; }}
        }}
        .jok-modulkort {{
            background: var(--panel); border: 1px solid var(--ram);
            border-top: 3px solid var(--guld); border-radius: 12px;
            padding: 1rem 1.2rem;
        }}
        .jok-modulkort .roll {{
            font-family: "IBM Plex Mono", monospace; font-size: 13px;
            color: var(--bla); text-transform: uppercase; letter-spacing: .08em;
        }}
        .jok-modulkort h3 {{
            font-family: Georgia, serif; font-size: 18px; color: var(--bl);
            margin: .2rem 0 .1rem 0;
        }}
        .jok-modulkort .tag {{ font-size: 13px; color: #6B6459; }}
        .jok-modulkort p {{ font-size: 15px; line-height: 1.55; margin: .4rem 0 0 0; }}
        .jok-pipeline {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: .5rem 0; }}
        .jok-pipeline span {{
            background: var(--panel); border: 1px solid var(--ram);
            border-radius: 999px; padding: .35rem .9rem; font-size: 14px;
        }}
        .jok-chip {{
            display: inline-flex; align-items: center; gap: .3rem;
            font-family: "IBM Plex Mono", monospace; font-size: 14px;
            border: 1px solid var(--guld); border-radius: 999px;
            padding: .15rem .6rem; color: var(--bl); text-decoration: none;
            background: #FFFDF7;
        }}
        .jok-chip.ovarifierad {{
            border-color: var(--varn-fg); background: var(--varn-bg);
        }}
        .jok-varning, .jok-info {{
            border-radius: 10px; padding: .8rem 1rem; margin: .6rem 0;
            font-size: 15px; line-height: 1.55; max-width: 46rem;
        }}
        .jok-varning {{ background: var(--varn-bg); border: 1px solid var(--varn-fg); color: var(--bl); }}
        .jok-info {{ background: #EAF1F7; border: 1px solid var(--bla); }}
        .jok-status {{ font-size: 14px; line-height: 1.5; }}
        .jok-status .rad {{ display: flex; justify-content: space-between; }}
        .jok-status .prick {{ font-weight: 600; }}
        .jok-footer {{
            margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--ram);
            font-size: 13px; color: #6B6459; max-width: 46rem;
        }}
        </style>
        """
    )


# --- HTML-byggstenar --------------------------------------------------------

def hero(eyebrow: str, title: str, lead: str) -> str:
    """Hjältesektion för landningssidan."""
    return (
        f'<div class="jok-hero"><div class="eyebrow">{html.escape(eyebrow)}</div>'
        f"<h1>{html.escape(title)}</h1><p>{html.escape(lead)}</p></div>"
    )


def section_heading(eyebrow: str, title: str) -> str:
    """Avsnittsrubrik med liten kapitälsetikett."""
    return (
        f'<div class="jok-section"><div class="eyebrow">{html.escape(eyebrow)}</div>'
        f"<h2>{html.escape(title)}</h2></div>"
    )


def summary_box(text: str) -> str:
    """Ingресstext i löpande maxbredd."""
    return f'<div class="jok-summary">{html.escape(text)}</div>'


def render_kort(titel: str, innehall: str, ikon: str = "") -> str:
    """Vit panel med tunn ram. Bas för scenarier och resultat."""
    prefix = f"{html.escape(ikon)} " if ikon else ""
    return (
        f'<div class="jok-kort"><h3>{prefix}{html.escape(titel)}</h3>'
        f"<div>{html.escape(innehall)}</div></div>"
    )


def module_map(nodes: list[dict[str, str]]) -> str:
    """Rutnät av modulkort (2 kolumner, 1 på mobil)."""
    kort = []
    for n in nodes:
        kort.append(
            '<div class="jok-modulkort">'
            f'<div class="roll">{html.escape(n.get("roll", ""))}</div>'
            f'<h3>{html.escape(n.get("titel", ""))}</h3>'
            f'<div class="tag">{html.escape(n.get("tag", ""))}</div>'
            f'<p>{html.escape(n.get("beskrivning", ""))}</p></div>'
        )
    return f'<div class="jok-modulrutnat">{"".join(kort)}</div>'


def pipeline_steps(steps: list[str]) -> str:
    """Vågrät stegindikator för arbetsgången."""
    inner = "".join(f"<span>{i}. {html.escape(s)}</span>" for i, s in enumerate(steps, 1))
    return f'<div class="jok-pipeline">{inner}</div>'


def render_lagrum_chip(ref: str, url: str | None = None, verifierad: bool = True,
                       titel: str = "") -> str:
    """Guldkantad pill för ett lagrum. Overifierad chip får varningsstil."""
    klass = "jok-chip" if verifierad else "jok-chip ovarifierad"
    prefix = "" if verifierad else "Ej verifierad: "
    etikett = f"§ {prefix}{html.escape(ref)}"
    tooltip = f' title="{html.escape(titel)}"' if titel else ""
    if url:
        return (
            f'<a class="{klass}" href="{html.escape(url)}" target="_blank"'
            f'{tooltip}>{etikett}</a>'
        )
    return f'<span class="{klass}"{tooltip}>{etikett}</span>'


def render_varning(text: str) -> None:
    """Gult, handlingsorienterat varningskort."""
    st.html(f'<div class="jok-varning">{html.escape(text)}</div>')


def render_info(text: str) -> None:
    """Blått informationskort (t.ex. disclaimer)."""
    st.html(f'<div class="jok-info">{html.escape(text)}</div>')


def footer_note(version: str = APP_VERSION, updated: str = APP_UPDATED) -> str:
    """Sidfot med disclaimer och version."""
    return (
        '<div class="jok-footer">'
        "Detta är ett studieverktyg för Juridisk översiktskurs, inte juridisk "
        "rådgivning. Kontrollera alltid lagrum mot lagen.nu. "
        f"Version {html.escape(version)} · uppdaterad {html.escape(updated)}."
        "</div>"
    )


# --- Budgetkort -------------------------------------------------------------

def render_session_cap_card() -> None:
    """Vänligt kort när sessionens LLM-tak är nått."""
    from utils.llm import SESSION_CAP_MESSAGE

    render_varning(SESSION_CAP_MESSAGE)


def render_daily_cap_card() -> None:
    """Vänligt kort när den gemensamma dagsbudgeten är slut."""
    from utils.llm_budget import DAILY_CAP_MESSAGE

    render_varning(DAILY_CAP_MESSAGE)


# --- Statuspanel och sidopanel ----------------------------------------------

def render_statuspanel() -> None:
    """LLM-status i sidopanelen: modell, anrop kvar i sessionen, dagsbudget."""
    from utils.llm import (
        SESSION_CALL_CAP,
        get_active_model,
        get_session_calls_remaining,
        is_llm_available,
    )
    from utils.llm_budget import get_daily_calls_remaining, get_daily_cap

    tillganglig = is_llm_available()
    prick = "🟢 Tillgänglig" if tillganglig else "⚪ Ej konfigurerad"
    modell = get_active_model().split("/")[-1]
    sess = get_session_calls_remaining()
    dag = get_daily_calls_remaining()

    st.html(
        '<div class="jok-status">'
        f'<div class="rad"><span>LLM-tutor</span><span class="prick">{prick}</span></div>'
        f'<div class="rad"><span>Modell</span><span>{html.escape(modell)}</span></div>'
        f'<div class="rad"><span>Anrop kvar (session)</span><span>{sess}/{SESSION_CALL_CAP}</span></div>'
        f'<div class="rad"><span>Dagsbudget kvar</span><span>{dag}/{get_daily_cap()}</span></div>'
        "</div>"
    )


def _render_model_selector() -> None:
    """Modellväljare (8B/14B) under en expander i sidopanelen."""
    from utils.llm import (
        ALTERNATIVE_MODEL,
        DEFAULT_MODEL,
        MODEL_SESSION_KEY,
        get_active_model,
    )

    with st.expander("Modell", expanded=False):
        val = st.radio(
            "Välj modell",
            options=(DEFAULT_MODEL, ALTERNATIVE_MODEL),
            format_func=lambda m: m.split("/")[-1],
            index=(0 if get_active_model() == DEFAULT_MODEL else 1),
            key="_jok_modellval",
            label_visibility="collapsed",
        )
        st.session_state[MODEL_SESSION_KEY] = val


def render_sidebar(active_page: str = "hem") -> None:
    """Sidopanel: navigering överst, statuspanel och modellväljare nederst."""
    with st.sidebar:
        st.html('<div class="jok-section"><h2>Juridisk översiktskurs</h2></div>')
        st.caption("Fallbaserad träning med RNTS-metoden.")
        st.divider()
        render_statuspanel()
        _render_model_selector()
