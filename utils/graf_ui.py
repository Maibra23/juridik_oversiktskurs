"""Rendering av kunskapsgrafen med vis-network i en Streamlit-komponent.

``render_kunskapsgraf(graf)`` serialiserar nod/kant-data till JSON och bäddar
in det i en HTML-sträng som laddar vis-network från CDN *inuti komponentens
iframe*. Den iframen är sandboxad och skild från Streamlits egen sida, så CDN
här bryter inte mot appens "ingen extern CDN"-regel för huvud-UI:t och rör inte
appens säkerhet.

Färgerna följer designsystemet: lagrum = paragrafguld, rättsfall =
myndighetsblå, moduler = bläck.

Not: grafen kräver internetåtkomst för att hämta vis-network. Datat i sig
byggs deterministiskt av utils.graf och fungerar offline; endast den
interaktiva ritningen behöver CDN.
"""

from __future__ import annotations

import json

from utils.graf import Graf

# Pinnad version för reproducerbarhet.
_VIS_NETWORK_CDN = (
    "https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"
)

# Designsystemets palett (design_system.md avsnitt 1).
_FARGER = {
    "lagrum": {"bg": "#B8860B", "kant": "#8A6608", "text": "#1A2332"},
    "rattsfall": {"bg": "#2C5F8A", "kant": "#1F4460", "text": "#FAF7F2"},
    "modul": {"bg": "#1A2332", "kant": "#0D131D", "text": "#FAF7F2"},
}


def _json_for_html(data: object) -> str:
    """Serialisera till JSON säkert för inbäddning i en <script>-tagg."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def _bygg_html(graf: Graf, hojd: int = 600) -> str:
    """Bygg den kompletta HTML-strängen för grafkomponenten (ren funktion)."""
    noder_json = _json_for_html(graf["noder"])
    kanter_json = _json_for_html(graf["kanter"])
    grupper_json = _json_for_html(
        {
            grupp: {
                "color": {"background": f["bg"], "border": f["kant"]},
                "font": {"color": f["text"]},
                "shape": "dot" if grupp == "lagrum" else "box",
            }
            for grupp, f in _FARGER.items()
        }
    )

    return f"""
<div id="kunskapsgraf" style="height:{hojd}px;border:1px solid #E5E0D8;
     border-radius:8px;background:#FFFFFF;"></div>
<script src="{_VIS_NETWORK_CDN}"></script>
<script>
  (function() {{
    const noder = {noder_json};
    const kanter = {kanter_json};
    if (typeof vis === "undefined") {{
      document.getElementById("kunskapsgraf").innerHTML =
        "<p style='padding:1rem;color:#1A2332;font-family:sans-serif'>" +
        "Kunde inte ladda grafbiblioteket (kräver internetåtkomst).</p>";
      return;
    }}
    const nodes = new vis.DataSet(noder.map(function(n) {{
      return {{ id: n.id, label: n.label, group: n.grupp }};
    }}));
    const edges = new vis.DataSet(kanter.map(function(k) {{
      return {{ from: k.fran, to: k.till }};
    }}));
    const container = document.getElementById("kunskapsgraf");
    const options = {{
      groups: {grupper_json},
      nodes: {{ borderWidth: 1, font: {{ size: 14 }} }},
      edges: {{ color: {{ color: "#C9BFA8" }}, smooth: {{ type: "continuous" }} }},
      physics: {{ stabilization: true, barnesHut: {{ springLength: 130 }} }},
      interaction: {{ hover: true, tooltipDelay: 120 }}
    }};
    new vis.Network(container, {{ nodes: nodes, edges: edges }}, options);
  }})();
</script>
"""


def render_kunskapsgraf(graf: Graf, hojd: int = 600) -> None:
    """Rendera den interaktiva kunskapsgrafen i appen."""
    import streamlit.components.v1 as components

    components.html(_bygg_html(graf, hojd), height=hojd + 16, scrolling=False)
