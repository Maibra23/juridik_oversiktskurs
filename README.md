# Juridisk översiktskurs – fallbaserad övningsapp

En Streamlit-app för studenter på Juridisk översiktskurs (JÖK). Appen tränar
juridisk metod fallbaserat enligt RNTS-strukturen (Rättsfrågan, Norm,
Tillämpning, Slutsats) med en LLM-tutor som granskar studentens eget
resonemang – och ett deterministiskt hallucinationsskydd som verifierar varje
citerat lagrum mot kursens lagrumsregister.

> Appen är ett studieverktyg och ger inte juridisk rådgivning.

## Vad du kan förvänta dig

Du skriver din egen analys först, och får återkoppling efteråt. Appen rättar
aldrig åt dig innan du gjort ett försök: facit ligger bakom ett eget klick,
och tutorn kommenterar det du faktiskt skrev i stället för att servera ett
modellsvar. Allt deterministiskt innehåll – quiz, lagrumsjakt, facit, kartor –
fungerar utan inloggning och utan API-nyckel.

Framstegen är **sessionsbundna**: de lever så länge fliken är öppen och
försvinner när du stänger den. Vill du spara något laddar du ner det från
startsidans framstegssektion innan du går.

## Funktioner

- **Tolv kursmoduler**: Juridisk metod, Personrätt, Allmän förmögenhetsrätt,
  Avtalsrätt, Köp- och konsumenträtt, Skadeståndsrätt, Arbetsrätt,
  Associationsrätt, Familje- och successionsrätt, Straff- och processrätt,
  Fastighetsrätt och Fordringsrätt. Varje modul har rättsfall med
  RNTS-formulär, flervalsfrågor och lagrumsjakt.
- **Lagrumsverifiering**: alla lagrum – studentens och tutorns – valideras mot
  `data/lagrum.json`. Verifierade lagrum blir klickbara chips till lagen.nu;
  overifierade markeras med gul varning. Förkortningar godtas oavsett skiftläge
  och även utskrivna former ("4 paragrafen avtalslagen").
- **Tutor on demand**: förklaringar genereras endast på knapptryck, cachas på
  hash av inputs och skyddas av sessionstak (40 anrop) och delat dagstak
  (300 anrop). Utan token fungerar allt deterministiskt innehåll ändå.
- **Deterministisk rättning**: quiz och lagrumsjakt rättas helt utan LLM.
- **Kunskapsutmaning**: LLM-genererade, fiktiva rättsfall som grundas mot
  lagrumsregistret innan de visas – med valbar svårighetsgrad och kuraterat
  fall som fallback.
- **Rättskartan**: en interaktiv karta över hela det svenska rättssystemet.
  Klicka en gren för att fokusera den, klicka en guldfärgad lagnod för att
  öppna lagen.nu. En kryssruta växlar mellan ren kurskarta (de 21 lagar kursen
  rättar mot) och hela rättssystemet i överblick. Sidan rymmer också en
  falltypsguide, en sökbar begreppslista och lagkort som visar var i lagens
  kapitelstruktur kursavsnitten ligger.
- **Kunskapskarta**: interaktiv graf över dina genomförda rättsfall och de
  lagrum de bygger på. Lagrum som återkommer i flera fall blir gemensamma noder.
- **Export**: quizresultat och genomförda rättsfall kan laddas ner som
  Markdownrapport eller Excelfil från startsidans framstegssektion.
- **Obsidianvalv**: en zip med en not per lag och en not per genomförd
  RNTS-analys, sammanlänkade via wikilänkar och backlinks.

## Innehållet i siffror

| | |
| --- | --- |
| Kursmoduler | 12 |
| Rättsfall (RNTS) | 19 |
| Flervalsfrågor | 86 |
| Lagrumsjakter | 43 |
| Nyckelbegrepp | 58 |
| Lagar i registret | 21 |
| Paragrafer i lagtextkorpusen | 1 008 |

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

Vid drift i Streamlit Cloud sätts `HF_TOKEN` i appens secrets-panel. Den lokala
`secrets.toml` följer aldrig med i en deploy.

## Arkitektur

```
streamlit_app.py          Entrépunkt: registrerar alla sidor via st.navigation
sidor/                    En tunn sida per modul och verktyg (17 st)
  └── anropar utils/modulvy.rendera_modulsida(...)
utils/
  modulvy.py              Delad modulvy: RNTS-formulär, quiz, lagrumsjakt
  lagrum.py               Regex-extraktion + validering mot data/lagrum.json
  lagstruktur.py          Lagarnas kapitel- och momentstruktur
  lagkort_avsnitt.py      Kursavsnitt grupperade per kapitel i lagkortet
  kursavsnitt_kontroll.py Kontroll av kursavsnitt mot lagens struktur
  lagtext.py              Paragraftexter ur lagtextkorpusen
  scenarier.py            Schema (frozen dataclasses) + inläsning/validering
  prompts.py              Systemprompt (RNTS, vitlista, anti-hallucination)
  tutor.py                On demand-generering, cache på inputhash, stale-flagg
  generator.py            LLM-genererade rättsfall med grundning + fallback
  svarighetsgrad.py       Svårighetsgrad för genererade rättsfall
  llm.py / llm_budget.py  HF InferenceClient, sessions- och dagstak
  quiz.py                 Deterministisk rättning + resultat i session_state
  framsteg.py             Sessionsbundna framsteg på startsidan
  rnts.py                 Vilket RNTS-steg varje aktivitet tränar
  export.py               Markdown-/Excelrapporter, genomförda case
  obsidian.py             Obsidianvalv: analyser som sammanlänkade noter
  rattskarta.py           Rättskartans data: hierarki, falltyper, begrepp
  rattssystem_graf.py     Bygger taxonomigrafen (kurslager + referenslager)
  taxonomi_ui.py          Renderar taxonomigrafen (vis-network i iframe)
  graf.py / graf_ui.py    Kunskapsgrafen över genomförda fall
  navigation.py           Navigeringsträd och sidopanelens hierarki
  css.py / ui.py          Designsystem: CSS-tokens, chips, RNTS-stepper
  texter.py               Central texthjälp (svensk kongruensböjning m.m.)
data/
  lagrum.json             Lagrumsregistret – appens enda sanningskälla
  rattssystem.json        Rättskartans hierarki (grundas mot lagrum.json)
  lagstruktur/*.json      Kapitel- och momentstruktur per lag
  lagtext/*.json          Paragraftexter, 1 008 paragrafer ur 21 lagar
  scenarier/*.json        Case, flervalsfrågor och lagrumsjakt per modul
tests/                    1 100+ pytest-tester (lagrum, quiz, prompts,
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
push och pull request, utan HF-token, samt JS-testerna för grafens skiktlogik.
Verktygsversionerna är pinnade med avsikt – höj dem medvetet, inte av misstag.

## Skärmbilder

| Startsida | Modulsida (RNTS) | Tutorsvar med chips |
| --- | --- | --- |
| _(skärmbild kommer)_ | _(skärmbild kommer)_ | _(skärmbild kommer)_ |
