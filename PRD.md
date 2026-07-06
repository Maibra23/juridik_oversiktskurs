# PRD: Juridisk översiktskurs, LLM driven lärplattform

Version 1.0. Språk: svenska. Referensarkitektur: Ekonomistyrning Sandbox (Maibra23/ekonomistyrning).

## 1. Problem och syfte

Studenter på Juridisk översiktskurs (JÖK) möter en mycket bred kursbok (Persson m.fl., Svensk juridik, ca 600 sidor och 22 kapitel) men examineras främst på förmågan att tillämpa juridisk metod på konkreta scenarier. Problemet är inte brist på material utan brist på träning i att *tänka* juridiskt: identifiera rättsfrågan, hitta rätt lagrum, tillämpa normen på fakta och dra en slutsats. Utan sådan träning läser studenter passivt och underpresterar på tentans fallfrågor.

Syftet med appen är att ge fallbaserad träning med en LLM tutor som förklarar och kvalitetssäkrar användarens egna resonemang, med fokus på de 20 procent av innehållet som ger 80 procent av tentanyttan.

## 2. Målgrupp

* Primär: studenter på Juridisk översiktskurs vid svenska universitet och högskolor.
* Sekundär: yrkesverksamma som behöver en juridisk orientering (ekonomer, HR, entreprenörer).

## 3. Mål

* En student ska kunna genomföra ett komplett scenario (fall, analys, feedback) på under 15 minuter.
* Minst 80 procent av tutorsvaren ska innehålla korrekta lagrumsreferenser som passerar appens verifiering.
* Quizresultat per modul ska förbättras mätbart mellan första och andra försöket (målsatt medianökning: 20 procentenheter).
* Noll okontrollerade LLM kostnader: sessionstak och dagligt tak får aldrig kunna kringgås från UI.

## 4. Icke mål (avgränsningar)

* Ingen juridisk rådgivning för verkliga fall. Appen är ett studieverktyg, inte en rättstjänst. En tydlig disclaimer visas.
* Ingen fulltextsökning i hela lagen.nu. Appen länkar till specifika lagrum och validerar dem, men bygger inte en egen rättsdatabas.
* Inga användarkonton eller server side persistens av studieresultat i v1 (framsteg sparas i session och kan exporteras). Skälet är tidsramen på tre dagar.
* Ingen täckning av samtliga 22 kapitel i v1. Endast Paretourvalet (se 5.1). Övriga kapitel är P2.
* Ingen finjustering (fine tuning) av modellen. All juridisk styrning sker via promptar och verifiering.

## 5. Funktionella krav

### 5.1 Moduler (Paretourvalet, P0)

Urvalet bygger på bokens innehållsförteckning och vad som typiskt examineras med fallfrågor på JÖK:

1. **Juridisk metod och rättskällor** (kap 1): rättskälleläran, lagtolkning, RNTS strukturen. Grunden för allt annat.
2. **Avtalsrätt** (kap 7): anbud och accept, fullmakt (behörighet mot befogenhet), ogiltighet, 36 § AvtL.
3. **Köprätt** (kap 8): KöpL mot KKöpL, dröjsmål, fel, påföljder, reklamation.
4. **Skadeståndsrätt** (kap 10): culparegeln, adekvat kausalitet, principalansvar, ren förmögenhetsskada.
5. **Arbetsrätt** (kap 11): anställningsformer, uppsägning mot avsked (LAS), diskriminering.
6. **Associationsrätt** (kap 12): bolagsformer, personligt ansvar, aktiebolagets organisation.
7. **Familjerätt och successionsrätt** (kap 18 till 21): giftorättsgods mot enskild egendom, bodelning, arvsordning, laglott, testamente, särkullbarn.
8. **Straffrätt och processrätt** (kap 22): brottsbegreppets objektiva och subjektiva sida, uppsåt mot oaktsamhet, ansvarsfrihetsgrunder.

P1 moduler: Fastighetsrätt (kap 9), Fordringsrätt (kap 15). P2: övriga kapitel.

### 5.2 Scenariotyper (P0)

* **Rättsfall (case)**: ett scenario i löptext, användaren skriver sin analys enligt RNTS i fyra fält (rättsfråga, norm, tillämpning, slutsats). Tutorn bedömer varje steg.
* **Flervalsfrågor (MC)**: 6 till 10 frågor per modul med deterministisk rättning i appen och valfri LLM förklaring per fråga.
* **Lagrumsjakt**: användaren ska ange vilket lagrum som reglerar en given situation. Appen validerar mot en intern lagrumsdatabas.
* **Kort essä** (P1): fri text med tutorbedömning mot en facitchecklista.

### 5.3 LLM tutor (P0)

* Modell: Qwen (Qwen/Qwen3-8B som standard, Qwen/Qwen3-14B som alternativ) via Hugging Face Inference Providers, samma mönster som referensrepot.
* Tutorn följer alltid RNTS strukturen: Rättsfrågan, Norm, Tillämpning, Slutsats.
* Tutorn refererar till lagrum i standardformat (t.ex. "36 § AvtL", "2 kap. 18 § ÄktB") och appen renderar dem som klickbara länkar till lagen.nu.
* Tutorn förklarar användarens *egna* inmatningar, den löser inte scenariot åt användaren förrän användaren själv lämnat ett försök.
* Generering sker endast på explicit knapptryck, aldrig automatiskt vid rerun (mönstret från utils/tutor.py i referensrepot).

### 5.4 Hallucinationsskydd (P0)

Detta är den juridiska motsvarigheten till referensrepots sifferverifiering (verify_grounding):

* Systemprompten förbjuder påhittade lagar, paragrafer och rättsfall och kräver formatet "N § Lagförkortning" alternativt "N kap. M § Lagförkortning".
* Appen extraherar alla lagrumsreferenser ur LLM svaret med regex och kontrollerar varje referens mot data/lagrum.json, en intern vitlista med kursens relevanta lagar, kapitel och paragrafintervall.
* Referenser som inte kan verifieras markeras visuellt med en varning ("Kunde inte verifieras mot kursens lagrumslista, kontrollera själv på lagen.nu") i stället för att tyst visas som fakta.
* Rättsfall (NJA referenser) visas alltid med varningstext i v1 eftersom de inte kan valideras lokalt.

### 5.5 Budgetskydd (P0)

* Sessionstak: max 40 LLM anrop per session (st.session_state räknare).
* Dagligt tak: filbaserad räknare delad mellan alla sessioner, standard 300 anrop per dag, ej återställbar från UI (mönstret från utils/llm_budget.py).
* Vid uppnått tak fungerar all deterministisk funktionalitet (rättning, quiz, länkar, export) som vanligt och en vänlig svensk infokort visas.
* Svarscache: identiska förfrågningar (hash av prompt och inputs) återanvänder tidigare svar utan nytt anrop.

### 5.6 lagen.nu integration (P0)

* Varje lagrum i data/lagrum.json innehåller en färdig URL till lagen.nu (t.ex. https://lagen.nu/1915:218#P36 för 36 § AvtL).
* UI komponenten render_lagrum visar paragrafen som en klickbar chip med lagens namn som tooltip.
* Ingen skrapning av lagen.nu i runtime i v1 (prestanda och robusthet), endast kuraterade länkar. En valfri "kontrollera online" funktion (HTTP HEAD mot URL) är P1.

### 5.7 Export och uppföljning (P1)

* Export av quizresultat och genomförda scenarier till Excel eller Markdown.
* Enkel framstegsvy per modul (andel klarade scenarier, senaste quizresultat).

## 6. Icke funktionella krav

* **Språk**: allt användarinnehåll, alla promptar och all dokumentation på svenska.
* **Prestanda**: deterministiska vyer renderas under 1 sekund, LLM svar streamas.
* **Robusthet**: appen ska vara fullt användbar utan LLM (fallbacktexter och deterministisk rättning). LLMUnavailableError fångas alltid.
* **Säkerhet**: HF token endast i st.secrets eller miljövariabel, aldrig i repo. Inga personuppgifter lagras.
* **Kvalitet**: pytest för all deterministisk logik, ruff för lint, mypy för typkontroll, GitHub Actions CI som kör allt vid push.
* **Tillgänglighet**: kontrast enligt WCAG AA, all interaktion möjlig med tangentbord (Streamlits standardkomponenter).

## 7. Mätning av lärandeeffekt

* Quizresultat före och efter (sparas i session, exporteras).
* Antal genomförda scenarier per modul.
* Andel RNTS steg som tutorn bedömer som korrekta vid första försöket (proxymått för metodmognad).
* Tid per scenario (Streamlit session timing).

## 8. Öppna frågor

* Ska rättsfall (NJA) ingå i vitlistan i v2 med en kuraterad lista per modul? (Innehållsfråga, ägare: du.)
* Ska framsteg persisteras med st.experimental_user eller enkel filbaserad lagring i v2? (Teknik, ägare: developer.)
* Behövs lärarläge med egna scenarier? (Produkt, P2.)

## 9. Acceptanskriterier för v1 (sammanfattning)

* [ ] Åtta P0 moduler synliga som sidor, var och en med minst 1 case, 6 MC frågor och 3 lagrumsjaktfrågor.
* [ ] Tutorn svarar på svenska i RNTS struktur och alla lagrum i svaret är antingen verifierade (klickbar länk) eller varningsmarkerade.
* [ ] Sessionstak och dagligt tak går inte att kringgå från UI och deterministiska funktioner fungerar när taket är nått.
* [ ] pytest, ruff och mypy passerar i CI.
* [ ] Appen deployad på Streamlit Community Cloud.
