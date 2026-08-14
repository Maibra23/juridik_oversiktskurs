# tasks.md: Arbetsplan för tre dagar

Roller (allt utförs av dig, men uppgifterna är märkta per roll):
* **DEV** = developer (kod, arkitektur, tester)
* **PE** = prompt engineer (systempromptar, tutorbeteende, hallucinationsskydd)
* **DES** = designer (designsystem, UI komponenter, presentationslogik)
* **INN** = innehållsansvarig (scenarier, quizfrågor, lagrumsdata från kursboken)

Varje uppgift har en konkret prompt att köra mot en kodassistent. Kör promptarna i ordning inom respektive dag. Committa efter varje grönt teststeg.

---

## Dag 1: Analys, struktur och skelett

Mål vid dagens slut: körbart Streamlit skelett med navigering, lagrumsdatabas, LLM wrapper med budgetskydd och första modulen synlig.

### 1.1 (DEV) Analysera referensrepot
Prompt:
> "Läs igenom repot Maibra23/ekonomistyrning (jag klistrar in utils/llm.py, utils/llm_budget.py, utils/tutor.py, utils/prompts.py och streamlit_app.py). Sammanfatta arkitekturmönstren i punktform: hur LLM anropas, hur session och dagsbudget fungerar, hur tutor genereras on demand med hash av inputs, hur grounding verifieras. Lista sedan exakt vilka moduler jag behöver skriva om för en juridikapp där verifieringen gäller lagrum i stället för siffror."

### 1.2 (DEV) Skapa projektstruktur
Prompt:
> "Skapa filstrukturen för projektet juridik_oversiktskurs enligt: streamlit_app.py, pages/ (en fil per juridikmodul), utils/ (llm.py, llm_budget.py, prompts.py, tutor.py, lagrum.py, scenarier.py, ui.py), data/ (lagrum.json, scenarier/*.json), tests/, .streamlit/config.toml, .streamlit/secrets.toml.example, requirements.txt, .github/workflows/ci.yml. Generera tomma filer med docstrings på svenska som beskriver varje fils ansvar."

### 1.3 (INN) Bygg lagrumsdatabasen (kärnan i hallucinationsskyddet)
Prompt:
> "Skapa data/lagrum.json med kursens viktigaste lagar för Juridisk översiktskurs. För varje lag: förkortning (AvtL, KöpL, KKöpL, SkL, LAS, ABL, ÄktB, SamboL, ÄB, BrB, FB, RB, JB, HBL, MFL, KonkL, UB, SkbrL), fullt namn, SFS nummer, lagen.nu bas URL och en lista över kapitel eller paragrafintervall som ingår i kursen. Använd lagen.nu URL formatet https://lagen.nu/SFSNUMMER#PN eller #KMPN för kapitelindelade lagar. Markera osäkra intervall med fältet 'verifiera': true så jag kan kontrollera dem manuellt mot lagen.nu."

Manuellt efterarbete (INN): öppna lagen.nu och stickprova 10 URLer, särskilt ÄktB, ÄB och BrB som är kapitelindelade.

### 1.4 (DEV) LLM wrapper och budgetskydd
Prompt:
> "Porta utils/llm.py och utils/llm_budget.py från ekonomistyrningrepot till juridikprojektet. Behåll: Qwen/Qwen3-8B som standard och Qwen/Qwen3-14B som alternativ via huggingface_hub InferenceClient, strippning av think taggar, sessionstak 40, filbaserat dagligt tak 300, cache på hash av meddelanden, LLMUnavailableError och LLMSessionCapError. Byt ut sifferverifieringen mot en tom platshållare verify_lagrum som jag implementerar i nästa steg. Alla användarmeddelanden på svenska."

### 1.5 (DEV) Lagrumsvalidering
Prompt:
> "Implementera utils/lagrum.py: (1) LAGRUM_PATTERN, en regex som fångar svenska lagrumsreferenser i formen 'N § FÖRK', 'N N § FÖRK' och 'N kap. M § FÖRK' inklusive intervall som '3 till 5 §§'. (2) extrahera_lagrum(text) som returnerar en lista av träffar med lag, kapitel, paragraf. (3) validera_lagrum(ref) som slår upp mot data/lagrum.json och returnerar en av statusarna VERIFIERAD, OKAND_PARAGRAF, OKAND_LAG. (4) lagen_nu_url(ref) som bygger korrekt länk. (5) verify_lagrum(text) som returnerar en rapport för hela texten. Skriv pytest tester med minst 15 fall inklusive negativa fall som 'NJA 2015 s. 1040' (ska ge status EJ_VALIDERBAR) och påhittade lagar."

### 1.6 (DEV) Streamlit skelett och startsida
Prompt:
> "Skriv streamlit_app.py: startsida på svenska med kursöversikt, Paretomotivering (vilka åtta moduler och varför), disclaimer om att appen inte ger juridisk rådgivning, statuspanel för LLM (tillgänglig, sessionsanrop kvar, dagsbudget kvar) och navigering till pages/. Följ referensrepots mönster med st.set_page_config och en gemensam utils/ui.py för sidhuvud och kort."

### 1.7 (INN + PE) Första modulens innehåll: Avtalsrätt
Prompt:
> "Skapa data/scenarier/avtalsratt.json enligt schemat i utils/scenarier.py med: 2 rättsfall (case) med RNTS facit (rättsfråga, tillämpliga lagrum ur lagrum.json, tillämpningspunkter, förväntad slutsats), 8 flervalsfrågor med förklaringar och lagrumsreferens per alternativ, 4 lagrumsjaktfrågor. Ämnen: anbud och accept (1 och 6 §§ AvtL), sen accept (4 § AvtL), fullmakt med behörighet mot befogenhet (10 och 11 §§ AvtL), ogiltighet (28 till 33 §§ AvtL) och oskälighet (36 § AvtL). Nivå: Juridisk översiktskurs. Allt på svenska."

Definition of done dag 1: appen startar, lagrumstester gröna, avtalsrättsdata inläst och validerad mot lagrum.json.

---

## Dag 2: Kärnflöden

Mål vid dagens slut: komplett scenarioflöde med LLM tutor, verifiering och quiz i minst tre moduler.

### 2.1 (PE) Systemprompt för tutorn
Prompt:
> "Skriv utils/prompts.py för en svensk juridiktutor på JÖK nivå. Systemprompten ska: (1) kräva RNTS strukturen med rubrikerna Rättsfrågan, Norm, Tillämpning, Slutsats, (2) förbjuda påhittade lagar, paragrafer och rättsfall med instruktionen att hellre skriva 'jag är osäker på exakt lagrum' än att gissa, (3) kräva lagrumsformatet 'N § FÖRK' eller 'N kap. M § FÖRK' med endast förkortningarna i den bifogade vitlistan, (4) instruera tutorn att bedöma studentens egna svar steg för steg och peka på vad som saknas i stället för att skriva om hela lösningen, (5) hålla svaret under 400 ord. Skapa även build_case_prompt(scenario, studentens_svar) och build_quiz_prompt(fraga, valt_alternativ) som injicerar scenariodata och den relevanta delen av lagrumsvitlistan i användarprompten."

### 2.2 (DEV) Tutor on demand med verifiering
Prompt:
> "Porta utils/tutor.py från referensrepot: förklaring genereras endast på knapptryck, cachas i st.session_state med hash av scenario och studentsvar, stale markering när inputs ändrats. Efter varje LLM svar: kör verify_lagrum, rendera texten med utils/ui.render_tutortext som byter ut verifierade lagrum mot klickbara lagen.nu chips och omger overifierade referenser med en gul varningsruta. Fånga LLMSessionCapError och LLMUnavailableError med svenska infokort."

### 2.3 (DEV) Case vyn (RNTS formulär)
Prompt:
> "Skriv pages/2_Avtalsratt.py med tre flikar: Rättsfall, Quiz, Lagrumsjakt. Rättsfallsfliken: visa scenariotexten i ett kort, därunder fyra textfält märkta Rättsfrågan, Norm (ange lagrum), Tillämpning, Slutsats, en knapp 'Be tutorn granska min analys' och en expander 'Visa facit' som visar RNTS facit deterministiskt utan LLM. Normfältet valideras direkt med validera_lagrum och visar grönt eller gult innan LLM alls anropas."

### 2.4 (DEV) Quiz och lagrumsjakt
Prompt:
> "Implementera utils/quiz.py och quizfliken: deterministisk rättning, poängräkning i session_state, resultat per modul, knapp 'Förklara' per fråga som anropar tutorn med build_quiz_prompt. Lagrumsjakt: fritextfält där studenten skriver ett lagrum, rättas deterministiskt med validera_lagrum plus jämförelse mot facit, ingen LLM krävs. Skriv tester för rättningslogiken."

### 2.5 (INN) Innehåll för Skadeståndsrätt och Familjerätt/Successionsrätt
Prompt (kör en gång per modul):
> "Skapa data/scenarier/skadestandsratt.json enligt samma schema. Ämnen: culpabedömningen (2 kap. 1 § SkL), principalansvar (3 kap. 1 § SkL), ren förmögenhetsskada (2 kap. 2 § SkL), adekvat kausalitet, jämkning (6 kap. 1 § SkL). 2 case, 8 MC, 4 lagrumsjakt."
> "Skapa data/scenarier/familj_succession.json. Ämnen: giftorättsgods mot enskild egendom (7 kap. ÄktB), bodelning (9 till 11 kap. ÄktB), arvsordningen (2 kap. ÄB), makes arvsrätt och särkullbarn (3 kap. 1 § ÄB), laglott (7 kap. 1 § ÄB), testamentes formkrav (10 kap. 1 § ÄB). Klassiskt tentafall: efterlevande make, särkullbarn och testamente i kombination."

### 2.6 (DEV) Röktest av hela flödet
Prompt:
> "Skriv tests/test_smoke.py som importerar alla pages moduler, laddar alla scenariofiler, validerar samtliga lagrumsreferenser i facit mot lagrum.json och kontrollerar att varje MC fråga har exakt ett rätt svar. Kör pytest och åtgärda alla fel."

Definition of done dag 2: tre moduler spelbara end to end, tutorsvar med verifierade chips, alla tester gröna.

---

## Dag 3: Design, resterande innehåll, test och deployment

### 3.1 (DES) Designsystem i kod
Prompt:
> "Implementera design_system.md (bifogas) i .streamlit/config.toml och utils/ui.py: färgpaletten, typografin och komponenterna render_kort, render_lagrum_chip, render_rnts_steg, render_varning, render_statuspanel. Använd st.markdown med en central CSS sträng, ingen extern CDN. Testa i både ljust läge och mobilbredd."

### 3.2 (INN) Resterande fem P0 moduler
Prompt (en per modul, samma schema): Juridisk metod (kap 1), Köprätt (kap 8), Arbetsrätt (kap 11), Associationsrätt (kap 12), Straffrätt (kap 22). Minst 1 case, 6 MC, 3 lagrumsjakt per modul.

### 3.3 (INN) Förkunskapsmodulerna Personrätt och Allmän förmögenhetsrätt

Tillkom efter helhetsgranskningen: Paretourvalet startade på Avtalsrätt (kap 7) och hoppade därmed över de begrepp som avtals- och köprätten vilar på. Åtgärdat med två moduler enligt samma schema (minst 1 case, 6 MC, 3 lagrumsjakt):

* **Personrätt** (kap 5): underårigs omyndighet och avtalsbundenhet (9 kap. FB), framtidsfullmakt (LFF), god man och förvaltare (11 kap. FB).
* **Allmän förmögenhetsrätt** (kap 6): godtrosförvärv av lösöre (GFL), undantaget för olovligen tagen egendom, lösningsrätt och hävd.

Lagrumsregistret utökades samtidigt med 9 kap. FB, lagen (1986:796) om godtrosförvärv av lösöre och lagen (2017:310) om framtidsfullmakter. Paragrafintervallen är kontrollerade mot rkrattsbaser.gov.se respektive lagen.nu. Rättskartan fick ett nytt underområde så att varje registrerad lag har en plats i kartan.

### 3.4 (INN) Civilrättens sista luckor: Fastighetsrätt och Fordringsrätt

Sidopanelen visade kap 9 och kap 15 till 17 som planerade. Båda är nu byggda enligt samma schema, så att civilrätten inte har några tomma sidor kvar. Lagrumsregistret utökades med 2 kap. JB (tillbehör) och preskriptionslagen (1981:130), kontrollerade mot lagen.nu. Kvar som planerade är endast konstitutionell rätt och förvaltningsrätt, alltså den offentliga rätten.

### 3.5 (LLM) Genererade rättsfall i varje modul

Rättsfallsfliken i varje modul kan nu generera ett nytt, fiktivt fall inom modulens rättsområde via utils.generator, med samma verifiering och fallback som Kunskapsutmaningen. Syftet är att studenten inte ska kunna memorera de kuraterade fallen. Generering sker endast på knapptryck enligt PRD 5.3: Streamlit kör om skriptet vid varje tangenttryck i RNTS-fälten, så automatisk generering vid rerun skulle byta ut fallet mitt i skrivandet. Knappen "Visa kursens rättsfall" tar tillbaka de kuraterade fallen.

### 3.6 (UI) Hierarkisk sidopanel

Sidopanelen ritas av utils.ui.render_sidopanel ur trädet i utils/navigation.py och följer bokens avdelningar i stället för en platt sidlista. Streamlits egen sidlista är avstängd med st.navigation(..., position="hidden"). Hela trädet visas samtidigt utan hopfällbara sektioner. Planerade men ej byggda moduler visas gråtonade med "(kommer)". tests/test_navigation.py vaktar att varje modul pekar på en befintlig fil eller är märkt som planerad, och att ingen sida i pages/ hamnar utanför trädet.

### 3.3 (PE) Promptjustering mot verklig modell
Prompt:
> "Här är fem verkliga tutorsvar från Qwen (klistras in). Identifiera avvikelser från RNTS strukturen, engelska ord, ej verifierbara lagrum och överlånga svar. Föreslå konkreta ändringar i systemprompten och regenerera prompts.py."

Manuellt (PE): kör tests/manual_llm_smoke.py mönstret från referensrepot mot riktiga API t, minst 10 anrop, dokumentera utfall i docs/PROMPT_LOGG.md.

### 3.4 (DEV) Export och framsteg
Prompt:
> "Implementera utils/export.py: exportera quizresultat och genomförda case till en Markdownrapport och en Excelfil (openpyxl). Lägg en framstegssektion på startsidan som läser session_state."

### 3.5 (DEV) CI, typkontroll, README
Prompt:
> "Skapa .github/workflows/ci.yml som kör ruff check, mypy utils och pytest på Python 3.11. Skriv README.md på svenska med installationssteg, hur HF token läggs i .streamlit/secrets.toml, arkitekturskiss och skärmbildsplatshållare."

### 3.6 (DEV) Deployment
Manuellt: pusha till GitHub, skapa app på Streamlit Community Cloud, lägg HF_TOKEN och LLM_DAILY_CAP i Secrets, verifiera att dagstaket skrivs till en skrivbar katalog (använd /tmp fallback som i referensrepot om data/ är read only).

### 3.7 (Alla) Slutlig genomgång
Checklista:
* [ ] Alla acceptanskriterier i PRD avsnitt 9 uppfyllda
* [ ] Session och dagstak testade genom att sänka LLM_DAILY_CAP till 2 lokalt
* [ ] Overifierat lagrum framprovocerat (be tutorn om ett påhittat lagrum) och varningen visas
* [ ] Disclaimer synlig på startsidan och i sidfoten
* [ ] Lighthouse eller manuell kontrastkontroll av paletten
