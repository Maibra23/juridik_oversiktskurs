# Design: Obsidianexport (tasks.md 3.7)

Datum: 2026-07-13

## Syfte

Studentens genomförda RNTS-analyser ska bli ett bestående, sammanlänkat
kunskapsvalv i Obsidian i stället för att dö med Streamlit-sessionen. Varje
lagrum blir en egen not så att Obsidians backlinks visar alla rättsfall där
lagrummet tillämpats. Repetitionskort (`fråga :: svar`) matar pluginen Spaced
Repetition. Funktionen är appens kapstone: den omvandlar ett övningspass till
ett permanent, självförstärkande studiesystem och återanvänder appens
kärntillgång, det verifierade lagrumsregistret, som valvets länkprimitiv.

## Arkitektur

Ett nytt rent modul `utils/obsidian.py` (inget Streamlit-beroende, fullt
enhetstestbart, samma disciplin som `utils/export.py`), plus tunn UI-koppling i
`utils/modulvy.py` och `streamlit_app.py`. Modulen återanvänder `utils/lagrum.py`
för all kanonisering, verifiering och lagen.nu-länkning, ingen regex- eller
URL-logik återuppfinns.

## Fångad data

Den befintliga `registrera_case_genomford` (boolesk spårning för framstegsbaren
och Markdown/Excel-exporten) lämnas orörd. En parallell rikare lagringsfunktion
läggs till så att inget befintligt går sönder:

- `registrera_case_analys(modul, case, svar)`, lagrar en post
  `{(modul, case_id): (modul, Case, svar_dict)}` i `st.session_state` under
  nyckeln `obsidian_analyser`.
- `hamta_case_analyser()`, returnerar posterna som en immutabel tuple för
  valvbyggaren.
- Anropas från `utils/modulvy.py:139`, intill det befintliga anropet, under
  samma trigger: alla fyra RNTS-fält ifyllda (fungerar utan LLM).

## Funktioner i `utils/obsidian.py`

- `notnamn(text)`, sanera Obsidians förbjudna filnamnstecken
  `* " \ / < > : | ? # ^ [ ]`; behåll `§ å ä ö`.
- `_kanonisk_lagrum(ref)`, en enda kanoniserare som ger t.ex. `"36 § AvtL"` /
  `"3 kap. 1 § SkL"`, använd för **både** notens filnamn och wikilänkens mål så
  att de alltid matchar.
- `lagrumsnot(ref)`, YAML frontmatter (`lag`, `sfs`, `status`,
  `taggar: [juridik/lagrum]`), en lagen.nu-länk när den är verifierbar (annars
  en rad som noterar att lagrummet inte kunde verifieras mot kursregistret).
- `rattsfallsnot(modul, case, svar)`, studentens fyra RNTS-fält plus det
  deterministiska facit; varje extraherat lagrum (studentens och facits) skrivs
  om till `[[kanonisk]]`; en `## Repetition`-sektion med facit-baserade kort
  `rättsfrågan :: slutsats + tillämpliga lagrum`.
- `modulnot(modul, rattsfall, lagrum)`, en MOC som länkar modulens rättsfalls-
  och lagrumsnoter.
- `bygg_valv(poster)`, bygger `zipfile`→`BytesIO`-bytes (samma mönster som
  `bygg_excel_rapport`). Valvstruktur: `Juridik/Start.md`,
  `Juridik/Moduler/<modul>.md`, `Juridik/Rattsfall/<case>.md`,
  `Juridik/Lagrum/<ref>.md`. Lagrumsnoter skapas endast för referenser som
  faktiskt förekommer i exporterade fall.

## Designbeslut

1. **Fångsttrigger:** alla fyra RNTS-fält ifyllda (samma som befintlig
   `registrera_case_genomford`). Fungerar offline / när LLM-taket är nått.
2. **Lagrumsomfång:** endast lagrum som refereras i exporterade fall får en
   egen not, tät graf utan föräldralösa noder.
3. **Wikilänkning:** varje lagrum som `extrahera_lagrum` faktiskt parsar blir en
   `[[...]]`-länk, även overifierade. Notens frontmatter bär statusen
   (VERIFIERAD / OKAND_PARAGRAF / OKAND_LAG) så grafen förblir sammanhängande
   utan brutna länkar medan verifieringen syns inne i varje not. Text som inte
   parsas som lagrum lämnas som klartext.
4. **Repetitionskort:** facit-baserade, kortets framsida är fallets rättsfråga,
   baksidan är slutsats + tillämpliga lagrum. Deterministiskt och alltid
   korrekt eftersom det hämtas ur det verifierade facit.

## UI-koppling

En tredje `st.download_button` i `_render_framsteg` (`streamlit_app.py`) intill
Markdown/Excel-knapparna → `bygg_valv(...)`, `file_name="juridik_valv.zip"`,
`mime="application/zip"`, med en `st.info` som säger åt studenten att öppna den
uppackade `Juridik`-mappen som ett valv i Obsidian.

## Testning

`tests/test_obsidian.py`, packa upp bytes i minnet (`ZipFile(BytesIO(...))`) och
verifiera: förväntade notsökvägar finns; wikilänkmål matchar verkliga
lagrumsnotfilnamn (inga brutna länkar); frontmatter parsar; ett påhittat
studentlagrum ger ändå en not men med icke-VERIFIERAD status;
repetitionssektionen har `::`-kort; `notnamn` sanerar förbjudna tecken men
behåller `§`. Rena funktioner, fail fast-stil som `test_export.py`.

## Avgränsningar (YAGNI)

- Tutorns feedbacktext exporteras inte, endast studentens svar och det
  deterministiska facit (per uppgiftstexten "studentens RNTS svar och facit").
- Ingen live-Obsidian-integration; endast nedladdningsbar zip.
