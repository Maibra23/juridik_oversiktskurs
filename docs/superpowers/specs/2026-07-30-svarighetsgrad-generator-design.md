# Svårighetsgrad för genererade rättsfall

**Datum:** 2026-07-30
**Status:** Design godkänd, väntar på spec-granskning
**Omfång:** Projekt A av fyra (se sessionens dekomposition). Fristående.

## Problem

När studenten trycker på **"Generera nytt rättsfall"** väljer LLM:en själv
svårighetsgrad. Studenten kan inte styra hur svårt fallet blir. Vi vill lägga
till en väljare som sätts *före* generering, och låta modellen kalibrera fallet
efter vald nivå.

Fältet `Case.svarighetsgrad` finns redan men är en fri sträng med tre stavningar
i omlopp: kuraterad data använder `grund`/`medel` (plus ett felaktigt `svar`),
medan `build_generate_prompt` deklarerar `"grund" | "medel" | "avancerad"`.

## Nivåer

Tre nivåer (nyckel → etikett):

- `grund` → **Grund**: en tydlig rättsfråga, 1–2 lagrum, 4–5 meningar.
- `medel` → **Medel**: som grund men med en komplikation eller konkurrerande norm.
- `avancerad` → **Avancerad**: flera sammanflätade frågor, tvetydighet, 3+ lagrum.

Standard: `grund`. "Slumpa svårighet" ingår inte (YAGNI).

## Komponenter

### 1. Ny modul `utils/svarighetsgrad.py`

Enda ägare av svårighetsbegreppet. Ren Python, ingen Streamlit, ingen LLM.

- `SVARIGHETSNIVAER: tuple[tuple[str, str], ...]` — ordnad
  `(("grund","Grund"), ("medel","Medel"), ("avancerad","Avancerad"))`.
- `STANDARDNIVA = "grund"`.
- `NYCKLAR: tuple[str, ...]` — bara nycklarna, för validering.
- `etikett_for(nyckel) -> str` — visningsetikett; okänt → etiketten för STANDARDNIVA.
- `normalisera(varde: str | None) -> str` — mappar godtyckligt/äldre värde till en
  kanonisk nyckel. Skiftlägesokänsligt. `"svar"`/`"svår"` → `avancerad`;
  okänt/tomt/`None` → `grund`. Muterar inget.
- `instruktion_for(nyckel) -> str` — det svenska promptblock som beskriver vad
  nivån innebär (antal fakta, antal sammanflätade frågor, antal lagrum). Distinkt
  text per nivå. Okänd nyckel normaliseras först.

### 2. `utils/prompts.py` — `build_generate_prompt` får parameter `svarighetsgrad`

Ny signatur:
```
build_generate_prompt(modul_namn, forkortningar=None, striktare=False,
                      variation=None, svarighetsgrad=STANDARDNIVA)
```

Ändringar i user-prompten:
- Lägg in ett block **"SVÅRIGHETSGRAD (obligatorisk nivå)"** från
  `svarighetsgrad.instruktion_for(niva)`, som instruerar modellen att kalibrera
  `scenariotext`, antal sammanflätade frågor och antal lagrum efter nivån.
- **Pinna** JSON-schemats `svarighetsgrad`-fält till den valda nivån
  (`"svarighetsgrad": "<vald nivå>"`) i stället för det fria
  `"grund" | "medel" | "avancerad"`, så att det studenten bad om är det som
  registreras och visas.

Källreglerna, lagrumsvitlistan och förbudet mot påhitt är **oförändrade** —
grundningen fungerar exakt som idag.

### 3. `utils/generator.py` — `generera_case` får parameter `svarighetsgrad`

Ny signatur:
```
generera_case(modul_namn, klient=None, rng=None, svarighetsgrad=STANDARDNIVA)
```

- Normaliseras defensivt med `svarighetsgrad.normalisera(...)` överst.
- Skickas vidare till `build_generate_prompt(...)` i **båda** försöken.
- Fallback-vägen (kuraterat case) och den deterministiska lagrumsverifieringen
  är oförändrade. Ett kuraterat fallback-case behåller sin egen svårighetsgrad
  (vi förfalskar inte nivån på ett kuraterat fall).

### 4. UI — väljare före "Generera nytt rättsfall"

`st.segmented_control` (finns i Streamlit 1.50), etikett **"Svårighetsgrad"**,
horisontell, alternativ = de tre etiketterna, `default="Grund"`. Returnerar `None`
om inget är valt → tolka som `STANDARDNIVA`.

**`utils/modulvy.py` `_rendera_rattsfall`:** väljaren placeras ovanför
knappkolumnerna (`kol_ny`/`kol_kuraterat`), keyad per modul (`gen_niva_{filnamn}`)
så att varje ämnesmodul får sin egen. Vald nivå skickas till
`generera_case(filnamn, svarighetsgrad=...)`.

**`pages/11_Kunskapsutmaning.py`:** en väljare nära modul-selectboxen. Vald nivå
skickas till `generera_case(stem, svarighetsgrad=...)` för både **"Generera nytt
rättsfall"** och **"🎲 Överraska mig"**. Överraska mig slumpar bara modulen —
svårigheten är alltid den studenten valt.

Etikett↔nyckel-mappning görs via `svarighetsgrad`-modulen; UI:t hårdkodar inte
strängar.

### 5. Datafix

`data/scenarier/familje_och_arvsratt.json`, case `fam-case-1`:
`"svarighetsgrad": "svar"` → `"avancerad"` (fallet gäller efterlevande make,
särkullbarn, laglott och testamente — genuint avancerat).

## Felhantering

- Ogiltig nivå kan i praktiken inte nå generatorn (fasta UI-alternativ), men
  `normalisera` gör vägen defensiv: allt oväntat blir `grund`.
- `segmented_control` som returnerar `None` tolkas som `STANDARDNIVA`.

## Tester (TDD)

`tests/test_svarighetsgrad.py`:
- `normalisera`: `"svar"`/`"SVÅR"`/`""`/`None`/okänt → förväntad kanonisk nyckel.
- `etikett_for`: känd nyckel → rätt etikett; okänd → STANDARDNIVA:s etikett.
- `instruktion_for`: distinkt, icke-tom text per nivå; okänd nyckel normaliseras.

`tests/test_prompts.py` (utöka):
- `build_generate_prompt(..., svarighetsgrad="avancerad")` innehåller
  avancerad-instruktionen och pinnar schemafältet till `avancerad`.
- Olika nivåer ger olika instruktionstext i prompten.

`tests/test_generator.py` (utöka):
- `generera_case(..., svarighetsgrad="medel")` vidarebefordrar nivån till prompten
  (fejkklient som fångar system/user-prompt).
- Default utan argument ger `grund` i prompten.
- Ogiltig nivå normaliseras till `grund`.
- Befintliga fallback- och grundningstester fortsätter passera.

## Utanför omfånget (YAGNI)

- Ingen "slumpa svårighet".
- Ingen persistens av vald nivå utöver sessionen.
- Ingen ändring av hur kuraterade fall visas utöver datafixen.
- Inga ändringar i tutor-, quiz- eller lagrumsjaktflödena.
