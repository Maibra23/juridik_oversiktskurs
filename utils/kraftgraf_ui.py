"""Rendering av Rättskartans kraftvy.

Samma taxonomi som den hierarkiska vyn i utils.taxonomi_ui, men ritad som
graphifys egen grafvy gör det: en fysiksimulering (forceAtlas2Based) placerar
noderna, varje nod skalas efter sin grad, varje toppgren ringas in med ett
konvext hölje, och en sidopanel bär sökruta, grenfilter, nyckeltal och en
infopanel för den valda noden.

Det designsystemet äger ändras däremot inte. Paletten importeras från
utils.taxonomi_ui i stället för att skrivas om här, så guld betyder fortfarande
lag och aldrig struktur, och varje toppgren behåller sin färg (design_system.md
avsnitt 1). Höljena målas i toppgrenens färg — aldrig i guld.

Datalagret ligger i utils.kraftgraf. Den här modulen lägger bara färg, chrome
och HTML ovanpå det.
"""

from __future__ import annotations

import html

from utils.kraftgraf import (
    Statistik,
    grafstatistik,
    hullgrupper,
    nodgrader,
    nodstorlek,
    startpositioner,
)
from utils.rattssystem_graf import GRUPP_LAG, GRUPP_REFERENS, Taxonomigraf
from utils.taxonomi_ui import (
    _VIS_NETWORK_CDN,
    BAKGRUNDSOPACITET,
    FOKUS_ANIMERING_MS,
    GRENFARGER,
    KANTFARG,
    MAX_FOKUS_SKALA,
    _json_for_html,
    _las_js,
    _nodfarg,
)

_JS_FIL = "kraftgraf.js"

# --- Fysiken ----------------------------------------------------------------
#
# Värdena är graphifys egna (graphify-out/graph.html), med en längre
# fjäderlängd: taxonomins etiketter är hela svenska grennamn och behöver mer
# luft än kodsymboler för att inte skriva över varandra.

FYSIK_SOLVER = "forceAtlas2Based"
FYSIK_GRAVITATION = -60
FYSIK_CENTRALGRAVITATION = 0.005
FYSIK_FJADERLANGD = 150
FYSIK_FJADERKONSTANT = 0.08
FYSIK_DAMPNING = 0.4
FYSIK_UNDVIK_OVERLAPP = 0.8
# Fysiken stängs av när stabiliseringen är klar, precis som i graphifys vy:
# annars kryper kartan omkring under läsningen.
FYSIK_STABILISERING = 300

# --- Höljena ----------------------------------------------------------------

# Hur långt utanför noderna höljets kant dras, som faktor från gruppens tyngd-
# punkt. 1,0 skulle skära rakt genom nodernas mittpunkter.
HULL_UTVIDGNING = 1.10
HULL_FYLLOPACITET = 0.10
HULL_KANTOPACITET = 0.45
HULL_ETIKETTOPACITET = 0.85
HULL_KANTBREDD = 2
# Toppgrenens namn i höljets mitt. Canvas tar font som en CSS-shorthand-sträng,
# inte som separata fält.
HULL_ETIKETTFONT = "bold 15px sans-serif"
# Etiketten lyfts ovanför tyngdpunkten: mitt i höljet ligger nästan alltid en
# nod, och de två texterna skulle skrivas över varandra.
HULL_ETIKETTLYFT = 26

# --- Sökrutan ---------------------------------------------------------------

# Träfflistan är 132px hög i panelen; fler träffar än så går inte att se utan
# att rulla, och sökningen är ändå till för att hitta en namngiven nod.
SOK_MAX_TRAFFAR = 12

# --- Chrome ------------------------------------------------------------------
#
# Neutrala ytfärger ur appens palett. Ingen av dem är guld.

_RAM = "#E5E0D8"
_YTA = "#FFFFFF"
_PANELYTA = "#FDFCFA"
_TEXT = "#1A2332"
_DAMPAD_TEXT = "#6B6459"
_LANK = "#2C5F8A"

_PANELBREDD = 250
_HOJD_STANDARD = 620


def kraftkonfig() -> dict[str, object]:
    """Inställningarna som skickas till kraftvyns JavaScript.

    Nycklarna är camelCase eftersom de läses av JS-sidan; värdena kommer
    uteslutande från modulkonstanterna ovan och från utils.taxonomi_ui, så att
    inget tal och ingen färg står på två ställen.
    """
    return {
        "fysik": {
            "solver": FYSIK_SOLVER,
            "gravitationskonstant": FYSIK_GRAVITATION,
            "centralGravitation": FYSIK_CENTRALGRAVITATION,
            "fjaderlangd": FYSIK_FJADERLANGD,
            "fjaderkonstant": FYSIK_FJADERKONSTANT,
            "dampning": FYSIK_DAMPNING,
            "undvikOverlapp": FYSIK_UNDVIK_OVERLAPP,
            "stabiliseringsIterationer": FYSIK_STABILISERING,
        },
        "hullUtvidgning": HULL_UTVIDGNING,
        "hullFyllopacitet": HULL_FYLLOPACITET,
        "hullKantopacitet": HULL_KANTOPACITET,
        "hullEtikettopacitet": HULL_ETIKETTOPACITET,
        "hullKantbredd": HULL_KANTBREDD,
        "hullEtikettfont": HULL_ETIKETTFONT,
        "hullEtikettlyft": HULL_ETIKETTLYFT,
        "bakgrundsopacitet": BAKGRUNDSOPACITET,
        "fokusSkala": MAX_FOKUS_SKALA,
        "animeringMs": FOKUS_ANIMERING_MS,
        "kantfarg": KANTFARG,
        "sokMaxTraffar": SOK_MAX_TRAFFAR,
    }


def kraft_noder(graf: Taxonomigraf) -> list[dict]:
    """Taxonominoderna som vis-network-noder, skalade efter grad.

    Ordningen är datats. Alla noder får formen ``dot``: i en fri layout lägger
    sig boxar med hela grennamn över varandra, och pricken är dessutom formen
    graphifys vy använder. Färgen kommer ur utils.taxonomi_ui._nodfarg, så
    färgkontraktet är exakt detsamma som i den hierarkiska vyn.
    """
    grader = nodgrader(graf)
    maxgrad = max(grader.values(), default=1)
    positioner = startpositioner(graf)
    ut: list[dict] = []
    for nod in graf["noder"]:
        farg = _nodfarg(nod)
        ar_lag = nod["grupp"] in (GRUPP_LAG, GRUPP_REFERENS)
        x, y = positioner[nod["id"]]
        ut.append(
            {
                "id": nod["id"],
                "label": nod["label"],
                "x": x,
                "y": y,
                "title": nod.get("titel", ""),
                "url": nod.get("url", ""),
                "toppgren": nod.get("toppgren", ""),
                "grupp": nod["grupp"],
                "shape": "dot",
                "size": nodstorlek(grader[nod["id"]], maxgrad),
                "color": {"background": farg["bg"], "border": farg["kant"]},
                "font": {
                    "color": _TEXT,
                    "size": 15 if not ar_lag else 13,
                    "face": "sans-serif",
                    # Etiketten ligger utanför pricken och behöver en bakgrund
                    # för att gå att läsa där höljen och kanter korsar den.
                    "background": _YTA,
                    "strokeWidth": 0,
                },
            }
        )
    return ut


def hullgrupper_for_js(graf: Taxonomigraf) -> list[dict]:
    """Höljena med sin toppgrensfärg, klara att bäddas in som JSON."""
    return [
        {
            "id": grupp.id,
            "etikett": grupp.etikett,
            "farg": GRENFARGER[grupp.id]["bg"],
            "nod_id": list(grupp.nod_id),
        }
        for grupp in hullgrupper(graf)
        if grupp.id in GRENFARGER
    ]


def _statistikrader(stat: Statistik) -> str:
    poster = (
        ("Noder", stat.noder),
        ("Grenar", stat.grenar),
        ("Kurslagar", stat.kurslagar),
        ("Referenslagar", stat.referenslagar),
        ("Djup", stat.djup),
    )
    return "".join(
        f'<div class="jok-kraft-stat"><span>{html.escape(etikett)}</span>'
        f"<b>{varde}</b></div>"
        for etikett, varde in poster
    )


def _grenfilter(graf: Taxonomigraf) -> str:
    rader = []
    for grupp in hullgrupper_for_js(graf):
        etikett = html.escape(grupp["etikett"])
        rader.append(
            '<label class="jok-kraft-filter">'
            f'<input type="checkbox" checked value="{html.escape(grupp["id"])}">'
            f'<span class="jok-kraft-swatch" style="background:{grupp["farg"]}"></span>'
            f"{etikett}</label>"
        )
    return "".join(rader)


def sidopanel_html(graf: Taxonomigraf) -> str:
    """Sidopanelen: sökruta, grenfilter, nyckeltal och infopanel.

    Allt innehåll som kommer ur data/rattssystem.json escapas. Infopanelen är
    tom här och fylls av JavaScripten när en nod väljs.
    """
    return f"""
<div id="jok-kraft-panel">
  <div class="jok-kraft-sektion">
    <input id="jok-kraft-sok" type="search" autocomplete="off"
           placeholder="Sök lag eller område" aria-label="Sök i kartan">
    <div id="jok-kraft-sokresultat"></div>
  </div>
  <div class="jok-kraft-sektion">
    <div class="jok-kraft-rubrik">Visa grenar</div>
    {_grenfilter(graf)}
  </div>
  <div class="jok-kraft-sektion">
    <div class="jok-kraft-rubrik">Kartan i tal</div>
    {_statistikrader(grafstatistik(graf))}
  </div>
  <div class="jok-kraft-sektion jok-kraft-vaxande">
    <div class="jok-kraft-rubrik">Vald nod</div>
    <div id="jok-kraft-info">
      <p class="jok-kraft-tom">Klicka på en nod i kartan.</p>
    </div>
  </div>
</div>
"""


def _stil(hojd: int) -> str:
    return f"""
<style>
  #jok-kraft-yta {{
    display: flex; gap: 0; height: {hojd}px;
    border: 1px solid {_RAM}; border-radius: 8px; overflow: hidden;
    background: {_YTA}; font-family: sans-serif; color: {_TEXT};
  }}
  #jok-kraft-duk {{ flex: 1; min-width: 0; position: relative; }}
  #jok-kraftgraf {{ width: 100%; height: 100%; }}
  #jok-kraft-panel {{
    width: {_PANELBREDD}px; flex: 0 0 {_PANELBREDD}px;
    border-left: 1px solid {_RAM}; background: {_PANELYTA};
    display: flex; flex-direction: column; overflow: hidden; font-size: 13px;
  }}
  .jok-kraft-sektion {{ padding: 10px 12px; border-bottom: 1px solid {_RAM}; }}
  .jok-kraft-vaxande {{ flex: 1; overflow-y: auto; border-bottom: none; }}
  .jok-kraft-rubrik {{
    font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
    color: {_DAMPAD_TEXT}; margin-bottom: 7px;
  }}
  #jok-kraft-sok {{
    width: 100%; padding: 7px 9px; border: 1px solid {_RAM}; border-radius: 6px;
    background: {_YTA}; color: {_TEXT}; font-size: 13px; font-family: inherit;
  }}
  #jok-kraft-sok:focus {{ outline: none; border-color: {_LANK}; }}
  #jok-kraft-sokresultat {{ max-height: 132px; overflow-y: auto; margin-top: 6px; }}
  .jok-kraft-traff {{
    padding: 4px 6px; border-radius: 4px; cursor: pointer;
    border-left: 3px solid transparent;
  }}
  .jok-kraft-traff:hover {{ background: {_RAM}; }}
  .jok-kraft-filter {{
    display: flex; align-items: center; gap: 7px; padding: 3px 0;
    cursor: pointer; line-height: 1.3;
  }}
  .jok-kraft-swatch {{
    width: 11px; height: 11px; border-radius: 3px; flex: 0 0 11px;
    border: 1px solid rgba(0,0,0,.15);
  }}
  .jok-kraft-stat {{ display: flex; justify-content: space-between; padding: 2px 0; }}
  .jok-kraft-stat span {{ color: {_DAMPAD_TEXT}; }}
  .jok-kraft-tom {{ color: {_DAMPAD_TEXT}; }}
  .jok-kraft-falt {{ margin-bottom: 6px; line-height: 1.4; }}
  .jok-kraft-lank {{ color: {_LANK}; }}
  .jok-kraft-grannar {{ display: flex; flex-direction: column; gap: 3px; margin-top: 4px; }}
  .jok-kraft-granne {{
    padding: 3px 6px; border-left: 3px solid {_RAM}; border-radius: 3px;
    cursor: pointer; background: {_YTA};
  }}
  .jok-kraft-granne:hover {{ background: {_RAM}; }}
  #jok-kraft-aterstall {{
    position: absolute; top: 12px; right: 12px; padding: .4rem .7rem;
    background: {_YTA}; border: 1px solid {_RAM}; border-radius: 8px;
    color: {_LANK}; font-family: serif; font-size: 14px; cursor: pointer;
  }}
</style>
"""


def bygg_kraft_html(graf: Taxonomigraf, hojd: int = _HOJD_STANDARD) -> str:
    """Bygg den kompletta HTML-strängen för kraftvyn (ren funktion)."""
    noder_json = _json_for_html(kraft_noder(graf))
    kanter_json = _json_for_html(
        [{"from": kant["fran"], "to": kant["till"]} for kant in graf["kanter"]]
    )
    hull_json = _json_for_html(hullgrupper_for_js(graf))
    konfig_json = _json_for_html(kraftkonfig())

    return f"""
{_stil(hojd)}
<div id="jok-kraft-yta">
  <div id="jok-kraft-duk">
    <div id="jok-kraftgraf"></div>
    <button id="jok-kraft-aterstall" type="button" hidden
            title="Visa hela kartan igen (Esc)">Återställ vyn</button>
  </div>
  {sidopanel_html(graf)}
</div>
<script src="{_VIS_NETWORK_CDN}"></script>
<script>
  const kraftNoder = {noder_json};
  const kraftKanter = {kanter_json};
  const JOK_HULLGRUPPER = {hull_json};
  const JOK_KRAFTKONFIG = {konfig_json};
</script>
<script>
{_las_js(_JS_FIL)}
</script>
"""


def render_kraftgraf(graf: Taxonomigraf, hojd: int = _HOJD_STANDARD) -> None:
    """Rendera kraftvyn i appen."""
    import streamlit.components.v1 as components

    components.html(bygg_kraft_html(graf, hojd), height=hojd + 16, scrolling=False)


__all__ = [
    "bygg_kraft_html",
    "hullgrupper_for_js",
    "kraft_noder",
    "kraftkonfig",
    "render_kraftgraf",
    "sidopanel_html",
]
