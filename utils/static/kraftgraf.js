// DOM-lagret för Rättskartans kraftvy.
//
// Läses av utils/kraftgraf_ui.py och bäddas in i komponentens sandboxade
// iframe. Alla tal och färger kommer från JOK_KRAFTKONFIG, JOK_HULLGRUPPER och
// nodernas eget färgfält, som Python skriver ut före den här filen. Kvar i
// filen ligger bara ren canvas-geometri.
//
// Variablerna kraftNoder, kraftKanter, JOK_HULLGRUPPER och JOK_KRAFTKONFIG är
// definierade i det föregående script-blocket.

(function () {
  const container = document.getElementById("jok-kraftgraf");

  if (typeof vis === "undefined") {
    // Statisk litteral utan inflätad data: ingen väg in för nodetiketter
    // eller annat innehåll, och därmed ingen injektionsyta.
    container.innerHTML =
      "<p style='padding:1rem;color:#1A2332;font-family:sans-serif'>" +
      "Kunde inte ladda grafbiblioteket (kräver internetåtkomst). " +
      "Områdesträdet nedanför fungerar ändå.</p>";
    return;
  }

  const konfig = JOK_KRAFTKONFIG;
  const fysik = konfig.fysik;

  // HTML-escape av allt som skrivs till innerHTML. Etiketterna kommer ur
  // data/rattssystem.json och lagrumsregistret; en apostrof eller ett < i ett
  // lagnamn får aldrig kunna bli markup.
  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // Länkar godtas bara mot https. URL:erna kommer ur lagrumsregistret och
  // data/rattssystem.json och är alltid lagen.nu, men en href får aldrig bli
  // en väg in för javascript:-scheman om en datafil någon gång skrivs fel.
  function saker_url(url) {
    return typeof url === "string" && url.indexOf("https://") === 0 ? url : "";
  }

  const nodes = new vis.DataSet(kraftNoder);
  const edges = new vis.DataSet(kraftKanter);

  // Knappen hämtas här uppe, före lyssnarna som visar den.
  const aterstallKnapp = document.getElementById("jok-kraft-aterstall");

  const network = new vis.Network(
    container,
    { nodes: nodes, edges: edges },
    {
      physics: {
        enabled: true,
        solver: fysik.solver,
        forceAtlas2Based: {
          gravitationalConstant: fysik.gravitationskonstant,
          centralGravity: fysik.centralGravitation,
          springLength: fysik.fjaderlangd,
          springConstant: fysik.fjaderkonstant,
          damping: fysik.dampning,
          avoidOverlap: fysik.undvikOverlapp,
        },
        stabilization: {
          iterations: fysik.stabiliseringsIterationer,
          fit: true,
        },
      },
      nodes: { borderWidth: 1.5, shadow: false },
      edges: {
        color: { color: konfig.kantfarg },
        width: 1,
        smooth: { type: "continuous", roundness: 0.2 },
      },
      interaction: { hover: true, tooltipDelay: 120, hideEdgesOnDrag: true },
    }
  );

  // Fysiken fryses när stabiliseringen är klar. Utan det kryper kartan omkring
  // medan studenten läser den.
  network.once("stabilizationIterationsDone", function () {
    network.setOptions({ physics: { enabled: false } });
  });

  // Grafen ritas på en canvas och har därför ingen DOM att klicka på utifrån.
  // Instansen exponeras för att vyn ska gå att verifiera i webbläsaren; appen
  // läser aldrig själv den här variabeln.
  window.jokKraftgraf = network;

  // --- Höljen per toppgren -------------------------------------------------

  // Monoton kedja (Andrew): övre och nedre skalet byggs var för sig och
  // fogas ihop till en omkrets i moturs ordning, vilket är den ordning
  // omkretsen måste ritas i. Sammanfallande punkter faller bort, så en grupp
  // med två noder ritas som ett streck i stället för en korsad nollyta.
  function konvextHolje(punkter) {
    const p = punkter
      .slice()
      .sort(function (a, b) {
        return a.x - b.x || a.y - b.y;
      });
    if (p.length < 3) return p;
    function kryss(o, a, b) {
      return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
    }
    function bygg(sekvens) {
      const ut = [];
      for (let i = 0; i < sekvens.length; i++) {
        const q = sekvens[i];
        while (ut.length >= 2 && kryss(ut[ut.length - 2], ut[ut.length - 1], q) <= 0) {
          ut.pop();
        }
        ut.push(q);
      }
      ut.pop();
      return ut;
    }
    const holje = bygg(p).concat(bygg(p.slice().reverse()));
    return holje.length >= 3 ? holje : p;
  }

  network.on("afterDrawing", function (ctx) {
    JOK_HULLGRUPPER.forEach(function (grupp) {
      const positioner = grupp.nod_id
        .filter(function (nid) {
          const n = nodes.get(nid);
          return n && !n.hidden;
        })
        .map(function (nid) {
          return network.getPositions([nid])[nid];
        })
        .filter(function (pos) {
          return pos !== undefined;
        });
      if (positioner.length < 2) return;

      const cx =
        positioner.reduce(function (s, pos) {
          return s + pos.x;
        }, 0) / positioner.length;
      const cy =
        positioner.reduce(function (s, pos) {
          return s + pos.y;
        }, 0) / positioner.length;

      // Omkretsen måste följa höljets ordning, inte medlemsordningen: den råa
      // ordningen korsar sig själv så fort fysiken inte råkar lägga noderna
      // i vinkelordning, och fylls då som kilar.
      const utvidgat = konvextHolje(positioner).map(function (pos) {
        return {
          x: cx + (pos.x - cx) * konfig.hullUtvidgning,
          y: cy + (pos.y - cy) * konfig.hullUtvidgning,
        };
      });

      ctx.save();
      ctx.fillStyle = grupp.farg;
      ctx.strokeStyle = grupp.farg;
      ctx.lineWidth = konfig.hullKantbredd;
      ctx.beginPath();
      ctx.moveTo(utvidgat[0].x, utvidgat[0].y);
      utvidgat.slice(1).forEach(function (pos) {
        ctx.lineTo(pos.x, pos.y);
      });
      ctx.closePath();
      ctx.globalAlpha = konfig.hullFyllopacitet;
      ctx.fill();
      ctx.globalAlpha = konfig.hullKantopacitet;
      ctx.stroke();

      // Toppgrenens namn skrivs i höljets tyngdpunkt, så att varje region går
      // att läsa utan att gå via legenden.
      ctx.globalAlpha = konfig.hullEtikettopacitet;
      ctx.fillStyle = grupp.farg;
      ctx.font = konfig.hullEtikettfont;
      ctx.textAlign = "center";
      ctx.fillText(grupp.etikett, cx, cy - konfig.hullEtikettlyft);
      ctx.restore();
    });
  });

  // --- Infopanelen ---------------------------------------------------------

  const infoRuta = document.getElementById("jok-kraft-info");

  const GRUPPNAMN = {
    rot: "Rot",
    gren: "Rättsområde",
    lag: "Kurslag",
    referenslag: "Referenslag (utanför kursen)",
  };

  function visaInfo(nodId) {
    const nod = nodes.get(nodId);
    if (!nod) return;
    const grannar = network.getConnectedNodes(nodId);
    const grannposter = grannar
      .map(function (nid) {
        const granne = nodes.get(nid);
        if (!granne) return "";
        return (
          '<span class="jok-kraft-granne" data-nid="' +
          esc(nid) +
          '" style="border-left-color:' +
          esc(granne.color.background) +
          '">' +
          esc(granne.label) +
          "</span>"
        );
      })
      .join("");

    const url = saker_url(nod.url);
    const lank = url
      ? '<div class="jok-kraft-falt"><a class="jok-kraft-lank" target="_blank" ' +
        'rel="noopener noreferrer" href="' +
        esc(url) +
        '">Öppna på lagen.nu</a></div>'
      : "";

    infoRuta.innerHTML =
      '<div class="jok-kraft-falt"><b>' +
      esc(nod.label) +
      "</b></div>" +
      '<div class="jok-kraft-falt">' +
      esc(GRUPPNAMN[nod.grupp] || nod.grupp) +
      "</div>" +
      (nod.title
        ? '<div class="jok-kraft-falt">' + esc(nod.title) + "</div>"
        : "") +
      lank +
      (grannar.length
        ? '<div class="jok-kraft-rubrik" style="margin-top:8px">Kopplade noder (' +
          grannar.length +
          ')</div><div class="jok-kraft-grannar">' +
          grannposter +
          "</div>"
        : "");
  }

  function tomInfo() {
    infoRuta.innerHTML =
      '<p class="jok-kraft-tom">Klicka på en nod i kartan.</p>';
  }

  // Grannlänkarna får en delegerad lyssnare och ett data-attribut i stället
  // för inline-onclick: ett nodnamn med citattecken skulle annars både bryta
  // länken och öppna en injektionsväg.
  infoRuta.addEventListener("click", function (handelse) {
    const mal = handelse.target.closest(".jok-kraft-granne");
    if (mal) fokusera(mal.dataset.nid);
  });

  function fokusera(nodId) {
    network.selectNodes([nodId]);
    network.focus(nodId, {
      scale: konfig.fokusSkala,
      animation: { duration: konfig.animeringMs, easingFunction: "easeInOutQuad" },
    });
    visaInfo(nodId);
    aterstallKnapp.hidden = false;
  }

  network.on("click", function (params) {
    if (params.nodes.length) {
      visaInfo(params.nodes[0]);
      aterstallKnapp.hidden = false;
    } else {
      network.unselectAll();
      tomInfo();
    }
  });

  // Lagen öppnas på dubbelklick, inte på enkelklick: i den här vyn är
  // enkelklicket infopanelens, och en oväntad ny flik vid varje klick gör
  // kartan obrukbar att utforska.
  network.on("doubleClick", function (params) {
    if (!params.nodes.length) return;
    const nod = nodes.get(params.nodes[0]);
    const url = nod ? saker_url(nod.url) : "";
    if (url) window.open(url, "_blank", "noopener,noreferrer");
  });

  // --- Sökrutan ------------------------------------------------------------

  const sokruta = document.getElementById("jok-kraft-sok");
  const sokresultat = document.getElementById("jok-kraft-sokresultat");

  function rensaSok() {
    sokresultat.innerHTML = "";
  }

  sokruta.addEventListener("input", function () {
    const fras = sokruta.value.trim().toLowerCase();
    if (!fras) {
      rensaSok();
      return;
    }
    const traffar = nodes
      .get()
      .filter(function (nod) {
        return !nod.hidden && nod.label.toLowerCase().indexOf(fras) !== -1;
      })
      .slice(0, konfig.sokMaxTraffar);

    if (!traffar.length) {
      sokresultat.innerHTML =
        '<p class="jok-kraft-tom">Ingen nod matchar.</p>';
      return;
    }
    sokresultat.innerHTML = traffar
      .map(function (nod) {
        return (
          '<div class="jok-kraft-traff" data-nid="' +
          esc(nod.id) +
          '" style="border-left-color:' +
          esc(nod.color.background) +
          '">' +
          esc(nod.label) +
          "</div>"
        );
      })
      .join("");
  });

  sokresultat.addEventListener("click", function (handelse) {
    const mal = handelse.target.closest(".jok-kraft-traff");
    if (mal) fokusera(mal.dataset.nid);
  });

  // --- Grenfiltret ---------------------------------------------------------
  //
  // Att dölja en gren döljer hela dess underträd, eftersom toppgrenen ärvs
  // nedåt på varje nod. Höljet försvinner med noderna eftersom ritningen
  // hoppar över dolda noder.

  const filterrutor = document.querySelectorAll(".jok-kraft-filter input");

  function tillampFilter() {
    const avmarkerade = {};
    filterrutor.forEach(function (ruta) {
      if (!ruta.checked) avmarkerade[ruta.value] = true;
    });
    nodes.update(
      nodes.get().map(function (nod) {
        return { id: nod.id, hidden: !!avmarkerade[nod.toppgren] };
      })
    );
    rensaSok();

    // Den valda noden kan just ha dolts; då säger infopanelen emot kartan.
    const valda = network.getSelectedNodes();
    if (valda.length) {
      const vald = nodes.get(valda[0]);
      if (!vald || vald.hidden) {
        network.unselectAll();
        tomInfo();
      }
    }

    // Vyn måste ramas om. Utan det blir duken tom så fort filtret slår till
    // medan kartan är inzoomad på en nod som nyss försvann: noderna som är
    // kvar ligger då utanför rutan.
    network.fit({
      animation: { duration: konfig.animeringMs, easingFunction: "easeInOutQuad" },
    });
  }

  filterrutor.forEach(function (ruta) {
    ruta.addEventListener("change", tillampFilter);
  });

  // --- Återställning -------------------------------------------------------

  // Knappen ligger dold i markupen och visas först här, så att den aldrig
  // lovar interaktivitet i fallbacken där vis-network saknas.
  aterstallKnapp.hidden = false;

  function aterstall() {
    network.unselectAll();
    network.fit({
      animation: { duration: konfig.animeringMs, easingFunction: "easeInOutQuad" },
    });
    tomInfo();
    rensaSok();
    sokruta.value = "";
  }

  aterstallKnapp.addEventListener("click", aterstall);
  document.addEventListener("keydown", function (handelse) {
    if (handelse.key === "Escape") aterstall();
  });
})();
