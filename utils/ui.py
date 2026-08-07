"""Delade UI-komponenter och tema.

Ansvarar för allt visuellt som delas mellan sidorna:
- inject_css: appens gemensamma stilar (palett ur design_system.md,
  varningsbadge för overifierade lagrum, lagrumschips)
- render_sidebar / render_sidopanel / render_statuspanel: navigeringsträdet
  ur utils.navigation och en statusrad för återstående LLM-anrop
  (session + dagsbudget), som utökas med modellnamn först när något
  faktiskt är begränsat
- hero, section_heading, pipeline_steps, footer_note:
  HTML-byggstenar för landnings- och modulsidor
- render_session_cap_card / render_daily_cap_card: vänliga svenska
  informationskort när anropsbudgeten är slut
- render_case, render_lagrum_chip, render_varning, render_info:
  återanvändbara block för scenarier, lagrum och meddelanden
- render_rnts_steg: fyrstegs vertikal stepper (Rättsfrågan, Norm,
  Tillämpning, Slutsats) med statusikoner per design_system.md avsnitt 3
"""

from __future__ import annotations

import html
import re

import streamlit as st

from utils.css import CSS_MALL
from utils.navigation import NAV_TRAD, Modul, Nod
from utils.rnts import RNTS_STEG

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
    """Injicera appens gemensamma CSS. Anropa direkt efter set_page_config().

    Själva mallen bor i utils.css (CSS_MALL): den här funktionen fyller i
    palettvärdena och injicerar resultatet, se den modulens docstring för
    varför CSS:en ligger i en egen fil.
    """
    st.html(
        CSS_MALL.format(
            BLACK=BLACK, PARCHMENT=PARCHMENT, PANEL=PANEL, BORDER=BORDER,
            BLUE=BLUE, GOLD=GOLD, GREEN=GREEN, WARN_FG=WARN_FG,
            WARN_BG=WARN_BG, WARN_DARK=WARN_DARK, ERROR=ERROR,
        )
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

# Tillstånden ritas med CSS (fyllning, ram, en ren bockform), inte med
# teckenglyfer: ikonförbudet i design_system.md 4.1 gäller hela appen. Klassen
# på .steg styr utseendet; ikonelementet är avsiktligt tomt.
_RNTS_TILLSTAND = (
    RNTS_STATUS_EJ_PABORJAD,
    RNTS_STATUS_PAGAR,
    RNTS_STATUS_GODKAND,
    RNTS_STATUS_BEHOVER_MER,
)


def render_rnts_steg(steg: tuple[tuple[str, str], ...]) -> str:
    """Vertikal RNTS-stepper: (etikett, status) per steg.

    Status måste vara en av RNTS_STATUS_*-konstanterna; annars ValueError
    (fail fast så att en felstavad status inte renderas tyst som tom cirkel).
    """
    rader = []
    for etikett, status in steg:
        if status not in _RNTS_TILLSTAND:
            raise ValueError(
                f"Okänd RNTS-status {status!r} för steget {etikett!r}. "
                f"Tillåtna: {sorted(_RNTS_TILLSTAND)}"
            )
        rader.append(
            f'<div class="steg {status}"><span class="ikon"></span>'
            f"<span>{html.escape(etikett)}</span></div>"
        )
    return f'<div class="jok-rnts">{"".join(rader)}</div>'


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


def render_tranar(text: str) -> str:
    """Kapitälsetikett som säger vilket RNTS-steg en aktivitet tränar.

    Dämpad med avsikt: den ska kunna läsas en gång och sedan ignoreras, inte
    konkurrera med uppgiften. Se utils.rnts för avbildningen.
    """
    return f'<div class="jok-tranar">{html.escape(text)}</div>'


# Tutorsvaren kommer som lättviktig markdown från modellen (fetstil, kursiv,
# ###-rubriker). Utan konvertering skulle studenten se råa asterisker.
_MD_RUBRIK = re.compile(r"^#{1,4}\s*(.+?)\s*$", re.MULTILINE)
_MD_FET = re.compile(r"\*\*(.+?)\*\*")
_MD_KURSIV = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
# Hämtas ur utils.rnts.RNTS_STEG så att stegens namn står på exakt ett ställe
# i projektet (se den modulens docstring).
_RNTS_RUBRIKTITLAR = RNTS_STEG


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
            # Säger avsnittet samma sak som kapitelrubriken ovanför blir raden
            # en upprepning. Då räcker spannet.
            upprepning = (
                grupp.rubrik
                and rad.rubrik.casefold().strip() == grupp.rubrik.casefold().strip()
            )
            text = (
                ""
                if upprepning
                else f'<span class="avsnittstext">{html.escape(rad.rubrik)}</span>'
            )
            delar.append(
                '<div class="avsnittsrad">'
                f'<a class="spann" href="{html.escape(rad.url)}" target="_blank">'
                f"{html.escape(rad.spann)}</a>"
                f"{text}"
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

# Under den här andelen återstående anrop är budgeten värd att visa i detalj.
STATUS_TROSKEL = 0.25


def statusrad(
    tillganglig: bool, sess: int, sess_tak: int, dag: int, dag_tak: int
) -> tuple[str, bool]:
    """Sidopanelens statustext, och om detaljerna bör visas.

    Ren funktion så att tröskellogiken kan testas utan Streamlit. Detaljerna
    visas bara när de betyder något: när tutorn är otillgänglig, eller när
    mindre än en fjärdedel av något tak återstår. Driftinformation ska inte
    konkurrera med navigeringen i normalläget.
    """
    if not tillganglig:
        return (
            "Tutorn är inte tillgänglig. Quiz, lagrumslänkar och facit "
            "fungerar som vanligt.",
            True,
        )

    def _lagt(kvar: int, tak: int) -> bool:
        if tak <= 0:
            return True
        return kvar / tak < STATUS_TROSKEL

    if _lagt(sess, sess_tak) or _lagt(dag, dag_tak):
        return (f"Tutorn: {sess} anrop kvar i sessionen, {dag} i dag.", True)
    return ("Tutorn: tillgänglig", False)


def render_statuspanel() -> None:
    """LLM-status i sidopanelen: en rad, som utökas bara när den behöver det."""
    from utils.llm import (
        SESSION_CALL_CAP,
        get_active_model,
        get_session_calls_remaining,
        is_llm_available,
    )
    from utils.llm_budget import get_daily_calls_remaining, get_daily_cap

    text, expandera = statusrad(
        is_llm_available(),
        get_session_calls_remaining(),
        SESSION_CALL_CAP,
        get_daily_calls_remaining(),
        get_daily_cap(),
    )
    st.caption(text)
    if expandera:
        modell = get_active_model().split("/")[-1]
        st.caption(f"Modell: {modell}")


def _planerad_text(moduler: tuple["Modul", ...]) -> str:
    """Namnen på flera planerade moduler sammanfogade till en mening.

    Rättsområdenas namn är vanliga substantiv på svenska, så alla utom det
    första skrivs med liten begynnelsebokstav: "Statsrätt och
    förvaltningsrätt". Ett namn som inleds med två versaler (EU-rätt) lämnas
    orört, eftersom det är en förkortning och inte ett substantiv.
    """
    namn: list[str] = []
    for i, modul in enumerate(moduler):
        n = modul.namn
        if i and not n[:2].isupper():
            n = n[0].lower() + n[1:]
        namn.append(n)
    if len(namn) == 1:
        return namn[0]
    return ", ".join(namn[:-1]) + " och " + namn[-1]


def _rendera_barn(
    barn: tuple["Nod", ...], niva: int, aktiv_kedja: frozenset[str]
) -> None:
    """Rita en grupps barn: byggda noder var för sig, planerade på en rad.

    Planerade moduler slås ihop eftersom de inte går att öppna: två obyggda
    rättsområden behöver inte två rader för att visa att de finns. Kursens
    omfattning syns fortfarande, vilket är hela skälet att de står kvar
    (design_system.md 4.1).
    """
    planerade = tuple(n for n in barn if isinstance(n, Modul) and n.sida is None)
    for nod in barn:
        if isinstance(nod, Modul) and nod.sida is None:
            continue
        _render_nod(nod, niva, aktiv_kedja)
    if planerade:
        text = html.escape(_planerad_text(planerade))
        st.html(f'<div class="jok-nav-kommer">{text} (kommer)</div>')


def _render_nod(nod: "Nod", niva: int, aktiv_kedja: frozenset[str] = frozenset()) -> None:
    """Rita en nod i navigeringsträdet rekursivt.

    ``niva`` är djupet under huvudkategorin: 1 = underkategori, 2 och nedåt
    = undergren. Moduler ritas som länkar, planerade moduler som gråtonad
    text med "(kommer)". Grupper som omsluter den öppna sidan får klassen
    ``aktiv`` och full bläckvikt, så att studenten ser var i trädet den är.

    En grupp vars enda barn är en modul med SAMMA namn ritar ingen egen
    rubrik: raden skulle bara upprepa ordet direkt under sig självt, vilket
    "Personrätt" gjorde bokstavligen. Gruppen finns kvar i NAV_TRAD, så
    systematiken och rubrikkedja() är oförändrade — det är bara raden som
    utgår.

    Villkoret är avsiktligt namnidentitet och inte "har bara ett barn".
    Modullänkar ritas av st.page_link och saknar indrag, så grupprubriken är
    det enda som knyter en modul till sin gren. Fäller man Ersättningsrätt
    hamnar Skadeståndsrätt visuellt under Kontraktsrätt, och panelen påstår
    då något juridiskt falskt: skadeståndsrätten är inte kontraktsrätt.
    Rubriker som bär doktrin står kvar även när de bara har ett barn.
    """
    if isinstance(nod, Modul):
        if nod.sida is None:
            st.html(
                f'<div class="jok-nav-kommer">{html.escape(nod.namn)} (kommer)</div>'
            )
        else:
            st.page_link(nod.sida, label=nod.namn)
        return

    if (
        len(nod.barn) == 1
        and isinstance(nod.barn[0], Modul)
        and nod.barn[0].namn == nod.namn
    ):
        _render_nod(nod.barn[0], niva, aktiv_kedja)
        return

    klass = "jok-nav-under" if niva <= 1 else "jok-nav-gren"
    if nod.namn in aktiv_kedja:
        klass += " aktiv"
    st.html(f'<div class="{klass}">{html.escape(nod.namn)}</div>')
    _rendera_barn(nod.barn, niva + 1, aktiv_kedja)


def render_sidopanel() -> None:
    """Rita hela navigeringsträdet som en sammanhållen lista.

    Speglar svensk rätts systematik enligt utils.navigation.NAV_TRAD i
    stället för en platt sidlista. Allt visas samtidigt: inga hopfällbara
    sektioner per huvudkategori, eftersom en panel som måste öppnas döljer
    kursens struktur i stället för att visa den. Nivåerna skiljs åt med
    indrag och färgstyrka enligt design_system.md 4.1.

    Rubrikerna ovanför den öppna sidan får full bläckvikt via klassen ``aktiv``.
    Ingen färg och ingen ikon: guld är reserverat för lagrum, och hierarkin ska
    bäras av vikt och indrag.
    """
    from utils.navigation import rubrikkedja

    try:
        aktiv = st.session_state.get("_jok_aktiv_sida") or ""
    except Exception:
        aktiv = ""
    aktiv_kedja = frozenset(rubrikkedja(aktiv)) if aktiv else frozenset()

    for kategori in NAV_TRAD:
        klass = "jok-nav-kategori"
        if kategori.namn in aktiv_kedja:
            klass += " aktiv"
        st.html(f'<div class="{klass}">{html.escape(kategori.namn)}</div>')
        _rendera_barn(kategori.barn, 1, aktiv_kedja)


def bred_sida() -> None:
    """Häv den centrerade textkolumnen för sidor som behöver full bredd.

    Innehållskolumnen är maxbreddad och centrerad (design_system.md 4), vilket
    är rätt för löptext men fel för Rättskartan och Kunskapskartan: båda ritar
    sin graf med components.html utan egen bredd, så grafen fyller behållaren
    och skulle klämmas ihop till textbredd. Anropas överst på de sidorna.
    """
    st.html(
        "<style>"
        '[data-testid="stMainBlockContainer"], .main .block-container'
        " { max-width: none; }"
        "</style>"
    )


def render_sidebar() -> None:
    """Sidopanelens innehåll: navigeringsträd och en rad LLM-status.

    Anropas en gång per körning från streamlit_app.py, som registrerar
    samma sidor i st.navigation med position="hidden" så att Streamlits
    egen platta sidlista inte ritas parallellt med trädet.

    Modellväljaren är borttagen: 8B/14B är ett val ingen student kan grunda,
    och mätningen i projektets historik visade att 14B inte var bättre — bara
    långsammare. Standardmodellen sätts i utils/llm.py.
    """
    with st.sidebar:
        st.html('<div class="jok-section"><h2>Juridisk översiktskurs</h2></div>')
        st.caption("Fallbaserad träning med RNTS-metoden.")
        st.divider()
        render_sidopanel()
        st.divider()
        render_statuspanel()
