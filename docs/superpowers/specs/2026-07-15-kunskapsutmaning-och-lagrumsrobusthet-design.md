# Designspec: Kunskapsutmaning + robust lagrumsverifiering + expertpersona

Datum: 2026-07-15
Status: godkänd design (brainstorming)

Denna spec omfattar fyra sammanhängande arbetsströmmar som utfördes i samma
omgång. De tre första är förutsättningar för att den fjärde (Kunskapsutmaning)
ska bli säker och effektiv.

---

## 1. Expertpersona i systemprompten

**Vad:** Byt tutorns roll i `utils/prompts.py::SYSTEM_PROMPT_BASE` från
"svensk juridiktutor på JÖK-nivå" till en **svensk juridisk expert med över 30
års erfarenhet av att undervisa juridik på alla nivåer**.

**Krav:**
- Behåll JÖK-kontexten (vitlistan är JÖK-avgränsad) och den pedagogiska
  principen "träna studenten, lös inte uppgiften".
- Behåll all struktur (RNTS), språkkrav, förbud mot påhitt, lagrumsformat och
  längdgräns oförändrade.
- Endast rollbeskrivningens inledande stycke ändras.

## 2. Robust lagrumsparser (löser formatglappet)

**Problem:** `LAGRUM_PATTERN` matchar bara ordningen `N § FÖRK`. Modellen skriver
i praktiken ofta omvänt (`AvtL 18 till 20 §§`), vilket gör att verifieringen inte ser
lagrummet, varken gröna lagen.nu-chips eller den gula hallucineringsvarningen
utlöses.

**Lösning (båda vägarna, per användarbeslut):**

### 2a. Parser fångar omvänd ordning
- Ny regex `LAGRUM_PATTERN_OMVAND` som fångar `FÖRK N §`, `FÖRK N,M §§` och
  `FÖRK N kap. M §`.
- `extrahera_lagrum` kör **båda** mönstren, samlar alla träffar med sina
  positioner, sorterar på startposition och väljer giriga icke-överlappande
  träffar (undviker dubbelräkning).
- **Säkerhet mot falska positiva:** en omvänd träff accepteras endast om dess
  förkortning finns i registret (`lagrum_register()`). Utan detta skulle varje
  versalinlett ord före ett `§` (t.ex. "Bestämmelsen 5 §") felaktigt flaggas.
  Framåtmönstret förblir registeroberoende (så påhittade `99 § AvtL` och
  `12 § FejkL` fortfarande fångas och flaggas).
- Kanonisk form (`_kanonisk`, obsidian-wikilänkar, chips) normaliserar alltid
  till `N § FÖRK` / `N kap. M § FÖRK` oavsett källordning.

### 2b. Skärpt prompt
- Lägg explicita exempel i `SYSTEM_PROMPT_BASE`: skriv `18 § AvtL`, ALDRIG
  `AvtL 18 §`; för intervall `28 till 30 §§ AvtL`.

**Tester:** utöka `tests/test_lagrum.py` med omvänd ordning (verifierad,
intervall, kapitel), falsk-positiv-skydd ("Bestämmelsen 5 §" → ingen träff), och
att omvänt påhittat paragrafnummer på känd lag flaggas OKAND_PARAGRAF.

## 3. Publik case-byggare

Exponera `bygg_case_fran_dict(rad)` i `utils/scenarier.py` som tunn publik
wrapper runt befintliga `_bygg_case`. Ger strukturvalidering gratis åt
generatorn och håller privatlogiken oförändrad.

## 4. Kunskapsutmaning (LLM-genererade rättsfall)

**Syfte:** studenten testar sin förmåga på ett färskt, fiktivt rättsfall som
genereras vid knapptryck, analyserar det med RNTS och får tutorns granskning ,
med samma hallucinationsskydd som resten av appen.

### Arkitektur (återbruk framför nybygge)
Ett genererat scenario tvingas in i befintliga `Case`/`CaseFacit`-dataklasser
och flödar därmed rakt in i befintligt case-kort, RNTS-formulär,
`build_case_prompt`-granskning och Obsidianexport. Inget parallellt flöde.

- **`utils/generator.py`** (ny): orkestrerar generering. LLM-klienten
  **injiceras** (unit-tester använder en fejk, inga live-anrop).
- **`utils/prompts.py`**: ny `build_generate_prompt(modul, whitelist)` som ber
  om ett strikt JSON-scenario som **endast** använder modulens vitlistade
  lagrum, under expertpersonan.
- **`utils/scenarier.py`**: `bygg_case_fran_dict` (se 3).
- **`pages/11_Kunskapsutmaning.py`** (ny): modulväljare + "Överraska mig".

### Dataflöde med grundning
```
välj modul (eller slumpa) → whitelist för modulen
  → LLM: build_generate_prompt → JSON-scenario
    → bygg_case_fran_dict()            (strukturvalidering)
      → validera_lagrum() på VARJE lagrum i facit
        alla VERIFIERAD?  → visa scenariot
        annars            → försök igen 1 gång (striktare påminnelse)
          fortfarande fel → fallback: slumpat kuraterat case ur modulen
```
Studenten ser aldrig ett scenario vars facit innehåller ett ogrundat lagrum.

### Felhantering
`LLMUnavailableError`/tak-fel → direkt till statisk fallback med svensk infotext
("LLM ej tillgänglig, här är ett kuraterat fall i stället"). Trasig/utebliven
JSON → räknas som misslyckat försök (retry → fallback).

### Retur
`generera_case(modul, klient=None)` returnerar en `GenereratResultat` med:
`case: Case`, `kalla: "genererad" | "fallback"`, och ev. `notis: str`. Genererade
case registreras i `session_state` för Obsidianexport, precis som författade case.

### Testning (TDD, inga live-anrop i unit-tester)
`tests/test_generator.py` med fejkklient:
- giltig JSON → `Case` byggs, alla lagrum VERIFIERAD, returneras som genererad
- JSON med påhittat lagrum (`99 § AvtL`) → retry, sedan fallback till statiskt case
- trasig/icke-JSON → fallback
- `LLMUnavailableError` → fallback utan krasch
- fallback-case är alltid ett verkligt, validerat case ur modulen
- "Överraska mig" väljer en giltig modul

---

## Icke-mål (YAGNI)
- Ingen MC-generering (endast RNTS-case i denna omgång).
- Ingen svårighetsväljare (kan läggas senare).
- Ingen omskrivning av obsidian-wikilänkning för omvänd ordning (kanonisk form
  räcker; studenttext normaliseras vid extrahering).
