"""Rendering av taxonomigrafen över svensk rätt.

Följer samma mönster som utils.graf_ui: nod- och kantdata serialiseras till
JSON och bäddas in i en HTML-sträng som laddar vis-network från CDN inuti
komponentens sandboxade iframe.

Två skillnader mot den personliga kunskapsgrafen:

- **Klickbara lagnoder.** Noder med ``url`` (endast lagnoder, se
  utils.rattssystem_graf) öppnar lagen.nu i en ny flik vid klick.
  Strukturnoder saknar url och är därmed inerta.
- **Färg per avdelning.** Strukturnoderna färgas efter bokens avdelning,
  medan lagnoder alltid är paragrafguld. Guld betyder alltid lagrum eller
  lag i appen (design_system.md avsnitt 1), och den kopplingen får inte
  brytas här.

``render_farglegend`` ritar legenden som riktiga färgrutor i HTML, inte som
prosa i en caption.
"""

from __future__ import annotations

import html
import json

from utils.rattssystem_graf import (
    AVDELNINGAR,
    GRUPP_AVDELNING,
    GRUPP_LAG,
    GRUPP_OMRADE,
    GRUPP_ROT,
    GRUPP_UNDEROMRADE,
    TaxNod,
    Taxonomigraf,
)

# Pinnad version, samma som utils.graf_ui.
_VIS_NETWORK_CDN = (
    "https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"
)

# Bläck och myndighetsblå ur paletten, plus två dämpade systerkulörer för
# straff/process och offentlig rätt. Ingen av dem är guld: guld är reserverat
# för lagar och lagrum (design_system.md avsnitt 1). Alla fyra klarar
# kontrastkravet mot vit text.
AVDELNINGSFARGER: dict[str, dict[str, str]] = {
    "avd1_introduktion": {"bg": "#4A5568", "kant": "#2D3748", "text": "#FFFFFF"},
    "avd2_offentlig_ratt": {"bg": "#6B6459", "kant": "#4A453D", "text": "#FFFFFF"},
    "avd3_civilratt": {"bg": "#2C5F8A", "kant": "#1F4460", "text": "#FFFFFF"},
    "avd4_straff_process": {"bg": "#8A4A3C", "kant": "#5E3228", "text": "#FFFFFF"},
}

_ROTFARG = {"bg": "#1A2332", "kant": "#0D131D", "text": "#FAF7F2"}
_LAGFARG = {"bg": "#B8860B", "kant": "#8A6608", "text": "#FFFFFF"}

# Nodstorlek per nivå: roten störst, lagarna minst.
_STORLEK = {0: 26, 1: 22, 2: 18, 3: 15, 4: 13}


def _json_for_html(data: object) -> str:
    """Serialisera till JSON säkert för inbäddning i en <script>-tagg."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def _nodfarg(nod: TaxNod) -> dict[str, str]:
    """Färgen för en nod: lag = guld, rot = bläck, annars per avdelning."""
    if nod["grupp"] == GRUPP_LAG:
        return _LAGFARG
    if nod["grupp"] == GRUPP_ROT:
        return _ROTFARG
    return AVDELNINGSFARGER.get(nod.get("avdelning", ""), _ROTFARG)


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
                "shape": "dot" if nod["grupp"] == GRUPP_LAG else "box",
                "size": _STORLEK.get(niva, 13),
                "color": {"background": farg["bg"], "border": farg["kant"]},
                "font": {
                    "color": farg["text"] if nod["grupp"] != GRUPP_LAG else "#1A2332",
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

    return f"""
<div id="taxonomigraf" style="height:{hojd}px;border:1px solid #E5E0D8;
     border-radius:8px;background:#FFFFFF;"></div>
<script src="{_VIS_NETWORK_CDN}"></script>
<script>
  (function() {{
    const noder = {noder_json};
    const kanter = {kanter_json};
    const container = document.getElementById("taxonomigraf");
    if (typeof vis === "undefined") {{
      container.innerHTML =
        "<p style='padding:1rem;color:#1A2332;font-family:sans-serif'>" +
        "Kunde inte ladda grafbiblioteket (kräver internetåtkomst). " +
        "Områdesträdet nedanför fungerar ändå.</p>";
      return;
    }}
    const nodes = new vis.DataSet(noder);
    const edges = new vis.DataSet(kanter);
    const options = {{
      layout: {{
        hierarchical: {{
          enabled: true, direction: "UD", sortMethod: "directed",
          levelSeparation: 130, nodeSpacing: 110, treeSpacing: 160
        }}
      }},
      nodes: {{ borderWidth: 1, shadow: false }},
      edges: {{
        color: {{ color: "#C9BFA8" }}, width: 1,
        smooth: {{ type: "cubicBezier", forceDirection: "vertical" }}
      }},
      physics: false,
      interaction: {{ hover: true, tooltipDelay: 120, navigationButtons: false }}
    }};
    const network = new vis.Network(container, {{ nodes: nodes, edges: edges }}, options);

    // Endast lagnoder bär url och är därmed klickbara. Strukturnoder är
    // inerta by design: de har ingen url att öppna.
    network.on("click", function(params) {{
      if (!params.nodes.length) return;
      const nod = nodes.get(params.nodes[0]);
      if (nod && nod.url) {{
        window.open(nod.url, "_blank", "noopener,noreferrer");
      }}
    }});

    // Handmarkören signalerar vilka noder som går att öppna.
    network.on("hoverNode", function(params) {{
      const nod = nodes.get(params.node);
      container.style.cursor = (nod && nod.url) ? "pointer" : "default";
    }});
    network.on("blurNode", function() {{ container.style.cursor = "default"; }});
  }})();
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
    poster += [
        (AVDELNINGSFARGER[a.id]["bg"], a.label) for a in AVDELNINGAR
    ]
    poster.append((_LAGFARG["bg"], "Lag (klicka för lagen.nu)"))

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
    "AVDELNINGSFARGER",
    "GRUPP_AVDELNING",
    "GRUPP_LAG",
    "GRUPP_OMRADE",
    "GRUPP_ROT",
    "GRUPP_UNDEROMRADE",
    "bygg_html",
    "farglegend_html",
    "render_farglegend",
    "render_taxonomigraf",
]
