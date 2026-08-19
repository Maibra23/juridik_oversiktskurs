# Avtalsrätt: sju avtalstyper i Rättskartan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bryt ned Rättskartans "Speciell avtalsrätt" i sju avtalstyper (enligt
kursmaterialets förlaga) genom att koppla fastighetsköp/-hyra till
avtalsrätten och lägga till tre lagfria kartnoder (transportavtal, leasing,
licensavtal), utan att röra grafens rendering eller trigga full
lagregistrering.

**Architecture:** Rent datadrivet. All ändring sker i `data/rattssystem.json`
den rekursiva doktrinära trädstruktur som `utils/rattskarta.py` läser och
validerar (`_bygg_gren`). Taxonomigrafen (`utils/rattssystem_graf.py`,
`utils/taxonomi_ui.py`, `utils/static/taxonomigraf.js`) läser trädet
generiskt via `niva`/`foralder` och kräver inga kodändringar.

**Tech Stack:** Python 3.11 (`python3.11`, inte systemets `python3`
3.9.6, se `pip3 --version`), pytest, ren JSON-data.

**Referens:** Fullständig design i
`docs/superpowers/specs/2026-08-06-avtalsratt-sarskild-nedbrytning-design.md`.

## Global Constraints

- En gren har ANTINGEN `"grenar"` ELLER `"lagar"`, aldrig båda/ingetdera
  (`_bygg_gren`, `utils/rattskarta.py:106 till 110`). Redan testat generiskt av
  `test_trasig_data_ger_tydligt_fel` i `tests/test_rattssystem_graf.py:170` ,
  ingen ny test för själva invarianten behövs i den här planen.
- Varje `lagar[].forkortning` måste finnas i `data/lagrum.json`. Ingen ny
  förkortning läggs till i den här planen, se specens "Utanför omfånget".
  `kop_av_fast_egendom`/`hyra_av_fast_egendom` återanvänder den redan
  registrerade förkortningen `JB`; `transportavtal`/`leasing`/`licensavtal`
  får `"lagar": []`.
- Slutlig ordning i `speciell_avtalsratt.grenar`: `kop_och_konsumentratt`,
  `kop_av_fast_egendom`, `hyra_av_fast_egendom`, `transportavtal`, `leasing`,
  `arbetsratt`, `licensavtal`.
- Full `pytest`-svit (798 tester före denna plan) + `ruff check .` +
  `python3.11 -m mypy` måste vara gröna innan sista committen.

---

### Task 1: Fastighetsköp och -hyra kopplas till avtalsrätten (JB delas i tre noder)

**Files:**
- Modify: `data/rattssystem.json` (inuti `speciell_avtalsratt.grenar`, precis
  före `"id": "arbetsratt"`; samt `fastighetsratt`-objektet längre ner i
  filen, sök `"id": "fastighetsratt"`)
- Test: `tests/test_rattssystem_graf.py` (lägg till efter
  `test_samma_lag_i_tva_grenar_ger_tva_distinkta_noder`, rad ~148, före
  kommentarraden `# --- Taxonomiträdet ---`)

**Interfaces:**
- Consumes: `utils.rattskarta.hitta_gren(gren_id: str) -> Gren | None`,
  `utils.rattssystem_graf.bygg_taxonomigraf() -> dict` (nycklarna `"noder"`
  och `"kanter"`, varje nod har `"id"`, `"label"`, `"grupp"`, och för
  lagnoder `"forkortning"`), `utils.rattssystem_graf.lag_id(gren_id: str,
  forkortning: str) -> str`.
- Produces: två nya gren-id:n i trädet, `kop_av_fast_egendom` och
  `hyra_av_fast_egendom`, som Task 2 och Task 3 förutsätter finns som
  `speciell_avtalsratt`-barn nr 2 och 3.

- [ ] **Step 1: Skriv de fallande testerna**

```python
def test_kop_och_hyra_av_fast_egendom_finns_under_speciell_avtalsratt():
    from utils.rattskarta import hitta_gren

    kop = hitta_gren("kop_av_fast_egendom")
    hyra = hitta_gren("hyra_av_fast_egendom")
    assert kop is not None, "kop_av_fast_egendom saknas i trädet"
    assert hyra is not None, "hyra_av_fast_egendom saknas i trädet"
    assert kop.ar_lov and hyra.ar_lov
    assert [lag.forkortning for lag in kop.lagar] == ["JB"]
    assert [lag.forkortning for lag in hyra.lagar] == ["JB"]
    assert "4 kap" in kop.lagar[0].beskrivning
    assert "12 kap" in hyra.lagar[0].beskrivning


def test_fastighetsratt_ar_nu_enbart_sakrattslig():
    from utils.rattskarta import hitta_gren

    fastighet = hitta_gren("fastighetsratt")
    assert fastighet is not None
    assert "köp" not in fastighet.beskrivning.lower()
    assert "hyra" not in fastighet.beskrivning.lower()
    assert fastighet.lagar[0].forkortning == "JB"


def test_jb_forekommer_som_tre_distinkta_lagnoder(graf):
    from utils.rattssystem_graf import lag_id

    jb_noder = {n["id"] for n in graf["noder"] if n.get("forkortning") == "JB"}
    assert jb_noder == {
        lag_id("fastighetsratt", "JB"),
        lag_id("kop_av_fast_egendom", "JB"),
        lag_id("hyra_av_fast_egendom", "JB"),
    }
```

- [ ] **Step 2: Kör testerna och bekräfta att de fallerar**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py -k "fast_egendom or jb_forekommer" -v`
Expected: FAIL, `hitta_gren("kop_av_fast_egendom")`/`hitta_gren("hyra_av_fast_egendom")`
returnerar `None`, och `jb_noder` innehåller bara en post
(`lag_id("fastighetsratt", "JB")`) i stället för tre.

- [ ] **Step 3: Lägg till de två nya noderna i `data/rattssystem.json`**

Öppna filen och hitta `speciell_avtalsratt.grenar` (sök `"id":
"kop_och_konsumentratt"`). Direkt före objektet med `"id": "arbetsratt"`,
infoga två nya syskonobjekt med samma indenteringsnivå som
`kop_och_konsumentratt`/`arbetsratt` (2-stegs JSON-indentering, läs av exakt
nivå från de omgivande raderna innan du redigerar):

```json
{
  "id": "kop_av_fast_egendom",
  "namn": "Köp av fast egendom",
  "beskrivning": "Köp, byte och gåva av fastighet: formkrav, fullbordan och fel i fastighet. Den obligationsrättsliga delen av jordabalken.",
  "nar": "Frågan gäller köp av fastighet (formkraven i 4 kap. JB) eller fel i fastigheten efter tillträde.",
  "lagar": [
    {
      "forkortning": "JB",
      "beskrivning": "Jordabalkens 4 kap. reglerar köp av fast egendom: formkrav för giltigt köp, fullbordan och fel i fastighet.",
      "nar": "Frågan rör formkraven för ett fastighetsköp eller fel i fastigheten efter tillträdet.",
      "relaterade": ["AvtL"]
    }
  ]
},
{
  "id": "hyra_av_fast_egendom",
  "namn": "Hyra av fast egendom",
  "beskrivning": "Hyra av bostad och lokal: besittningsskydd, uppsägning och hyresvillkor. Regleras i jordabalkens 12 kap., den s.k. hyreslagen.",
  "nar": "Frågan gäller ett hyresförhållande för fast egendom, besittningsskydd, uppsägning eller villkoren i hyresavtalet.",
  "lagar": [
    {
      "forkortning": "JB",
      "beskrivning": "Jordabalkens 12 kap. (hyreslagen) reglerar hyra av bostad och lokal: besittningsskydd, uppsägning och hyresvillkor.",
      "nar": "Frågan rör ett hyresförhållande: besittningsskydd, uppsägning av hyresgäst eller hyresvillkorens giltighet.",
      "relaterade": ["AvtL"]
    }
  ]
},
```

- [ ] **Step 4: Renodla `fastighetsratt` till sin sakrättsliga del**

Sök `"id": "fastighetsratt"` (en fristående toppgren under civilrätt, längre
ner i filen). Ersätt objektets `"beskrivning"`, `"nar"` och dess enda
`lagar[0]`-posts `"beskrivning"`/`"nar"`/`"relaterade"`, behåll `"id"` och
objektets plats i trädet oförändrade:

```json
{
  "id": "fastighetsratt",
  "namn": "Fastighetsrätt",
  "beskrivning": "Fast egendom som sakrättsligt objekt: fastighetstillbehör, servitut och panträtt.",
  "nar": "Frågan gäller vad som räknas som fastighetstillbehör, eller en rättighet som belastar fastigheten genom servitut eller panträtt, inte själva köpet eller hyresförhållandet.",
  "lagar": [
    {
      "forkortning": "JB",
      "beskrivning": "Jordabalken reglerar fast egendom sakrättsligt: fastighetstillbehör, servitut och panträtt.",
      "nar": "Frågan rör vad som är fastighetstillbehör, eller en rättighet som belastar fastigheten genom servitut eller panträtt.",
      "relaterade": ["ÄktB"]
    }
  ]
}
```

- [ ] **Step 5: Kör testerna igen och bekräfta att de passerar**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py -k "fast_egendom or jb_forekommer" -v`
Expected: PASS

- [ ] **Step 6: Regressionskontroll på de tre relaterade testfilerna**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py tests/test_rattskarta.py tests/test_grenar.py -v`
Expected: alla PASS (inga hårdkodade nodantal där som denna ändring bryter ,
se spec, avsnitt "Testning").

- [ ] **Step 7: Commit**

```bash
git add data/rattssystem.json tests/test_rattssystem_graf.py
git commit -m "feat: koppla köp och hyra av fast egendom till avtalsrätten"
```

---

### Task 2: Transportavtal, leasing och licensavtal som lagfria kartnoder

**Files:**
- Modify: `data/rattssystem.json` (samma `speciell_avtalsratt.grenar`-array
  som Task 1)
- Test: `tests/test_rattssystem_graf.py`

**Interfaces:**
- Consumes: `utils.rattskarta.hitta_gren` (som i Task 1). Förutsätter att
  Task 1 redan lagt in `kop_av_fast_egendom` och `hyra_av_fast_egendom` som
  `speciell_avtalsratt`-barn 2 och 3.
- Produces: tre nya lagfria gren-id:n, `transportavtal`, `leasing`,
  `licensavtal`, och den slutgiltiga 7-listan i `speciell_avtalsratt.grenar`
  som Task 3:s APPGUIDE-uppdatering utgår från.

- [ ] **Step 1: Skriv de fallande testerna**

Lägg till direkt efter testerna från Task 1:

```python
def test_transportavtal_leasing_licensavtal_ar_lagfria_placeholders():
    from utils.rattskarta import hitta_gren

    forvantad_text = {
        "transportavtal": "vägtransport",
        "leasing": "leasinglag",
        "licensavtal": "upphovsrättslagen",
    }
    for gren_id, text in forvantad_text.items():
        gren = hitta_gren(gren_id)
        assert gren is not None, f"{gren_id} saknas i trädet"
        assert gren.ar_lov
        assert gren.lagar == ()
        assert text in gren.beskrivning.lower()
        assert "inga lagrum ur kursens register" in gren.nar.lower()


def test_speciell_avtalsratt_har_sju_avtalstyper_i_ratt_ordning():
    from utils.rattskarta import hitta_gren

    speciell = hitta_gren("speciell_avtalsratt")
    assert speciell is not None
    assert [g.id for g in speciell.grenar] == [
        "kop_och_konsumentratt",
        "kop_av_fast_egendom",
        "hyra_av_fast_egendom",
        "transportavtal",
        "leasing",
        "arbetsratt",
        "licensavtal",
    ]
```

- [ ] **Step 2: Kör testerna och bekräfta att de fallerar**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py -k "placeholders or sju_avtalstyper" -v`
Expected: FAIL, `transportavtal`/`leasing`/`licensavtal` finns inte än, och
`speciell_avtalsratt.grenar` har bara 5 barn efter Task 1.

- [ ] **Step 3: Lägg till `transportavtal` och `leasing` före `arbetsratt`**

I samma array som Task 1, infoga direkt efter `hyra_av_fast_egendom` och
före `arbetsratt`:

```json
{
  "id": "transportavtal",
  "namn": "Transportavtal",
  "beskrivning": "Avtal om godsbefordran. Vilken lag som gäller beror på transportslag: väg (lagen (1974:610) om inrikes vägtransport, internationellt CMR-lagen (1969:12)), sjö (sjölagen, 1994:1009), järnväg (järnvägstrafiklagen, 1985:192) och luft (luftfartslagen, 2010:500).",
  "nar": "Frågan gäller ansvar för gods under transport. Avgör transportslaget först, det styr vilken lag som är tillämplig. Inga lagrum ur kursens register. Kartan pekar bara ut området.",
  "lagar": []
},
{
  "id": "leasing",
  "namn": "Leasing",
  "beskrivning": "Ingen särskild leasinglag finns i Sverige. Avtalet bedöms utifrån allmänna avtalsrättsliga principer, med försiktig analogi till köplagen eller konsumentköplagen. Konsumentkreditlagen (2010:1846) kan bli tillämplig om leasingen i realiteten är ett avbetalningsköp.",
  "nar": "Frågan gäller ett leasingavtal. Utgångspunkten är avtalet självt och allmänna avtalsrättsliga principer, det finns ingen dedikerad lagstiftning att falla tillbaka på. Inga lagrum ur kursens register. Kartan pekar bara ut området.",
  "lagar": []
},
```

- [ ] **Step 4: Lägg till `licensavtal` efter `arbetsratt`**

`arbetsratt`s avslutande `}` har i dag INGET kommatecken efter sig (den är
sista barnet i arrayen). Lägg till ett kommatecken där, och infoga
`licensavtal` som nytt sista barn direkt efter:

```json
{
  "id": "licensavtal",
  "namn": "Licensavtal",
  "beskrivning": "Avtal om rätt att använda någon annans immateriella rättighet. Vilken lag som styr beror på vad som licensieras: upphovsrättslagen (1960:729), patentlagen (1967:837) eller varumärkeslagen (2010:1877). Själva avtalet regleras i övrigt av allmän avtalsrätt.",
  "nar": "Frågan gäller rätten att nyttja någon annans immateriella rättighet. Avgör vilken rättighetstyp som licensieras, det styr vilken speciallag som är relevant. Inga lagrum ur kursens register. Kartan pekar bara ut området.",
  "lagar": []
}
```

`licensavtal` är nu den sista posten i arrayen, inget kommatecken efter dess
avslutande `}`.

- [ ] **Step 5: Kör testerna igen och bekräfta att de passerar**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py -k "placeholders or sju_avtalstyper" -v`
Expected: PASS

- [ ] **Step 6: Regressionskontroll**

Run: `python3.11 -m pytest tests/test_rattssystem_graf.py tests/test_rattskarta.py tests/test_grenar.py -v`
Expected: alla PASS

- [ ] **Step 7: Commit**

```bash
git add data/rattssystem.json tests/test_rattssystem_graf.py
git commit -m "feat: lägg till transportavtal, leasing och licensavtal som lagfria kartnoder"
```

---

### Task 3: Dokumentation och full verifiering

**Files:**
- Modify: `APPGUIDE.md:338`
- Verify: full `pytest`, `ruff`, `mypy`

**Interfaces:**
- Consumes: den färdiga 7-barns `speciell_avtalsratt` och de tre JB-noderna
  från Task 1 + Task 2.
- Produces: inget som senare tasks bygger på, sista tasken i planen.

- [ ] **Step 1: Räkna fram de verkliga nod-/kanttalen**

Run:
```bash
python3.11 -c "
from utils.rattssystem_graf import bygg_taxonomigraf
g = bygg_taxonomigraf()
print('noder:', len(g['noder']))
print('kanter:', len(g['kanter']))
"
```
Expected: `noder: 53`, `kanter: 52` (baslinjen var 46/45 före denna plan; +5
nya grennoder + 2 nya JB-lagnoder under `kop_av_fast_egendom`/
`hyra_av_fast_egendom`, `transportavtal`/`leasing`/`licensavtal` ger
grennoder men inga lagnoder). Om de utskrivna talen skiljer sig från 53/52,
använd de faktiska talen i nästa steg, gissa inte.

- [ ] **Step 2: Uppdatera APPGUIDE.md**

Filen `APPGUIDE.md`, rad ~335 till 339, innehåller i dag:

```
Hela taxonomin över svensk rätt som interaktiv graf, byggd efter rättens
doktrinära systematik: roten **Svensk rätt** delas i **offentlig rätt** (statsrätt,
förvaltningsrätt, straffrätt, processrätt och exekutionsrätt) och **civilrätt**, där
civilrätten följer spinen förmögenhetsrätt → obligationsrätt / sakrätt. Trädet är
ojämnt djupt, sex nivåer på civilrättssidan (t.ex. Civilrätt → Förmögenhetsrätt →
Obligationsrätt → Speciell avtalsrätt → Köprätt och konsumenträtt → KöpL), färre på den
offentliga. 46 noder, 45 kanter, ett strikt träd. Juridisk metod ingår inte i kartan;
den nås via sidopanelen.
```

Byt ut de tre sista meningarna (från "46 noder" till "sidopanelen.") mot
(ersätt `<NODER>`/`<KANTER>` med de riktiga talen från Step 1):

```
Speciell avtalsrätt rymmer sju avtalstyper (köprätt och konsumenträtt, köp
respektive hyra av fast egendom, transportavtal, leasing, arbetsrätt och
licensavtal); de tre sistnämnda saknar egna lagrum i kursens register och
pekar bara ut området. <NODER> noder, <KANTER> kanter, ett strikt träd.
Juridisk metod ingår inte i kartan; den nås via sidopanelen.
```

- [ ] **Step 3: Full verifiering**

Run:
```bash
python3.11 -m pytest -q
ruff check .
python3.11 -m mypy utils/rattskarta.py utils/rattssystem_graf.py
```
Expected: `803 passed` (798 tidigare + 5 nya i denna plan), `All checks
passed!` från ruff, `Success: no issues found` från mypy.

- [ ] **Step 4: Commit**

```bash
git add APPGUIDE.md
git commit -m "docs: uppdatera rättskartans nodantal och avtalstyper i APPGUIDE"
```
