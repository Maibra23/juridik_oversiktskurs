# design_system.md: UI riktlinjer för juridikappen

Målbild: lugnt, förtroendeingivande och läsbart, som en modern juridisk publikation snarare än en dashboard. Designen ska bära långa textstycken (scenarier, analyser) utan trötthet.

## 1. Färgpalett

Definieras i .streamlit/config.toml och i en central CSS sträng i utils/ui.py.

* **Bläck** `#1A2332` : primär text och rubriker. Mörkblå snarare än svart, mjukare för långläsning.
* **Pergament** `#FAF7F2` : appbakgrund. Varm off white som signalerar dokument och bok.
* **Panel** `#FFFFFF` : kortbakgrund, med tunn ram `#E5E0D8`.
* **Myndighetsblå** `#2C5F8A` : primär accent, knappar, länkar, aktiva flikar.
* **Paragrafguld** `#B8860B` : sekundär accent, används uteslutande för lagrumschips och paragrafsymboler. Att guld alltid betyder lagrum ger snabb visuell igenkänning.
* **Godkänd** `#2E7D4F` : korrekt svar, verifierade referenser.
* **Varning** accent `#C9971C`, bakgrund `#FFF8E1`, ram och text `#8A6914` : overifierade lagrum, stale förklaringar. Ramar och text på varningsbakgrund använder den mörka nyansen så att kontrasten klarar WCAG (ram ≥ 3:1, text ≥ 4.5:1).
* **Fel** `#B3402A` : felaktiga svar. Röd med varm ton, inte alarmröd.

Kontrastkrav: all brödtext minst 7:1 mot bakgrund, accentfärger minst 4.5:1 (WCAG AA).

config.toml:
```toml
[theme]
primaryColor = "#2C5F8A"
backgroundColor = "#FAF7F2"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#1A2332"
font = "serif"
```

## 2. Typografi

* **Rubriker**: systemserif – Georgia, "Iowan Old Style", "Times New Roman". Serif för rubriker ger den juridiska, bokliga karaktären. Inga typsnittsfiler skeppas och ingen CDN används; stackarna är rena systemstackar så att appen ser likadan ut lokalt och på Streamlit Cloud.
* **Brödtext och UI**: system sans (Streamlits standard).
* **Lagrum och kod**: systemmonospace – ui-monospace, "SF Mono", Menlo, Consolas. Monospace för lagrum gör dem lätta att skanna och kopiera.
* Storlekar: brödtext 17px med radavstånd 1.65 (långläsning), rubriknivåer 28/22/18px, chips och metadata 14px.
* Maxbredd för löptext: 46rem. Scenariotext får aldrig löpa över hela skärmbredden.

## 3. Komponentbibliotek (utils/ui.py)

Alla komponenter är Pythonfunktioner som renderar st.markdown med klasser ur den centrala CSS strängen.

* **render_kort(titel, innehall, ikon)**: vit panel med tunn ram, radie 12px, diskret skugga. Bas för scenarier och resultat.
* **render_lagrum_chip(ref)**: guldkantad pill med paragrafsymbol, lagrummet i monospace och lagens fulla namn som tooltip. Klick öppnar lagen.nu i ny flik. Verifierad chip har guldram, overifierad chip har varningsbakgrund och prefixet "Ej verifierad:".
* **render_rnts_steg(steg, status)**: fyrstegs vertikal stepper (Rättsfrågan, Norm, Tillämpning, Slutsats) med statusikoner: tom cirkel (ej påbörjad), blå (under arbete), grön bock (godkänd), gul (behöver mer). Visas till vänster om formuläret på bred skärm, ovanför på smal.
* **render_case(scenario)**: scenariokort med rubrik, faktatext, diskret metadatarad (modul, svårighetsgrad, uppskattad tid) och en tunn guldlinje överst.
* **render_tutortext(text, rapport)**: tutorsvar där verifierade lagrum ersatts av chips och overifierade avsnitt fått gul markering. RNTS rubrikerna i svaret renderas som små kapitäler i myndighetsblått.
* **render_varning(text)** och **render_info(text)**: gula respektive blå informationskort, används för budgettak, stale förklaringar och disclaimer.
* **render_statuspanel()**: sidopanelens LLM status: modell, anrop kvar i sessionen, dagsbudget. Alltid synlig så att kostnadsläget är transparent.
* **render_quizfraga(fraga)**: fråga i kort, alternativ som radio, efter rättning färgas valt alternativ grönt eller rött och en förklaringsexpander visas per alternativ.

## 4. Layout och navigering

* **Startsidan**: hjältesektion med kursnamn och en mening om metoden, disclaimer, en enda call-to-action-knapp (fortsätt i senast besökta modul, eller kursens första modul för en ny session), framstegssektion (quizresultat, genomförda case, exportknappar) och arbetsgången i fyra steg. Ingen modullista: sidopanelen är appens enda navigering, så startsidan visar var du är i kursen i stället för att upprepa vad som redan finns i den. Disclaimer i sidfoten.
* **Modulsida**: tre flikar i fast ordning: Rättsfall, Quiz, Lagrumsjakt. Samma struktur i alla moduler så att navigationen blir automatisk.
* **Case vyn**: två kolumner på bred skärm: vänster scenariokortet (sticky känsla, alltid läsbart), höger RNTS formuläret med steppern. Knappordning alltid: primär "Be tutorn granska min analys", sekundär "Visa facit".
* **Sidopanel**: modulnavigering överst, statuspanel nederst, modellväljare (8B/14B) under en expander.

## 4.1 Navigeringshierarki

Sidopanelen speglar svensk rätts systematik i stället för filordningen i pages/. Trädet är data i `utils/navigation.py` och ritas av `render_sidopanel` i `utils/ui.py`. Fyra nivåer, som skiljs åt med indrag, storlek och färgstyrka, aldrig med ikoner:

| Nivå | Exempel | Komponent | Typografi och färg |
|---|---|---|---|
| Huvudkategori | CIVILRÄTT | `.jok-nav-kategori` | 12 px monospace, versaler, teckenmellanrum 0.1 em, myndighetsblå (`--bla`), fet. |
| Underkategori | Förmögenhetsrätt | `.jok-nav-under` | 13 px, halvfet, bläck (`--bl`). Marginal ovanför för att gruppera. |
| Undergren | Kontraktsrätt | `.jok-nav-gren` | 12 px, halvfet, grå `#6B6459`, indrag 0.6 rem. |
| Modul (byggd) | Avtalsrätt | `st.page_link` | Streamlits länkstil, ärver appens accentfärg. |
| Modul (planerad) | Fastighetsrätt (kommer) | `.jok-nav-kommer` | 13 px, dämpad grå `#9A9384`, indrag 0.6 rem. Aldrig klickbar. |

Regler:

* Endast moduler med en faktisk sida är länkar. Planerade moduler visas gråtonade med suffixet "(kommer)" så att kursens omfattning syns utan att ge trasiga länkar.
* Hela trädet visas samtidigt. Panelen har inga hopfällbara sektioner: en navigering som måste öppnas döljer kursens struktur i stället för att visa den, och studenten ska kunna se hela rättssystemet på en gång.
* Paragrafguld (`--guld`) används aldrig i navigeringen. Guld är reserverat för lagrum enligt avsnitt 1.
* Nivåerna får inte skiljas åt med emoji eller ikoner. Hierarkin bärs av indrag
  och färgstyrka. **Förbudet gäller hela appen**, inte bara navigeringen: inga
  emoji, inga dekorativa glyfer (tärningar, rundpilar, statusprickar) och inga
  teckenbaserade ikoner i komponenter. Tillstånd ritas med CSS-form, som
  RNTS-steppern gör. Enda dokumenterade undantaget är `page_icon` i
  `streamlit_app.py`: webbläsarflikens identitet är inte appkrom, och där gör en
  ikon något ett ord inte kan. `tests/test_sprak.py` vaktar regeln.

## 4.2 Rättskartan: appens orienteringssida

Rättskartan (`pages/16_Rattskartan.py`) är kursens karta över rättssystemet och är fullständig på dag noll: den kräver varken tutor eller genomförda övningar. Den ska inte förväxlas med **Kunskapskartan**, som är studentens personliga graf och växer med de egna rättsfallen.

Sidan har tre flikar i fast ordning:

| Flik | Innehåll | Datakälla |
|---|---|---|
| Systemet | Taxonomigraf + områdesträd med ett kort per lag | `utils/rattssystem_graf.py` ur `data/rattssystem.json` + lagrumsregistret |
| Falltypsguide | Sökbar tabell "vilken lag gäller för mitt fall?" | `utils.rattskarta.falltypsguide()` |
| Nyckelbegrepp | Begreppsbank grupperad per delområde | `data/nyckelbegrepp.json` |

**Taxonomigrafens visuella kanaler.** Hierarkin bärs av tre oberoende kanaler, aldrig av ikoner:

* **Färg = huvudgren.** Rättens två huvudgrenar har var sin färg: offentlig rätt (`#6B6459`) och civilrätt (`#2C5F8A`). Färgen ärvs nedåt genom hela grenen, så en nods färg alltid svarar på frågan "offentlig rätt eller civilrätt?". Källan är trädets toppgren i `data/rattssystem.json`; färgerna definieras som `GRENFARGER` i `utils/taxonomi_ui.py`.
* **Storlek = nivå.** Roten störst (26 px), lagarna minst (13 px). Trädet är ojämnt djupt (upp till sex nivåer på civilrättssidan), så storleken följer djupet, inte en fast nivålista.
* **Form = grupp.** Lagar är cirklar, strukturnoder rutor.

**Lagkortets kursavsnitt.** Paragrafspannet bär paragrafguld eftersom det är ett lagrum; kapitelrubriken bär bläck eftersom den är struktur. Det är samma regel som i avsnitt 1: guld betyder alltid lagrum, och kopplingen får inte brytas av navigeringsfärger. Täckningsraden ("kursen täcker 6 av lagens 38 kapitel") sätts i kapitälhöjd till höger om KURSAVSNITT-etiketten och är avsiktligt lågmäld — den ska kunna läsas, inte dominera kortet.

Paragrafguld används **enbart** för lagnoder, aldrig för någon strukturnivå. Det är samma regel som i avsnitt 1: guld betyder alltid lagrum eller lag, och den kopplingen får inte brytas av navigeringsfärger. Färglegenden ritas som riktiga färgrutor (`.jok-swatch`), aldrig som prosa i en caption.

**Klickbarhet.** Endast noder med `url` är klickbara, och `url` sätts bara på lagnoder. Klick öppnar lagen.nu i ny flik; strukturnoder är inerta genom konstruktion, inte genom ett villkor i klickhanteraren.

**Begreppskort.** Varje begrepp visas med fyra fasta fält i denna ordning: Definition, Varför det spelar roll, Exempel, och Så känner du igen det i ett scenario. Det sista fältet får guldstreckad ram eftersom det kopplar begreppet till RNTS-steget Rättsfrågan: det är signalorden i scenariot som ska få studenten att välja rätt norm. Kontrastpar (behörighet vs befogenhet och liknande) får dessutom en framhävd `skillnaden`-rad direkt under definitionen.

**Deterministiskt först.** Flikarnas grunddata är verifierad mot lagrumsregistret och fungerar utan LLM. Endast knappen "Förklara djupare med tutorn" anropar modellen, och den ligger i en popover (inte en expander, eftersom korten redan ligger i områdesexpanders och Streamlit inte tillåter nästlade expanders). LLM-svaret läggs alltid **under** grunddatan och ersätter den aldrig.

## 4.3 Sidhjälp

Varje sida inleds med en hopfälld `render_sidhjalp(...)` — en `st.expander("Så använder du den här sidan")` med 3–5 korta, handlingsorienterade punkter. Stängd som standard så att den inte konkurrerar med innehållet för den som redan vet. Kompletteras av `help=` på de kontroller vars beteende inte framgår av etiketten.

## 5. Presentationsriktlinjer för juridiskt innehåll

* Lagrum skrivs alltid i standardform ("36 § AvtL", "3 kap. 1 § ÄB") och alltid som chip, aldrig som ren text, så att varje norm är ett klick från källan.
* Skilj visuellt på **norm** (guldchip), **fakta** (brödtext i scenariokort) och **bedömning** (tutortext med blå RNTS rubriker). Blanda aldrig dessa i samma visuella stil.
* Rekvisit listas som avbockningsbara punkter i facit, ett rekvisit per rad, så att subsumtionen blir synlig.
* Alternativa utfall i slutsatser markeras med prefixet "Alternativt:" i kursiv, aldrig gömda i löptext.
* Tomma tillstånd: innan studenten skrivit något visar tutorpanelen en kort instruktion om RNTS i stället för en tom yta.
* Fel och varningar formuleras alltid handlingsorienterat ("Kontrollera paragrafen på lagen.nu") och aldrig skuldbeläggande.

## 6. Ton och mikrocopy

Saklig, varm och kortfattad svenska. Du tilltal. Inga utropstecken i bedömningar. Exempel: "Din norm stämmer. Tillämpningen behöver koppla ond tro till att köparen kände till felet." Systemmeddelanden om budget förklarar alltid vad som fortfarande fungerar.
