# APPGUIDE.md: vad varje sida gör, hur den fungerar och var den brister

Det här dokumentet beskriver den **byggda** appen, sida för sida. `PRD.md`
beskriver avsikten, `design_system.md` utseendet och `methodology.md`
pedagogiken. Ingen av dem berättar vad som faktiskt händer när du klickar.

Allt som påstås här är kontrollerat mot koden eller mätt i skarp körning mot
`Qwen/Qwen3-8B`. Där en siffra anges är den uppmätt, inte uppskattad.

Senast verifierad: 2026-07-21, mot 626 gröna tester. (Dokumentet du läser
räknas in i den siffran: `tests/test_sprak.py` kontrollerar teckenkodning och
frånvaro av kyrilliska tecken i varje markdownfil i roten, så den här filen
lade till två tester.)

---

## 1. Snabbstart

```bash
cd /Users/Brook/Downloads/juridik_oversiktskurs
streamlit run streamlit_app.py
```

Appen öppnas på `http://localhost:8501`. Avsluta med `Ctrl+C`.

**Token är valfri.** Utan `HF_TOKEN` i `.streamlit/secrets.toml` fungerar allt
utom tutorn och rättsfallsgenereringen: samtliga scenarier, quiz,
lagrumsjakter, facit, kartor och exporter är deterministiska. Tutorknapparna
visar då ett vänligt felkort i stället för att krascha.

Detta är en medveten designlinje och den bär hela appen: **LLM är ett tillägg,
aldrig en förutsättning.**

---

## 2. Din första session — vad du möter, i tur och ordning

Det här avsnittet beskriver upplevelsen. Avsnitt 4–9 beskriver sidorna var
för sig; det här beskriver hur de hänger ihop när någon faktiskt använder
appen.

### Sidopanelen ligger fast

Till vänster står hela kursen som ett träd, byggt av `utils/navigation.py`,
grupperat i fem block: **START OCH METOD**, **OFFENTLIG RÄTT**,
**CIVILRÄTT**, **STRAFF- OCH PROCESSRÄTT** och **TRÄNING**.

Trädet speglar rättssystemets systematik, inte filordningen: Avtalsrätt
ligger under Civilrätt → Förmögenhetsrätt → Kontraktsrätt. Att navigera i
appen är därför i sig en repetition av hur svensk rätt är indelad.

Två poster — Statsrätt och Förvaltningsrätt — visas som
**planerade men obyggda**. De är medvetet kvar: kartan ska visa hela
rättssystemet, även de delar kursen inte täcker.

Längst ned i panelen ligger en statuspanel med modellväljare (Qwen3-8B eller
14B) och kvarvarande LLM-anrop för sessionen.

### 1. Hem — orientering och framsteg

Du landar på `0_Hem`. Överst en disclaimer om att appen inte är juridisk
rådgivning. Sedan ett rutnät av modulkort, arbetsgången som en vågrät
stegindikator, och längst ned **Framsteg** — tomt vid första besöket.

Modulkorten är avsiktligt **inte** klickbara; de riktiga länkarna ligger
under kartan. Skälet är att korten är en översiktsbild, inte en meny.

### 2. Rättskartan — dit man bör gå härnäst

`16_Rattskartan` är den enda sidan som är **full på dag noll**. Den kräver
varken token, LLM eller genomförda övningar, och svarar på frågan "var i
rättssystemet befinner jag mig?".

Här kan du klicka dig runt i hela taxonomin, slå upp "vilken lag gäller för
mitt fall?" och läsa 52 nyckelbegrepp.

### 3. En modulsida — själva arbetet

Säg `2_Avtalsratt`. Tre flikar: **Rättsfall**, **Quiz**, **Lagrumsjakt**.

I fliken Rättsfall läser du ett scenario och fyller i fyra textfält enligt
RNTS (se ordlistan, avsnitt 13). Medan du skriver i **Norm**-fältet rättas
det direkt: skriver du `4 § AvtL` dyker ett guldchip upp, klickbart till
lagen.nu. Skriver du något ogiltigt får du en gul varning. Ingen LLM är
inblandad — det är ren mönstermatchning mot lagrumsregistret.

Till vänster visar en stegindikator status per RNTS-steg: tom cirkel, blå
"pågår", gul "behöver mer" eller grön bock.

Först när du skrivit klart trycker du **"Be tutorn granska min analys"**.
Ordningen är pedagogiskt avsiktlig: du ska ha formulerat ett eget svar innan
du ser någon annans.

### 4. Vad som räknas som framsteg

Ett rättsfall räknas som genomfört när **alla fyra fälten har innehåll** —
utan att tutorn behöver ha körts. Det är den händelsen som matar
Kunskapskartan, framstegsvyn på Hem och Obsidianexporten.

Det betyder att hela framstegssystemet fungerar **utan token**.

### 5. Kunskapskartan växer fram

Efter några genomförda fall är `10_Kunskapskarta` inte längre tom. Lagrum som
återkommer i flera fall blir gemensamma noder, så du ser hur samma paragraf
tillämpas i olika situationer.

### 6. Innan du stänger fliken

**Ladda ner något.** Allt framsteg lever i webbläsarsessionen och försvinner
vid omladdning (avsnitt 11). Hem erbjuder tre nedladdningar: studierapport i
Markdown, samma som Excel, och ett Obsidianvalv som zip.

Detta är appens allvarligaste svaghet, och inget i gränssnittet påminner dig
om det.

---

## 3. Arkitektur i korthet

`streamlit_app.py` registrerar 17 sidor via `st.navigation`. Sidopanelens
hierarki byggs separat i `utils/navigation.py`, som också känner till
planerade men obyggda moduler (Statsrätt, Förvaltningsrätt).

Elva av de sjutton sidorna är skal på 15–22 rader som bara anropar
`rendera_modulsida(...)`. Motorn ligger i `utils/modulvy.py`.

| Sida | Motor | Datakälla |
|---|---|---|
| `0_Hem` | egen | `session_state` + `utils/export`, `utils/obsidian` |
| 11 modulsidor | `utils/modulvy.py` | `data/scenarier/*.json` |
| `9_Kunskapstest` | egen | `utils/quiz` (`session_state`) |
| `10_Kunskapskarta` | `utils/graf`, `utils/graf_ui` | `session_state` |
| `11_Kunskapsutmaning` | `utils/generator` + `modulvy.rendera_case_ovning` | LLM + `data/scenarier` |
| `16_Rattskartan` | `utils/rattssystem_graf`, `utils/taxonomi_ui` | `data/rattssystem.json`, `data/nyckelbegrepp.json` |

**Innehållsvolym:** 12 scenariofiler, 19 rättsfall, 86 quizfrågor,
43 lagrumsjakter, 52 nyckelbegrepp, 21 lagar i registret.

---

## 4. Modulsidorna (11 av 17)

Alla elva ser likadana ut och beter sig likadant. Bara innehållet skiljer.

| Sida | Modul | Rättsfall | Quiz | Lagrumsjakt |
|---|---|---|---|---|
| `1_Juridisk_metod` | Kap. 1 · Juridisk metod | 1 | 6 | 3 |
| `12_Personratt` | Kap. 5 · Personrätt | 2 | 8 | 4 |
| `13_Allman_formogenhetsratt` | Kap. 6 · Allmän förmögenhetsrätt | 2 | 8 | 4 |
| `2_Avtalsratt` | Kap. 7 · Avtalsrätt | 2 | 8 | 4 |
| `3_Kop_och_konsumentratt` | Kap. 8 · Köprätt | 1 | 6 | 3 |
| `14_Fastighetsratt` | Kap. 9 · Fastighetsrätt | 2 | 8 | 4 |
| `4_Skadestandsratt` | Kap. 10 · Skadeståndsrätt | 2 | 8 | 4 |
| `5_Arbetsratt` | Kap. 11 · Arbetsrätt | 1 | 6 | 3 |
| `6_Associationsratt` | Kap. 12 · Associationsrätt | 1 | 6 | 3 |
| `15_Fordringsratt` | Kap. 15–17 · Fordringsrätt | 2 | 8 | 4 |
| `7_Familje_och_arvsratt` | Kap. 18–21 · Familj och arv | 2 | 8 | 4 |
| `8_Straff_och_processratt` | Kap. 22 · Straffrätt | 1 | 6 | 3 |

### Vad du ser

Sidhuvud, sedan tre flikar: **Rättsfall**, **Quiz**, **Lagrumsjakt**.

### Flik 1 — Rättsfall, steg för steg

1. **Två knappar överst.** "Generera nytt rättsfall" (LLM) och "Visa kursens
   rättsfall". Den senare är utgråad tills du genererat något.
2. **Välj rättsfall** i en rullista, om modulen har flera.
3. **Scenariokortet** visar rubrik, svårighetsgrad och uppskattad tid.
4. **RNTS-formuläret**, fyra textfält: Rättsfrågan, Norm, Tillämpning,
   Slutsats. Till vänster en stepper som visar status per steg.
5. **Normfältet rättas medan du skriver.** Skriver du `4 § AvtL` dyker ett
   guldchip upp direkt, klickbart till lagen.nu. Skriver du något ogiltigt får
   du en gul varning. Detta sker helt utan LLM (`modulvy._norm_feedback`).
6. **Steppern** markerar Norm som godkänd först när *alla* lagrum i fältet
   verifierats. Övriga steg räknas som påbörjade så snart de har text.
7. **"Be tutorn granska min analys"** — enda stället där LLM anropas i fliken.
8. **"Visa facit (utan tutor)"** i en expander: rättsfråga, lagrum som chips,
   tillämpningspunkter och slutsats. Helt deterministiskt.

**Viktigt:** ett rättsfall räknas som genomfört när alla fyra fälten har
innehåll — **utan att tutorn behöver ha körts**. Det är den händelsen som
matar Kunskapskartan, framstegsvyn och Obsidianexporten.

### Flik 2 — Quiz

Flervalsfrågor. Du väljer alternativ, trycker **Svara**, och rättas
**deterministiskt** mot data. Rätt svar ger grönt med förklaring, fel svar
ger rött plus vilket alternativ som var rätt. Har alternativet ett lagrum
visas det som chip. Därefter kan du valfritt be tutorn förklara.

Resultatet registreras per modul och syns på Hem och Kunskapstest.

### Flik 3 — Lagrumsjakt

En situation beskrivs i text, du skriver vilket lagrum den handlar om. Rättas
deterministiskt av `utils/quiz.ratta_lagrumsjakt`. Skriver du en lag som inte
finns i registret får du veta det uttryckligen. Ledtråd och facit finns.

**Ingen LLM alls i den här fliken.**

### Under huven

`modulvy.rendera_case_ovning` delas med Kunskapsutmaningen, så kuraterade och
genererade fall får identiskt flöde och identisk verifiering.

Generering sker **endast på knapptryck**, aldrig vid rerun. Skälet står i
koden: Streamlit kör om skriptet vid varje tangenttryck, och ett fall som byts
ut mitt i skrivandet vore obrukbart. Misslyckas grundningen mot
lagrumsregistret faller appen tillbaka på ett kuraterat fall och säger till.

### Styrkor

- Tre olika övningsformer mot samma stoff: analys, igenkänning, uppslagning.
- Två av tre flikar kräver ingen LLM alls.
- Normfältets omedelbara återkoppling lär ut citeringsformatet innan tutorn
  ens är inblandad.
- Ett fall räknas som genomfört utan LLM, så framsteg fungerar utan token.

### Begränsningar

- **Innehållet är tunt i vissa moduler.** Fem moduler har bara ett rättsfall.
  Har du gjort det finns inget mer kuraterat att öva på i den modulen.
- Rullistan för rättsfall visas även när modulen bara har ett.
- Tutorns kvalitet varierar — se avsnitt 11.

---

## 5. `0_Hem` — landningssidan

### Vad du ser

Sidhuvud, en disclaimer om att appen inte är juridisk rådgivning, en karta
över modulerna, riktiga navigeringslänkar under kartan (modulkorten är
avsiktligt inte klickbara), arbetsgången i fyra steg, och sist **Framsteg**.

### Framstegssektionen

- Progressbar per modul med quizresultat.
- Lista över genomförda rättsfall per modul.
- **Tre nedladdningar:** studierapport i Markdown, studierapport i Excel, och
  ett Obsidianvalv som zip.

Obsidianvalvet är värt att ladda ner **även med noll genomförda fall**, för
Rättskartan följer alltid med: 28 filer, cirka 47 kB.

### Begränsningar

- Rubriken säger "Tolv moduler" men sidan renderar **13 modulkort**.
- Framstegen försvinner vid omladdning av webbläsaren (avsnitt 11).

---

## 6. `9_Kunskapstest` — resultatöversikt

### Vad du ser

Dina quizresultat per modul, och under det en lista över vilka moduler som har
quizfrågor och hur många.

### Begränsningar

Detta är **inte ett test**. Sidan ställer inga frågor — den summerar bara vad
du redan svarat i modulerna. Sidhuvudet ("Dina resultat per modul") är ärligt,
men namnet *Kunskapstest* leder fel, och modulens docstring beskriver ett
blandat slumptest över alla moduler som aldrig byggdes.

Sidan använder dessutom råa `st.info`, mot designsystemet.

---

## 7. `10_Kunskapskarta` — din egen graf

### Vad du ser

Tomt läge tills du genomfört minst ett rättsfall, med en förklaring av hur du
fyller den. Därefter en interaktiv graf: **guld = lagrum, blå = rättsfall,
mörkblå = modul.**

Poängen är att lagrum som återkommer i flera fall blir **gemensamma noder**,
så du ser hur samma paragraf tillämpas i olika situationer.

### Under huven

Data hämtas ur `session_state` via `obsidian.hamta_case_analyser`. Byggs
deterministiskt av `utils/graf.bygg_graf`. Ingen LLM.

### Begränsningar

Kartan är helt beroende av `session_state`. **En omladdning tömmer den.** Det
är den sida där persistensproblemet gör mest skada, eftersom värdet växer med
tiden och därför är som störst precis när det riskerar att förloras.

---

## 8. `11_Kunskapsutmaning` — genererat rättsfall

### Steg för steg

1. Välj rättsområde i rullistan, eller tryck **🎲 Överraska mig**.
2. Tryck **Generera nytt rättsfall**.
3. Appen anropar LLM, **verifierar varje lagrum i facit mot registret**, och
   visar fallet först därefter.
4. Därefter exakt samma RNTS-flöde som modulsidorna.

### Under huven

`utils/generator.generera_case` följer mönstret constrain–validate–fallback.
Går grundningen inte igenom returneras ett kuraterat fall med källa
`"fallback"` och en notis som förklarar varför. Du testas alltså **aldrig på
en påhittad paragraf** — men du kan få ett kuraterat fall när du bad om ett
nytt.

### Begränsningar

- Kräver token. Utan den blir det alltid fallback.
- Ett genererat fall har inget riktigt facit i kursens mening — det är
  modellens egen lösning, grundad i registret men inte kvalitetsgranskad av
  en människa. Det gör tutorgranskningen svagare här än på modulsidorna
  (avsnitt 11).

---

## 9. `16_Rattskartan` — kursens orienteringssida

Till skillnad från Kunskapskartan är den här **full på dag noll**. Den kräver
varken LLM, token eller genomförda övningar.

### Flik 1 — Systemet

Hela taxonomin över svensk rätt som interaktiv graf, byggd efter rättens
doktrinära systematik: roten **Svensk rätt** delas i **offentlig rätt** (statsrätt,
förvaltningsrätt, straffrätt, process- och exekutionsrätt) och **civilrätt**, där
civilrätten följer spinen förmögenhetsrätt → obligationsrätt / sakrätt. Trädet är
ojämnt djupt — sex nivåer på civilrättssidan (t.ex. Civilrätt → Förmögenhetsrätt →
Obligationsrätt → Speciell avtalsrätt → Köp- och konsumenträtt → KöpL), färre på den
offentliga. 46 noder, 45 kanter, ett strikt träd. Juridisk metod ingår inte i kartan;
den nås via sidopanelen.

**Guldfärgade lagnoder är klickbara** och öppnar lagen.nu i ny flik.
Strukturnoder saknar länk och är avsiktligt inerta. Under grafen ligger
områdesträdet som hopfällbara expandrar med brödsmula och ett kort per lag.
Överst finns en **återställningsknapp** som tömmer sök- och områdesfiltren.

Varje lagkort visar lagens **kursavsnitt**: vilka paragrafintervall kursen
omfattar, med lagens egen rubrik för varje avsnitt och en djuplänk till
lagen.nu. För kapitelindelade lagar grupperas avsnitten under lagens egna
kapitelrubriker, hämtade ur `data/lagstruktur/`, och en **täckningsrad** anger
hur stor del av lagen kursen berör ("kursen täcker 6 av lagens 38 kapitel").
Raden är kortets ärlighetskrav: utan den läser studenten avsnittslistan som om
lagen tog slut där. Under varje lista står "Urvalet följer kursen, inte hela
lagen."

Kapitlen visas i lagens egen ordning, inte i registrets redaktionella. En
avsnittsrubrik som bara upprepar kapitelrubriken utelämnas; då räcker spannet.

Går grafbiblioteket inte att ladda (kräver internet) visas ett meddelande om
det, och områdesträdet fungerar ändå.

### Flik 2 — Falltypsguide

Sökbar tabell: "vilken lag gäller för mitt fall?". Sökningen träffar på dolda
sökord, så *uppsagd* hittar LAS-raden utan att sökorden syns i tabellen.

### Flik 3 — Nyckelbegrepp

52 begrepp med fyra fasta fält: definition, förklaring, exempel och hur
begreppet känns igen i ett scenario. Sökbart och filtrerbart per rättsområde.
Varje begrepp har en valfri LLM-fördjupning bakom **"Förklara djupare"**, med
två lägen: längre förklaring eller ett övningsscenario att lösa.

**Samtliga 84 lagrumsreferenser i begreppsbanken är verifierade** mot
registret vid inläsning. Filen vägrar laddas om en referens inte går att
verifiera.

### Begränsningar

- Alla 52 begreppskort byggs vid varje rerun, även i hopfällda expandrar. Det
  ger 107 widgets på sidan och gör den till den tyngsta i appen.
- Begreppsfördjupningen saknar facit i den mening ett rättsfall har det, men
  är sedan 2026-07-21 inte längre ogrundad: begreppets grunddata och
  paragrafernas **ordagranna lagtext** injiceras, och svaret granskas mot
  begreppets egna lagrum.

---

## 10. Visualiseringar — vad som ritas, och varför

Ja, appen är visuell, men sparsamt och med avsikt. Det finns **inga diagram
över studieresultat** — inga stapeldiagram, inga cirkeldiagram, ingen
statistik över tid. Det är ett medvetet val: metodiken är formativ, inte
summativ (`methodology.md` avsnitt 1). Studenten ska se *vad hen kan*, inte
en poäng att jaga.

De visualiseringar som finns är av två slag: **grafer** som visar struktur,
och **statusindikatorer** som visar var du är.

### Interaktiva grafer (vis-network)

Två av dem, båda renderade i en sandlådad iframe med `vis-network` från CDN.
De kräver internet; utan uppkoppling visas ett meddelande och sidans övriga
innehåll fungerar ändå.

| Graf | Sida | Innehåll | Interaktion |
|---|---|---|---|
| **Rättssystemets taxonomi** | `16_Rattskartan` | 46 noder, 45 kanter, strikt träd med ojämnt djup: rot → offentlig rätt / civilrätt → … → lag | Zooma, dra, klicka. **Guldfärgade lagnoder öppnar lagen.nu i ny flik.** Strukturnoder är avsiktligt inerta |
| **Din kunskapskarta** | `10_Kunskapskarta` | Dina genomförda fall och deras lagrum | Zooma, dra. Lagrum som återkommer i flera fall blir gemensamma noder |

Nodstorleken i taxonomigrafen följer djupet (26 px i roten ned till 13 px för
lagnoder), så trädets nivåer går att läsa av utan att följa kanterna.

### Färgspråket bär betydelse

Färgerna är inte dekoration. De är samma i båda graferna, i chipsen och i
korten, och de betyder alltid samma sak:

| Färg | Hex | Betyder |
|---|---|---|
| **Paragrafguld** | `#B8860B` | **Alltid och enbart lagrum.** Ser du guld är det en paragraf |
| Myndighetsblå | `#2C5F8A` | Rättsfall, och appens primära accent |
| Bläck | `#1A2332` | Modul- och strukturnoder, brödtext |
| Grön | `#2E7D4F` | Godkänt |
| Gul | `#C9971C` | Varning, "behöver mer" |
| Röd | `#B3402A` | Fel |

Att guld är reserverat för lagrum är den bärande regeln: den lär studenten
känna igen en paragrafhänvisning på formen innan hen kan läsa den.

### Statusindikatorer och kort

- **RNTS-steppern** — fyra steg bredvid formuläret, var och en i ett av fyra
  lägen: tom cirkel (ej påbörjad), blå (pågår), gul (behöver mer), grön bock
  (godkänd). Norm blir grön först när *alla* lagrum i fältet verifierats.
- **Lagrumschips** — guldkantade piller. Verifierade chips länkar till
  lagen.nu; overifierade får varningsstil och prefixet "Ej verifierad:".
- **Progressbar per modul** på Hem, med quizresultat.
- **Modulrutnät** på Hem — kort i två kolumner, en på mobil.
- **Stegindikator** för arbetsgången, vågrät.
- **Begreppskort och lagkort** på Rättskartan.

### Vad som inte finns

- Ingen graf över resultat, poäng eller utveckling över tid.
- Ingen jämförelse mot andra studenter.
- Ingen tidslinje.
- Kunskapskartan är bara sedd med få noder — läsbarheten vid växande data är
  oprövad (avsnitt 16).

---

## 11. Tvärgående system

### Lagrumsgarden — vad den faktiskt intygar

`utils/lagrum.validera_lagrum` svarar på frågan **"finns paragrafen i kursens
register?"**. Den svarar *inte* på "är det rätt paragraf för frågan?".

Det betyder att ett guldchip garanterar existens, inte relevans. Sedan
2026-07-21 visar tutorsvar med verifierade lagrum därför en not som säger
just det.

Verifieringen skärptes samma dag: tidigare godkändes `99 kap. 1 § AvtL`
eftersom kapitelledet ignorerades för lagar utan kapitelindelning. Ett
påhittat kapitel gick alltså rakt igenom garden.

### Lagtextkorpusen — vad modellen läser i stället för att minnas

`data/lagtext/` innehåller **1 010 paragrafer ur 21 lagar**, hämtade med
`scripts/hamta_lagtext.py`. Endast författningstext, som är undantagen
upphovsrätt enligt 9 § upphovsrättslagen. lagen.nu:s egna kommentarer hämtas
aldrig — de är författade verk, och kursen ska lära studenten läsa lagtext.

Korpusen ligger i git, så appen fungerar offline och belastar inte lagen.nu
vid varje tutorsvar. Tjugo lagar kom från lagen.nu; UB (1981:774) hämtades
från Riksdagens öppna data eftersom lagen.nu:s sida bara renderade
kapitelrubriker och gav 2 av 39 paragrafer.

**Ordagrann lagtext injiceras nu i samtliga fyra promptbyggare** — rättsfall,
quiz, begrepp och generering. Modellen behöver därför inte minnas vad en
paragraf säger; den har den framför sig.

### Granskningen — sista ledet före studenten

`utils/granskning.granska_tutorsvar` avgör om ett svar över huvud taget får
visas. Den avgörande insikten är att det inte räcker att leta efter
overifierade lagrum, för **det bästa tutorsvaret innehåller ofta ett
påhittat lagrum** — nämligen studentens eget, korrekt avvisat:

> "87 § AvtL finns inte i lagrumslistan. Detta är ett allvarligt fel."

En gard som bara letade efter påhitt hade stoppat exakt det svaret och
släppt igenom det sämre som påstod "Rätt norm är 87 § AvtL". Avgörande är
alltså inte OM ett lagrum nämns, utan i vilken **roll**: ett lagrum utanför
uppgiftens underlag måste avvisas i texten för att svaret ska godkännas.

Underkänns ett svar görs **ett** omförsök med skärpt instruktion. Underkänns
även det visas inget svar alls, utan en varning som pekar mot sidans
deterministiska underlag ("Öppna *Visa facit* nedan"). Den underkända texten
sparas medvetet inte. Hellre inget svar än felaktig juridik: studenten kan
inte skilja dem åt.

Vid tveksamhet godkänns svaret. Ett tveksamt svar som släpps igenom kostar
en varningsruta; ett korrekt svar som stoppas kostar undervisning.

### Tutorn

- Modell: `Qwen/Qwen3-8B`
- Sessionstak: **40 anrop** (`llm.SESSION_CALL_CAP`)
- Dagstak: **300 anrop** (`llm_budget.DEFAULT_DAILY_CALL_CAP`)
- Svarslängd: 400 ord för fallgranskning, 250 för begrepp
- Latens uppmätt: **3,7–10,0 sekunder**
- Cache på promptinnehåll, så identiska frågor kostar inget nytt anrop

Alla svar går genom `verify_lagrum`. Overifierade hänvisningar samlas i en gul
varningsruta i stället för att renderas som fakta.

### Persistens — den viktigaste begränsningen

**Allt studentframsteg lever i `session_state`.** Quizresultat, genomförda
rättsfall, RNTS-analyser, kunskapsgrafen och tutorsvaren finns bara i
webbläsarsessionen. En omladdning, en timeout eller en stängd flik tömmer
allt.

Det finns ingen disklagring för framsteg. Enda sättet att rädda arbete är att
ladda ner en rapport eller Obsidianvalvet **innan** sessionen tar slut, och
inget i gränssnittet uppmanar till det.

### Export

| Format | Innehåll |
|---|---|
| Markdown | Quizresultat och genomförda fall per modul |
| Excel | Samma, som kalkylark |
| Obsidian (zip) | 28 filer: Rättskartan, modulnoter, lagrumsnoter, en not per genomförd RNTS-analys |

---

## 12. Mätresultat, 2026-07-21

Fyra fall (tre avtalsrätt, ett skadeståndsrätt), skarpa anrop mot Qwen3-8B.

### Rendering

17 av 17 sidor renderade utan fel med tom `session_state` och utan token, och
utan att röra LLM:en.

### Fallgranskningen, före och efter facitinjektion

| | Före | Efter |
|---|---|---|
| Facits lagrum träffade | **2/9** | **9/9** |
| Hänvisningar utanför facit | **8** | **0** |
| Påhittad paragraf intygad som rätt | **1** | **0** |
| Felaktigt svar kallat korrekt | **1** | **0** |

Före ändringen fick ett studentsvar som citerade det påhittade `87 § AvtL`
svaret *"Rätt norm är 87 § AvtL"* och *"Slutsatsen är korrekt"* — trots att
slutsatsen var fel. Efter ändringen avvisas båda påhitten uttryckligen och
rätt lagrum pekas ut.

I ett annat fall pekade tutorn en **korrekt löst** uppgift vidare till
`36 § AvtL` med påståendet att paragrafen reglerar avtals ingående. 36 § är
generalklausulen om jämkning. Både den och den korrekta hänvisningen
verifierades som gröna chips.

Orsaken var att `build_case_prompt` bara injicerade facits *rättsfråga*.
Lagrum, tillämpningspunkter och slutsats hölls tillbaka, så modellen fick
härleda svensk rätt ur sina egna vikter. Hela facit injiceras nu.

### Granskningen, skarp körning

Två fall replikerade mot Qwen3-8B efter att granskningen kopplats in:

| Fall | Utfall |
|---|---|
| Studenten citerar påhittade `87 § AvtL` | Tutorn avvisar paragrafen uttryckligen och pekar ut 1 § och 4 § AvtL. Godkänt på **första** anropet — avvisningen känns igen som avvisning, inte som påhitt |
| Studenten svarar **helt korrekt** | Tutorn drev svaret mot `3 § AvtL`, utanför facit. **Granskningen stoppade svaret**, omförsöket gav ett rent svar utan drift |

Det andra fallet är samma felmönster som `36 § AvtL`-incidenten ovan, och
det är nu fångat i produktion och inte bara i test. Ett godkänt svar kostar
fortfarande exakt ett anrop; omförsöket betalas bara när det behövs.

### Qwen3-8B mot Qwen3-14B

Tre rundor à 15 körningar per modell: fem moduler (avtal, skadestånd, arbete,
fastighet, fordring) × tre studentprofiler (helt korrekt svar, svar som
citerar påhittade `87 § X`, vagt svar utan lagrum).

| | direkt | omförsök | stoppad | median | max |
|---|---|---|---|---|---|
| Qwen3-8B | 43 | 2 | **0** | 6,2 s | 17,4 s |
| Qwen3-14B | 39 | 5 | **1** | 7,6 s | 15,7 s |

**Den större modellen bär inte sin kostnad.** Den är omkring en sekund
långsammare per svar, behövde fler omförsök, och stod för det enda svar som
underkändes två gånger och därför inte kunde visas alls.

Felen är inte jämnt spridda utan samlade i en profil: när studenten citerar
en påhittad paragraf upprepar 14B den oftare som gällande rätt i stället för
att avvisa den. I runda 2 gällde det fyra av fem sådana fall. Mekanismen är
alltså identifierbar och inte bara brus, även om 45 körningar per modell är
ett litet underlag.

Slutsatsen är att 8B förblir standard. Ordningen i avsnitt 15 håller: de
billiga greppen — facit, lagtext, granskning — gav mätbara lyft, medan
modellstorlek inte gjorde det. 14B är kvar som valbart alternativ i
sidopanelen.

### Begreppsfördjupningen

Sex körningar: **0 overifierade lagrum**, 0 engelska ord. Men modellen
producerade påhittad svensk terminologi — *"proxim meningskausalitet"*,
*"negligens"*, *"nättillverkad"*, *"försämringsföljd"* — som varken är
engelska ord eller riktiga juridiska termer, och därför passerade den gamla
språkregeln. Efter skärpningen: **0 kvar**.

Ett studentsvar skrivet helt på engelska besvaras helt på svenska.

---

## 13. Ordlista — termer i appen och i koden

Appen blandar tre ordförråd: juridikens, pedagogikens och kodens. Den som
läser koden möter svenska variabelnamn för juridiska begrepp, och den som
använder appen möter facktermer utan förklaring. Här är båda.

### Juridiska termer studenten möter

**Lagrum** — en precis hänvisning till en bestämmelse, t.ex. `4 § AvtL`
(paragraf 4 i avtalslagen) eller `2 kap. 1 § SkL` (kapitel 2, paragraf 1 i
skadeståndslagen). Appen skriver alltid paragrafen först och förkortningen
sist. Den *läser* även omvänd ordning (`AvtL 4 §`), eftersom studenter
skriver så, men lär ut den kanoniska formen.

**SFS** — Svensk författningssamling, lagens officiella nummer, t.ex.
`1915:218` för avtalslagen. Används som filnamn i lagtextkorpusen.

**Rekvisit** — de villkor som måste vara uppfyllda för att en regel ska bli
tillämplig. Att pröva dem ett i taget mot fakta är *subsumtion*.

**Subsumtion** — att föra in de faktiska omständigheterna under regelns
rekvisit. Det är detta som sker i RNTS-steget Tillämpning, och enligt
`methodology.md` det steg studenter oftast hastar förbi — därför har det ett
eget fält och egen bedömning.

**Dispositiv rätt** — regler parterna kan avtala bort (stora delar av
köprätten). **Tvingande rätt** — regler som gäller oavsett avtal (stora delar
av arbetsrätten och konsumenträtten). Skillnaden är central i flera moduler.

**Rättskällelära** — hierarkin mellan lag, förarbeten, prejudikat och
doktrin. Modul 1 lär ut den; övriga moduler tillämpar den underförstått.

**Anbud och accept** — erbjudande och svar, de två viljeförklaringar som
bildar ett avtal. En *sen accept* gäller enligt 4 § AvtL som ett nytt anbud —
det återkommande skolexemplet i den här appen.

### Pedagogiska begrepp

**RNTS** — appens bärande analysmodell, den juridiska metodens fyra steg:

| Steg | Frågan du besvarar |
|---|---|
| **R** — Rättsfrågan | Vad är den juridiskt relevanta frågan? Inte "vem har rätt?" utan t.ex. "har bindande avtal uppkommit trots den sena accepten?" |
| **N** — Norm | Vilken rättsregel styr frågan? Kräver precist lagrum. **Detta steg validerar appen maskinellt.** |
| **T** — Tillämpning | Subsumtion: regelns rekvisit prövas ett i taget mot fakta |
| **S** — Slutsats | Svaret på rättsfrågan, med reservation för alternativa utfall |

**Facit** — kursens kontrollerade lösning på ett rättsfall: rättsfråga,
lagrum, tillämpningspunkter och slutsats. Deterministisk, skriven av
människa, och sedan 2026-07-21 tutorns sanningsunderlag. Studenten når den
via "Visa facit (utan tutor)".

**Generationseffekten** — att själv formulera ett svar ger mätbart bättre
retention än att läsa ett färdigt. Det är skälet till att tutorn aldrig körs
automatiskt utan bara på knapptryck, efter ett eget försök.

**Formativ bedömning** — återkoppling som stöder lärande, till skillnad från
*summativ* bedömning som sätter betyg. Appen är genomgående formativ, vilket
är skälet till att det inte finns några resultatdiagram (avsnitt 10).

**Lagrumsjakt** — övningsformen där en situation beskrivs i text och
studenten ska ange vilket lagrum den handlar om. Uppslagning snarare än
analys. Rättas deterministiskt, ingen LLM.

### Termer i koden

Koden är skriven på svenska. Dessa dyker upp oftast:

| Term | Betyder |
|---|---|
| `underlag` | Uppgiftens kända korrekta lagrum, det tutorn ska hålla sig inom |
| `granskning` | Kontrollen av ett tutorsvar *innan* studenten ser det (avsnitt 11) |
| `verifierad` | Lagrummet finns i kursens register — **inte** att det är rätt för frågan |
| `vitlista` | De lagar tutorn får hänvisa till i en given uppgift |
| `grundning` | Att binda modellens svar till kontrollerad data i stället för dess minne |
| `fallback` | Kuraterat innehåll som visas när genereringen inte kan verifieras |
| `case` / `rättsfall` | Ett övningsscenario med facit |
| `modulvy` | Motorn som renderar alla elva modulsidor |
| `skarpning` | Den skärpta instruktionen vid tutorns omförsök |

---

## 14. Styrkor och svagheter

### Styrkor

1. **Appen fungerar utan LLM.** Det är ovanligt och det är rätt.
2. **Grundningsprincipen hålls genomgående.** Lagnamn, SFS och URL:er hämtas
   ur registret, aldrig konstruerade. Data vägrar laddas hellre än att visa
   ogrundade lagrum.
3. **Rättningen är deterministisk där den kan vara det** — quiz, lagrumsjakt,
   normfält, facit.
4. **En källa per sak.** Rättskartan i appen och i Obsidianvalvet bygger på
   samma data sedan 2026-07-21.
5. **Tre lager mellan modellen och studenten:** ordagrann lagtext i prompten,
   facit som sanningsunderlag, och en granskning som hellre visar inget än
   fel juridik.
6. **626 tester**, ruff och mypy rena.

### Svagheter

1. **Persistensen.** Allt framsteg försvinner vid omladdning. Störst problem
   i appen.
2. **Begreppsfördjupningen är fortfarande den svagaste LLM-ytan.** Den har
   nu grunddata, lagtext och granskning, men inget kurskontrollerat facit
   med gränsfall och kontrastpar.
3. **Tunt innehåll i fem moduler** — ett rättsfall vardera.
4. **Kunskapstest är ingen test**, bara en resultatvy.
5. **`use_container_width` är deprecerad** i 5 anrop i 3 filer; borttagningen
   passerade 2025-12-31.
6. **Råa `st.success/info/warning`** i fyra filer, mot designsystemet.
7. **"Tolv moduler" men 13 kort** på Hem.
8. **Rättskartan bygger 52 begreppskort vid varje rerun**, även hopfällda.

---

## 15. Optimeringsmöjligheter, prioriterade

| # | Åtgärd | Insats | Löser |
|---|---|---|---|
| 1 | **Framsteg till disk** (JSON per student-id, eller `st.cache_resource`) | 1–2 d | Svaghet 1 — den enda som gör att en students arbete går förlorat |
| 2 | **Uppmana till export innan sessionen dör** | 2 h | Dämpar 1 tills 1 är byggt |
| 3 | **Sanningsunderlag för begrepp** — utöka `nyckelbegrepp.json` med gränsfall och kontrastpar som facit | 1 d | Svaghet 2, samma grepp som gav 2/9 → 9/9 |
| 4 | **Fler rättsfall i tunna moduler** | löpande | Svaghet 3 |
| 5 | **Bygg det blandade slumptestet** som docstringen redan lovar | 1 d | Svaghet 4 |
| 6 | **Städa `use_container_width` och råa statuskomponenter** | 2 h | Svagheterna 5, 6 |
| 7 | **Rätta "Tolv moduler" till 13**, eller räkna listan i koden | 5 min | Svaghet 7 |
| 8 | **Lat rendering av begreppskort** — bygg bara utfällt område | 3 h | Svaghet 8 |
| 9 | **Logga granskningens utfall** så andelen stoppade svar går att mäta över tid | 3 h | Gör LLM-kvaliteten mätbar i stället för anekdotisk |
| ~~10~~ | ~~**Större modell för tutorn**~~ | — | **Prövad och avfärdad.** Qwen3-14B var långsammare och behövde fler omförsök än 8B, se avsnitt 12 |

Ordningen är avsiktlig: 1 och 2 skyddar studentens arbete, och 3 höjer den
svagaste LLM-ytan med ett grepp som redan är mätt och bevisat.

Att punkt 10 föll bort är i sig ett resultat. Antagandet att en större modell
sänker felfrekvensen höll inte vid mätning — de billiga greppen som ger
modellen bättre *underlag* har gett varje lyft hittills, medan mer parametrar
inte gav något.

**Genomfört 2026-07-21:** lagtextinjektion (tidigare punkt 9) och
granskningen av tutorsvar. Båda är beskrivna i avsnitt 11 och mätta i
avsnitt 12.

---

## 16. Vad dokumentet inte täcker

- **Tutorns pedagogiska kvalitet** utöver lagrumsträffarna. Att tutorn citerar
  rätt paragraf betyder inte att förklaringen är pedagogiskt god.
- **Prestanda under last.** Allt är mätt med en användare lokalt.
- **Tillgänglighet.** Kontrastkraven i `design_system.md` är angivna men inte
  verifierade med verktyg.
- **Grafens läsbarhet vid växande data.** Kunskapskartan är bara sedd med få
  noder.
