# Juridisk översiktskurs – fallbaserad övningsapp

En Streamlit-app för studenter på Juridisk översiktskurs (JÖK). Appen tränar
juridisk metod fallbaserat enligt RNTS-strukturen (Rättsfrågan, Norm,
Tillämpning, Slutsats) med en LLM-tutor som granskar studentens eget
resonemang – och ett deterministiskt hallucinationsskydd som verifierar varje
citerat lagrum mot kursens lagrumsregister.

> Appen är ett studieverktyg och ger inte juridisk rådgivning.

## Funktioner

- **Åtta P0-moduler**: Juridisk metod, Avtalsrätt, Köp- och konsumenträtt,
  Skadeståndsrätt, Arbetsrätt, Associationsrätt, Familje- och successionsrätt
  samt Straff- och processrätt. Varje modul har rättsfall med RNTS-formulär,
  quiz och lagrumsjakt.
- **Lagrumsverifiering**: alla lagrum – studentens och tutorns – valideras
  mot `data/lagrum.json`. Verifierade lagrum blir klickbara chips till
  lagen.nu; overifierade markeras med gul varning.
- **Tutor on demand**: förklaringar genereras endast på knapptryck, cachas på
  hash av inputs och skyddas av sessionstak (40 anrop) och delat dagstak
  (300 anrop). Utan token fungerar allt deterministiskt innehåll ändå.
- **Deterministisk rättning**: quiz och lagrumsjakt rättas helt utan LLM.
- **Kunskapsutmaning**: LLM-genererade, fiktiva rättsfall som grundas mot
  lagrumsregistret innan de visas – med kuraterat fall som fallback.
- **Kunskapskarta**: interaktiv graf i appen över genomförda rättsfall och
  de lagrum de bygger på.
- **Export**: quizresultat och genomförda rättsfall kan laddas ner som
  Markdownrapport eller Excelfil från startsidans framstegssektion.
- **Obsidianvalv med Rättskartan**: en zip med en hopfällbar, klickbar
  karta över det svenska rättssystemet (en not per lag: vad den täcker,
  när den övervägs, relaterade lagar) plus en not per genomförd
  RNTS-analys, sammanlänkade via wikilänkar och backlinks.

## Installation

Kräver Python 3.11 eller senare.

```bash
git clone https://github.com/Maibra23/juridik_oversiktskurs.git
cd juridik_oversiktskurs
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Appen startar på `http://localhost:8501`. Utan Hugging Face-token körs den i
offlineläge: allt innehåll, all rättning och alla facit fungerar, men
tutorknapparna visar ett informationskort i stället för LLM-svar.

## Hugging Face-token (aktiverar tutorn)

1. Skapa en läs-token på [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
2. Kopiera mallen och fyll i din token:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

```toml
# .streamlit/secrets.toml (gitignorerad – checka aldrig in den)
HF_TOKEN = "hf_..."
# Valfritt:
# LLM_MODEL = "Qwen/Qwen3-8B"      # eller "Qwen/Qwen3-14B"
# LLM_DAILY_CAP = "300"            # delad daglig anropsbudget
```

## Arkitektur

```
streamlit_app.py          Startsida: modulkarta, framsteg, export
pages/                    En tunn sida per modul (1–8), Kunskapstest (9),
  │                       Kunskapskarta (10) och Kunskapsutmaning (11)
  └── anropar utils/modulvy.rendera_modulsida(...)
utils/
  modulvy.py              Delad modulvy: RNTS-formulär, quiz, lagrumsjakt
  lagrum.py               Regex-extraktion + validering mot data/lagrum.json
  scenarier.py            Schema (frozen dataclasses) + inläsning/validering
  prompts.py              Systemprompt (RNTS, vitlista, anti-hallucination)
  tutor.py                On demand-generering, cache på inputhash, stale-flagg
  generator.py            LLM-genererade rättsfall med grundning + fallback
  llm.py / llm_budget.py  HF InferenceClient, sessions- och dagstak
  quiz.py                 Deterministisk rättning + resultat i session_state
  export.py               Markdown-/Excelrapporter, genomförda case
  obsidian.py             Obsidianvalv: analyser som sammanlänkade noter
  rattskarta.py           Rättskartan: hopfällbar karta över rättssystemet
  graf.py / graf_ui.py    Kunskapsgrafen i appen (vis-network i iframe)
  texter.py               Central texthjälp (svensk kongruensböjning m.m.)
  ui.py                   Designsystem: CSS, chips, RNTS-stepper, statuspanel
data/
  lagrum.json             Lagrumsregistret – appens enda sanningskälla
  rattssystem.json        Rättskartans hierarki (grundas mot lagrum.json)
  scenarier/*.json        Case, flervalsfrågor och lagrumsjakt per modul
tests/                    340+ pytest-tester (lagrum, quiz, prompts,
                          generator, rättskarta, språk-QA, smoke)
```

Flödet för hallucinationsskyddet: studentens normfält valideras direkt
(grönt/gult) innan LLM alls anropas; varje tutorsvar körs genom
`verify_lagrum` och renderas med verifierade chips respektive varningsrutor.

## Utveckling

```bash
pip install pytest ruff mypy
ruff check .                        # lint
mypy --ignore-missing-imports utils # typkontroll
pytest -q                           # testsvit
```

CI (`.github/workflows/ci.yml`) kör samma tre steg på Python 3.11 vid varje
push och pull request, utan HF-token.

## Skärmbilder

| Startsida | Modulsida (RNTS) | Tutorsvar med chips |
| --- | --- | --- |
| _(skärmbild kommer)_ | _(skärmbild kommer)_ | _(skärmbild kommer)_ |
