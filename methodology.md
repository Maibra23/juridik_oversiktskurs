# methodology.md: Pedagogisk och juridisk metod

## 1. Pedagogisk metod

### 1.1 Paretoprincipen 80/20

Appens innehåll omfattar 22 kapitel men skriftliga prov på Juridikverkstan prövar nästan alltid samma kärnförmågor: juridisk metod tillämpad på avtal, köp, skadestånd, arbetsliv, bolag, familj/arv och brott. Appen väljer därför medvetet bort bredd till förmån för djup i tolv moduler, samtliga inom civilrätten och straffrätt och processrätten. Urvalskriterier:

* Områden som examineras med fallfrågor (högst poängvikt).
* Områden med tydliga, tränbara regelstrukturer (rekvisit som kan bockas av).
* Områden studenter erfarenhetsmässigt blandar ihop (behörighet mot befogenhet, uppsägning mot avsked, giftorättsgods mot enskild egendom, uppsåt mot oaktsamhet). Förväxlingspar är extra värdefulla att träna eftersom de ger flest fel per nedlagd studietimme.

Ett fjärde kriterium tillkom efter granskningen av innehållet: områden som senare moduler *förutsätter*, även när de sällan examineras för egen del. Personrätt (kap 5) och allmän förmögenhetsrätt (kap 6) valdes in på den grunden. Utan rättshandlingsförmåga går fullmaktsläran i avtalsrätten inte att motivera, och utan äganderättens övergång saknar köprättens felregler sitt föremål. Ett förkunskapsområde som bär flera senare moduler ger hög avkastning även med låg egen tentavikt.

Inom varje modul gäller samma princip: hellre fem rekvisit som studenten verkligen kan tillämpa än tjugo som bara känns igen.

### 1.2 Fallbaserad inlärning

All träning utgår från konkreta scenarier, inte från regelreferat. Skälet är att juridisk kunskap är procedurell: man kan inte "kunna" 36 § AvtL utan att ha tillämpat den på fakta. Varje modul erbjuder tre svårighetstrappor:

1. **Lagrumsjakt** (igenkänning): given situation, hitta normen. Lägst kognitiv belastning, tränar rättskällenavigering.
2. **Flervalsfrågor** (förståelse): distraktorerna bygger på typiska missförstånd och varje alternativ har en förklaring med lagrum.
3. **Rättsfall med RNTS formulär** (tillämpning): studenten producerar en egen analys innan facit eller tutor visas. Detta är generationseffekten: att själv formulera ett svar ger mätbart bättre retention än att läsa ett färdigt.

### 1.3 Stegvisa förklaringar och produktiv kamp

Tutorn löser aldrig fallet först. Ordningen är alltid: studenten försöker, appen ger deterministisk återkoppling där det går (lagrumsvalidering, quizrättning), och först därefter kan studenten be tutorn granska. Tutorn instrueras att peka på luckor ("din norm är rätt men tillämpningen kopplar inte rekvisitet ond tro till fakta X") i stället för att skriva om lösningen. Facit finns alltid som deterministisk expander, så lärandet är aldrig beroende av LLM budgeten.

### 1.4 Mätning

Lärandeeffekt operationaliseras som: quizresultat första mot andra försöket, andel RNTS steg godkända vid första försöket, antal genomförda scenarier. Allt visas för studenten själv (formativ, inte summativ bedömning).

## 2. Juridisk metod

### 2.1 RNTS strukturen

Appens bärande analysmodell är den juridiska metodens fyra steg, i boken och appen kallad RNTS:

1. **Rättsfrågan**: vad är den juridiskt relevanta frågan i scenariot? (Inte "vem har rätt?" utan t.ex. "har bindande avtal uppkommit trots den sena accepten?")
2. **Norm**: vilken rättsregel styr frågan? Här krävs precist lagrum och korrekt rättskälla. Appen validerar detta steg maskinellt.
3. **Tillämpning**: subsumtion, dvs normens rekvisit prövas ett i taget mot fakta i scenariot. Detta är steget studenter oftast hastar förbi, därför har det ett eget textfält och egen bedömning.
4. **Slutsats**: svaret på rättsfrågan, med eventuell reservation för alternativa utfall (t.ex. beroende på bevisläge eller skälighetsbedömning).

### 2.2 Rättskälleläran

Modul 1 lär ut hierarkin lag, förarbeten, prejudikat, doktrin samt EU rättens och Europakonventionens ställning (bokens kapitel 1). Övriga moduler tillämpar den implicit: tutorn hänvisar primärt till lagtext, anger när ett område styrs av dispositiv respektive tvingande rätt (centralt i köprätten och arbetsrätten) och markerar tydligt när något vilar på praxis snarare än lagtext.

### 2.3 Lagtolkning och systematik

Scenarierna är byggda för att kräva tolkningsval: ordalydelse, systematisk tolkning (var i lagen står regeln?), ändamålstolkning. Exempel: är en reklam ett anbud eller ett utbud (9 § AvtL systematik)? Tutorn ska namnge vilken tolkningsmetod som används när frågan inte löses av ordalydelsen ensam.

### 2.4 lagen.nu som primärkälla

Alla normhänvisningar länkas till lagen.nu så att studenten alltid läser den faktiska lagtexten i stället för en parafras. Det tränar vanan att gå till källan, vilket är själva kärnfärdigheten i rättskälleläran.

## 3. LLM tutorns roll: förstärka, inte ersätta

### 3.1 Principer

* **Studenten först**: tutorn aktiveras endast efter ett eget försök och endast på explicit begäran.
* **Granskare, inte facit**: tutorns uppgift är att bedöma studentens RNTS steg och ställa en riktad motfråga, inte att producera en modellösning (modellösningen finns deterministiskt i facit).
* **Verifierad grund**: varje lagrum i tutorns svar kontrolleras mot appens lagrumsdatabas. Verifierade referenser blir länkar till lagen.nu, overifierade får en synlig varning. Studenten lär sig därmed också källkritik mot AI, en explicit lärandemål i sig.
* **Transparens om osäkerhet**: systemprompten kräver att modellen hellre uttrycker osäkerhet än preciserar ett lagrum den inte är säker på.

### 3.2 Skydd mot hallucinationer, i lager

1. **Prompt**: förbud mot påhittade källor, låst referensformat, vitlistade lagförkortningar injicerade i prompten.
2. **Extraktion och validering**: regex plus uppslag i data/lagrum.json efter varje svar.
3. **Presentation**: overifierat innehåll markeras, döljs inte, så att studenten ser var granskning krävs.
4. **Deterministisk kärna**: rättning, facit och länkar fungerar helt utan LLM, så en hallucination kan aldrig bli enda sanningskällan.

### 3.3 Budgetdisciplin som pedagogik

Sessionstaket gör LLM anrop till en knapp resurs, vilket i sig styr studenten mot att tänka själv först och använda tutorn som bollplank vid genuin osäkerhet, precis som man använder en lärare.
