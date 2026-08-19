# Rättskartans grafinteraktion: fokus, zoomgolv och återställning

**Datum:** 2026-08-05
**Status:** Genomförd 2026-08-05 (commit 4d2e57a,HEAD). Samtliga komponenter finns
och hela checklistan är verifierad i webbläsaren. Två avvikelser mot designen:
grafinstansen exponeras som `window.jokTaxonomigraf` (grafen ritas på en canvas
och har ingen DOM att klicka på utifrån, så vyn gick annars inte att verifiera),
och skiktlogiken laddas i testet med `new Function` i stället för `node:vm` ,
en vm-sandlåda är ett eget realm vars arrayer `deepStrictEqual` underkänner.
**Omfång:** Taxonomigrafen på Rättskartans flik "Systemet" och sidans
återställningsknapp. Rör inte grafens data, färgsättning eller de tre flikarnas
övriga innehåll.

## Problem

Tre saker på Rättskartan arbetar mot studenten.

1. **Återställningsknappen sitter på fel sak.** Knappen `↺ Återställ`
   (`sidor/16_Rattskartan.py:81 till 87`) ligger ovanför flikraden och tömmer
   `falltyp_sok`, `begrepp_sok` och `begrepp_omrade`, nycklar som hör till
   flikarna **Falltypsguide** och **Nyckelbegrepp**. Studenten som står på fliken
   **Systemet** och tittar på kartan ser alltså en återställningsknapp som inte gör
   någonting synligt. Knappen är inte trasig; den är placerad ovanför ett innehåll
   den inte styr.

2. **Kartan går inte att fokusera.** Grafen renderar hela taxonomin samtidigt: rot,
   två toppgrenar, 31 delområden och samtliga lagnoder. Det enda klicket som gör
   något är på en guldfärgad lagnod, som öppnar lagen.nu
   (`utils/taxonomi_ui.py:146 till 152`). Strukturnoderna är uttryckligen inerta. Vill
   studenten studera förmögenhetsrätten finns ingen väg dit annat än att panorera
   och zooma för hand.

3. **Utzoomningen är obegränsad.** `vis.Network` saknar globalt zoomtak, och inget
   sätts i optionsobjektet (`utils/taxonomi_ui.py:127 till 141`). Studenten kan zooma ut
   tills hela trädet är en oläslig prick i mitten av rutan och måste då
   ladda om sidan för att komma tillbaka.

## Mål

Gör kartan till ett navigerbart studieverktyg: klicka på ett rättsområde för att
fokusera det, se kedjan ned från roten dit, kom aldrig längre ut än att helheten
syns, och ta dig tillbaka till utgångsläget med ett klick, allt utan att sidan
laddas om.

## Tekniska förutsättningar

Tre fakta ur koden och ur vis-network 9.1.9 (bundeln nedladdad och granskad
2026-08-05) styr designen:

- **Grafen lever i en sandboxad iframe.** `render_taxonomigraf` renderar via
  `components.html` (`utils/taxonomi_ui.py:169`). Streamlit kan skicka data **in**
  men tar inte emot något **ut**. All interaktion måste därför vara JavaScript
  inuti iframen. Fördelen: den blir omedelbar och kräver ingen `st.rerun()`.
- **`opacity` är en riktig nodoption.** Den ligger i nodens defaultobjekt och
  returneras av `getFormattingValues`. Nedtoning blir alltså ett
  `nodes.update({id, opacity})` och kräver ingen färgväxling.
- **Det finns inget globalt zoomtak.** `minZoom`/`maxZoom` existerar enbart som
  argument till `fit()` (som `minZoomLevel`/`maxZoomLevel`), inte som
  interaktionsoptioner. Ett golv måste klampas i `zoom`-händelsen.

## Valda beslut

- **Nedtoning, inte bortfiltrering.** Vid fokus ligger övriga noder kvar nedtonade
  i stället för att tas ur `DataSet`. Studenten behåller känslan av var grenen
  sitter, och återställningen blir en toning i stället för en ombyggnad av grafen.
- **Förfäderna är skarpa, inte nedtonade.** Kedjan rot → fokuserad nod visas i full
  opacitet med fetare guldkant på kanterna. Alternativet, att tona ned även
  förfäderna, valdes bort: sidans hela pedagogiska poäng är systematiken, och
  kedjan `Svensk rätt → Civilrätt → Förmögenhetsrätt` är just den.
- **Lagnoder behåller sitt klick.** Guldnoder är löv och har ingenting att zooma in
  i, så de öppnar lagen.nu precis som förut. Dubbelklick som ny idiom valdes bort:
  det är osynligt för studenten och ändrar ett beteende som redan är inlärt.
- **Zoomgolvet härleds, inte hårdkodas.** Golvet sätts till skalan efter den
  första `fit()` gånger 0,9. Det följer med containerns bredd och trädets
  storlek; ett hårdkodat `0.3` hade ruttnat så fort grafen växte.
- **Inget zoomtak för handzoomning inåt.** Att förstora en gren är hela poängen.
  Den automatiska fokuseringen har däremot ett tak, annars fyller en ensam nod
  hela rutan (se gränsfallen nedan).
- **Två knappar, inte en.** Kartans återställning och filtrens återställning är
  olika saker och hamnar därför på olika ställen.
- **JavaScripten flyttar till en egen fil.** `bygg_html` är redan en f-sträng på
  ~55 rader med dubblerade klammerparenteser. Att lägga fokus, nedtoning, klampning
  och kedjemarkering där hade fördubblat den och gjort varje `{` till en fälla.

## Komponenter

### `utils/static/taxonomigraf.js` (ny)

Interaktionslagret som riktig JavaScript, inläst vid byggtid och injicerad i
HTML-strängen. Ansvar:

- `fokusera(nodId)`, dela noderna i tre skikt (se nedan), sätt opacitet, markera
  förfäderskedjans kanter och kör `network.fit()` över den fokuserade grenen.
- `aterstall()`, återställ opacitet och kantbredd, `network.fit()` över allt.
- Zoomklampning i `network.on("zoom")`.
- Klickrouting: nod med `url` → öppna, strukturnod → `fokusera`, tom yta →
  `aterstall`.
- `Escape` bunden till `aterstall`.

Filen tar emot sin konfiguration (opacitetsnivå, färger, animeringstid) från ett
`JOK_GRAFKONFIG`-objekt som Python skriver ut före `<script>`-taggen. Inga
hårdkodade värden i JS:en.

### `utils/rattssystem_graf.py` (ändras)

`TaxNod` får ett fält: **`foralder: str`**, förälderns nod-id, tom sträng för
roten. `bygg_taxonomigraf` sätter det när den ändå bygger kanten.

Alternativet att skicka färdiga förfäderslistor och ättlingslistor per nod valdes bort:
varje nod hade då burit sitt eget delträd och JSON-nyttolasten vuxit kvadratiskt.
Med en förälder per nod härleder JS:en kedjan uppåt med en `while`-loop och
ättlingarna genom att invertera föräldrakartan en gång vid laddning.

Att fältet räknas ut i Python och inte parsas ur kantlistan i JS är medvetet: här
finns pytest, och `tests/test_rattssystem_graf.py` vaktar redan trädinvarianten.

### `utils/taxonomi_ui.py` (ändras)

`bygg_html` krymper till sitt egentliga uppdrag: serialisera noder och kanter,
skriva ut konfigurationsblocket, bädda in JS-filen och rita containern plus
overlay-knappen. `_vis_noder` skickar med `foralder`.

### `sidor/16_Rattskartan.py` (ändras)

Blocket på rad 77 till 87 tas bort. I stället får `flik_falltyp` och `flik_begrepp`
var sin egen knapp som bara rör sina egna nycklar.

## De tre skikten

| Skikt | Noder | Opacitet | Kanter |
|---|---|---|---|
| Fokus | Fokuserad nod + alla ättlingar | 1,0 | normala |
| Kedja | Förfäder rot → fokuserad nod | 1,0 | fetare, guld |
| Bakgrund | Alla övriga | 0,15 | nedtonade |

Utgångsläget (ingen fokusering) är allt i skikt "fokus": oförändrat mot i dag.

Tre gränsfall, uttryckligen bestämda:

- **Roten (`Svensk rätt`).** Alla noder är dess ättlingar, så fokus på roten är per
  definition utgångsläget. Klick på roten anropar därför `aterstall()`.
- **Redan fokuserad nod.** Klick på den nod som redan är fokuserad kör om samma
  fokusering (idempotent), vilket i praktiken centrerar om grenen. Den växlar
  alltså inte tillbaka, det gör tom yta, knappen och `Escape`.
- **Löv utan ättlingar bland strukturnoderna.** Ett delområde utan undergrenar och
  utan lagar fokuseras på sig självt. `fit()` över en ensam nod skulle annars
  förstora den absurt, zoomgolvet hjälper inte, det hindrar bara utzoomning. Här
  används därför `fit()`:s eget `maxZoomLevel`-argument som tak på fokuseringen.

## Kartans återställningsknapp

En `↺ Återställ vyn`-knapp absolutpositionerad i grafcontainerns övre högra hörn,
inuti iframen. Den anropar `aterstall()` direkt, ingen `st.rerun()`, ingen
sidladdning, ingen blinkning. Knappen ligger i samma DOM som canvasen och följer
därför med grafens ram.

Stil enligt `design_system.md`: vit botten, `#E5E0D8` kant, radie 8 px,
`#2C5F8A` text.

## Filtrens återställningsknappar

- **Falltypsguide:** `↺ Rensa sökningen`, tömmer `falltyp_sok`.
- **Nyckelbegrepp:** `↺ Rensa filtren`, tömmer `begrepp_sok` och `begrepp_omrade`.

Var och en återställer bara sin egen flik, så etiketten motsvarar äntligen
effekten. Båda behåller `st.rerun()`, som är rätt mekanism för Streamlit-tillstånd.

## Felhantering

Grafen har redan en CDN-fallback: laddas inte vis-network skrivs en förklarande
ruta ut och områdesträdet under grafen fungerar ändå
(`utils/taxonomi_ui.py:118 till 124`). Den vägen får inte brytas, overlay-knappen ritas
därför bara när `vis` finns. Saknas `utils/static/taxonomigraf.js` vid inläsning
ska `bygg_html` höja ett tydligt fel vid uppstart snarare än att rendera en trasig
graf.

## Testning

Python-sidan, i pytest:

- varje nod bär `foralder`; värdet stämmer mot kantlistan; endast roten har tom
  sträng
- `bygg_html` bäddar in JS-filen, konfigurationsblocket och overlay-knappen
- fliken Systemet renderar ingen sidövergripande återställningsknapp; de två andra
  flikarna renderar var sin
- befintliga trädtester, färgtester och lagkortstester fortsätter passera

**Inget webbläsartest i CI, medvetet.** CI kör offline (se `.github/workflows/ci.yml`)
och grafen hämtar vis-network från CDN; offline renderas fallbacktexten by design.
Ett Playwright-test av fokus och zoom hade fallit i CI av skäl som inte har med
koden att göra.

JS-beteendet verifieras i stället manuellt mot appen som körs, enligt denna lista:

1. Klicka `Förmögenhetsrätt` → grenen centreras och skärps, kedjan från
   `Svensk rätt` är skarp med fetare kant, övrigt är nedtonat.
2. Klicka en guldnod → lagen.nu öppnas i ny flik, fokus ändras inte.
3. Klicka tom yta → allt återgår.
4. Zooma ut med hjulet → det går inte att komma längre ut än att hela trädet syns.
5. `↺ Återställ vyn` och `Escape` → båda återställer, sidan laddas inte om.
6. Ladda vis-network-CDN:en avstängd → fallbacktexten visas, ingen JS-krasch.

## Känd risk att undersöka, avskriven 2026-08-05

Farhågan var att Streamlit monterar om iframen vid varje omkörning, så att fokus
och zoom nollställs när studenten skriver i en annan fliks sökruta.

**Den inträffar inte.** Uppmätt: en markör sattes på `window` inuti iframen, en
gren fokuserades, sökrutan i Falltypsguide fylldes i och kördes (omkörningen
bekräftad genom att värdet slog igenom), och därefter lästes grafen om. Markören
hade samma värde och fokusläget var oförändrat (skala 1,0 och 24 nedtonade noder
före och efter). Streamlit återanvänder alltså iframen när HTML:en är oförändrad.
Ingen åtgärd behövs.

## Utanför omfånget

Valdes bort denna omgång:

- fälla ihop lagnoderna tills grenen fokuseras
- klickbar brödsmula ovanför grafen
- sökruta som hoppar till en nod i kartan
- zoomtak inåt
- åtgärd av omkörningsrisken ovan
