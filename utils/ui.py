"""Delade UI-komponenter och tema.

Ansvarar för allt visuellt som delas mellan sidorna:
- inject_css: appens gemensamma stilar (palett ur design_system.md,
  varningsbadge för overifierade lagrum, lagrumschips)
- render_sidebar / render_sidopanel / render_statuspanel: navigeringsträdet
  ur utils.navigation, modellväljare och räknare för återstående LLM-anrop
  (session + dagsbudget)
- hero, section_heading, summary_box, module_map, pipeline_steps,
  footer_note: HTML-byggstenar för landnings- och modulsidor
- render_session_cap_card / render_daily_cap_card: vänliga svenska
  informationskort när anropsbudgeten är slut
- render_kort, render_case, render_lagrum_chip, render_varning,
  render_info: återanvändbara block för scenarier, lagrum och meddelanden
- render_rnts_steg: fyrstegs vertikal stepper (Rättsfrågan, Norm,
  Tillämpning, Slutsats) med statusikoner per design_system.md avsnitt 3
"""

from __future__ import annotations

import html
import re

import streamlit as st

from utils.navigation import NAV_TRAD, Modul, Nod

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
WARN_FG = "#C9971C"     # Varning, ram och accent
WARN_BG = "#FFF8E1"     # Varning, bakgrund
WARN_DARK = "#8A6914"   # Varning, text/ikon på varningsbakgrund (WCAG ≥ 4.5:1)
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
            --varn-mork: {WARN_DARK}; --fel: {ERROR};
        }}
        .jok-hero {{
            max-width: 46rem; margin: 0 0 1.5rem 0;
        }}
        .jok-hero .eyebrow {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 14px;
            letter-spacing: .12em; color: var(--bla); text-transform: uppercase;
        }}
        .jok-hero h1 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif; color: var(--bl);
            font-size: 28px; line-height: 1.2; margin: .3rem 0 .6rem 0;
        }}
        .jok-hero p {{
            font-size: 17px; line-height: 1.65; color: var(--bl); margin: 0;
        }}
        .jok-section {{ margin: 1.8rem 0 .6rem 0; }}
        .jok-section .eyebrow {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 14px;
            letter-spacing: .12em; color: var(--bla); text-transform: uppercase;
        }}
        .jok-section h2 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif; color: var(--bl);
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
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 13px;
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
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 14px;
            border: 1px solid var(--guld); border-radius: 999px;
            padding: .15rem .6rem; color: var(--bl); text-decoration: none;
            background: #FFFDF7;
        }}
        .jok-chip.ovarifierad {{
            border-color: var(--varn-mork); background: var(--varn-bg);
        }}
        .jok-varning, .jok-info {{
            border-radius: 10px; padding: .8rem 1rem; margin: .6rem 0;
            font-size: 15px; line-height: 1.55; max-width: 46rem;
        }}
        .jok-varning {{ background: var(--varn-bg); border: 1px solid var(--varn-mork); color: var(--bl); }}
        .jok-info {{ background: #EAF1F7; border: 1px solid var(--bla); }}
        .jok-tutortext {{
            background: var(--panel); border: 1px solid var(--ram);
            border-left: 3px solid var(--bla); border-radius: 10px;
            padding: .9rem 1.2rem; margin: .6rem 0; max-width: 46rem;
            font-size: 16px; line-height: 1.6; color: var(--bl);
        }}
        .jok-tutortext p {{ margin: 0 0 .6rem 0; }}
        .jok-tutortext p:last-child {{ margin-bottom: 0; }}
        .jok-tutortext .rnts-rubrik {{
            font-variant: small-caps; letter-spacing: .05em;
            color: var(--bla); font-weight: 700;
        }}
        .jok-varning ul {{ margin: .4rem 0 .2rem 1.1rem; padding: 0; }}
        .jok-case {{
            background: var(--panel); border: 1px solid var(--ram);
            border-top: 3px solid var(--guld); border-radius: 12px;
            padding: 1.1rem 1.3rem; margin: .6rem 0; max-width: 46rem;
            box-shadow: 0 1px 3px rgba(26,35,50,.06);
        }}
        .jok-case h3 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif; color: var(--bl);
            font-size: 18px; margin: 0 0 .2rem 0;
        }}
        .jok-case .meta {{ font-size: 13px; color: #6B6459; margin-bottom: .5rem; }}
        .jok-case p {{ font-size: 17px; line-height: 1.65; color: var(--bl); margin: 0; }}
        .jok-rnts {{ margin: .4rem 0 .8rem 0; }}
        .jok-rnts .steg {{
            display: flex; align-items: center; gap: .55rem;
            font-size: 14px; color: var(--bl); padding: .22rem 0;
        }}
        .jok-rnts .ikon {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 1.25rem; height: 1.25rem; border-radius: 999px;
            font-size: 11px; line-height: 1; flex: 0 0 auto;
            border: 2px solid var(--ram); background: var(--panel); color: transparent;
        }}
        .jok-rnts .steg.pagar .ikon {{ border-color: var(--bla); background: var(--bla); color: #fff; }}
        .jok-rnts .steg.godkand .ikon {{ border-color: var(--gron); background: var(--gron); color: #fff; }}
        .jok-rnts .steg.behover-mer .ikon {{ border-color: var(--varn-mork); background: var(--varn-bg); color: var(--varn-mork); }}
        .jok-status {{ font-size: 14px; line-height: 1.5; }}
        .jok-status .rad {{ display: flex; justify-content: space-between; }}
        .jok-status .prick {{ font-weight: 600; }}

        /* Navigeringshierarki i sidopanelen (design_system.md 4.1).
           Nivåerna skiljs åt med indrag, storlek och färgstyrka, inte med
           ikoner: huvudkategori (versaler, blå) > underkategori (bläck)
           > undergren (grå) > modul (st.page_link). */
        .jok-nav-kategori {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px; letter-spacing: .1em; text-transform: uppercase;
            color: var(--bla); font-weight: 700;
            margin: 1.1rem 0 .2rem 0;
        }}
        .jok-nav-under {{
            font-size: 13px; font-weight: 600; color: var(--bl);
            margin: .5rem 0 .15rem 0;
        }}
        .jok-nav-gren {{
            font-size: 12px; font-weight: 600; color: #6B6459;
            letter-spacing: .02em; margin: .4rem 0 .15rem .6rem;
        }}
        .jok-nav-kommer {{
            font-size: 13px; color: #9A9384; margin: .1rem 0 .1rem .6rem;
        }}
        /* Färglegend för taxonomigrafen: riktiga färgrutor, inte prosa. */
        .jok-legend {{
            display: flex; flex-wrap: wrap; gap: .5rem 1.1rem;
            margin: .6rem 0 1rem 0; font-size: 14px; color: var(--bl);
        }}
        .jok-legend-post {{ display: inline-flex; align-items: center; gap: .4rem; }}
        .jok-swatch {{
            display: inline-block; width: .85rem; height: .85rem;
            border-radius: 3px; border: 1px solid rgba(26,35,50,.25);
            flex: 0 0 auto;
        }}

        /* Lagkort i områdesträdet (flik Systemet). */
        .jok-lagkort {{
            background: var(--panel); border: 1px solid var(--ram);
            border-left: 3px solid var(--guld); border-radius: 10px;
            padding: .8rem 1rem; margin: .5rem 0; max-width: 46rem;
        }}
        .jok-lagkort h4 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
            font-size: 16px; color: var(--bl); margin: 0 0 .1rem 0;
        }}
        .jok-lagkort .sfs {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px; color: #6B6459;
        }}
        .jok-lagkort p {{ font-size: 15px; line-height: 1.55; margin: .45rem 0 0 0; }}
        .jok-lagkort .nar {{ font-size: 14px; color: #4A453D; margin-top: .4rem; }}
        .jok-lagkort .nar strong {{ color: var(--bla); }}
        .jok-lagkort .avsnitt {{
            margin-top: .7rem; padding-top: .6rem;
            border-top: 1px solid rgba(107, 100, 89, .18);
        }}
        .jok-lagkort .avsnittsrubrik {{
            font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
            color: #6B6459; display: flex; justify-content: space-between;
            gap: 1rem; margin-bottom: .35rem;
        }}
        .jok-lagkort .tackning {{ text-transform: none; letter-spacing: 0; }}
        .jok-lagkort .kapitelrad {{
            font-size: 13px; font-weight: 600; color: var(--bla);
            margin: .45rem 0 .2rem 0;
        }}
        .jok-lagkort .avsnittsrad {{
            display: flex; gap: .6rem; font-size: 14px; line-height: 1.5;
            padding: .1rem 0 .1rem .6rem;
        }}
        .jok-lagkort .avsnittsrad .spann {{
            flex: 0 0 6.5rem; color: var(--guld); font-variant-numeric: tabular-nums;
            text-decoration: none; font-weight: 600;
        }}
        .jok-lagkort .avsnittsrad .spann:hover {{ text-decoration: underline; }}
        .jok-lagkort .avsnittstext {{ color: #4A453D; }}
        .jok-lagkort .avsnittsnot {{
            font-size: 12px; color: #6B6459; margin-top: .5rem; font-style: italic;
        }}

        /* Begreppskort (flik Nyckelbegrepp). */
        .jok-begrepp {{
            background: var(--panel); border: 1px solid var(--ram);
            border-radius: 12px; padding: 1rem 1.2rem; margin: .5rem 0 .2rem 0;
            max-width: 46rem; box-shadow: 0 1px 3px rgba(26,35,50,.06);
        }}
        .jok-begrepp h3 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
            font-size: 19px; color: var(--bl); margin: 0 0 .1rem 0;
        }}
        .jok-begrepp .kapitel {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
            font-size: 12px; letter-spacing: .08em; text-transform: uppercase;
            color: var(--bla);
        }}
        .jok-begrepp .falt {{ margin: .7rem 0 0 0; }}
        .jok-begrepp .falt .etikett {{
            font-variant: small-caps; letter-spacing: .05em; font-weight: 700;
            color: var(--bla); font-size: 14px; display: block;
            margin-bottom: .15rem;
        }}
        .jok-begrepp .falt p {{
            font-size: 16px; line-height: 1.6; color: var(--bl); margin: 0;
        }}
        /* Skillnadsraden för kontrastpar: en enda framhävd rad. */
        .jok-begrepp .skillnad {{
            background: #F5F1EA; border-left: 3px solid var(--bla);
            border-radius: 0 6px 6px 0; padding: .5rem .8rem; margin: .7rem 0 0 0;
            font-size: 15px; line-height: 1.5;
        }}
        .jok-begrepp .igenkanning {{
            background: #FFFDF7; border: 1px dashed var(--guld);
            border-radius: 8px; padding: .6rem .8rem; margin-top: .7rem;
        }}

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
    """Ingresstext i löpande maxbredd."""
    return f'<div class="jok-summary">{html.escape(text)}</div>'


def render_kort(titel: str, innehall: str, ikon: str = "") -> str:
    """Vit panel med tunn ram. Bas för scenarier och resultat."""
    prefix = f"{html.escape(ikon)} " if ikon else ""
    return (
        f'<div class="jok-kort"><h3>{prefix}{html.escape(titel)}</h3>'
        f"<div>{html.escape(innehall)}</div></div>"
    )


def render_case(rubrik: str, metadata: str, scenariotext: str) -> str:
    """Scenariokort med rubrik, metadatarad och tunn guldlinje överst."""
    meta = f'<div class="meta">{html.escape(metadata)}</div>' if metadata else ""
    return (
        f'<div class="jok-case"><h3>{html.escape(rubrik)}</h3>{meta}'
        f"<p>{html.escape(scenariotext)}</p></div>"
    )


# --- RNTS-stepper (design_system.md avsnitt 3) --------------------------------

RNTS_STATUS_EJ_PABORJAD = "ej-paborjad"   # tom cirkel
RNTS_STATUS_PAGAR = "pagar"               # blå: under arbete
RNTS_STATUS_GODKAND = "godkand"           # grön bock
RNTS_STATUS_BEHOVER_MER = "behover-mer"   # gul: behöver mer

_RNTS_IKONER = {
    RNTS_STATUS_EJ_PABORJAD: "",
    RNTS_STATUS_PAGAR: "●",
    RNTS_STATUS_GODKAND: "✓",
    RNTS_STATUS_BEHOVER_MER: "!",
}


def render_rnts_steg(steg: tuple[tuple[str, str], ...]) -> str:
    """Vertikal RNTS-stepper: (etikett, status) per steg.

    Status måste vara en av RNTS_STATUS_*-konstanterna; annars ValueError
    (fail fast så att en felstavad status inte renderas tyst som tom cirkel).
    """
    rader = []
    for etikett, status in steg:
        if status not in _RNTS_IKONER:
            raise ValueError(
                f"Okänd RNTS-status {status!r} för steget {etikett!r}. "
                f"Tillåtna: {sorted(_RNTS_IKONER)}"
            )
        rader.append(
            f'<div class="steg {status}"><span class="ikon">{_RNTS_IKONER[status]}</span>'
            f"<span>{html.escape(etikett)}</span></div>"
        )
    return f'<div class="jok-rnts">{"".join(rader)}</div>'


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
    # Refererna innehåller redan "§" (t.ex. "1 § AvtL"); lägg bara till
    # paragraftecknet som prydnad för bara-nummer-referenser.
    paragraf = "" if "§" in ref else "§ "
    etikett = f"{paragraf}{prefix}{html.escape(ref)}"
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


# Tutorsvaren kommer som lättviktig markdown från modellen (fetstil, kursiv,
# ###-rubriker). Utan konvertering skulle studenten se råa asterisker.
_MD_RUBRIK = re.compile(r"^#{1,4}\s*(.+?)\s*$", re.MULTILINE)
_MD_FET = re.compile(r"\*\*(.+?)\*\*")
_MD_KURSIV = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
_RNTS_RUBRIKTITLAR = ("Rättsfrågan", "Norm", "Tillämpning", "Slutsats")


def _md_till_html(kropp: str) -> str:
    """Konvertera modellens markdown (i redan HTML-escapad text) till HTML.

    RNTS-rubriker ("**1. Rättsfrågan**", "### Norm") får klassen rnts-rubrik
    och renderas som kapitäler i myndighetsblått (design_system.md avsnitt 3);
    övrig fetstil/kursiv blir vanlig <strong>/<em>.
    """
    kropp = _MD_RUBRIK.sub(lambda m: f"**{m.group(1)}**", kropp)

    def _ersatt_fet(m: re.Match[str]) -> str:
        inre = m.group(1).strip()
        rubrik = re.sub(r"^\d+\s*[.)]\s*", "", inre).rstrip(".:").strip()
        if rubrik in _RNTS_RUBRIKTITLAR:
            return f'<span class="rnts-rubrik">{inre}</span>'
        return f"<strong>{inre}</strong>"

    kropp = _MD_FET.sub(_ersatt_fet, kropp)
    return _MD_KURSIV.sub(r"<em>\1</em>", kropp)


def _tutortext_html(text: str) -> tuple[str, tuple]:
    """Bygg HTML för ett tutorsvar och returnera (html, overifierade träffar).

    Ren funktion utan Streamlit-anrop så att den kan enhetstestas. Modellens
    markdown konverteras till HTML (aldrig råa asterisker i UI:t), verifierade
    lagrum byts ut mot klickbara lagen.nu-chips och overifierade referenser
    lämnas kvar i texten och returneras separat för varningsrutan.
    """
    from utils.lagrum import STATUS_VERIFIERAD, Lagrumstraff, verify_lagrum

    traffar = verify_lagrum(text or "")
    verifierade: dict[str, Lagrumstraff] = {}
    ovarifierade: list[Lagrumstraff] = []
    for t in traffar:
        if t.status == STATUS_VERIFIERAD and t.url:
            verifierade.setdefault(t.ra, t)
        else:
            ovarifierade.append(t)

    kropp = _md_till_html(html.escape(text or ""))
    # Längsta råtext först så att "1 kap. 1 § SkL" inte delvis matchas av "1 § SkL".
    for ra in sorted(verifierade, key=len, reverse=True):
        t = verifierade[ra]
        titel = getattr(t, "beskrivning", None) or ""
        tooltip = f' title="{html.escape(titel)}"' if titel else ""
        chip = (
            f'<a class="jok-chip" href="{html.escape(t.url or "")}" target="_blank"'
            f'{tooltip}>{html.escape(ra)}</a>'
        )
        kropp = kropp.replace(html.escape(ra), chip)

    kropp = kropp.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f'<div class="jok-tutortext"><p>{kropp}</p></div>', tuple(ovarifierade)


# Vad ett grönt chip betyder, och inte betyder. Verifieringen slår upp
# paragrafen i kursens lagrumslista: den intygar att lagrummet FINNS, aldrig
# att det är det tillämpliga för studentens fall. Tutorn har observerats
# hänvisa till existerande men irrelevanta paragrafer med självsäker och
# felaktig beskrivning, och de renderas då som vanliga guldchips.
VERIFIERINGSNOT = (
    "Guldmarkerade lagrum finns i kursens lagrumslista och går att öppna på "
    "lagen.nu. Det betyder inte att lagrummet är rätt för just ditt fall: läs "
    "paragrafen och bedöm själv om den är tillämplig."
)


def _har_verifierade_lagrum(kropp_html: str) -> bool:
    """Sant om tutorsvaret innehåller minst ett verifierat lagrumschip.

    Läser den renderade HTML:en i stället för att köra verify_lagrum en gång
    till: chipsen sätts bara in för träffar med status VERIFIERAD och egen URL.
    """
    return 'class="jok-chip"' in kropp_html


def render_tutortext(text: str) -> None:
    """Rendera ett tutorsvar med verifierade lagrumschips och varningsruta.

    Verifierade lagrum blir klickbara lagen.nu-chips. Overifierade lagrum och
    rättsfall (t.ex. påhittade paragrafer eller NJA-referenser) samlas i en gul
    varningsruta så att studenten uppmanas kontrollera dem mot lagen.nu.

    Finns det verifierade lagrum följer dessutom en kort not om vad
    verifieringen faktiskt intygar. Overifierade lagrum får ingen not: de har
    redan sin egen, starkare varningsruta.
    """
    kropp_html, ovarifierade = _tutortext_html(text)
    st.html(kropp_html)

    if _har_verifierade_lagrum(kropp_html):
        st.caption(VERIFIERINGSNOT)

    if ovarifierade:
        poster = "".join(
            f"<li><strong>{html.escape(t.ra)}</strong></li>" for t in ovarifierade
        )
        st.html(
            '<div class="jok-varning">'
            "<strong>Kontrollera dessa referenser själv.</strong> Följande "
            "hänvisningar kunde inte verifieras mot kursens lagrumslista och kan "
            "vara felaktiga eller ligga utanför kursen:"
            f"<ul>{poster}</ul>"
            "Slå upp dem på lagen.nu innan du litar på dem."
            "</div>"
        )


def render_info(text: str) -> None:
    """Blått informationskort (t.ex. disclaimer)."""
    st.html(f'<div class="jok-info">{html.escape(text)}</div>')


def render_sidhjalp(punkter: tuple[str, ...], rubrik: str = "Så använder du den här sidan") -> None:
    """Kollapsad hjälpruta överst på en sida.

    Samma mönster på alla sidor: en hopfälld expander med 3-5 korta,
    handlingsorienterade punkter. Stängd som standard så att den inte
    konkurrerar med sidans innehåll för den som redan vet.
    """
    with st.expander(rubrik, expanded=False):
        for punkt in punkter:
            st.markdown(f"- {punkt}")


def render_lagkort(
    forkortning: str,
    namn: str,
    sfs: str,
    beskrivning: str,
    nar: str,
    url: str,
    relaterade: tuple[str, ...] = (),
    kursavsnitt: tuple = (),
    tackning: str = "",
) -> str:
    """Kort för en lag i områdesträdet: vad den täcker och när den övervägs.

    ``kursavsnitt`` är Kapitelgrupp-poster från utils.lagkort_avsnitt. Är den
    tom renderas kortet precis som förr, utan tom avsnittsrubrik.
    """
    rel = ""
    if relaterade:
        rel = (
            '<div class="nar"><strong>Relaterade lagar:</strong> '
            f"{html.escape(', '.join(relaterade))}</div>"
        )
    return (
        '<div class="jok-lagkort">'
        f"<h4>{html.escape(forkortning)}: {html.escape(namn)}</h4>"
        f'<div class="sfs">SFS {html.escape(sfs)}</div>'
        f"<p>{html.escape(beskrivning)}</p>"
        f'<div class="nar"><strong>När övervägs den?</strong> {html.escape(nar)}</div>'
        f"{rel}"
        f"{_avsnittsblock(kursavsnitt, tackning)}"
        f'<div class="nar"><a href="{html.escape(url)}" target="_blank">'
        f"Öppna {html.escape(forkortning)} på lagen.nu</a></div>"
        "</div>"
    )


def _avsnittsblock(grupper: tuple, tackning: str) -> str:
    """Kursavsnitten grupperade under lagens egna kapitelrubriker.

    Guld är reserverat för lagrum, så paragrafspannet får paragrafguld medan
    kapitelrubriken bär bläck. Se design_system.md avsnitt 1 och 4.
    """
    if not grupper:
        return ""

    tack = f'<span class="tackning">{html.escape(tackning)}</span>' if tackning else ""
    delar = [
        f'<div class="avsnitt"><div class="avsnittsrubrik">KURSAVSNITT{tack}</div>'
    ]
    for grupp in grupper:
        if grupp.kapitel:
            rubrik = f"{grupp.kapitel} kap."
            if grupp.rubrik:
                rubrik = f"{rubrik} {grupp.rubrik}"
            delar.append(f'<div class="kapitelrad">{html.escape(rubrik)}</div>')
        for rad in grupp.avsnitt:
            delar.append(
                '<div class="avsnittsrad">'
                f'<a class="spann" href="{html.escape(rad.url)}" target="_blank">'
                f"{html.escape(rad.spann)}</a>"
                f'<span class="avsnittstext">{html.escape(rad.rubrik)}</span>'
                "</div>"
            )
    delar.append(
        '<div class="avsnittsnot">Urvalet följer kursen, inte hela lagen.</div></div>'
    )
    return "".join(delar)


def render_begreppskort(
    term: str,
    kapitel: str,
    definition: str,
    forklaring: str,
    exempel: str,
    igenkanning: str,
    skillnaden: str = "",
    lagrum_chips: str = "",
) -> str:
    """Begreppskort med de fyra fasta fälten.

    Igenkänningsfältet får guldstreckad ram eftersom det är den del som
    kopplar begreppet till RNTS-steget Rättsfrågan: det är signalorden i
    scenariot som ska få studenten att tänka på begreppet.
    """
    kap = f'<div class="kapitel">{html.escape(kapitel)}</div>' if kapitel else ""
    skillnad = (
        f'<div class="skillnad">{html.escape(skillnaden)}</div>' if skillnaden else ""
    )
    chips = (
        f'<div class="falt"><span class="etikett">Lagrum</span>{lagrum_chips}</div>'
        if lagrum_chips
        else ""
    )
    return (
        '<div class="jok-begrepp">'
        f"{kap}<h3>{html.escape(term)}</h3>"
        f'<div class="falt"><span class="etikett">Definition</span>'
        f"<p>{html.escape(definition)}</p></div>"
        f"{skillnad}"
        f'<div class="falt"><span class="etikett">Varför det spelar roll</span>'
        f"<p>{html.escape(forklaring)}</p></div>"
        f'<div class="falt"><span class="etikett">Exempel</span>'
        f"<p>{html.escape(exempel)}</p></div>"
        f'<div class="falt igenkanning"><span class="etikett">'
        f"Så känner du igen det i ett scenario</span>"
        f"<p>{html.escape(igenkanning)}</p></div>"
        f"{chips}"
        "</div>"
    )


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
        f'<div class="rad"><span>Anrop kvar i sessionen</span><span>{sess}/{SESSION_CALL_CAP}</span></div>'
        f'<div class="rad"><span>Anrop kvar i dag</span><span>{dag}/{get_daily_cap()}</span></div>'
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

    with st.expander("Byt modell", expanded=False):
        val = st.radio(
            "Välj modell",
            options=(DEFAULT_MODEL, ALTERNATIVE_MODEL),
            format_func=lambda m: m.split("/")[-1],
            index=(0 if get_active_model() == DEFAULT_MODEL else 1),
            key="_jok_modellval",
            label_visibility="collapsed",
        )
        st.session_state[MODEL_SESSION_KEY] = val


def _render_nod(nod: "Nod", niva: int) -> None:
    """Rita en nod i navigeringsträdet rekursivt.

    ``niva`` är djupet under huvudkategorin: 1 = underkategori, 2 och nedåt
    = undergren. Moduler ritas som länkar, planerade moduler som gråtonad
    text med "(kommer)".
    """
    if isinstance(nod, Modul):
        if nod.sida is None:
            st.html(
                f'<div class="jok-nav-kommer">{html.escape(nod.namn)} (kommer)</div>'
            )
        else:
            st.page_link(nod.sida, label=nod.namn)
        return

    klass = "jok-nav-under" if niva <= 1 else "jok-nav-gren"
    st.html(f'<div class="{klass}">{html.escape(nod.namn)}</div>')
    for barn in nod.barn:
        _render_nod(barn, niva + 1)


def render_sidopanel() -> None:
    """Rita hela navigeringsträdet som en sammanhållen lista.

    Speglar svensk rätts systematik enligt utils.navigation.NAV_TRAD i
    stället för en platt sidlista. Allt visas samtidigt: inga hopfällbara
    sektioner per huvudkategori, eftersom en panel som måste öppnas döljer
    kursens struktur i stället för att visa den. Nivåerna skiljs åt med
    indrag och färgstyrka enligt design_system.md 4.1.
    """
    for kategori in NAV_TRAD:
        st.html(
            f'<div class="jok-nav-kategori">{html.escape(kategori.namn)}</div>'
        )
        for barn in kategori.barn:
            _render_nod(barn, niva=1)


def render_sidebar() -> None:
    """Sidopanelens innehåll: navigeringsträd, LLM-status och modellväljare.

    Anropas en gång per körning från streamlit_app.py, som registrerar
    samma sidor i st.navigation med position="hidden" så att Streamlits
    egen platta sidlista inte ritas parallellt med trädet.
    """
    with st.sidebar:
        st.html('<div class="jok-section"><h2>Juridisk översiktskurs</h2></div>')
        st.caption("Fallbaserad träning med RNTS-metoden.")
        st.divider()
        render_sidopanel()
        st.divider()
        render_statuspanel()
        _render_model_selector()
