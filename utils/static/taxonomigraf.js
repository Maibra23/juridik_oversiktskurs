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

  // Knappen är dold i markupen och visas först här, så att den aldrig lovar
  // interaktivitet i fallbacken där vis-network saknas.
  const aterstallKnapp = document.getElementById("jok-aterstall-vy");
  aterstallKnapp.hidden = false;

  // --- Fokusering ----------------------------------------------------------
  //
  // Tre skikt enligt specen: den fokuserade grenen och kedjan upp mot roten
  // är skarpa, allt annat tonas ned. Kedjans kanter markeras i guld, så att
  // systematiken från "Svensk rätt" och ned syns.

  const kantensForalder = new Map(kanter.map((k) => [k.to, k.from]));
  const allaNodId = noder.map((n) => n.id);

  function satOpacitet(idn, opacitet) {
    nodes.update(idn.map((id) => ({ id: id, opacity: opacitet })));
  }

  function markeraKedjan(kedja, fokusId) {
    // Kanten in till varje nod i kedjan, plus kanten in till den fokuserade
    // noden själv -- annars slutar spåret ett steg för tidigt.
    const noderIKedjan = kedja.concat(fokusId ? [fokusId] : []);
    const uppdateringar = edges.get().map(function (kant) {
      const iKedjan =
        noderIKedjan.includes(kant.to) &&
        kantensForalder.get(kant.to) === kant.from;
      return {
        id: kant.id,
        color: {
          color: iKedjan ? JOK_GRAFKONFIG.kedjefarg : JOK_GRAFKONFIG.kantfarg,
        },
        width: iKedjan ? JOK_GRAFKONFIG.kedjebredd : 1,
      };
    });
    edges.update(uppdateringar);
  }

  function fokusera(nodId) {
    const skikt = beraknaSkikt(noder, nodId);
    if (!skikt.fokus.length) return;
    satOpacitet(skikt.fokus.concat(skikt.kedja), 1);
    satOpacitet(skikt.bakgrund, JOK_GRAFKONFIG.bakgrundsopacitet);
    markeraKedjan(skikt.kedja, nodId);
    network.fit({
      nodes: skikt.fokus,
      maxZoomLevel: JOK_GRAFKONFIG.maxFokusSkala,
      animation: { duration: JOK_GRAFKONFIG.animeringMs },
    });
  }

  function aterstall() {
    satOpacitet(allaNodId, 1);
    markeraKedjan([], null);
    network.fit({ animation: { duration: JOK_GRAFKONFIG.animeringMs } });
  }

  aterstallKnapp.addEventListener("click", aterstall);
  document.addEventListener("keydown", function (handelse) {
    if (handelse.key === "Escape") aterstall();
  });

  // --- Zoomgolv ------------------------------------------------------------
  //
  // vis-network har inget globalt zoomtak: minZoom/maxZoom finns bara som
  // argument till fit(). Golvet klampas därför i zoom-händelsen. Det härleds
  // ur den första fit():en i stället för att hårdkodas, så att det följer med
  // containerns bredd och trädets storlek.
  let minSkala = null;
  // moveTo() utlöser i sin tur zoom-händelsen. Utan den här spärren skulle
  // klampningen anropa sig själv i en loop.
  let klampar = false;

  network.once("afterDrawing", function () {
    minSkala = network.getScale() * JOK_GRAFKONFIG.minSkalaFaktor;
  });
  network.on("zoom", function () {
    if (minSkala === null || klampar) return;
    if (network.getScale() < minSkala) {
      klampar = true;
      network.moveTo({ scale: minSkala });
      klampar = false;
    }
  });

  network.on("click", function (params) {
    // Tom yta återställer vyn.
    if (!params.nodes.length) {
      aterstall();
      return;
    }
    const nod = nodes.get(params.nodes[0]);
    if (!nod) return;

    // Lagnoder är löv och har ingenting att zooma in i: de öppnar lagen.nu,
    // precis som innan fokuseringen fanns.
    if (nod.url) {
      window.open(nod.url, "_blank", "noopener,noreferrer");
      return;
    }

    // Roten omfattar allt, så att fokusera den är per definition utgångsläget.
    if (!nod.foralder) {
      aterstall();
      return;
    }
    fokusera(nod.id);
  });

  // Handmarkören signalerar vilka noder som svarar på klick: lagnoderna
  // öppnar lagen.nu, strukturnoderna fokuserar. Roten gör varken eller.
  network.on("hoverNode", function (params) {
    const nod = nodes.get(params.node);
    const klickbar = Boolean(nod && (nod.url || nod.foralder));
    container.style.cursor = klickbar ? "pointer" : "default";
  });
  network.on("blurNode", function () {
    container.style.cursor = "default";
  });
})();
