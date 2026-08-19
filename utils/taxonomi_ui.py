"""Rendering av taxonomigrafen över svensk rätt.

Följer samma mönster som utils.graf_ui: noddata och kantdata serialiseras till
JSON och bäddas in i en HTML-sträng som laddar vis-network från CDN inuti
komponentens sandboxade iframe.

Två skillnader mot den personliga kunskapsgrafen:

- **Klickbara lagnoder.** Noder med ``url`` (endast lagnoder, se
  utils.rattssystem_graf) öppnar lagen.nu i en ny flik vid klick.
  Strukturnoder saknar url och är därmed inerta.
- **Färg per huvudgren.** Strukturnoderna färgas efter sin toppgren
  (offentlig rätt / civilrätt), medan lagnoder alltid är paragrafguld. Guld
  betyder alltid lagrum eller lag i appen (design_system.md avsnitt 1), och
  den kopplingen får inte brytas här.

``render_farglegend`` ritar legenden som riktiga färgrutor i HTML, inte som
prosa i en caption.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from utils.rattskarta import ladda_rattssystem
from utils.rattssystem_graf import (
    GRUPP_GREN,
    GRUPP_LAG,
    GRUPP_REFERENS,
    GRUPP_ROT,
    TaxNod,
    Taxonomigraf,
)

# Pinnad version, samma som utils.graf_ui.
_VIS_NETWORK_CDN = (
    "https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"
)

# Myndighetsblå ur paletten för civilrätten och en dämpad grå systerkulör för
# offentlig rätt. Ingen av dem är guld: guld är reserverat för lagar och lagrum
# (design_system.md avsnitt 1). Båda klarar kontrastkravet mot vit text.
GRENFARGER: dict[str, dict[str, str]] = {
    "offentlig_ratt": {"bg": "#6B6459", "kant": "#4A453D", "text": "#FFFFFF"},
    "civilratt": {"bg": "#2C5F8A", "kant": "#1F4460", "text": "#FFFFFF"},
    # Dämpad grön systerkulör för det rena överblicksområdet internationell
    # rätt/EU-rätt. Klarar kontrastkravet mot vit text och är varken guld
    # (reserverat för lag) eller någon av de två inhemska toppgrenarnas färg.
    "internationell_ratt": {"bg": "#3E7C5A", "kant": "#2C5A40", "text": "#FFFFFF"},
}

# Etiketter för legenden. Läses inte ur datat för att hålla legenden ren även
# om en toppgren saknar noder.
_GRENETIKETT: dict[str, str] = {
    "offentlig_ratt": "Offentlig rätt",
    "civilratt": "Civilrätt",
    "internationell_ratt": "Internationell rätt & EU-rätt",
}

_ROTFARG = {"bg": "#1A2332", "kant": "#0D131D", "text": "#FAF7F2"}
_LAGFARG = {"bg": "#B8860B", "kant": "#8A6608", "text": "#FFFFFF"}
# Referenslag: blek guld med guldkant, samma guldsläkt (det ÄR en lag) men
# ihålig i stället för fylld, så att appens lagar syns som de tyngre noderna
# och referenslagarna läses som ren överblick utanför appens urval.
_REFERENSFARG = {"bg": "#FBF4E0", "kant": "#B8860B", "text": "#6E5206"}

# Nodstorlek per djup: roten störst, lagarna minst. Djupare nivåer klampas
# till minsta storleken.
_STORLEK = {0: 26, 1: 22, 2: 18, 3: 16, 4: 14, 5: 13, 6: 12}

# --- Interaktionens inställningar -------------------------------------------
#
# Alla värden som styr fokusering och zoom ligger här och skickas till
# JavaScripten som ett enda objekt. JS-filerna innehåller inga egna tal.

# Bakgrundsnodernas opacitet när en gren är fokuserad. 0,15 räcker för att
# formen ska anas utan att konkurrera med den fokuserade grenen.
BAKGRUNDSOPACITET = 0.15

# Zoomgolv. Skalan efter den första fit() gånger den här faktorn är så långt
# ut studenten får gå. Golvet härleds i stället för att hårdkodas, så att det
# följer med containerns bredd och trädets storlek.
MIN_SKALA_FAKTOR = 0.9

# Tak för den *automatiska* fokuseringen. Utan det fyller en ensam nod utan
# ättlingar hela rutan. Handzoomning inåt är fortfarande obegränsad.
MAX_FOKUS_SKALA = 1.6

# Animeringstid vid fokus och återställning.
FOKUS_ANIMERING_MS = 400

# Förfäderskedjans kanter. Guld är lagens färg i appen, men det här är en
# kant och inte en nod, så kopplingen bryts inte (design_system.md avsnitt 1).
KEDJEFARG = "#B8860B"
KEDJEBREDD = 3

# Kanternas normalfärg, samma som tidigare låg inbäddad i optionsobjektet.
KANTFARG = "#C9BFA8"

# JavaScripten ligger som riktiga .js-filer i stället för i f-strängen nedan:
# varje { i en f-sträng måste dubbleras, vilket gör all icke-trivial JS till
# en fälla. Filerna läses vid rendering och bäddas in i iframen.
_JS_KATALOG = Path(__file__).resolve().parent / "static"


def _las_js(filnamn: str) -> str:
    """Läs en JS-fil ur utils/static/ eller höj ett begripligt fel."""
    sokvag = _JS_KATALOG / filnamn
    if not sokvag.is_file():
        raise FileNotFoundError(
            f"Grafens JavaScript saknas: {sokvag}. Filerna ligger i "
            "utils/static/ och måste följa med i distributionen."
        )
    return sokvag.read_text(encoding="utf-8")


def _json_for_html(data: object) -> str:
    """Serialisera till JSON säkert för inbäddning i en <script>-tagg."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def _nodfarg(nod: TaxNod) -> dict[str, str]:
    """Färgen för en nod: lag = guld, referens = blek guld, rot = bläck, annars per toppgren."""
    if nod["grupp"] == GRUPP_LAG:
        return _LAGFARG
    if nod["grupp"] == GRUPP_REFERENS:
        return _REFERENSFARG
    if nod["grupp"] == GRUPP_ROT:
        return _ROTFARG
    return GRENFARGER.get(nod.get("toppgren", ""), _ROTFARG)


def grafkonfig() -> dict[str, object]:
    """Inställningarna som skickas till grafens JavaScript.

    Nycklarna är camelCase eftersom de läses av JS-sidan; värdena kommer
    uteslutande från modulkonstanterna ovan.
    """
    return {
        "bakgrundsopacitet": BAKGRUNDSOPACITET,
        "minSkalaFaktor": MIN_SKALA_FAKTOR,
        "maxFokusSkala": MAX_FOKUS_SKALA,
        "animeringMs": FOKUS_ANIMERING_MS,
        "kedjefarg": KEDJEFARG,
        "kedjebredd": KEDJEBREDD,
        "kantfarg": KANTFARG,
    }


def _vis_noder(graf: Taxonomigraf) -> list[dict]:
    """Omvandla taxonominoder till vis-network-noder med färg och form."""
    ut = []
    for nod in graf["noder"]:
        farg = _nodfarg(nod)
        niva = nod.get("niva", 0)
        ut.append(
            {
                "id": nod["id"],
                "label": nod["label"],
                "title": nod.get("titel", ""),
                "url": nod.get("url", ""),
                "foralder": nod.get("foralder", ""),
                "shape": "dot" if nod["grupp"] in (GRUPP_LAG, GRUPP_REFERENS) else "box",
                "size": _STORLEK.get(niva, 13),
                "color": {"background": farg["bg"], "border": farg["kant"]},
                "font": {
                    "color": farg["text"]
                    if nod["grupp"] not in (GRUPP_LAG, GRUPP_REFERENS)
                    else "#1A2332",
                    "size": 16 if niva <= 1 else 13,
                },
                "level": niva,
            }
        )
    return ut


def bygg_html(graf: Taxonomigraf, hojd: int = 620) -> str:
    """Bygg den kompletta HTML-strängen för taxonomikomponenten (ren funktion)."""
    noder_json = _json_for_html(_vis_noder(graf))
    kanter_json = _json_for_html(
        [{"from": k["fran"], "to": k["till"]} for k in graf["kanter"]]
    )
    konfig_json = _json_for_html(grafkonfig())

    return f"""
<div style="position:relative;">
  <div id="taxonomigraf" style="height:{hojd}px;border:1px solid #E5E0D8;
       border-radius:8px;background:#FFFFFF;"></div>
  <button id="jok-aterstall-vy" type="button" hidden
          title="Visa hela kartan igen (Esc)"
          style="position:absolute;top:12px;right:12px;padding:.4rem .7rem;
                 background:#FFFFFF;border:1px solid #E5E0D8;border-radius:8px;
                 color:#2C5F8A;font-family:serif;font-size:14px;cursor:pointer;">
    Återställ vyn
  </button>
</div>
<script src="{_VIS_NETWORK_CDN}"></script>
<script>
  const noder = {noder_json};
  const kanter = {kanter_json};
  const JOK_GRAFKONFIG = {konfig_json};
  const container = document.getElementById("taxonomigraf");
</script>
<script>
{_las_js("taxonomigraf_logik.js")}
</script>
<script>
{_las_js("taxonomigraf.js")}
</script>
"""


def render_taxonomigraf(graf: Taxonomigraf, hojd: int = 620) -> None:
    """Rendera den interaktiva taxonomigrafen i appen."""
    import streamlit.components.v1 as components

    components.html(bygg_html(graf, hojd), height=hojd + 16, scrolling=False)


def farglegend_html() -> str:
    """Bygg färglegenden som riktiga färgrutor, inte som prosa."""
    poster = [
        (_ROTFARG["bg"], "Svensk rätt (rot)"),
    ]
    # Toppgrenarna i datats ordning, så legenden matchar kartan.
    poster += [
        (GRENFARGER[g.id]["bg"], _GRENETIKETT.get(g.id, g.namn))
        for g in ladda_rattssystem()
        if g.id in GRENFARGER
    ]
    poster.append((_LAGFARG["bg"], "Kurslag (klicka för lagen.nu)"))
    poster.append((_REFERENSFARG["bg"], "Referenslag, överblick utanför appens urval"))

    rutor = "".join(
        '<span class="jok-legend-post">'
        f'<span class="jok-swatch" style="background:{farg}"></span>'
        f"{html.escape(etikett)}</span>"
        for farg, etikett in poster
    )
    return f'<div class="jok-legend">{rutor}</div>'


def render_farglegend() -> None:
    """Rendera färglegenden under grafen."""
    import streamlit as st

    st.html(farglegend_html())


# Exporteras för sidan: gruppkonstanterna används vid filtrering av noder.
__all__ = [
    "GRENFARGER",
    "GRUPP_GREN",
    "GRUPP_LAG",
    "GRUPP_REFERENS",
    "GRUPP_ROT",
    "bygg_html",
    "farglegend_html",
    "render_farglegend",
    "render_taxonomigraf",
]
