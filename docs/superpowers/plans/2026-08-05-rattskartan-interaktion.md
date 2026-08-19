# Rättskartans grafinteraktion, implementationsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gör taxonomigrafen på Rättskartan navigerbar: klick på ett rättsområde fokuserar grenen med nedtonad omgivning och skarp förfäderskedja, utzoomningen får ett golv, och vyn återställs med en knapp i kartan, allt utan sidladdning.

**Architecture:** Grafen lever i en enkelriktad `components.html`-iframe, så all interaktion är JavaScript inuti iframen. JS:en flyttas ut ur f-strängen i `bygg_html` till två filer under `utils/static/`: ett rent logiklager utan DOM-beroende (node-testbart) och ett DOM-lager som kopplar logiken till `vis.Network`. Python bidrar med ett nytt datafält (`foralder`) och ett konfigurationsblock, båda testade med pytest.

**Tech Stack:** Python 3.11, Streamlit 1.55, vis-network 9.1.9 (CDN), pytest 9.0.2, ruff 0.16.1, mypy 2.3.0, node 20 (endast för JS-testerna).

## Global Constraints

- **Språk:** all kod, alla kommentarer, alla docstrings och all UI-text på svenska. Variabelnamn och funktionsnamn på svenska, som i resten av `utils/`.
- **Lint:** `ruff check .` måste passera. Regeluppsättningen är `E4, E7, E9, F, I` med `line-length = 88` (`ruff.toml`). Importer ska vara sorterade (I).
- **Typkontroll:** `mypy --ignore-missing-imports utils` måste passera. Alla nya funktionssignaturer i `utils/` ska ha typannoteringar.
- **Inga hårdkodade värden:** opacitet, skalfaktorer, färger och animeringstider ligger som namngivna konstanter i `utils/taxonomi_ui.py` och skickas till JS:en via konfigurationsblocket. Inga magiska tal i JS-filerna.
- **Immutabilitet:** Python-sidan bygger nya dictar, muterar aldrig indata.
- **Färger:** endast palett ur `design_system.md`. Guld (`#B8860B`) betyder lag eller lagrum och får inte återanvändas för strukturnivåer, undantaget är förfäderskedjans kantmarkering, som är en *kant*, inte en nod.
- **CDN-fallbacken får inte brytas:** utan internet ska grafen fortfarande skriva "Kunde inte ladda grafbiblioteket" och peka på områdesträdet.
- **Commit-format:** `<type>: <beskrivning>` på svenska (feat, fix, refactor, docs, test, chore).

---

### Task 1: Varje nod bär sin förälder

Grafen är redan ett strikt träd, men noderna vet inte om det, släktskapet finns bara i kantlistan. JS:en behöver kunna gå uppåt (förfäder) och nedåt (ättlingar) från en klickad nod. Ett fält per nod räcker; färdiga förfäderslistor och ättlingslistor per nod skulle få JSON-nyttolasten att växa kvadratiskt.

**Files:**
- Modify: `utils/rattssystem_graf.py:62-73` (TypedDict `TaxNod`), `utils/rattssystem_graf.py:109-159` (`bygg_taxonomigraf`)
- Test: `tests/test_rattssystem_graf.py`

**Interfaces:**
- Consumes: inget (första uppgiften)
- Produces: `TaxNod` får nyckeln `foralder: str`, förälderns nod-id, tom sträng för roten. Task 2 läser den.

- [ ] **Step 1: Write the failing tests**

Lägg till sist i `tests/test_rattssystem_graf.py`:

```python
# --- Släktskap --------------------------------------------------------------


def test_varje_nods_foralder_matchar_kantlistan(graf):
    """foralder ska vara härledd ur samma träd som kanterna, inte gissad."""
    per_id = {n["id"]: n for n in graf["noder"]}
    for kant in graf["kanter"]:
        barn = per_id[kant["till"]]
        assert barn["foralder"] == kant["fran"], (
            f"{barn['label']} pekar på {barn['foralder']}, "
            f"men kanten kommer från {kant['fran']}"
        )


def test_endast_roten_saknar_foralder(graf):
    """Ett strikt träd har exakt en nod utan förälder."""
    utan = [n["id"] for n in graf["noder"] if not n["foralder"]]
    assert utan == [ROT_ID]


def test_alla_noder_bar_faltet(graf):
    """Saknas fältet på någon nod faller JS-sidans föräldrakarta tyst."""
    for nod in graf["noder"]:
        assert "foralder" in nod, f"{nod['label']} saknar foralder"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py -k "foralder or faltet" -v`
Expected: FAIL, `KeyError: 'foralder'` i alla tre.

- [ ] **Step 3: Add the field to the TypedDict**

I `utils/rattssystem_graf.py`, i `class TaxNod`, efter `niva: int`:

```python
    # Förälderns nod-id, tom sträng för roten. Renderingen härleder både
    # förfäderskedja och ättlingar ur det här fältet i stället för att gå
    # igenom kantlistan; se utils/static/taxonomigraf_logik.js.
    foralder: str
```

- [ ] **Step 4: Set it on all three node kinds**

I `bygg_taxonomigraf`, rotnoden:

```python
    noder: list[TaxNod] = [
        {
            "id": ROT_ID,
            "label": ROT_LABEL,
            "grupp": GRUPP_ROT,
            "niva": 0,
            "foralder": "",
            "toppgren": "",
            "titel": "Svensk rätts doktrinära indelning.",
        }
    ]
```

I `_lagg_till`, grennoden, lägg `"foralder": foralder_id,` direkt efter `"niva": niva,`.

I `_lagg_till`, lagnoden, lägg `"foralder": gid,` direkt efter `"niva": niva + 1,`.

- [ ] **Step 5: Run the full graph suite**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py -q`
Expected: PASS, inklusive de befintliga trädinvarianttesterna.

- [ ] **Step 6: Commit**

```bash
git add utils/rattssystem_graf.py tests/test_rattssystem_graf.py
git commit -m "feat: låt varje taxonominod bära sin förälder"
```

---

### Task 2: Konfigurationsblock och foralder ut i renderingen

Alla värden som styr fokus, nedtoning och zoom ska vara namngivna konstanter i Python och nå JS:en genom ett enda objekt. Då finns inga magiska tal i JS-filerna, och pytest kan vakta kontraktet.

**Files:**
- Modify: `utils/taxonomi_ui.py:58-60` (konstanter), `utils/taxonomi_ui.py:77-99` (`_vis_noder`), `utils/taxonomi_ui.py:102-162` (`bygg_html`)
- Test: `tests/test_taxonomi_ui.py`

**Interfaces:**
- Consumes: `TaxNod["foralder"]` från Task 1.
- Produces: modulkonstanterna `BAKGRUNDSOPACITET`, `MIN_SKALA_FAKTOR`, `MAX_FOKUS_SKALA`, `FOKUS_ANIMERING_MS`, `KEDJEFARG`, `KEDJEBREDD`, `KANTFARG` och funktionen `grafkonfig() -> dict[str, object]`. `bygg_html` skriver ut den som `const JOK_GRAFKONFIG = {...};`. Task 4 till 6 läser objektet i JS.

- [ ] **Step 1: Write the failing tests**

Lägg till i `tests/test_taxonomi_ui.py`:

```python
# --- Konfiguration ----------------------------------------------------------


def test_vis_noder_bar_foralder(graf):
    """Utan foralder kan JS:en inte bygga sin föräldrakarta."""
    for vis_nod, kall_nod in zip(_vis_noder(graf), graf["noder"]):
        assert vis_nod["foralder"] == kall_nod["foralder"]


def test_konfigurationen_baddas_in(html):
    assert "JOK_GRAFKONFIG" in html


def test_konfigurationen_bar_alla_varden():
    from utils.taxonomi_ui import grafkonfig

    konfig = grafkonfig()
    assert konfig["bakgrundsopacitet"] == BAKGRUNDSOPACITET
    assert konfig["minSkalaFaktor"] == MIN_SKALA_FAKTOR
    assert konfig["maxFokusSkala"] == MAX_FOKUS_SKALA
    assert konfig["animeringMs"] == FOKUS_ANIMERING_MS
    assert konfig["kedjefarg"] == KEDJEFARG
    assert konfig["kedjebredd"] == KEDJEBREDD


def test_inga_magiska_tal_i_konfigurationen():
    """Varje värde ska komma från en namngiven konstant, inte skrivas två gånger."""
    from utils.taxonomi_ui import grafkonfig

    assert set(grafkonfig()) == {
        "bakgrundsopacitet",
        "minSkalaFaktor",
        "maxFokusSkala",
        "animeringMs",
        "kedjefarg",
        "kedjebredd",
        "kantfarg",
    }
```

Utöka importblocket överst i filen med de sex konstanterna:

```python
from utils.taxonomi_ui import (
    _LAGFARG,
    BAKGRUNDSOPACITET,
    FOKUS_ANIMERING_MS,
    GRENFARGER,
    KEDJEBREDD,
    KEDJEFARG,
    MAX_FOKUS_SKALA,
    MIN_SKALA_FAKTOR,
    _vis_noder,
    bygg_html,
    farglegend_html,
)
```

**Gissa inte ordningen.** ruffs isort-regel (I) sorterar namn inom ett
importblock efter egna regler för understreck och versaler. Kör
`ruff check --fix tests/test_taxonomi_ui.py` och behåll den ordning ruff
skriver, ordningen ovan är inte normerande.

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3.11 -m pytest tests/test_taxonomi_ui.py -q`
Expected: FAIL, `ImportError: cannot import name 'BAKGRUNDSOPACITET'`.

- [ ] **Step 3: Add the constants**

I `utils/taxonomi_ui.py`, efter `_STORLEK`:

```python
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
```

- [ ] **Step 4: Add `grafkonfig` and wire it in**

I `utils/taxonomi_ui.py`, efter `_nodfarg`:

```python
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
```

I `_vis_noder`, lägg in i den dict som byggs per nod, efter `"url"`:

```python
                "foralder": nod.get("foralder", ""),
```

I `bygg_html`, efter raden som bygger `kanter_json`:

```python
    konfig_json = _json_for_html(grafkonfig())
```

och i f-strängens `<script>`-block, direkt efter `const kanter = {kanter_json};`:

```
    const JOK_GRAFKONFIG = {konfig_json};
```

Byt samtidigt den hårdkodade kantfärgen i optionsobjektet mot konfigurationen:
`color: {{ color: JOK_GRAFKONFIG.kantfarg }}`.

- [ ] **Step 5: Run tests**

Run: `python3.11 -m pytest tests/test_taxonomi_ui.py -q`
Expected: PASS, alla, inklusive de befintliga färgtesterna och klickbarhetstesterna.

- [ ] **Step 6: Commit**

```bash
git add utils/taxonomi_ui.py tests/test_taxonomi_ui.py
git commit -m "feat: samla grafens interaktionsinställningar i ett konfigurationsblock"
```

---

### Task 3: Flytta ut JavaScripten ur f-strängen

Ren refaktorering, inget beteende ändras. `bygg_html` är i dag en f-sträng på ~55 rader där varje `{` måste dubbleras. Fokus, nedtoning, klampning och kedjemarkering ska inte in där. Efteråt är JS:en riktig JavaScript i en egen fil.

**Files:**
- Create: `utils/static/taxonomigraf.js`
- Modify: `utils/taxonomi_ui.py` (`bygg_html`)
- Test: `tests/test_taxonomi_ui.py`

**Interfaces:**
- Consumes: `JOK_GRAFKONFIG` från Task 2.
- Produces: `_las_js(filnamn: str) -> str` och katalogen `utils/static/`. Task 4 lägger en fil till där.

- [ ] **Step 1: Write the failing tests**

```python
# --- JavaScript som egen fil ------------------------------------------------


def test_js_filen_finns():
    from utils.taxonomi_ui import _JS_KATALOG

    assert (_JS_KATALOG / "taxonomigraf.js").is_file()


def test_js_baddas_in_i_html(html):
    """Innehållet ska ligga i svaret, inte länkas, iframen är sandboxad."""
    from utils.taxonomi_ui import _las_js

    assert _las_js("taxonomigraf.js").strip() in html


def test_saknad_js_fil_ger_tydligt_fel():
    from utils.taxonomi_ui import _las_js

    with pytest.raises(FileNotFoundError, match="Grafens JavaScript saknas"):
        _las_js("finns_inte.js")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3.11 -m pytest tests/test_taxonomi_ui.py -k "js" -v`
Expected: FAIL, `ImportError: cannot import name '_JS_KATALOG'`.

- [ ] **Step 3: Create the JS file with the existing behaviour**

Skapa `utils/static/taxonomigraf.js` med exakt det beteende som i dag ligger i f-strängen:

```javascript
// DOM-lagret för Rättskartans taxonomigraf.
//
// Läses av utils/taxonomi_ui.py och bäddas in i komponentens sandboxade
// iframe. Alla inställningar kommer från JOK_GRAFKONFIG, som Python skriver
// ut före den här filen. Inga tal eller färger hårdkodas här.
//
// Variablerna noder, kanter och JOK_GRAFKONFIG är definierade i det
// föregående script-blocket.

(function () {
  const container = document.getElementById("taxonomigraf");

  if (typeof vis === "undefined") {
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
  // inerta tills Task 4 ger dem fokusering.
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
```

- [ ] **Step 4: Replace the f-string body with the loader**

I `utils/taxonomi_ui.py`, lägg till överst bland importerna `from pathlib import Path` (ruff I kräver att den sorteras in bland standardbiblioteken, efter `import json`).

Efter konstanterna:

```python
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
```

Ersätt hela `<script>`-kroppen efter konfigurationsraden med `{_las_js("taxonomigraf.js")}`. `bygg_html` blir då:

```python
    return f"""
<div id="taxonomigraf" style="height:{hojd}px;border:1px solid #E5E0D8;
     border-radius:8px;background:#FFFFFF;"></div>
<script src="{_VIS_NETWORK_CDN}"></script>
<script>
  const noder = {noder_json};
  const kanter = {kanter_json};
  const JOK_GRAFKONFIG = {konfig_json};
</script>
<script>
{_las_js("taxonomigraf.js")}
</script>
"""
```

- [ ] **Step 5: Run the whole suite**

Run: `python3.11 -m pytest -q`
Expected: PASS, 766+ tester. De befintliga testerna `test_klickhanterare_oppnar_ny_flik` och `test_fallback_utan_internet` måste fortfarande passera, de bevisar att refaktoreringen inte tappade beteende.

- [ ] **Step 6: Lint and typecheck**

Run: `ruff check . && mypy --ignore-missing-imports utils`
Expected: båda rena. (Använd de pinnade versionerna om de finns installerade.)

- [ ] **Step 7: Commit**

```bash
git add utils/static/taxonomigraf.js utils/taxonomi_ui.py tests/test_taxonomi_ui.py
git commit -m "refactor: flytta grafens JavaScript till utils/static"
```

---

### Task 4: Skiktlogiken som testbar JavaScript

Vilka noder som hör till fokus, kedja respektive bakgrund är ren beräkning utan DOM. Den läggs därför i en egen fil som både webbläsaren och `node --test` kan ladda, så att JS:ens enda icke-triviala logik faktiskt testas.

**Files:**
- Create: `utils/static/taxonomigraf_logik.js`
- Create: `tests/js/test_taxonomigraf_logik.mjs`
- Modify: `utils/taxonomi_ui.py` (`bygg_html` bäddar in även logikfilen), `.github/workflows/ci.yml`
- Test: `tests/js/test_taxonomigraf_logik.mjs`, `tests/test_taxonomi_ui.py`

**Interfaces:**
- Consumes: `foralder` per nod från Task 1 och 2.
- Produces: de globala funktionerna `byggForalderkarta(noder)`, `byggBarnkarta(noder)`, `attlingar(barnkarta, rotId)`, `forfader(foralderkarta, nodId)` och `beraknaSkikt(noder, fokusId) -> {fokus, kedja, bakgrund}` (tre listor med nod-id). Task 5 anropar `beraknaSkikt`.

- [ ] **Step 1: Write the failing JS test**

Skapa `tests/js/test_taxonomigraf_logik.mjs`. Filen laddas utan modulsystem via `node:vm`, så att `utils/static/taxonomigraf_logik.js` kan förbli ett vanligt `<script>` i webbläsaren:

```javascript
// Tester för grafens skiktlogik. Körs med:  node --test tests/js/
//
// Logikfilen är ett vanligt script utan export, eftersom webbläsaren laddar
// den som en <script>-tagg. vm.runInContext gör dess toppnivåfunktioner
// tillgängliga som egenskaper på sandlådan.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const kod = readFileSync(
  new URL("../../utils/static/taxonomigraf_logik.js", import.meta.url),
  "utf8",
);
const sandlada = {};
vm.createContext(sandlada);
vm.runInContext(kod, sandlada);
const { beraknaSkikt } = sandlada;

// Ett litet träd med samma form som den riktiga taxonomin:
//   rot -> civilratt -> formogenhet -> obligation -> [AvtL]
//   rot -> offentlig
const NODER = [
  { id: "rot", foralder: "" },
  { id: "offentlig", foralder: "rot" },
  { id: "civilratt", foralder: "rot" },
  { id: "formogenhet", foralder: "civilratt" },
  { id: "obligation", foralder: "formogenhet" },
  { id: "avtl", foralder: "obligation" },
];

test("fokus omfattar noden och alla dess ättlingar", () => {
  const { fokus } = beraknaSkikt(NODER, "formogenhet");
  assert.deepEqual(new Set(fokus), new Set(["formogenhet", "obligation", "avtl"]));
});

test("kedjan går från roten ned till noden, i ordning", () => {
  const { kedja } = beraknaSkikt(NODER, "obligation");
  assert.deepEqual(kedja, ["rot", "civilratt", "formogenhet"]);
});

test("bakgrunden är exakt resten", () => {
  const { bakgrund } = beraknaSkikt(NODER, "formogenhet");
  assert.deepEqual(new Set(bakgrund), new Set(["offentlig"]));
});

test("fokus på roten lämnar ingen bakgrund", () => {
  const { fokus, kedja, bakgrund } = beraknaSkikt(NODER, "rot");
  assert.equal(fokus.length, NODER.length);
  assert.deepEqual(kedja, []);
  assert.deepEqual(bakgrund, []);
});

test("ett löv fokuserar bara sig självt", () => {
  const { fokus } = beraknaSkikt(NODER, "avtl");
  assert.deepEqual(fokus, ["avtl"]);
});

test("okänt id ger tom fokus och allt i bakgrunden", () => {
  const { fokus, bakgrund } = beraknaSkikt(NODER, "finns-inte");
  assert.deepEqual(fokus, []);
  assert.equal(bakgrund.length, NODER.length);
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `node --test tests/js/`
Expected: FAIL, `ENOENT: no such file or directory ... taxonomigraf_logik.js`.

- [ ] **Step 3: Write the logic file**

Skapa `utils/static/taxonomigraf_logik.js`:

```javascript
// Rena funktioner för Rättskartans grafinteraktion: vilka noder som hör till
// den fokuserade grenen, till kedjan upp mot roten, och till bakgrunden.
//
// Ingen DOM och inget vis-beroende, så att filen kan köras både i iframen
// (som <script>) och under node --test (via node:vm). Se
// tests/js/test_taxonomigraf_logik.mjs.

function byggForalderkarta(noder) {
  const karta = new Map();
  for (const nod of noder) {
    karta.set(nod.id, nod.foralder || "");
  }
  return karta;
}

function byggBarnkarta(noder) {
  const karta = new Map();
  for (const nod of noder) {
    if (!nod.foralder) continue;
    if (!karta.has(nod.foralder)) karta.set(nod.foralder, []);
    karta.get(nod.foralder).push(nod.id);
  }
  return karta;
}

// Noden själv plus hela dess delträd, i bredden först.
function attlingar(barnkarta, rotId) {
  const ut = [rotId];
  const ko = [rotId];
  while (ko.length) {
    const nuvarande = ko.shift();
    for (const barn of barnkarta.get(nuvarande) || []) {
      ut.push(barn);
      ko.push(barn);
    }
  }
  return ut;
}

// Kedjan från roten ned till nodens förälder, i den ordningen.
function forfader(foralderkarta, nodId) {
  const kedja = [];
  let nuvarande = foralderkarta.get(nodId);
  while (nuvarande) {
    kedja.unshift(nuvarande);
    nuvarande = foralderkarta.get(nuvarande);
  }
  return kedja;
}

// Tre skikt: fokus (grenen), kedja (vägen dit) och bakgrund (allt annat).
// Ett okänt id ger tom fokus och tom kedja, så att anroparen kan behandla
// det som "ingen fokusering" utan särfall.
function beraknaSkikt(noder, fokusId) {
  const foralderkarta = byggForalderkarta(noder);
  if (!foralderkarta.has(fokusId)) {
    return { fokus: [], kedja: [], bakgrund: noder.map((n) => n.id) };
  }
  const fokus = attlingar(byggBarnkarta(noder), fokusId);
  const kedja = forfader(foralderkarta, fokusId);
  const markerade = new Set([...fokus, ...kedja]);
  const bakgrund = noder.map((n) => n.id).filter((id) => !markerade.has(id));
  return { fokus: fokus, kedja: kedja, bakgrund: bakgrund };
}
```

- [ ] **Step 4: Run the JS tests**

Run: `node --test tests/js/`
Expected: PASS, 6 tester.

- [ ] **Step 5: Embed the logic file and assert it in pytest**

I `utils/taxonomi_ui.py`, i `bygg_html`, lägg logikfilen **före** DOM-filen, den senare anropar den:

```
<script>
{_las_js("taxonomigraf_logik.js")}
</script>
<script>
{_las_js("taxonomigraf.js")}
</script>
```

Lägg till i `tests/test_taxonomi_ui.py`:

```python
def test_logikfilen_baddas_in_fore_dom_filen(html):
    """DOM-lagret anropar beraknaSkikt, så logiken måste komma först."""
    from utils.taxonomi_ui import _las_js

    logik = _las_js("taxonomigraf_logik.js").strip()
    dom = _las_js("taxonomigraf.js").strip()
    assert logik in html and dom in html
    assert html.index(logik) < html.index(dom)
```

- [ ] **Step 6: Add the JS step to CI**

I `.github/workflows/ci.yml`, efter steget "Tester":

```yaml
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - name: JS-tester
        run: node --test tests/js/
```

Uppdatera samtidigt filens toppkommentar så att den nämner JS-testerna.

- [ ] **Step 7: Run everything**

Run: `python3.11 -m pytest -q && node --test tests/js/ && ruff check .`
Expected: allt grönt.

- [ ] **Step 8: Commit**

```bash
git add utils/static/taxonomigraf_logik.js tests/js/ utils/taxonomi_ui.py \
        tests/test_taxonomi_ui.py .github/workflows/ci.yml
git commit -m "feat: skiktlogik för grafens fokusering, med node-tester i CI"
```

---

### Task 5: Fokusera grenen vid klick

Nu kopplas skiktlogiken till grafen: klick på en strukturnod tonar ned bakgrunden, håller förfäderskedjan skarp med fetare guldkant, och centrerar kameran på grenen. Lagnoder öppnar lagen.nu precis som förut.

**Files:**
- Modify: `utils/static/taxonomigraf.js`
- Test: browser-checklistan i Task 8 (DOM-beteende, se motiveringen i specen)

**Interfaces:**
- Consumes: `beraknaSkikt` (Task 4), `JOK_GRAFKONFIG` (Task 2), `foralder` per nod (Task 1).
- Produces: funktionerna `fokusera(nodId)` och `aterstall()` i DOM-filens closure. Task 6 binder dem till knapp och tangent.

- [ ] **Step 1: Add focus and reset inside the closure**

I `utils/static/taxonomigraf.js`, efter att `network` skapats:

```javascript
  // --- Fokusering ----------------------------------------------------------
  //
  // Tre skikt enligt specen: den fokuserade grenen och kedjan upp mot roten
  // är skarpa, allt annat tonas ned. Kedjans kanter markeras i guld, så att
  // systematiken från "Svensk rätt" och ned syns.

  const kantensForalder = new Map(kanter.map((k) => [k.to, k.from]));

  function satOpacitet(idn, opacitet) {
    nodes.update(idn.map((id) => ({ id: id, opacity: opacitet })));
  }

  function markeraKedjan(kedja, fokusId) {
    // Kanten in till varje nod i kedjan, plus kanten in till den fokuserade
    // noden själv -- annars slutar spåret ett steg för tidigt.
    const noderIKedjan = kedja.concat([fokusId]);
    const uppdateringar = [];
    for (const kant of edges.get()) {
      const iKedjan =
        noderIKedjan.includes(kant.to) && kantensForalder.get(kant.to) === kant.from;
      uppdateringar.push({
        id: kant.id,
        color: { color: iKedjan ? JOK_GRAFKONFIG.kedjefarg : JOK_GRAFKONFIG.kantfarg },
        width: iKedjan ? JOK_GRAFKONFIG.kedjebredd : 1,
      });
    }
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
    satOpacitet(
      noder.map((n) => n.id),
      1,
    );
    markeraKedjan([], null);
    network.fit({ animation: { duration: JOK_GRAFKONFIG.animeringMs } });
  }
```

- [ ] **Step 2: Route clicks to focus or to lagen.nu**

Ersätt den befintliga `network.on("click", ...)`-handlern med:

```javascript
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
```

- [ ] **Step 3: Make structure nodes look clickable**

Byt `hoverNode`-handlern så att alla noder utom roten får handmarkören:

```javascript
  network.on("hoverNode", function (params) {
    const nod = nodes.get(params.node);
    const klickbar = Boolean(nod && (nod.url || nod.foralder));
    container.style.cursor = klickbar ? "pointer" : "default";
  });
```

- [ ] **Step 4: Verify nothing regressed in pytest**

Run: `python3.11 -m pytest tests/test_taxonomi_ui.py -q`
Expected: PASS. `test_klickhanterare_oppnar_ny_flik` letar efter `network.on("click"` och `window.open(nod.url`, båda finns kvar.

- [ ] **Step 5: Commit**

```bash
git add utils/static/taxonomigraf.js
git commit -m "feat: fokusera grenen vid klick och markera vägen från roten"
```

---

### Task 6: Zoomgolv, återställningsknapp och Escape

**Files:**
- Modify: `utils/static/taxonomigraf.js`, `utils/taxonomi_ui.py` (`bygg_html`, knappens markup)
- Test: `tests/test_taxonomi_ui.py`

**Interfaces:**
- Consumes: `aterstall()` (Task 5), `JOK_GRAFKONFIG.minSkalaFaktor` (Task 2).
- Produces: knappen `#jok-aterstall-vy` i grafcontainern.

- [ ] **Step 1: Write the failing test**

```python
def test_overlayknappen_finns_i_grafen(html):
    assert "jok-aterstall-vy" in html
    assert "Återställ vyn" in html


def test_overlayknappen_ligger_inuti_grafcontainern(html):
    """Knappen ska följa med grafens ram, inte flyta ovanpå sidan."""
    assert html.index('id="taxonomigraf"') < html.index("jok-aterstall-vy")
```

- [ ] **Step 2: Run to verify failure**

Run: `python3.11 -m pytest tests/test_taxonomi_ui.py -k overlay -v`
Expected: FAIL, strängen saknas.

- [ ] **Step 3: Add the button markup**

I `bygg_html`, byt containerdiven mot en positionerad omslutning med knappen inuti. Färgerna följer `design_system.md`:

```python
    return f"""
<div style="position:relative;">
  <div id="taxonomigraf" style="height:{hojd}px;border:1px solid #E5E0D8;
       border-radius:8px;background:#FFFFFF;"></div>
  <button id="jok-aterstall-vy" type="button" hidden
          title="Visa hela kartan igen (Esc)"
          style="position:absolute;top:12px;right:12px;padding:.4rem .7rem;
                 background:#FFFFFF;border:1px solid #E5E0D8;border-radius:8px;
                 color:#2C5F8A;font-family:serif;font-size:14px;cursor:pointer;">
    ↺ Återställ vyn
  </button>
</div>
"""
```

`hidden` är avsiktligt: knappen visas först när vis-network laddat, så att den inte står kvar och lovar interaktivitet i CDN-fallbacken.

- [ ] **Step 4: Wire the button, Escape and the zoom floor**

I `utils/static/taxonomigraf.js`, direkt efter att `network` skapats:

```javascript
  // Knappen är dold i markupen och visas först här, så att den aldrig lovar
  // interaktivitet i fallbacken där vis-network saknas.
  const aterstallKnapp = document.getElementById("jok-aterstall-vy");
  aterstallKnapp.hidden = false;
```

och efter `aterstall`-definitionen:

```javascript
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
```

- [ ] **Step 5: Run tests, lint and typecheck**

Run: `python3.11 -m pytest -q && node --test tests/js/ && ruff check . && mypy --ignore-missing-imports utils`
Expected: allt grönt.

- [ ] **Step 6: Commit**

```bash
git add utils/static/taxonomigraf.js utils/taxonomi_ui.py tests/test_taxonomi_ui.py
git commit -m "feat: zoomgolv och återställningsknapp i kartan"
```

---

### Task 7: Flytta filtrens återställning till de flikar som äger dem

Knappen ovanför flikraden tömmer nycklar som hör till Falltypsguide och Nyckelbegrepp. På fliken Systemet ser den ut att inte göra någonting. Den delas i två, en per flik.

**Files:**
- Modify: `sidor/16_Rattskartan.py:77-87` (ta bort), `sidor/16_Rattskartan.py:145-158` (Falltypsguide), `sidor/16_Rattskartan.py:286-303` (Nyckelbegrepp)
- Test: `tests/test_rattskartan_sida.py`

**Interfaces:**
- Consumes: inget från tidigare uppgifter.
- Produces: inget som senare uppgifter läser.

- [ ] **Step 1: Write the failing tests**

Lägg till i `tests/test_rattskartan_sida.py`:

```python
def test_ingen_sidovergripande_aterstallningsknapp(sida):
    """Kartans vy återställs i iframen; sidknappen rörde bara filtren."""
    etiketter = [k.label for k in sida.button]
    assert "↺ Återställ" not in etiketter


def test_varje_filterflik_har_sin_egen_rensningsknapp(sida):
    etiketter = [k.label for k in sida.button]
    assert "↺ Rensa sökningen" in etiketter
    assert "↺ Rensa filtren" in etiketter
```

- [ ] **Step 2: Run to verify failure**

Run: `python3.11 -m pytest tests/test_rattskartan_sida.py -k "aterstallning or rensning" -v`
Expected: FAIL, `"↺ Återställ" not in etiketter` slår, och de två nya saknas.

- [ ] **Step 3: Remove the page-level block**

Ta bort raderna 77 till 87 i `sidor/16_Rattskartan.py` (kommentaren, `_RESET_NYCKLAR`, kolumnerna och knappen). Flikraden ska följa direkt efter `render_sidhjalp(...)`.

- [ ] **Step 4: Add the Falltypsguide button**

I `with flik_falltyp:`, direkt efter `fras = st.text_input(...)`:

```python
    # Rensar bara den här flikens sökruta. Kartans vy återställs i grafen,
    # med knappen i dess övre högra hörn.
    if st.button("↺ Rensa sökningen", help="Töm sökrutan ovan."):
        st.session_state.pop("falltyp_sok", None)
        st.rerun()
```

- [ ] **Step 5: Add the Nyckelbegrepp button**

I `with flik_begrepp:`, direkt efter kolumnblocket som bygger `sokfras` och `valt_omrade`:

```python
    if st.button("↺ Rensa filtren", help="Töm sökrutan och områdesfiltret."):
        for _nyckel in ("begrepp_sok", "begrepp_omrade"):
            st.session_state.pop(_nyckel, None)
        st.rerun()
```

Knapparna får medvetet ingen `key`: `test_varje_begrepp_far_sin_egen_tutorknapp` räknar nycklade knappar och förutsätter att återställningsknappar saknar nyckel.

- [ ] **Step 6: Update the stale comment in the existing test**

I `tests/test_rattskartan_sida.py`, i `test_varje_begrepp_far_sin_egen_tutorknapp`, byt kommentaren:

```python
    # En nycklad tutorknapp per begrepp. Flikarnas rensningsknappar saknar
    # nyckel och räknas därför inte in här.
```

- [ ] **Step 7: Run the page suite**

Run: `python3.11 -m pytest tests/test_rattskartan_sida.py -q`
Expected: PASS, alla.

- [ ] **Step 8: Commit**

```bash
git add sidor/16_Rattskartan.py tests/test_rattskartan_sida.py
git commit -m "fix: flytta filtrens återställning till de flikar som äger dem"
```

---

### Task 8: Verifiering i webbläsaren och omkörningsrisken

DOM-beteendet kan inte testas i CI (offline, ingen CDN). Det verifieras därför mot appen som körs, och den kända risken i specen undersöks och rapporteras.

**Files:**
- Modify: `APPGUIDE.md` (avsnittet om Rättskartan), `docs/superpowers/specs/2026-08-05-rattskartan-interaktion-design.md` (statusraden)

**Interfaces:**
- Consumes: allt ovan.
- Produces: inget kodmässigt.

- [ ] **Step 1: Start the app**

```bash
cd /Users/Brook/Downloads/juridik_oversiktskurs
streamlit run streamlit_app.py --server.port 8517 --server.headless true
```

- [ ] **Step 2: Walk the checklist on the Systemet tab**

Gå igenom och notera utfallet för var och en:

1. Klicka `Förmögenhetsrätt` → grenen centreras och är skarp; kedjan `Svensk rätt → Civilrätt → Förmögenhetsrätt` är skarp med fetare guldkant; övrigt är nedtonat.
2. Klicka en guldnod → lagen.nu öppnas i ny flik; fokus ändras inte.
3. Klicka tom yta → allt återgår.
4. Klicka roten `Svensk rätt` → samma som återställning.
5. Zooma ut med hjulet → det går inte längre ut än att hela trädet syns.
6. `↺ Återställ vyn` och `Escape` → båda återställer utan att sidan laddas om.
7. Fokusera ett delområde utan undergrenar → det förstoras men fyller inte hela rutan.

- [ ] **Step 3: Verify the CDN fallback still works**

Kör appen med nätverket blockerat för `unpkg.com` (eller ändra `_VIS_NETWORK_CDN` tillfälligt till en ogiltig URL) och bekräfta:
- texten "Kunde inte ladda grafbiblioteket" visas
- `↺ Återställ vyn` syns **inte** (knappen är `hidden` tills vis laddat)
- inga JS-fel i konsolen

Återställ URL:en efteråt.

- [ ] **Step 4: Investigate the rerun risk**

Fokusera en gren, gå till fliken Falltypsguide, skriv i sökrutan (vilket kör om skriptet), gå tillbaka till Systemet. Notera om fokus och zoom överlevde.

Rapportera utfallet i klartext. Åtgärda **inte** inom detta omfång, specen har det som känd risk. Blev svaret "nollställs", lägg till en rad om det under "Känd risk" i specen.

- [ ] **Step 5: Update the documentation**

I `APPGUIDE.md`, i avsnittet om Rättskartan, beskriv den nya interaktionen: klick fokuserar, guldnoder öppnar lagen.nu, `↺ Återställ vyn` och `Escape` återställer, utzoomningen har ett golv. Sätt specens statusrad till `Genomförd 2026-08-05` med commit-spannet.

- [ ] **Step 6: Full gate run**

```bash
python3.11 -m pytest -q
node --test tests/js/
ruff check .
mypy --ignore-missing-imports utils
```
Expected: alla fyra gröna. Kör ruff och mypy med de pinnade versionerna (0.16.1 / 2.3.0), lokal drift är precis vad som sänkte CI tidigare.

- [ ] **Step 7: Commit**

```bash
git add APPGUIDE.md docs/superpowers/specs/2026-08-05-rattskartan-interaktion-design.md
git commit -m "docs: beskriv Rättskartans grafinteraktion och stäng specen"
```
