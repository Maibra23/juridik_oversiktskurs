// DOM-lagret för Rättskartans taxonomigraf.
//
// Läses av utils/taxonomi_ui.py och bäddas in i komponentens sandboxade
// iframe. Alla inställningar kommer från JOK_GRAFKONFIG, som Python skriver
// ut före den här filen. Inga tal eller färger hårdkodas här.
//
// Variablerna noder, kanter, JOK_GRAFKONFIG och container är definierade i
// det föregående script-blocket.

(function () {
  if (typeof vis === "undefined") {
    // Statisk litteral utan inflätad data: ingen väg in för nodetiketter
    // eller annat innehåll, och därmed ingen injektionsyta.
    container.innerHTML =
      "<p style='padding:1rem;color:#1A2332;font-family:sans-serif'>" +
      "Kunde inte ladda grafbiblioteket (kräver internetåtkomst). " +
      "Områdesträdet nedanför fungerar ändå.</p>";
    return;
  }

  const nodes = new vis.DataSet(noder);
  const edges = new vis.DataSet(kanter);
  const options = {
    layout: {
      hierarchical: {
        enabled: true,
        direction: "UD",
        sortMethod: "directed",
        levelSeparation: 130,
        nodeSpacing: 110,
        treeSpacing: 160,
      },
    },
    nodes: { borderWidth: 1, shadow: false },
    edges: {
      color: { color: JOK_GRAFKONFIG.kantfarg },
      width: 1,
      smooth: { type: "cubicBezier", forceDirection: "vertical" },
    },
    physics: false,
    interaction: { hover: true, tooltipDelay: 120, navigationButtons: false },
  };
  const network = new vis.Network(container, { nodes: nodes, edges: edges }, options);

  // Endast lagnoder bär url och är därmed klickbara. Strukturnoder är
  // inerta tills fokuseringen kopplas på.
  network.on("click", function (params) {
    if (!params.nodes.length) return;
    const nod = nodes.get(params.nodes[0]);
    if (nod && nod.url) {
      window.open(nod.url, "_blank", "noopener,noreferrer");
    }
  });

  // Handmarkören signalerar vilka noder som går att öppna.
  network.on("hoverNode", function (params) {
    const nod = nodes.get(params.node);
    container.style.cursor = nod && nod.url ? "pointer" : "default";
  });
  network.on("blurNode", function () {
    container.style.cursor = "default";
  });
})();
