# Designspec: Alternativa sätt att ange lagrum i lagrumsjakten

Datum: 2026-08-06
Status: godkänd design (brainstorming)

## Bakgrund

Lagrumsjakten (och Normfältets direktfeedback) rättas deterministiskt via
`utils.lagrum.extrahera_lagrum` + `validera_lagrum`, delade av alla
modulsidor via `utils/modulvy.py` och `utils.quiz.ratta_lagrumsjakt`.
Matchningen känner i dag bara igen registrets kanoniska förkortningar
(skiftlägesokänsligt, båda ordningarna `"36 § AvtL"`/`"AvtL 36 §"`). En
student som korrekt skriver `"36 § avtalslagen"` eller
`"1 kap. 1 § brottsbalken"`, det normala sättet svenska juriststudenter
faktiskt talar och skriver om lagarna, får svaret bedömt som fel, trots att
det är rätt lagrum.

Undersökt samtidigt (informativt, ingen kodändring): modulernas
sakrättsliga sidor (Avtalsrätt, Köp och konsumenträtt, Straff och
processrätt m.fl.) är avsiktligt smalt avgränsade till sin egen lagfamilj
(`AvtL`; `KöpL`/`KKöpL`; `BrB`+`RB`). Juridisk metod är undantaget: dess
rättsfall, quiz och lagrumsjakt spänner medvetet över flera rättsområden
(`KöpL`, `BrB`, `AvtL`, `RB`) eftersom modulen undervisar rättskälleläran
som metod, inte ett enskilt rättsområdes sakinnehåll. Ingen ändring behövs
här, det är redan rätt avvägt för respektive moduls syfte.

## Mål

- Lagrumsjakten (och Normfältets feedback) ska bedöma ett svar som rätt
  oavsett om studenten skriver den kanoniska förkortningen, lagens fulla
  vardagliga namn, eller en etablerad alternativ förkortning, i valfritt
  skiftläge och i båda ordningarna (`N § X` / `X N §`).
- Databasen för godkända alias ska vara explicit och granskningsbar, inte
  grammatiskt härledd, så att framtida lagar med oregelbundna namn inte kan
  ge tysta felmatchningar.
- Data med kolliderande alias (två lagar som råkar dela ett alias, eller ett
  alias som krockar med en annan lags förkortning) ska stoppa appen vid
  inläsning (fail fast), inte ge en tyst felaktig matchning i produktion.

## Icke-mål

- SFS-nummer som lagrumsreferens (t.ex. `"36 § 1915:218"`), inte hur
  studenter faktiskt skriver svar i en lagrumsjakt.
- Att ändra hur paragrafintervall (`paragraf_till`) jämförs i
  `ratta_lagrumsjakt`, ett separat, redan existerande beteende som inte
  rör aliasmatchning.
- Automatisk grammatisk härledning av bestämd form (`balk`→`balken`,
  `lag`→`lagen`). Se motivering nedan.

## Design

### 1. Datamodell: `aliaser` per lag i `data/lagrum.json`

Varje lagpost i `lagrum.json` får ett nytt, valfritt fält `"aliaser"`: en
lista strängar med lagens fulla vardagliga namn och eventuella etablerade
alternativa förkortningar. Listan är **manuellt författad**, inte härledd
från `namn`-fältet.

Skälet till att inte härleda automatiskt: mönstret `X-lag → X-lagen` /
`X-balk → X-balken` håller för 15 av registrets 21 lagar, men 6 är
registrerade under en `"Lag om …"`-titel utan mekanisk väg till det
vardagliga namnet (`AvtL` → "avtalslagen" går inte att härleda ur "Lag om
avtal och andra rättshandlingar på förmögenhetsrättens område"). En enda
explicit lista undviker en skör svensk grammatiktransformator och håller
varje godkänt alias synligt och granskningsbart i datafilen, samma princip
som `kursavsnitt`-gränserna redan följer (explicita, Riksdagen-verifierade,
inte gissade).

Fullständig aliastabell för de 21 lagarna (fulla namn verifierade mot
gängse juridisk källa; `KKL` och `PreskrL` är etablerade alternativa
förkortningar, inte bara fulla namn):

| Förkortning | Aliaser |
|---|---|
| AvtL | avtalslagen |
| SkbrL | skuldebrevslagen |
| ÄB | ärvdabalken |
| BrB | brottsbalken |
| JB | jordabalken |
| SkL | skadeståndslagen |
| HBL | handelsbolagslagen |
| UB | utsökningsbalken |
| LAS | anställningsskyddslagen |
| KonkL | konkurslagen |
| ÄktB | äktenskapsbalken |
| KöpL | köplagen |
| FB | föräldrabalken |
| RB | rättegångsbalken |
| SamboL | sambolagen |
| ABL | aktiebolagslagen |
| MFL | marknadsföringslagen |
| KKöpL | konsumentköplagen, KKL |
| GFL | godtrosförvärvslagen |
| LFF | framtidsfullmaktslagen |
| PreskL | preskriptionslagen, PreskrL |

### 2. Matchning: `utils/lagrum.py`

`_forkortning_gemener_karta()` byggs om till att, utöver
`forkortning.lower() -> forkortning`, även indexera varje
`alias.lower() -> forkortning`. Samma karta används redan av
`_normalisera_forkortning` (skiftlägesnormalisering) och av
`_godtagen`/`extrahera_lagrum` (accepterar kanoniska/omvända träffar vars
förkortning är "känd"). Ingen regexändring krävs: svenska lagnamn är ett
enda ord, så `"avtalslagen"`/`"brottsbalken"` fångas redan av det
befintliga fånget `[A-Za-zÅÄÖåäö]+` i både `LAGRUM_PATTERN` och
`LAGRUM_PATTERN_OMVAND`.

Ny valideringsregel vid registerinläsning (`lagrum_register()` eller en
hjälpfunktion den anropar): bygg aliaskartan och kasta `ValueError` om
- ett alias (skiftlägesokänsligt) redan är en annan lags förkortning, eller
- två lagar delar samma alias.

Detta följer samma fail-fast-princip som `_validera_ra_lag` redan
tillämpar på saknade fält och icke-numeriska paragrafer.

### 3. UI och rapportering

Inga ändringar. `Lagrumsref.forkortning` normaliseras redan till den
kanoniska förkortningen oavsett vilket alias som matchade, så
`lagen_nu_url`, `validera_lagrum` och chip-rendering fortsätter fungera
omodifierat. Studentens råtext (`Lagrumsref.ra`) bevaras redan och visas
oförändrad i Normfältets direktfeedback, ett svar skrivet som
`"36 § avtalslagen"` visas alltså som studenten skrev det, med grön chip.

## Testning

`tests/test_lagrum.py`:
- `extrahera_lagrum`/`validera_lagrum` känner igen fullt namn i båda
  ordningarna (`"36 § avtalslagen"`, `"avtalslagen 36 §"`) och godtyckligt
  skiftläge.
- Alternativa förkortningar `KKL` → `KKöpL` och `PreskrL` → `PreskL`
  normaliseras och valideras korrekt.
- Kapitelindelade lagar (t.ex. `"1 kap. 1 § brottsbalken"`) matchar samma
  kursavsnitt som `"1 kap. 1 § BrB"`.
- Registerinläsning kastar `ValueError` vid ett konstruerat kolliderande
  alias (testdata, inte den riktiga registerfilen).

`tests/test_quiz.py`:
- `ratta_lagrumsjakt` bedömer ett svar skrivet med fullt namn som rätt när
  facit är angivet som förkortning, och omvänt.

## Risker / avgränsningar

- Listan är inte uttömmande för alla tänkbara talspråkliga varianter
  (t.ex. skämtsamma eller regionala smeknamn), omfånget är etablerade
  namn/förkortningar, i linje med målet ovan.
- Om en framtida lag läggs till i registret måste dess aliaser författas
  manuellt; detta är en avsedd avvägning (se "Icke-mål").
