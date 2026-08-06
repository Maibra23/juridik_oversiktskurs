# UX-granskning och omdesign av Juridisk översiktskurs

Datum: 2026-08-06
Gren: `feat/ux-omdesign`
Status: granskningsdokument. Ingen kod ändras i den här cykeln.

## Om dokumentet

En fullständig produktgranskning av appens användarupplevelse, inte av dess kod.
Granskningen utgår från tre beslut som fattades innan den skrevs:

1. **Bärande idé:** RNTS blir appens ryggrad, inte ett formulär. Kursens redan
   befintliga ordning (`utils/navigation.py`) lyfts fram som en *rekommendation*
   om nästa steg, aldrig som en låsning. Övriga förbättringar hålls till
   disciplinen "lägsta möjliga risk, inga nya beroenden".
2. **`design_system.md` får ändras, men aldrig tyst.** Där granskningen bryter mot
   en dokumenterad regel namnges regeln, motiveras avvikelsen och dokumentet
   ändras i samma ändring. Regler som håller behålls. Se avsnitt 12.
3. **Målgrupp: publik och anonym.** Vem som helst kan öppna appen. Det finns
   ingen inloggning och därmed ingen ärlig serverlagring per student. Onboarding,
   tomma tillstånd och degraderade tillstånd bär därför mer vikt än i en app med
   konton.

**Ramar:** enbart Streamlit, inga nya beroenden, inga ikoner. Varje förslag anger
vilket problem det löser, varför det förbättrar lärandet, vilken etablerad
UX-praxis det följer, och insatsen (Låg/Medel/Hög). Rent dekorativa förslag är
avvisade. Avsnitt 11 vänder sig mot granskningens egna rekommendationer.

---

## 1. Sammanfattning

### Helhetsbedömning

Appen är ovanligt välbyggd i sitt fundament och ovanligt svag i sin vägledning.
Den pedagogiska grunden är genuint bra: studenten skriver före återkopplingen
(generationseffekten), rättningen är deterministisk innan någon LLM anropas,
lagrum verifieras mot ett register, och `VERIFIERINGSNOT` i `utils/ui.py`
lär ut den svåraste insikten av alla — att ett lagrum kan existera utan att vara
tillämpligt. Det är omdömesgillt gjort och ovanligt hos utbildningsappar.

Problemet ligger inte i innehållet utan i *vägledningen*. Appen svarar aldrig på
frågan "vad ska jag göra nu?". Den visar hela svensk rätt i sidopanelen, ger
studenten tolv likvärdiga rättsområdesmoduler, tre likvärdiga flikar per modul, och
placerar svårast möjliga uppgift först. En nybörjare möter ett fritextfält som
ber dem identifiera en rättsfråga utan att någonstans ha sett hur en rättsfråga
formuleras. Kursens ordning finns redan som data och används aldrig.

Sammanfattat: **appen är byggd för någon som redan vet hur man studerar juridik.**
Omdesignen handlar om att göra den brukbar för den som inte vet det, utan att
förlora det som redan fungerar.

### Främsta styrkor

* **Deterministiskt först.** Quiz, lagrumsjakt och Normfältet rättas utan LLM.
  Tutorn är alltid ett tillägg, aldrig en förutsättning. Det gör appen ärlig när
  modellen är otillgänglig — vilket i en publik driftsättning är ett normaltillstånd.
* **Verifieringskedjan.** `utils/granskning.py` stoppar underkända tutorsvar helt
  hellre än att visa osäker juridik, och den underkända texten sparas medvetet
  inte (`utils/tutor.py`, `Tutorsvar.godkand`). Det är rätt avvägning.
* **Färgsemantik med en enda stark regel.** Guld betyder alltid lagrum. En
  student lär sig den kopplingen på minuter och kan sedan skanna en sida visuellt.
* **Läsbarhet för långtext.** 46rem radlängd, 17px/1.65, serifrubriker. Appen är
  byggd för att bära scenariotext, och det märks.
* **Rättskartan är komplett dag noll.** Referensmaterialet kräver varken tutor
  eller genomförda övningar. Det ger en nybörjare någonstans att gå som inte
  kräver prestation.

### Främsta svagheter

1. **Ingen nästa handling.** `cta_mal()` pekar mot *senast besökta* modul, inte
   mot nästa i kursen. En student som råkar öppna Associationsrätt skickas dit
   för alltid. Startsidans enda knapp kan alltså aktivt leda fel.
2. **RNTS är osynligt utom i formuläret.** Ryggraden syns som fyra `text_area`
   och en stepper på 1/4 spaltbredd i flik ett. Lagrumsjakten tränar *Norm*,
   Nyckelbegrepp tränar *Rättsfrågan*, quizet tränar *Tillämpning* — ingen av dem
   säger det.
3. **Allt väger lika mycket.** Tre flikar i fast ordning med svåraste uppgiften
   först. Ingen ramp från igenkänning till fri produktion.
4. **Ingenting överlever att fliken stängs, och appen säger det inte.** All
   framgång ligger i `st.session_state`. Rubriken "Dina resultat den här
   sessionen" är det enda som antyder det.
5. **Startsidan skriker om det oviktiga.** För en förstagångsbesökare är sidans
   visuellt starkaste element en blå ansvarsfriskrivning, följd av ett tomt
   framstegsmeddelande och en Obsidianförklaring. Tre informationskort och två
   knappar konkurrerar med den enda handling sidan vill åstadkomma.
6. **Två aviseringssystem.** `st.info/success/error/warning` blandas med
   `jok-info`/`jok-varning` på samma sida (se `utils/modulvy.py`). Samma
   betydelse får två utseenden och samma utseende två betydelser.
7. **Specifikationen har glidit från koden.** `design_system.md` §3 listar
   `render_quizfraga(fraga)` som en komponent; den finns inte i `utils/ui.py`.
   `render_kort` och `summary_box` finns men används bara av testerna.

### Största möjligheterna

| # | Möjlighet | Vinst | Insats |
|---|---|---|---|
| 1 | Låt nästa steg vara nästa i kursen, inte senast besökta | Tar bort appens allvarligaste vägledningsfel | Låg |
| 2 | Märk varje aktivitet med det RNTS-steg den tränar | Gör ryggraden synlig utan ny funktionalitet | Låg |
| 3 | Ramp inom modulen: igenkänning → hågkomst → produktion | Sänker ingångströskeln utan att sänka kraven | Medel |
| 4 | En framstegssida i stället för tre halva | Besvarar "hur långt har jag kommit?" på ett ställe | Medel |
| 5 | Var ärlig om att sessionen är flyktig, och gör exporten till svaret | Bygger tillit; exporten finns redan | Låg |

---

## 2. Informationsarkitektur

### Nuvarande arkitektur

Sidopanelen ritas av `render_sidopanel()` ur `NAV_TRAD` i `utils/navigation.py`:

```
START OCH METOD          Hem · Juridisk metod · Rättskartan
OFFENTLIG RÄTT           Statsrätt (kommer) · Förvaltningsrätt (kommer)
CIVILRÄTT
  Personrätt             Personrätt
  Förmögenhetsrätt       Allmän förmögenhetsrätt
    Kontraktsrätt        Avtalsrätt · Köp- och konsumenträtt · Fastighetsrätt
    Ersättningsrätt      Skadeståndsrätt
    Näringsrätt          Arbetsrätt · Associationsrätt
    Kredit- och obeståndsrätt   Fordringsrätt
  Familjerätt            Familje- och successionsrätt
STRAFF- OCH PROCESSRÄTT  Straff- och processrätt
TRÄNING                  Kunskapstest · Kunskapskarta · Kunskapsutmaning
```

### Problem

**P1 — Två oförenliga ordningsprinciper i samma träd.** "CIVILRÄTT" och
"OFFENTLIG RÄTT" är rättssystematik. "START OCH METOD" och "TRÄNING" är
appfunktioner. De ritas med exakt samma komponent (`.jok-nav-kategori`) och samma
typografiska vikt. Studenten kan därför inte avgöra om sidopanelen är en karta
över rätten eller en lista över verktyg. Den är båda, och signalerar ingetdera.
"Hem" ligger sorterat under en doktrinärt klingande rubrik.

**P2 — Djupet kostar mer än det ger.** För att nå Avtalsrätt passerar blicken
CIVILRÄTT → Förmögenhetsrätt → Kontraktsrätt: tre abstraktioner som en nybörjare
inte kan tolka, före den första klickbara saken. Systematiken är värdefull, men
den betalas i sin helhet innan studenten fått något tillbaka.

**P3 — "TRÄNING" innehåller tre olika slags saker.** Läser man
`sidor/9_Kunskapstest.py` visar det sig att Kunskapstest inte testar något: den
listar resultat och länkar tillbaka till moduler. Det är en resultattavla.
Kunskapskarta är en visualisering av studentens eget arbete. Bara
Kunskapsutmaning är träning. Namnet *Kunskapstest* lovar ett prov som inte finns.

**P4 — Framsteg finns på tre ställen och är helt på inget.** Hem visar quizandel
per modul plus genomförda fall plus export. Kunskapstest visar quizresultat igen.
Kunskapskarta visar de genomförda fallen som graf. Tre ytor besvarar samma fråga,
ingen fullständigt.

**P5 — Två "kartor" med snarlika namn och motsatta syften.** Rättskartan är
kursens referens, komplett dag noll. Kunskapskartan är studentens personliga
artefakt, tom dag noll. `design_system.md` §4.2 måste uttryckligen varna för att
de förväxlas — när dokumentationen behöver en varning är namngivningen problemet.

**P6 — Två döda poster i full vikt.** Statsrätt och Förvaltningsrätt visas som
egna rader med "(kommer)". Avsikten är god (visa kursens omfång), men priset är
att kategorin direkt efter START OCH METOD är helt oklickbar — det första
studenten möter under rubriken OFFENTLIG RÄTT är två återvändsgränder.

### Rekommenderad arkitektur

Tre plan, namngivna efter vad studenten vill göra — inte efter vad koden innehåller:

```
STUDERA
  Nästa steg                 (Hem: var du är, vad som kommer härnäst)
  Juridisk metod
  ── kursens moduler i systematisk ordning ────────────────
  Personrätt
  Förmögenhetsrätt
    Allmän förmögenhetsrätt
    Kontraktsrätt            Avtalsrätt · Köp- och konsumenträtt · Fastighetsrätt
    Ersättningsrätt          Skadeståndsrätt
    Näringsrätt              Arbetsrätt · Associationsrätt
    Kredit- och obeståndsrätt  Fordringsrätt
  Familjerätt                Familje- och successionsrätt
  Straff- och processrätt
  Blandad träning            (f.d. Kunskapsutmaning)
  Offentlig rätt kommer senare.        ← en dämpad rad, inte två poster

SLÅ UPP
  Rättskartan                (systemet, falltypsguide, nyckelbegrepp)

MINA FRAMSTEG
  Framsteg och samband       (f.d. Kunskapstest + Kunskapskarta + export)
```

Förändringar mot i dag:

| Åtgärd | Motiv |
|---|---|
| `START OCH METOD` och `TRÄNING` upphör | De var appfunktioner klädda som rättsområden (P1) |
| Doktrinära rubriker behålls oförändrade inuti `STUDERA` | Systematiken är kursens värde; den flyttas, förminskas inte |
| `Kunskapstest` + `Kunskapskarta` → **Framsteg och samband** | Ett svar på "hur långt har jag kommit" (P3, P4) |
| `Kunskapsutmaning` → **Blandad träning**, placerad i `STUDERA` | Det är faktiskt träning, och namnet förklarar varför den finns |
| `Kunskapskarta` som namn upphör | Löser namnkollisionen med Rättskartan (P5) |
| Två "(kommer)"-poster → en dämpad mening | Omfånget syns, men tar inte plats som navigering (P6) |
| `Hem` → **Nästa steg** | Etiketten beskriver sidans uppgift, inte dess filnamn |

**Varför tre plan.** Studera / Slå upp / Mina framsteg motsvarar de tre
tillstånd en student faktiskt befinner sig i: jag arbetar, jag behöver kolla
något, jag vill veta hur det går. Det är samma indelning Stripes dashboard och
Linears sidopanel använder — arbetsytor först, referens sedan, kontoläge sist —
och den låter varje plan ha sin egen visuella täthet. Rättssystematiken behålls
i sin helhet inuti planet där den hör hemma, så `design_system.md` §4.1:s premiss
(studenten ska kunna se hela rättssystemet på en gång) överlever oförändrad.

**Vad detta löser, och för vem.** Nybörjaren får ett träd där det klickbara
kommer före det abstrakta, och där ingen rubrik ljuger om vad den innehåller.
Den vane studenten förlorar ingenting: samma sidor, samma ordning, kortare väg.
**Insats: Medel** (en omstrukturering av `NAV_TRAD`, en sammanslagen sida, två
omdöpta sidor; `tests/test_navigation.py` vaktar redan att träd och sidregister
hålls i synk och måste följa med).

---

## 3. Startsidan

### Vad som är fel i dag

`sidor/0_Hem.py` renderar, i ordning: hero → blå ansvarsfriskrivning →
NÄSTA STEG med en knapp → FRAMSTEG → ARBETSGÅNG → sidfot. Strukturen är rimlig.
Tre saker gör den ändå fel för en förstagångsbesökare:

* **Friskrivningen är sidans visuellt starkaste element.** `render_info` ger en
  mättad blå ram direkt under hero, före den enda handlingen. Det första appen
  betonar är alltså en juridisk brasklapp, som inte lär ut något.
* **Det tomma tillståndet är fullt av knappar.** Utan resultat visas: ett
  `st.info` om att inget finns, en nedladdningsknapp för Obsidianvalvet, och ett
  `st.info` som förklarar Obsidian. Tillsammans med friskrivningen ger det tre
  informationskort och två knappar på en sida vars uppgift är *börja här*.
* **RNTS nämns men definieras inte.** Hero-texten säger "identifiera rättsfrågan,
  hitta rätt lagrum, tillämpa normen och dra en slutsats" — och sist på sidan
  upprepar ARBETSGÅNG samma fyrstegsidé med andra ord. Två komponenter lär ut
  samma sak i olika vokabulär, och ingen av dem namnger RNTS.

### Ny startsida, uppifrån och ner

**1. Hero — progressiv, två tillstånd.**
Första besöket: ögonbryn `JURIDISK ÖVERSIKTSKURS`, rubrik *Träna att tänka
juridiskt, inte att läsa passivt*, en mening om metoden. Återkommande i samma
session: hero krymper till en rad. Sidans överkant ska inte upprepa vad studenten
redan läst.
*Problem:* konstant hög introduktionskostnad. *Lärande:* frigör första skärmen åt
handling. *Praxis:* progressive disclosure. *Insats: Låg.*

**2. Friskrivningen — kvar, men dämpad.**
En `st.caption`-rad direkt under hero: "Studieverktyg, inte juridisk rådgivning.
Mata inte in personuppgifter." Fullständig text står redan i `footer_note()`.
Kravet i PRD 4 uppfylls; kravet var synlighet, inte dominans.
*Problem:* det oviktiga är starkast. *Lärande:* uppmärksamheten går till uppgiften.
*Praxis:* visuell hierarki efter uppgiftsvärde. *Insats: Låg.*

**3. NÄSTA STEG — ett kort, inte bara en knapp.**
Kortet svarar på fyra frågor innan studenten klickar: vilken modul, vilket
RNTS-steg det tränar, ungefärlig tid, och varför just den. Exempel:

```
NÄSTA STEG
Avtalsrätt · kap. 7
Tränar Norm och Tillämpning · ca 15 min
Du har gjort Juridisk metod. Avtalsrätt är kursens första
egentliga rättsområde och bygger på den.
[ Börja: Avtalsrätt → ]                    Fortsätt där du var (Arbetsrätt)
```

Målet byts: `cta_mal()` ska föredra **nästa ej påbörjade modul i kursordning**
(ordningen finns redan i `NAV_TRAD`), med "fortsätt där du var" som en tystare
sekundärlänk när båda finns. I dag är det omvänt, vilket är appens allvarligaste
enskilda vägledningsfel.
*Problem:* knappen kan leda fel; ingen vet vad som kommer härnäst. *Lärande:*
sekvensering är den mest grundläggande skaffoldningen som finns. *Praxis:* en
primär handling per skärm, med kontext (Duolingo, Khan Academy). *Insats: Låg.*

**4. RNTS-panelen — den bärande nyheten.**
De fyra stegen på appens första skärm, med en rad klarspråk var:

```
METODEN
Rättsfrågan   Vad är det egentligen som ska avgöras?
Norm          Vilken paragraf styr frågan?
Tillämpning   Hur faller omständigheterna ut mot paragrafen?
Slutsats      Vad blir svaret?
```

Samma komponent har två tillstånd. Utan data är den *förklaringen*. Med data
lägger den till vad studenten hittills arbetat med per steg. Den ersätter
ARBETSGÅNG helt: en fyrstegspipeline och en fyrstegsmetod på samma sida är
samma sak sagd två gånger.
*Problem:* appens ryggrad är osynlig; RNTS namnges aldrig där studenten börjar.
*Lärande:* chunking — fyra namngivna steg är ett schema studenten kan hänga allt
efterföljande på. *Praxis:* progressive disclosure, en modell i stället för två
vokabulär. *Insats: Medel.*

**5. FRAMSTEG — kort, ärligt, länkat.**
Ersätt listan av `st.progress` per modul (den växer obegränsat och visar bara
det studenten råkat röra) med tre tal på en rad — moduler påbörjade, fall
genomförda, quizandel — och en länk till *Framsteg och samband*. Under dem, en
rad som säger sanningen: "Framstegen gäller den här sessionen. Ladda ner dem för
att behålla dem." Nedladdningsknapparna flyttas dit de hör hemma och visas inte
alls när det inte finns något att ladda ner.
*Problem:* tre halva framstegsytor; tyst dataförlust; knappar utan innehåll.
*Lärande:* tillit är en förutsättning för ansträngning. En student som förlorat
en timmes arbete utan varning kommer inte tillbaka. *Praxis:* ärliga tomma
tillstånd; inga kontroller utan effekt. *Insats: Låg.*

**6. Sidfot.** `footer_note()` oförändrad: fullständig friskrivning och version.

### Vad studenten kan besvara på tio sekunder

| Fråga | Vad som svarar |
|---|---|
| Var är jag? | Hero + sidopanelens markerade plan |
| Vad är det här? | Hero-rubriken, en mening |
| Varför finns det? | RNTS-panelen: appen lär ut en metod, inte fakta |
| Var börjar jag? | NÄSTA STEG-kortet, en primär knapp |
| Vad gör jag sedan? | Samma kort, och det uppdateras |
| Hur långt har jag kommit? | FRAMSTEG, tre tal |
| Vad är mitt nästa mål? | Modulnamn + RNTS-steg i kortet |

---

## 4. Sidopanelen

### Bedömning av det som finns

Sidopanelen är appens mest genomtänkta yta och behöver minst omarbetning.
`design_system.md` §4.1 är välargumenterad: fyra nivåer skilda med indrag,
storlek och färgstyrka, aldrig ikoner; guld aldrig i navigering; hela trädet
synligt. Det är rätt, och det behålls.

Fem konkreta brister:

1. **Ingen kontext för var du är.** `st.page_link` markerar den aktiva sidan,
   men de egna rubrikerna vet inget: inget säger att *Förmögenhetsrätt →
   Kontraktsrätt* innehåller den öppna sidan. Datat finns redan —
   `streamlit_app.py:63` lägger `_jok_aktiv_sida` i session_state och ingen
   läser det.
2. **Statuspanelen har samma vikt som navigeringen.** Fyra rader om LLM-modell
   och anropsbudget, alltid utfällda, plus en modellväljare. För en publik
   besökare betyder "Anrop kvar i sessionen 40/40" ingenting.
3. **Ikoner har läckt in.** `🟢`/`⚪` i `render_statuspanel()` bryter mot appens
   egen regel.
4. **Modellväljaren är utvecklaryta i en publik app.** 8B/14B är ett val ingen
   student kan grunda — och enligt tidigare mätning är 14B inte bättre.
5. **Trädet är långt för att det innehåller sådant som inte är rättsområden.**
   Problemet §4.1 skyddade mot är längden, inte öppenheten. Avsnitt 2 löser det
   genom att flytta fyra poster, inte genom att fälla ihop något.

### Ny sidopanel

```
Juridisk översiktskurs
Fallbaserad träning med RNTS-metoden
────────────────────────────────
STUDERA
  Nästa steg
  Juridisk metod

  Personrätt
    Personrätt
  Förmögenhetsrätt
    Allmän förmögenhetsrätt
    Kontraktsrätt
      Avtalsrätt              3/5
      Köp- och konsumenträtt
      Fastighetsrätt
    Ersättningsrätt
      Skadeståndsrätt
    …
  Straff- och processrätt
  Blandad träning
  Offentlig rätt kommer senare.
────────────────────────────────
SLÅ UPP
  Rättskartan
────────────────────────────────
MINA FRAMSTEG
  Framsteg och samband
────────────────────────────────
Tutorn: tillgänglig
```

**Hierarki och gruppering.** Tre plan i versal monospace (`.jok-nav-kategori`,
oförändrad stil). Inuti `STUDERA` behålls den doktrinära nivåtrappan exakt som
§4.1 beskriver den.

**Ikoner.** Inga. Regeln utvidgas i avsnitt 12 från att gälla navigeringen till
att gälla hela appen.

**Framstegsmarkering.** En dämpad siffergrupp (`3/5`) höger om modulnamnet, i
kapitälhöjd och grå — endast för moduler där arbete faktiskt registrerats.
*Problem:* studenten måste öppna en modul för att minnas om den är gjord.
*Lärande:* igenkänning slår hågkomst; det avlastar arbetsminnet för juridiken.
*Praxis:* Notions och GitHubs dämpade metadata i sidopaneler. *Insats: Medel*
(kräver framstegsdata per modul i navigeringslagret).
Avvisat: procentstaplar per modul. De gör en karta till en instrumentpanel, och
med sessionsdata står de på noll varje gång studenten kommer tillbaka — det är
demoraliserande utan att vara informativt.

**Aktiv sida i sammanhang.** Rubrikkedjan ovanför den öppna sidan får bläckvikt
i stället för grått, så blicken hittar sin plats i trädet utan färg eller ikon.
*Problem:* ingen orientering i ett fyra nivåer djupt träd. *Lärande:* minskad
extraneous load — man ska inte behöva leta efter sig själv. *Praxis:* aktiv
sökväg i VS Code, Obsidian, Linear. *Insats: Låg* (datat finns redan).

**Statuspanel.** En rad: "Tutorn: tillgänglig". Den expanderar till dagens
detaljer bara när något faktiskt är begränsat — under en fjärdedel återstående,
eller otillgänglig. Modellväljaren flyttas ur sidopanelen.
*Problem:* driftinformation konkurrerar med navigering. *Lärande:* mindre
extraneous load. *Praxis:* systemstatus syns när den betyder något (Stripe).
*Insats: Låg.*

**Sökfält och fästa objekt: avvisas.** Sjutton poster motiverar inte en sökruta
som i Streamlit dessutom kostar en rerun per tangenttryck. Och sökningen finns
redan, för den fråga studenten faktiskt ställer: Rättskartans falltypsguide
svarar på "vilken lag gäller för mitt fall?". Bättre att peka dit än att bygga
en sämre variant i panelen.

**Hopfällbara sektioner: avvisas, med reservation.** Se avsnitt 11.

---

## 5. Komponenter

Genomgång av varje komponent som bär vikt. Format: iakttagelse → åtgärd → insats.

### Navigering och ram

**`hero()`** — bra typografiskt. Används identiskt på alla sidor, även där
ingressen upprepar vad rubriken redan sagt (`_ingress()` i `utils/modulvy.py`
ignorerar sitt `filnamn`-argument och ger samma text på alla tolv modulsidor).
Åtgärd: låt modulsidans ingress säga något
modulspecifikt, eller ta bort den. En mening som är sann för alla moduler bär
ingen information. *Insats: Låg.*

**`section_heading()`** — konsekvent och bra. Behålls.

**`footer_note()`** — behålls oförändrad.

**`render_sidhjalp()`** — mönstret (hopfälld expander, 3–5 punkter) är rätt, men
används bara på Rättskartan. §4.3 säger "varje sida". Åtgärd: antingen inför den
överallt eller ändra regeln. Specifikation som inte följs är sämre än ingen.
*Insats: Låg.*

### Kort och behållare

**`render_kort()` och `summary_box()`** — död kod, refererade bara av
`tests/test_ui.py`. `render_kort` har dessutom en `ikon`-parameter som strider mot
ikonregeln. Åtgärd: ta bort båda, eller gör `render_kort` till den enda
kortprimitiven som avsnitt 6 föreslår. *Insats: Låg.*

**`render_case()`** — bra: guldlinje överst, metadatarad, begränsad radlängd.
Latent brist: hela scenariotexten läggs i ett enda `<p>` utan radbrytshantering,
till skillnad från `_tutortext_html()` som översätter `\n\n`. Inget nuvarande
scenario innehåller radbrytningar, så felet syns inte — men det utlöses av det
första flerstyckesscenariot någon skriver. Åtgärd: samma stycketolkning som
tutortexten. *Insats: Låg.*

**`render_lagkort()` / `render_begreppskort()`** — de starkaste komponenterna i
appen. Begreppskortets fyra fasta fält, och guldstreckade igenkänningsfältet som
kopplar begreppet till RNTS-steget Rättsfrågan, är utmärkt pedagogisk design.
Behålls oförändrade. En anmärkning: `jok-begrepp h3` är 19px och bryter
typskalan (18 eller 20, se avsnitt 6).

### RNTS-formuläret — appens viktigaste yta

**`render_rnts_steg()`** — tre problem.

1. *Statusarna är nästan meningslösa.* `_rnts_statusar()` ger "pågår" för varje
   icke-tomt fält. Ett enda tecken i Tillämpning ser ut som framsteg. Bara Norm
   bedöms på riktigt (mot lagrumsregistret).
2. *Glyferna `●`, `✓`, `!` är ikoner.* Åtgärd: rita tillstånden med CSS —
   ofylld ring, fylld ring, fylld ring med bock i ren form — utan teckenglyfer.
3. *Placeringen isolerar den.* `st.columns([1, 3])` lägger steppern i en smal
   ränna vid sidan av formuläret. Åtgärd: lägg den ovanför formuläret i full
   bredd, som en vågrät fyrstegsindikator.

*Problem:* den enda ytan som visar metoden är dekorativ. *Lärande:* en stepper
som mäter något verkligt ger formativ återkoppling; en som mäter tecken ger
falsk trygghet. *Praxis:* framstegsindikatorer måste vara sanna. *Insats: Medel.*

**RNTS-fälten** — fyra `text_area` på 90px, samma placeholder varje gång, ingen
förlaga. `_norm_feedback()` är däremot utmärkt: chips direkt, varning vid
overifierat, allt utan LLM. Åtgärd: lägg ett hopfällt "Så kan ett svar se ut"
intill Rättsfrågan i modulens första fall (fadande skaffoldning, se avsnitt 7),
och låt Normfältets placeholder visa formen i stället för att förklara den.
*Insats: Medel* (kräver ett författat exempel per modul).

**Fältordning och knappar.** På skärmen ligger i dag: svårighetsväljare, två
knappar, en selectbox, scenariokort, stepper, fyra fält, en caption, tutorknapp
(`type="primary"`), en facitexpander. Två primära knappar samtidigt
("Generera nytt rättsfall" och tutorknappen) och sex kontroller innan studenten
skrivit ett ord. Åtgärd: se avsnitt 10, modulsidan.

**Facitexpandern** — ligger direkt under tutorknappen, öppen för ett klick innan
studenten försökt. Åtgärd: göm bakom en enkel avsiktsbekräftelse ("Jag har
försökt — visa facit"), inte en låsning. *Lärande:* desirable difficulty; ett
facit som är gratis före försöket tar bort hela generationseffekten appen bygger
på. *Insats: Låg.*

### Quiz och lagrumsjakt

**Quizfrågan** — `design_system.md` §3 specificerar `render_quizfraga(fraga)`.
Den finns inte. I stället ritar `_rendera_quizfraga()` fet markdown, en radio,
en Svara-knapp och `st.divider()` mellan varje fråga. Följder: frågorna är inte
kort, rubrikerna är inte rubriker, och resultatet försvinner om studenten
avmarkerar radion (villkoret är `st.session_state.get(...) and valt is not None`).
Åtgärd: implementera komponenten som specifikationen redan beskriver, och låt
resultatet överleva avmarkering. *Insats: Medel.*

**Lagrumsjakten** — en verklig bugg: `with st.expander("Visa facit")` ligger
inuti `if st.button("Rätta")`-blocket (`utils/modulvy.py:457–474`). Facit visas
alltså bara i den rerun där knappen trycktes och försvinner vid nästa
interaktion. Dessutom visas facit direkt vid första felsvaret, tillsammans med
ledtråden — ingen anledning att försöka igen. Åtgärd: flytta expandern ut ur
blocket; visa ledtråd först, facit efter ytterligare ett försök.
*Lärande:* retrieval practice kräver att hågkomsten får kosta något.
*Insats: Låg.*

**Svårighetsväljaren** — `st.segmented_control` med Grund/Medel/Avancerad,
placerad överst innan studenten sett ett enda fall. En nybörjare kan inte välja
nivå på en uppgiftstyp de aldrig mött. Åtgärd: förvälj Grund för sessionens
första fall i en modul, och flytta väljaren intill genereringsknappen med en
förklarande rad. *Insats: Låg.*

### Aviseringar och tutor

**Två aviseringssystem.** `utils/modulvy.py` använder `st.info`, `st.success`,
`st.error`, `st.warning` *och* `render_varning`/`render_info`. Samma betydelse
får två utseenden. Åtgärd: en enda uppsättning — `jok`-korten — med fyra
dokumenterade roller: instruktion (blå), varning (gul), rätt (grön), fel (rött).
Streamlits egna används inte i studentflöden. *Insats: Medel* (många anropsställen).

**`render_info()` bär fyra betydelser** — friskrivning, tomt tillstånd,
tutor otillgänglig, inaktuellt svar. Åtgärd: skilj *instruktion* från
*systemtillstånd*; systemtillstånd ska vara tystare, inte likvärdigt.
*Insats: Låg.*

**`render_tutortext()`** — mycket bra. Verifierade lagrum blir chips,
overifierade samlas i en varningsruta, RNTS-rubriker blir kapitäler i blått, och
`VERIFIERINGSNOT` förklarar vad verifieringen *inte* betyder. Behålls. Enda
åtgärd: noten ligger i `st.caption` under varje svar och blir därmed brus vid
upprepad läsning. Se avsnitt 7.

**`tutorknapp()`** — degraderingen är föredömlig (tre feltyper, tre svenska kort,
`reservhanvisning` pekar mot deterministiskt underlag). En brist: när
granskningen underkänner svaret får studenten en gul varning som handlar om
appens interna verifiering. Det är systemets problem formulerat som studentens.
Åtgärd: led med vad som fungerar ("Facit nedan visar analysen"), nämn orsaken
kort därefter. *Insats: Låg.*

### Övrigt

**Nedladdningsknappar** — tre på startsidan i samma vikt (Markdown, Excel,
Obsidianvalv). Åtgärd: flytta till *Framsteg och samband*; en primär (valvet,
som är det pedagogiskt intressanta) och två sekundära.
*Insats: Låg.*

**Falltypsguidens `st.dataframe`** — en tabell mitt i en app som annars består av
kort. Den fungerar, men "Börja här"-kolumnen innehåller lagförkortningar som
inte är chips och därmed inte klickbara — guldregeln bryts på appens mest
sökorienterade yta. Åtgärd: rendera träfflistan som kompakta rader med riktiga
lagrumschips. *Insats: Medel.*

**Justeringshack** — `st.caption("&nbsp;", unsafe_allow_html=True)` i
`sidor/11_Kunskapsutmaning.py` finns bara för att trycka ner en knapp i linje med
en selectbox. Åtgärd: `st.columns` med `vertical_alignment="bottom"`.
*Insats: Låg.*

---

## 6. Visuell design

### Typografi

Grunden är bra: 46rem radlängd, 17px/1.65 brödtext, systemserif i rubriker, inga
typsnittsfiler eller CDN. Två brister:

**Skalan har hål och dubbletter.** 28 (hero h1) → 22 (section h2) → 19
(begrepp h3) → 18 (kort/case h3) → 16 (lagkort h4). 19 och 18 gör samma jobb.
Och etikettrollen har tre storlekar: 14px (hero/section eyebrow), 12px
(nav-kategori), 11px (avsnittsrubrik).

Föreslagen skala, som CSS-variabler:

| Token | px | Roll |
|---|---|---|
| `--t-hero` | 28 | Sidrubrik, en per sida |
| `--t-h2` | 22 | Avsnittsrubrik |
| `--t-h3` | 18 | Kortrubrik |
| `--t-brod` | 17 | Brödtext, scenarier |
| `--t-ui` | 15 | Kontroller, kortmetadata |
| `--t-etikett` | 13 | Kapitäler, chips, metadata |

*Problem:* fem rubriknivåer utan tydlig rangordning. *Lärande:* konsekvent
typografi låter studenten skanna i stället för att läsa allt. *Praxis:* en
modulär skala med begränsat antal steg. *Insats: Låg.*

### Spacing

Marginalerna i `inject_css()` är handsatta: `.1`, `.15`, `.2`, `.35`, `.4`,
`.45`, `.5`, `.6`, `.7`, `.8`, `1.1`, `1.8`, `2` rem. Ingen skala, alltså ingen
visuell rytm — avstånden signalerar inte gruppering.

Föreslagen 4px-bas som variabler: `--s1` 4px, `--s2` 8px, `--s3` 12px, `--s4`
16px, `--s5` 24px, `--s6` 32px, `--s7` 48px. Regeln: avstånd *inom* en grupp
aldrig större än avstånd *mellan* grupper.
*Problem:* gruppering syns inte. *Lärande:* närhet är den starkaste
grupperingssignal som finns; korrekt spacing gör struktur läsbar utan ramar.
*Praxis:* spacing-skala (Material 3, Apple HIG). *Insats: Låg.*

### Kort, radier och skuggor

Nuvarande radier: 12px (`kort`, `case`, `begrepp`), 10px (`lagkort`, `varning`,
`info`, `tutortext`), 8px (`igenkanning`), 6px (`skillnad`), 999px (chips,
pipeline). Skuggan `0 1px 3px rgba(26,35,50,.06)` finns på `kort`, `case`,
`begrepp` men inte på `lagkort` eller `tutortext`. Och 3px vänsterlinje används
till tre olika saker: tutortext (blå), lagkort (guld), skillnad (blå).

Föreslagen ordning:

| Primitiv | Radie | Ram | Skugga | Används till |
|---|---|---|---|---|
| Kort | 12px | 1px `--ram` | ja | Innehållsblock: case, begrepp, quizfråga |
| Panel | 10px | 1px | nej | Referens: lagkort, tutortext |
| Not | 10px | 1px färgad | nej | Instruktion, varning, resultat |
| Chip | 999px | 1px `--guld` | nej | Enbart lagrum |

Vänsterlinjen får en enda betydelse: *citat eller härlett innehåll* (tutortext,
skillnadsrad). Lagkortets guldlinje flyttar till överkanten, som `render_case`
redan gör — då betyder en guldlinje överst konsekvent "det här handlar om lagrum".
*Problem:* fyra radier och två skuggregimer utan systematik. *Lärande:*
konsekvent form gör att studenten känner igen *typ av innehåll* före den läst det.
*Praxis:* ett kortsystem med dokumenterade varianter. *Insats: Medel.*

### Färg

Paletten i `design_system.md` §1 är välargumenterad och behålls i sin helhet.
Två problem:

**Odokumenterade literaler.** `#6B6459`, `#4A453D`, `#9A9384`, `#F5F1EA`,
`#EAF1F7`, `#FFFDF7` förekommer i CSS men finns varken i paletten eller bland
Python-konstanterna. Åtgärd: befordra till namngivna tokens (`--gra-text`,
`--gra-svag`, `--yta-lugn`) eller ta bort.

**En färg med två betydelser.** `#6B6459` är både undergrensfärg i navigeringen
(`.jok-nav-gren`) och grenfärg för *offentlig rätt* i taxonomigrafen
(`GRENFARGER`). Samma värde bär alltså en navigerings- och en doktrinär
betydelse. Åtgärd: ge grafens offentligrättsgren en egen, dokumenterad ton.
*Problem:* färgsemantiken är appens starkaste inlärda regel och urholkas av
kollisionen. *Insats: Låg.*

### Ikoner

Regeln i §4.1 gäller bara navigeringen. Fyra glyfer har läckt in:

| Glyf | Plats | Åtgärd |
|---|---|---|
| `🟢` `⚪` | `render_statuspanel()` | Ersätt med ordet ("tillgänglig") |
| `🎲` | "Överraska mig", Kunskapsutmaning | Ta bort glyfen, behåll texten |
| `↺` | Två "Rensa"-knappar, Rättskartan | Ta bort glyfen |
| `●` `✓` `!` | `_RNTS_IKONER` | Ersätt med CSS-ritade tillstånd |
| `⚖️` | `page_icon` i `streamlit_app.py` | Se nedan |

`page_icon` är ett gränsfall och bör avgöras uttryckligen. Den är inte
appkrom utan webbläsarflikens identitet, och det är den enda plats där en ikon
gör något ord inte kan: skilja fliken från tjugo andra. **Rekommendation:
behåll `⚖️` som dokumenterat undantag och fäll de fyra övriga.** Vill du ha noll
glyfer i projektet är alternativet `page_icon=None`, till priset av en anonym
flik.
*Insats: Låg.*

### Mikrointeraktioner och animationer

I dag finns i praktiken inga, utöver Streamlits egna och `st.spinner`. Det är
nästan rätt. Två som förtjänar sin plats:

* **Hovring på lagrumschips.** Understrykning vid hovring finns redan på
  `.avsnittsrad .spann` men inte på `.jok-chip`. Att alla guldchips beter sig
  likadant förstärker regeln "guld = klickbart lagrum". *Insats: Låg.*
* **Spinnertexterna.** "Tutorn läser ditt svar …" och "Genererar ett nytt
  rättsfall och kontrollerar lagrummen …" är redan förklarande, inte generiska.
  Behålls som mönster.

**Avvisas:** konfetti, poäng, streak-animationer, animerade framstegsstaplar.
De är extraneous load och belönar fel sak. I en app om juridiskt resonemang ska
belöningen vara att förstå ett rekvisit, inte att en stapel fylls. Det är också
skälet att appen inte ska härma Duolingos belöningsslinga — den är byggd för
vanebildning i korta moment, inte för analytiskt arbete i femtonminuterspass.

---

## 7. Lärandeupplevelsen

Hur gränssnittet självt kan lära ut juridik bättre.

**7.1 Märk varje aktivitet med det RNTS-steg den tränar.** Lagrumsjakt tränar
Norm. Nyckelbegrepp tränar Rättsfrågan. Quiz tränar Tillämpning. Rättsfall
tränar alla fyra. I dag säger ingen av dem det. En kapitälrad över varje
aktivitet räcker: `TRÄNAR: NORM`.
*Problem:* studenten samlar övningar utan att se att de bygger samma förmåga.
*Lärande:* det är hela överföringsmekanismen — RNTS ska bli ett schema, inte ett
formulär. *Praxis:* etiketter som gör struktur explicit. *Insats: Låg.*

**7.2 Ramp inom modulen: igenkänning → hågkomst → produktion.** Flikordningen är
i dag Rättsfall, Quiz, Lagrumsjakt — svårast först. Föreslagen ordning:
Nyckelbegrepp för modulen (igenkänning) → Lagrumsjakt (styrd hågkomst) → Quiz
(tillämpning i valsituation) → Rättsfall (fri produktion). Ingen låsning; bara
ordning, med en rad som förklarar varför.
*Problem:* nybörjaren möter fri produktion före allt annat. *Lärande:*
scaffolding och gradvis ökande svårighet. *Praxis:* Brilliant och Khan Academy
bygger båda upp mot fri uppgift. *Insats: Medel.*

**7.3 Fadande skaffoldning på Rättsfrågan.** Det svåraste steget för en
nybörjare är att formulera rättsfrågan — de vet inte ens vilken *form* svaret
ska ha. För modulens **första** fall: erbjud tre kandidatformuleringar att välja
bland, varav en är rimlig, med kort motivering efter valet. Därefter tomt fält
som i dag.
*Problem:* tomt fält utan förlaga är inte en övning, det är en gissning.
*Lärande:* worked example-effekten gäller starkast för nybörjare; skaffoldningen
måste sedan tas bort, vilket är precis vad "bara första fallet" gör.
*Praxis:* fading scaffolding. *Insats: Hög* (kräver författat innehåll per modul).

**7.4 Låt facit kosta ett försök.** Facitexpandern är gratis före första
försöket, både i rättsfallsvyn och i lagrumsjakten. Ett medvetet klick
("Jag har försökt") räcker som tröskel.
*Problem:* generationseffekten, appens hela premiss, kan kringgås med ett klick.
*Lärande:* desirable difficulty. *Praxis:* svar bakom avsikt, inte bakom lås.
*Insats: Låg.*

**7.5 Gör exporten till kursens repetitionsmekanism, inte en nedladdning.**
Eftersom sessionen är flyktig och målgruppen anonym är Obsidianvalvet den enda
ärliga vägen till spaced repetition. `utils/obsidian.py` bygger redan en not per
RNTS-analys, sammanlänkad via lagrum, plus Rättskartan. Åtgärd: säg det i
copyn — "Ta med dig det du gjort och läs om det i morgon" — i stället för att
presentera det som en filnedladdning.
*Problem:* appens bästa långtidsmekanism är märkt som en teknisk detalj.
*Lärande:* spacing-effekten är den mest robusta effekten i inlärningsforskningen.
*Praxis:* ärlig framing av vad ett verktyg är till för. *Insats: Låg.*

**7.6 Lyft verifieringsnoten från brus till princip.** `VERIFIERINGSNOT`
förklarar att ett guldchip betyder att lagrummet *finns*, inte att det är
*tillämpligt*. Det är kursens viktigaste metodinsikt. I dag upprepas den som
`st.caption` under varje tutorsvar och blir därmed något studenten slutar läsa.
Åtgärd: förklara den en gång, ordentligt, i Juridisk metod; behåll därefter en
kort, konsekvent formulering.
*Problem:* upprepning avtrubbar den viktigaste varningen appen har.
*Lärande:* en princip lärs en gång och påminns kort, inte tvärtom.
*Insats: Låg.*

**7.7 Förklara varför blandad träning är svårare — och bättre.** Kunskapsutmaning
gör redan interleaving. Studenten vet inte att en blandad omgång känns sämre men
ger mer än en blockad. En mening på sidan gör skillnaden mellan en funktion och
en metod.
*Insats: Låg.*

**7.8 Chunka RNTS-formuläret.** Fyra fält, scenariokort, stepper, två knappar och
en facitexpander på en skrollhöjd. Erbjud ett läge som visar ett steg i taget med
föregående steg synligt sammanfattat ovanför.
*Problem:* intrinsic load i uppgiften är redan hög; layouten lägger på extraneous
load. *Lärande:* chunking frigör arbetsminne åt juridiken.
*Praxis:* ett fokuserat steg per skärm. *Insats: Medel.*

---

## 8. Nybörjarens första fem minuter

Antag att studenten aldrig läst juridik. Så ser det ut i dag, minut för minut.

**0:00 — Hem.** Läser rubriken "Träna att tänka juridiskt, inte att läsa
passivt". Bra. Under den, sidans starkaste visuella element: en blå ruta om att
detta inte är juridisk rådgivning. Först därefter kommer knappen.
*Friktion:* det första ögat dras till är en brasklapp.

**0:20 — Sidopanelen.** Söker "var börjar jag". Ser START OCH METOD, sedan
OFFENTLIG RÄTT med två gråa oklickbara poster, sedan CIVILRÄTT →
Förmögenhetsrätt → Kontraktsrätt → Avtalsrätt. Fyra okända ord innan något går
att klicka på.
*Friktion:* systematiken kostas ut i sin helhet innan något ges tillbaka.

**0:40 — Klickar CTA:n, hamnar i Juridisk metod.** Möter tre flikar och, i flik
ett: en svårighetsväljare (Grund/Medel/Avancerad — utan att veta vad något av dem
innebär), två knappar, en selectbox, ett scenariokort, en stepper, fyra tomma
fält.
*Friktion:* sex kontroller före första ordet skrivits; sidans egentliga uppgift
ligger nedanför dem.

**1:30 — Läser scenariot, skriver i Rättsfrågan.** Vet inte om "Är avtalet
bindande?" är rätt *form*. Ingenstans finns ett exempel.
*Friktion:* uppgiften är fri produktion utan förlaga.

**2:00 — Normfältet.** Skriver "avtalslagen". Får en gul varning: inget giltigt
lagrum, skriv "4 § AvtL". Rättningen är korrekt och snabb — men appens första
återkoppling gäller formatet, inte tänkandet.
*Friktion:* första upplevelsen är ett avvisat format.

**3:00 — Trycker på tutorn.** I en publik driftsättning är dagsbudgeten delad,
så det troliga utfallet är "Tutorn är inte tillgänglig just nu" eller
dagsbudgetkortet. Fallbacken pekar mot facit, vilket är rätt gjort — men
studenten har ännu inte sett hur en god analys ser ut.
*Friktion:* det som marknadsförs som appens kärna kan vara borta vid första
försöket, och tomheten förklaras inte i förväg.

**4:00 — Öppnar facit.** Läser rättsfråga, lagrumschips, rekvisitpunkter,
slutsats. Här sker lärandet — men genom jämförelse, inte konstruktion.

**5:00 — Och nu?** Ett fall till? Quizet? Nästa modul? Ingenting säger det.
Stänger fliken. Allt är borta.

### Hur gränssnittet ska bära dem i stället

| Minut | Åtgärd |
|---|---|
| 0:00 | Friskrivning som caption; NÄSTA STEG-kortet är det starkaste på sidan |
| 0:20 | RNTS-panelen namnger metoden på första skärmen, före all systematik |
| 0:20 | Sidopanelen: `STUDERA` först, klickbart före abstrakt, "kommer" som en rad |
| 0:40 | Modulen öppnar i Nyckelbegrepp (igenkänning), inte i fri produktion |
| 0:40 | Svårighet förvald till Grund; väljaren flyttad intill genereringsknappen |
| 1:30 | "Så kan ett svar se ut" intill Rättsfrågan i modulens första fall |
| 2:00 | Normfältets placeholder visar formen: `4 § AvtL` eller `2 kap. 1 § SkL` |
| 3:00 | Tutorns tillgänglighet syns *före* klicket; facit framställs som fullgott |
| 4:00 | Facit efter "Jag har försökt", så jämförelsen följer på ett eget försök |
| 5:00 | Efter genomfört fall: ett nästa steg, plus exporten som "ta med dig det" |

---

## 9. Prioriterad plan

### Hög effekt / låg insats

| # | Åtgärd | Löser |
|---|---|---|
| 1 | `cta_mal()` föredrar nästa modul i kursordning, inte senast besökta | Svaghet 1 |
| 2 | Kapitälrad `TRÄNAR: <RNTS-steg>` över varje aktivitet | Svaghet 2 |
| 3 | Flytta facitexpandern ut ur `if st.button("Rätta")` (verklig bugg) | Avsnitt 5 |
| 4 | Fäll de fyra ikonläckorna; besluta om `page_icon` | Ramen |
| 5 | Typ- och spacingtokens som CSS-variabler | Avsnitt 6 |
| 6 | Ta bort nedladdningsknappar ur tomt tillstånd | Svaghet 5 |
| 7 | Statuspanelen till en rad; modellväljaren ut ur sidopanelen | Avsnitt 4 |
| 8 | Markera aktiv sidas rubrikkedja (`_jok_aktiv_sida` finns redan) | Avsnitt 4 |
| 9 | Facit bakom "Jag har försökt" | Avsnitt 7.4 |
| 10 | Säg rent ut att framstegen gäller sessionen; exporten som svar | Svaghet 4 |
| 11 | Ta bort död kod (`render_kort`, `summary_box`) eller gör den till primitiv | Avsnitt 5 |
| 12 | Modulingressen säger något modulspecifikt, eller tas bort | Avsnitt 5 |

### Hög effekt / medelinsats

| # | Åtgärd | Löser |
|---|---|---|
| 13 | RNTS-panelen på startsidan; ARBETSGÅNG utgår | Svaghet 2, 5 |
| 14 | Sidopanelen i tre plan (`STUDERA` / `SLÅ UPP` / `MINA FRAMSTEG`) | P1–P6 |
| 15 | Slå ihop Kunskapstest + Kunskapskarta till *Framsteg och samband* | P3, P4, P5 |
| 16 | Flikramp i modulen: begrepp → jakt → quiz → fall | Svaghet 3 |
| 17 | Implementera `render_quizfraga` som §3 redan specificerar | Avsnitt 5 |
| 18 | En enda aviseringsuppsättning | Svaghet 6 |
| 19 | Steppern vågrät ovanför formuläret; sanna statusar; CSS i stället för glyfer | Avsnitt 5 |
| 20 | Ett kortsystem: fyra primitiver, en betydelse per vänsterlinje | Avsnitt 6 |
| 21 | Framstegsmarkering per modul i sidopanelen | Avsnitt 4 |
| 22 | Ett-steg-i-taget-läge för RNTS-formuläret | Avsnitt 7.8 |

### Hög effekt / stor insats

| # | Åtgärd | Anmärkning |
|---|---|---|
| 23 | Författade worked examples per modul (7.3) | Innehållsarbete, 12 moduler |
| 24 | Framstegsmodell per RNTS-steg i stället för per modul | Se avsnitt 11: mätbarheten är tvivelaktig |
| 25 | Onboarding för anonym förstagångsbesökare | Tre skärmar, hoppbara, en gång per session |
| 26 | Falltypsguiden som ingång "jag har ett eget fall" | Vänder appen från kurs till verktyg |

### Framtida idéer

* **Bokmärkbar framstegslänk.** `st.query_params` kan bära ett kompakt
  framstegstoken utan nya beroenden: studenten bokmärker sin URL och kommer
  tillbaka till sina resultat. Enda ärliga vägen till persistens för en anonym
  målgrupp. Begränsas av URL-längd; kräver noggrann kodning.
* **Tillgänglighetsgenomgång med riktiga hjälpmedel** (avsnitt 10.6).
* **Tidsuppskattning per modul** utifrån `uppskattad_tid_min` som redan finns i
  scenariodatan.

---

## 10. Wireframes

Textuella skisser. Där två alternativ finns anges avvägningen.

### 10.1 Startsidan — alternativ A (rekommenderat): en spalt, avtagande vikt

```
┌──────────────────────────────────────────────────────────────┐
│ JURIDISK ÖVERSIKTSKURS                                       │
│ Träna att tänka juridiskt, inte att läsa passivt             │
│ Öva fallbaserat: identifiera rättsfrågan, hitta rätt lagrum, │
│ tillämpa normen och dra en slutsats.                         │
│ Studieverktyg, inte juridisk rådgivning.          ← caption  │
│                                                              │
│ NÄSTA STEG                                                   │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Avtalsrätt · kap. 7                                      │ │
│ │ Tränar Norm och Tillämpning · ca 15 min                   │ │
│ │ Kursens första egentliga rättsområde.                    │ │
│ │ [ Börja: Avtalsrätt → ]     Fortsätt där du var (Arbets…) │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ METODEN                                                      │
│ Rättsfrågan   Vad är det egentligen som ska avgöras?         │
│ Norm          Vilken paragraf styr frågan?                   │
│ Tillämpning   Hur faller omständigheterna ut mot paragrafen? │
│ Slutsats      Vad blir svaret?                               │
│                                                              │
│ FRAMSTEG                                                     │
│ 2 moduler påbörjade · 3 fall genomförda · 7/9 rätt på quiz   │
│ Gäller den här sessionen. → Framsteg och samband             │
│                                                              │
│ ─────────────────────────────────────────────────────────────│
│ Studieverktyg, inte juridisk rådgivning. Version 0.1.0       │
└──────────────────────────────────────────────────────────────┘
```

Tomt tillstånd: FRAMSTEG-blocket utgår helt (inte "inga resultat ännu"), METODEN
flyttar upp direkt under NÄSTA STEG. Första skärmen får då exakt en knapp.

### 10.2 Startsidan — alternativ B: metoden först

Byt plats på NÄSTA STEG och METODEN, så att en förstagångsbesökare möter metoden
före uppmaningen.
*Avvägning:* pedagogiskt renare för den som aldrig varit där, men det lägger ett
lässteg före varje besök för den som återkommer. **A är att föredra** eftersom
hero redan har krympt vid andra besöket och ordningen då blir naturlig; B kan
väljas som förstagångsvariant om onboarding (åtgärd 25) inte byggs.

### 10.3 Sidopanelen — alternativ A (rekommenderat): tre plan, allt öppet

Se avsnitt 4. Full höjd, ingen hopfällning, framstegssiffror dämpade höger,
aktiv rubrikkedja i bläckvikt, statuspanel som en rad längst ner.

### 10.4 Sidopanelen — alternativ B: plan öppna, doktrinära grenar hopfällda

Endast `STUDERA`s undergrenar (Kontraktsrätt, Ersättningsrätt, Näringsrätt …)
kan fällas ihop, med den aktiva grenen alltid öppen.
*Avvägning:* halverar panelens höjd på liten skärm, men bryter §4.1:s premiss att
hela systematiken ska vara synlig. Se avsnitt 11.

### 10.5 Modulsidan — alternativ A (rekommenderat): ramp, ett fokus

```
┌──────────────────────────────────────────────────────────────┐
│ KAP. 7 · AVTALSRÄTT                                          │
│ Avtalsrätt                                                   │
│ ▸ Så använder du den här sidan                               │
│                                                              │
│ [ Begrepp ] [ Lagrumsjakt ] [ Quiz ] [ Rättsfall ]           │
│  igenkänning   hågkomst      tillämpning  produktion         │
│ ────────────────────────────────────────────────────────────  │
│ TRÄNAR: RÄTTSFRÅGAN, NORM, TILLÄMPNING, SLUTSATS             │
│                                                              │
│ ┌ Rättsfall ───────────────────────────────────────────────┐ │
│ │ Bilköpet som ångrades                                    │ │
│ │ Grund · ca 12 min                                        │ │
│ │ Anna beställer en bil av Bertil …                        │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│ ○ Rättsfrågan  ○ Norm  ○ Tillämpning  ○ Slutsats  ← vågrät   │
│                                                              │
│ Rättsfrågan                        ▸ Så kan ett svar se ut   │
│ ┌──────────────────────────────────────────────────────────┐ │
│ └──────────────────────────────────────────────────────────┘ │
│ Norm (ange lagrum)          t.ex. 4 § AvtL, 2 kap. 1 § SkL   │
│ ┌──────────────────────────────────────────────────────────┐ │
│ └──────────────────────────────────────────────────────────┘ │
│  § 4 § AvtL  ← chip direkt, deterministiskt                  │
│ … Tillämpning, Slutsats …                                    │
│                                                              │
│ [ Be tutorn granska min analys ]   ← enda primära knappen    │
│ Tutorn granskar steg för steg. Den skriver inte lösningen.   │
│ ▸ Jag har försökt — visa facit                               │
│                                                              │
│ ▸ Byt fall eller generera ett nytt        ← hopfälld, nedan  │
└──────────────────────────────────────────────────────────────┘
```

Nyckeländringar: flikarna får en underetikett som visar rampen; en enda primär
knapp; steppern vågrät ovanför formuläret; svårighetsväljare, generering och
fallval flyttade *under* uppgiften i en hopfälld sektion, eftersom de är
inställningar och inte uppgiften.

### 10.6 Modulsidan — alternativ B: ett RNTS-steg per skärm

Scenariokortet stannar överst, under det ett enda fält med "Nästa steg →". Redan
ifyllda steg sammanfattas i en rad var.
*Avvägning:* lägst kognitiv belastning, men studenten ser inte hela analysen
samtidigt — och juridiskt resonemang bygger på att slutsatsen hänger ihop med
normen. **Rekommendation: erbjud B som val, behåll A som standard.**

### 10.7 Framsteg och samband

```
┌──────────────────────────────────────────────────────────────┐
│ MINA FRAMSTEG                                                │
│ Framsteg och samband                                         │
│                                                              │
│ Den här sessionen: 2 moduler · 3 fall · 7/9 rätt på quiz     │
│                                                              │
│ PER RNTS-STEG                                                │
│ Rättsfrågan   3 besvarade                                    │
│ Norm          3 besvarade · 5 av 6 lagrum verifierade        │
│ Tillämpning   3 besvarade                                    │
│ Slutsats      2 besvarade                                    │
│                                                              │
│ PER MODUL                                                    │
│ Avtalsrätt              2 fall · 4/5 quiz    → Öva vidare    │
│ Skadeståndsrätt         1 fall · 3/4 quiz    → Öva vidare    │
│                                                              │
│ SAMBAND                                                      │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │  (grafen: fall ←→ lagrum ←→ modul)                       │ │
│ └──────────────────────────────────────────────────────────┘ │
│ Guld = lagrum · blå = rättsfall · mörkblå = modul            │
│                                                              │
│ TA MED DIG                                                   │
│ Läs om det du gjort i morgon — då fastnar det.               │
│ [ Obsidianvalv (zip) ]   Markdown · Excel                    │
└──────────────────────────────────────────────────────────────┘
```

Tomt tillstånd: rubrik, en mening om vad sidan kommer att visa, en länk till
NÄSTA STEG, och Obsidianvalvet — som är värdefullt tomt eftersom Rättskartan
alltid följer med.

### 10.8 Rättskartan

Nuvarande struktur (tre flikar: Systemet, Falltypsguide, Nyckelbegrepp) behålls;
den är appens bäst fungerande sida. Tre justeringar:

```
┌──────────────────────────────────────────────────────────────┐
│ SLÅ UPP · RÄTTSKARTAN                                        │
│ Kartan över rättssystemet                                    │
│ ▸ Så använder du den här sidan                               │
│                                                              │
│ [ Systemet ] [ Vilken lag gäller? ] [ Nyckelbegrepp ]        │
│ ────────────────────────────────────────────────────────────  │
│ ┌ taxonomigraf ───────────────────────────────────────────┐  │
│ │              (offentlig rätt / civilrätt)               │  │
│ └─────────────────────────────────────────────────────────┘  │
│ ■ offentlig rätt   ■ civilrätt   ● lag   ▪ struktur          │
│                                                              │
│ OMRÅDEN                                                      │
│ ▸ Kontraktsrätt                                              │
│ ▸ Ersättningsrätt                                            │
└──────────────────────────────────────────────────────────────┘
```

1. Fliken *Falltypsguide* döps till **Vilken lag gäller?** — studentens fråga,
   inte datastrukturens namn.
2. Träfflistan renderas som rader med riktiga lagrumschips i stället för
   `st.dataframe`, så guldregeln gäller även här.
3. Färglegenden ligger redan som riktiga färgrutor. Behålls.

---

## 11. Invändningar mot granskningens egna förslag

Där ett alternativ är starkare anges det.

**11.1 Framsteg per RNTS-steg riskerar att vara osant.** Förslag 24 och panelen i
10.7 antyder att appen kan säga något om studentens förmåga per steg. Men bara
*Norm* går att bedöma deterministiskt (mot lagrumsregistret). Rättsfrågan,
Tillämpning och Slutsats är fritext, och `_rnts_statusar()` kan i praktiken bara
mäta att fältet inte är tomt. En panel som säger "din Tillämpning är svag" vore
härledd ur teckenlängd — precis den sorts falska mätning granskningen kritiserar
i avsnitt 5.
**Alternativ:** redovisa *volym*, inte *kvalitet* — "3 besvarade", aldrig
"stark/svag" — utom för Norm, där verifieringsandelen är en riktig siffra. Så är
10.7 skriven. Rekommendationen kvarstår därför i den svagare, sanna formen, och
förslag 24 bör inte byggas som en kvalitetsmodell.

**11.2 Tre plan kan kännas arbiträra för den doktrinärt tänkande.** En student som
redan har systematiken i huvudet kan uppfatta `SLÅ UPP` som en främmande låda:
Rättskartan *är* systematiken, och nu ligger den utanför trädet.
**Alternativ:** behåll ett enda träd och lös P1 enbart genom att göra
appfunktionsrubrikerna visuellt olika de doktrinära (t.ex. utan versaler och utan
blått). Billigare och mindre ingripande. **Avvägning:** det löser förvirringen om
vad rubrikerna *är*, men inte P3–P5 (Kunskapstest som inte testar, framsteg på
tre ställen, två kartor med samma namn). Tre plan är att föredra, men om bara en
åtgärd får plats är den visuella differentieringen mest värde per krona.

**11.3 Flikrampen kan göra modulen till en quizapp.** Att flytta Rättsfall sist
riskerar att det som *är* poängen hamnar bakom tre andra saker, och att studenten
aldrig kommer dit.
**Alternativ:** behåll Rättsfall först, men lägg en rad ovanför flikarna: "Ny
här? Börja i Begrepp." **Avvägning:** bevarar tyngdpunkten till priset av att
nybörjaren måste välja rätt själv — vilket är precis vad de är dåliga på. Rampen
är att föredra, men rekommenderas med en synlig genväg till Rättsfall i flikraden
så att den vane studenten inte straffas.

**11.4 Skaffoldning på Rättsfrågan urholkar generationseffekten.** Att erbjuda tre
kandidatformuleringar gör en produktionsuppgift till en igenkänningsuppgift —
och generationseffekten är appens hela premiss.
**Avvägning:** därför endast modulens *första* fall, och därför med en motivering
efter valet i stället för bara rätt/fel. Skaffoldningen ska försvinna av sig
själv. Skulle den visa sig göra studenter beroende av alternativ är åtgärden att
i stället visa ett *färdigt* worked example från ett annat fall — man läser någon
annans analys, men skriver alltid sin egen.

**11.5 Att avvisa hopfällbar navigering kan vara fel på liten skärm.** §4.1:s
argument (en panel som måste öppnas döljer kursens struktur) är starkt på
skrivbordet. På en telefon blir samma träd en lång skrollning före allt innehåll.
Granskningen behåller §4.1 därför att avsnitt 2 kortar trädet genom att flytta ut
fyra poster — men om appen faktiskt används mycket på telefon är 10.4 det bättre
valet. **Detta bör avgöras av verklig användning, inte av principen.**

**11.6 "Nästa i kursordning" antar att kursordningen är rätt för alla.** En
student som läser inför en tentamen i skadeståndsrätt vill inte skickas till
Avtalsrätt.
**Avvägning:** därför en *rekommendation* med synlig sekundärväg ("Fortsätt där
du var") och ett träd som aldrig låser något. Kortet bör dessutom motivera sitt
val i en rad, så att avvikelse blir ett informerat val och inte ett olydigt.

**11.7 Granskningen kan ha fel om att en publik målgrupp utesluter persistens.**
Slutsatsen "ingen identitet, alltså ingen lagring" gäller serverlagring. Idén om
bokmärkbar URL i avsnitt 9 kringgår det utan nya beroenden och utan konton. Den
är placerad under Framtida idéer på grund av URL-längd och kodningsrisk, men om
återkommande studenter visar sig vara det viktigaste målet bör den flyttas upp —
den vore då den enskilt mest värdefulla åtgärden i hela dokumentet.

---

## 12. Ändringar i `design_system.md`

Enligt beslutet i inledningen: varje avvikelse namnges.

### Behålls oförändrat

| Regel | Varför den håller |
|---|---|
| §1 paletten, guld = enbart lagrum | Appens starkaste inlärda semantik |
| §1 kontrastkrav (brödtext 7:1, accent 4.5:1) | Rätt nivå, över WCAG AA |
| §2 systemtypsnitt, inga filer eller CDN | Identiskt utseende lokalt och i molnet |
| §2 maxbredd 46rem för löptext | Rätt för scenariotext |
| §4.1 nivåer skiljs med indrag och färgstyrka, aldrig ikoner | Välargumenterat |
| §4.1 guld aldrig i navigeringen | Skyddar guldregeln |
| §4.1 hela trädet synligt, inga hopfällbara sektioner | Behålls; se 11.5 |
| §4.2 Rättskartans tre visuella kanaler och klickbarhetsregel | Fungerar |
| §4.2 deterministiskt först, LLM-svar alltid under grunddatan | Rätt princip |
| §5 presentationsriktlinjer för juridiskt innehåll | Bär appens pedagogik |
| §6 ton och mikrocopy | Rätt röst |

### Ändras

| § | Från | Till | Skäl |
|---|---|---|---|
| Ny §2.1 | Storlekar i prosa | Sex namngivna typtokens | Fem rubriknivåer utan rangordning (avsnitt 6) |
| Ny §2.2 | Handsatta marginaler | 4px-baserad spacingskala | Ingen visuell rytm (avsnitt 6) |
| §3 | `render_quizfraga` specificerad men obyggd | Antingen byggd eller struken | Specifikation som inte följs vilseleder |
| §3 | `render_kort(titel, innehall, ikon)` | Utan `ikon`; eller borttagen | Strider mot ikonregeln; död kod |
| §3 | Stepperns statusikoner som glyfer | CSS-ritade tillstånd | Ikonregeln |
| §3 | Fyra radier, två skuggregimer | Fyra dokumenterade primitiver | Avsnitt 6 |
| §4 | "Startsidan: … arbetsgången i fyra steg" | RNTS-panelen ersätter arbetsgången | Två vokabulär för samma modell |
| §4 | "Modulsida: tre flikar Rättsfall, Quiz, Lagrumsjakt" | Fyra flikar i ramp | Svårast först (avsnitt 7.2) |
| §4 | Sidopanel: modulnavigering + statuspanel + modellväljare | Tre plan; statusrad; ingen modellväljare | Avsnitt 2 och 4 |
| §4.1 | Ikonförbudet gäller navigeringen | Gäller hela appen; `page_icon` enda dokumenterade undantag | Användarens ram; fyra läckor |
| §4.3 | "Varje sida inleds med `render_sidhjalp`" | Antingen genomförd eller omformulerad | Följs bara på Rättskartan |
| §5 | Nytt: en aviseringsuppsättning, fyra roller | — | Två system i dag (avsnitt 5) |
| Ny §7 | — | Framsteg är sessionsbundet och ska sägas rent ut; exporten är kontinuiteten | Tyst dataförlust (svaghet 4) |

### Avvisat ur uppdragsbeskrivningen, med skäl

| Önskemål | Beslut | Skäl |
|---|---|---|
| Ikoner i navigering och komponenter | Avvisas | Användarens egen ram, och §4.1 är välargumenterad |
| Hopfällbara sektioner i sidopanelen | Avvisas för skrivbord | §4.1; se 11.5 för när det bör omprövas |
| Sökfält i sidopanelen | Avvisas | 14 poster; falltypsguiden är den sökning som behövs |
| Framstegsstaplar per modul i sidopanelen | Avvisas | Gör karta till instrumentpanel; noll vid varje återkomst |
| Duolingo-liknande belöningsslinga | Avvisas | Extraneous load; belönar fel sak i analytiskt arbete |
| Animationer utöver hovring och spinners | Avvisas | Rent dekorativa enligt ramen |

---

## 13. Vad som inte granskats

Ärlighet om täckningen.

* **Tillgänglighet är granskad statiskt, inte med hjälpmedel.** Paletten är
  dokumenterat kontrastprövad och glyfberoendet åtgärdas ovan. Men inget är
  provat med skärmläsare eller enbart tangentbord, och Streamlits egna
  komponenter (`st.tabs`, `st.segmented_control`, `st.popover`) sätter ett tak
  som appen inte kan höja. Det som konkret kan sägas: `st.html`-blocken saknar
  landmärken och rubriksemantik — `.jok-section h2` är en riktig `h2`, men
  kapitäletiketterna är `div`, så en skärmläsare får rubriker utan sina
  etiketter. Klickytor: chips är ~1.4rem höga, under 44px-rekommendationen.
  En riktig genomgång kräver hjälpmedel och står under Framtida idéer.
* **Responsivitet är inte provad på riktiga enheter.** `st.columns` staplar på
  smal skärm, vilket ger rätt ordning i 10.5, men taxonomigrafens iframe och
  `st.dataframe` är de troliga brytpunkterna. 11.5 hänger på detta.
* **Ingen användning är observerad.** Hela granskningen är expertheuristik. Den
  starkaste invändningen mot vilket förslag som helst här är en student som gör
  något annat än dokumentet antar.
