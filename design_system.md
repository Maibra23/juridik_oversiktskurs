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

* **Startsidan**: hjältesektion med kursnamn, en mening om metoden, tre nyckeltal (moduler, scenarier, din framsteg), därunder ett rutnät av modulkort (2 kolumner) med framstegsindikator per modul. Disclaimer i sidfoten.
* **Modulsida**: tre flikar i fast ordning: Rättsfall, Quiz, Lagrumsjakt. Samma struktur i alla moduler så att navigationen blir automatisk.
* **Case vyn**: två kolumner på bred skärm: vänster scenariokortet (sticky känsla, alltid läsbart), höger RNTS formuläret med steppern. Knappordning alltid: primär "Be tutorn granska min analys", sekundär "Visa facit".
* **Sidopanel**: modulnavigering överst, statuspanel nederst, modellväljare (8B/14B) under en expander.

## 5. Presentationsriktlinjer för juridiskt innehåll

* Lagrum skrivs alltid i standardform ("36 § AvtL", "3 kap. 1 § ÄB") och alltid som chip, aldrig som ren text, så att varje norm är ett klick från källan.
* Skilj visuellt på **norm** (guldchip), **fakta** (brödtext i scenariokort) och **bedömning** (tutortext med blå RNTS rubriker). Blanda aldrig dessa i samma visuella stil.
* Rekvisit listas som avbockningsbara punkter i facit, ett rekvisit per rad, så att subsumtionen blir synlig.
* Alternativa utfall i slutsatser markeras med prefixet "Alternativt:" i kursiv, aldrig gömda i löptext.
* Tomma tillstånd: innan studenten skrivit något visar tutorpanelen en kort instruktion om RNTS i stället för en tom yta.
* Fel och varningar formuleras alltid handlingsorienterat ("Kontrollera paragrafen på lagen.nu") och aldrig skuldbeläggande.

## 6. Ton och mikrocopy

Saklig, varm och kortfattad svenska. Du tilltal. Inga utropstecken i bedömningar. Exempel: "Din norm stämmer. Tillämpningen behöver koppla ond tro till att köparen kände till felet." Systemmeddelanden om budget förklarar alltid vad som fortfarande fungerar.
