# Juridikverkstan

Ett fallbaserat övningsverktyg för svensk juridik. Du skriver din egen analys
först och får återkoppling efteråt, aldrig ett färdigt modellsvar att kopiera.

> Juridikverkstan är ett studieverktyg och ger inte juridisk rådgivning.
> Kontrollera alltid lagrum mot [lagen.nu](https://lagen.nu).

## Om appen

Den som lär sig juridik har sällan brist på läsmaterial. Bristen sitter i
träningen: att gå från en hög med fakta till en hållbar rättslig slutsats.
Juridikverkstan tränar just det steget och inget annat.

Arbetet följer metoden RNTS i fyra led: Rättsfrågan, Norm, Tillämpning och
Slutsats. Du får ett rättsfall, fyller i de fyra fälten själv, och först
därefter öppnas facit. En handledare driven av språkmodell kommenterar det du
faktiskt skrev, i stället för att lösa uppgiften åt dig.

Det som skiljer appen från en vanlig chattbot är grundningen. Varje lagrum som
nämns, ditt eget såväl som handledarens, valideras mot ett register med 21
lagar innan det visas. Ett lagrum som inte kan verifieras blir en synlig
varning, inte en tystad felaktighet. Registret är i sin tur kontrollerat mot
lagarnas egen kapitelindelning hämtad från Riksdagens öppna data, så att ett
påhittat paragrafnummer inte kan slinka igenom.

Innehållet i siffror:

| Innehåll | Antal |
|---|---|
| Övningsmoduler | 12 |
| Lagar i registret | 21 |
| Rättsfall med facit | 19 |
| Flervalsfrågor | 86 |
| Uppgifter i lagrumsjakten | 43 |
| Nyckelbegrepp | 58 |
| Delområden i Rättskartan | 30 |

**Teknik.** Python och [Streamlit](https://streamlit.io) för hela gränssnittet.
Språkmodellen nås via [Hugging Face](https://huggingface.co) Inference
Providers (`huggingface_hub`) och är helt valfri: allt deterministiskt innehåll
fungerar utan nyckel. Grafvyerna ritas med vis-network, rapportexporten med
`openpyxl`. Inget externt beroende utöver detta, ingen databas och ingen
inloggning.

## Installation

Du behöver `git` och Python 3.10 eller senare. Python 3.9 fungerar också, men
låser dig till en äldre Streamlit, eftersom versioner från 1.51 kräver 3.10.
CI kör på 3.11.

```bash
git clone https://github.com/Maibra23/juridik_oversiktskurs.git
cd juridik_oversiktskurs

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

Det räcker för att köra appen. Handledaren kräver dock en nyckel till Hugging
Face, och den lägger du i en egen fil som aldrig checkas in:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Fyll i din nyckel:

```toml
HF_TOKEN = "hf_..."

# Valfritt.
LLM_MODEL = "Qwen/Qwen3-8B"     # eller "Qwen/Qwen3-14B"
LLM_DAILY_CAP = "300"           # delat dagstak för antalet anrop
```

Skapa nyckeln under [Access Tokens](https://huggingface.co/settings/tokens) och
ge den enbart behörigheten *Make calls to Inference Providers*. Filen
`.streamlit/secrets.toml` är gitignorerad. Vid drift i Streamlit Community
Cloud lägger du samma värden i appens egen hemlighetspanel i stället.

## Användning

Starta appen:

```bash
streamlit run streamlit_app.py
```

Appen öppnas på `http://localhost:8501`. Ingen inloggning behövs.

**Utan nyckel** fungerar tolv övningsmoduler, alla flervalsfrågor, hela
lagrumsjakten, facit, Rättskartan, Kunskapskartan och exporten. Det enda som
kräver nyckel är de genererade förklaringarna och de nya rättsfallen i
Kunskapsutmaningen.

En rundtur på fem minuter:

1. **Hem** visar var du står och pekar ut ett enda nästa steg.
2. **Juridisk metod** introducerar RNTS. Börja här om metoden är ny för dig.
3. Välj en modul, till exempel **Avtalsrätt**. Fyll i alla fyra RNTS-fälten och
   tryck på *Rätta*. Facit ligger bakom ett eget klick, så du hinner tänka
   färdigt först.
4. **Rättskartan** visar hur rättsområdena hänger samman. Trädvyn är förvald,
   kraftvyn väljer du aktivt när du vill se sambanden som en graf.
5. **Kunskapstest** och **Kunskapskarta** sammanfattar det du gjort.

Framstegen är bundna till sessionen. De lever så länge fliken är öppen och
försvinner när du stänger den. Vill du spara något laddar du ner en rapport
eller ett Obsidianvalv från framstegssektionen på startsidan innan du går.

Ett par skript sköter underhållet av datan:

```bash
python scripts/hamta_lagstruktur.py    # kapitelindelning från Riksdagen
python scripts/hamta_lagtext.py        # paragraftext för registrets lagar
python scripts/verifiera_lagavsnitt.py # jämför registret mot lagarnas struktur
```

## Utveckling och bidrag

Felrapporter och förslag är välkomna som ett ärende (*issue*) i repot. Skriv
gärna vad du gjorde, vad du väntade dig och vad som hände i stället. Rör det
ett lagrum eller ett facit, ange lagrummet så att påståendet kan kontrolleras
mot källan.

Vill du bidra med kod:

1. Skapa en gren från `main` med prefixet `feat/`, `fix/` eller `chore/`.
2. Skriv testet först. Sviten är projektets kravspecifikation och ska växa med
   varje ändring.
3. Kör hela kvalitetsgrinden lokalt innan du öppnar en *pull request*:

```bash
python -m pytest -q                              # 1582 tester
python -m ruff check .                           # lint
python -m mypy --ignore-missing-imports utils    # typkontroll
node --test tests/js/                            # grafens skiktlogik
```

Samma fyra steg körs i CI vid varje push, utan nyckel, alltså i offlineläge.

Tre regler är hårdare än de ser ut, och en granskning kommer att fråga om dem:

- **Inget lagrum utan täckning i registret.** Data i `data/lagrum.json` är
  appens enda sanningskälla för tillåtna hänvisningar. Ny text får inte
  referera till lagrum som saknas där.
- **Ordagrann författningstext ändras aldrig.** Innehållet i `data/lagtext/`
  och `data/lagstruktur/` är hämtat från Riksdagen och citeras, inte skrivs.
- **Språket är svenskt och granskas automatiskt.** `tests/test_sprak.py`
  vaktar teckenkodning, förbjuder ikoner och emoji, och stoppar
  tankstrecksinterpunktion.

Vänligt och sakligt tonläge gäller i ärenden och kodgranskning. Kritik riktas
mot koden eller texten, aldrig mot personen.

## Licens

Utgiven under MIT-licensen. Du får använda, ändra, sprida och sälja koden,
även i egna projekt, så länge upphovsrättsnotisen och licenstexten följer med.
Se [LICENSE](LICENSE) för hela villkoret.

Författningstexten i `data/lagtext/` och `data/lagstruktur/` kommer från
Riksdagens öppna data. Svenska författningar omfattas inte av upphovsrätt
enligt 9 § upphovsrättslagen.
