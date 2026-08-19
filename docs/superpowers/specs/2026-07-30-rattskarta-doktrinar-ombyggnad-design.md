# Rättskartan: doktrinär ombyggnad (projekt B+C)

**Datum:** 2026-07-30
**Status:** Design godkänd (riktning + delbeslut), väntar på spec-granskning
**Omfång:** Projekt B+C av fyra. Bygger på §2 i sessionens klassificeringsgranskning.

## Problem

Rättskartan är i dag organiserad efter kursbokens fyra **avdelningar** (AVD I,IV),
inte efter rättens doktrinära systematik. Två konsekvenser:

1. **Straffrätt och processrätt** ligger i en egen AVD IV. Doktrinärt hör de till
   **offentlig rätt** (staten ↔ enskild).
2. **Civilrätten är platt**: avtalsrätt, köp-/konsumenträtt, skadeståndsrätt,
   fastighetsrätt, associationsrätt, arbetsrätt och fordringsrätt ligger som
   syskon. Doktrinen är hierarkisk: **förmögenhetsrätt → obligationsrätt / sakrätt**,
   där köprätt och arbetsrätt är *speciell avtalsrätt* under obligationsrätten.

Dessutom: användaren vill **inte** se avdelningarna, vill ha **färg per gren** och
en **återställningsknapp**.

## Mål

Bygg om taxonomin till rättens verkliga systematik, ta bort avdelningsnivån, färga
efter huvudgren och lägg till en återställningsknapp. Juridisk metod visas **inte** i
kartan (den nås via sidopanelen).

## Kärnbeslut: rekursivt träd

Dagens modell har **fast djup** (rot → avdelning → område → delområde → lag) och
hela stacken förutsätter det. Doktrinen är **ojämnt djup**:

```
Svensk rätt → Civilrätt → Förmögenhetsrätt → Obligationsrätt → Speciell avtalsrätt → Köprätt → KöpL
```

Sex namngivna nivåer på civilrättssidan, två,tre på den offentliga. Fast djup kan
inte representera det. Datamodellen byts därför till ett **rekursivt träd av grenar**
med lagar som löv.

## Hård begränsning: bevara delområdes-id:na

`data/nyckelbegrepp.json` knyter varje begrepp till ett **delområdes-id**
(`avtalsratt`, `kop_och_konsumentratt`, `skadestandsratt`, `arbetsratt`,
`fastighetsratt`, `associationsratt`, `fordringsratt`, `personratt`,
`makar_och_sambor`, `foraldrar_och_barn`, `arv_och_testamente`,
`brott_och_ansvar`, `rattegangen`, `verkstallighet_och_obestand`), och
`utils.nyckelbegrepp` fail-fast-validerar att id:t finns i taxonomin.

**Dessa 14 id:n MÅSTE bevaras** som grennoder i det nya trädet, de flyttas bara till
nya doktrinära föräldrar. Inga begrepp får behöva röras.

## Nytt träd (grenar med bevarade löv-id inom parentes)

```
Svensk rätt
├─ Offentlig rätt
│   ├─ Statsrätt            → (nytt id) statsratt        [inga kurslagrum ännu]
│   ├─ Förvaltningsrätt     → (nytt id) forvaltningsratt [inga kurslagrum ännu]
│   ├─ Straffrätt           → brott_och_ansvar (BrB)
│   └─ Processrätt och exekutionsrätt
│        ├─ Rättegången               → rattegangen (RB)
│        └─ Verkställighet och obestånd → verkstallighet_och_obestand (UB, KonkL)
└─ Civilrätt
    ├─ Förmögenhetsrätt
    │   ├─ Obligationsrätt
    │   │   ├─ Allmän avtalsrätt      → avtalsratt (AvtL)
    │   │   ├─ Speciell avtalsrätt
    │   │   │   ├─ Köprätt och konsumenträtt → kop_och_konsumentratt (KöpL, KKöpL, MFL)
    │   │   │   └─ Arbetsrätt              → arbetsratt (LAS)
    │   │   ├─ Skadeståndsrätt        → skadestandsratt (SkL)
    │   │   └─ Fordringsrätt och krediträtt → fordringsratt (SkbrL, PreskL)
    │   └─ Sakrätt
    │        └─ Godtrosförvärv m.m.   → personratt-delen som är sakrätt: GFL
    ├─ Familjerätt och successionsrätt
    │   ├─ Makar och sambor           → makar_och_sambor (ÄktB, SamboL)
    │   ├─ Föräldrar och barn         → foraldrar_och_barn (FB)
    │   └─ Arv och testamente         → arv_och_testamente (ÄB)
    ├─ Associationsrätt               → associationsratt (ABL, HBL)
    └─ Fastighetsrätt                 → fastighetsratt (JB)
```

Öppna punkter att lösa vid implementation (noteras, inte blockerande):
- Dagens delområde **`personratt`** ("Personrätt och allmän förmögenhetsrätt") bär två
  saker: LFF (framtidsfullmakt, personrätt) och GFL (godtrosförvärv, sakrätt). Begrepp
  pekar på id:t `personratt`. Lösning: behåll id:t `personratt` som ett löv och placera
  det under **Sakrätt** (dess tyngdpunkt i kartan är godtrosförvärv/lösningsrätt);
  behåll LFF där. Alternativt splittra vid ett senare tillfälle. Vi bevarar id:t.
- Statsrätt/Förvaltningsrätt har inga kurslagrum i dag (visas som "kommer"). De blir
  grennoder utan lag-löv, precis som i sidopanelen.

## Datamodell (`data/rattssystem.json`)

En rekursiv `gren`-nod:

```json
{
  "id": "obligationsratt",
  "namn": "Obligationsrätt",
  "beskrivning": "...",
  "nar": "...",              // valfritt
  "barn": [ <gren> | <lagref> ]
}
```

En löv-lagref behåller dagens form: `{ "forkortning": "KöpL", "beskrivning": "...", "nar": "...", "relaterade": [...] }`.

En gren har **antingen** `barn` som är grenar **eller** `barn` som är lagref:er (löv).
Topp-grenarna är `offentlig_ratt` och `civilratt`. Roten är implicit ("Svensk rätt").

## Kodändringar

### `utils/rattskarta.py`
- Ersätt `Avdelning`/`Omrade`/`Underomrade` med en rekursiv `Gren`-dataklass
  (`id, namn, beskrivning, nar, barn: tuple[Gren, ...] | tuple[LagPost, ...]`).
- `ladda_rattssystem()` returnerar topp-grenarna. `ladda_avdelningar()` tas bort.
- Ny hjälpare `delomraden()` som ger alla löv-grenar (de som bär lagar) för
  `nyckelbegrepp`-validering och för `begrepp_per_omrade`.
- Obsidian-exporten (`lagnot`, `omradesnot`, `rattskarta_not`, `_tradgren`,
  `rattskarta_filer`, `falltypsguide`, `_lagindex`) skrivs om att rekursera trädet.
  Utfallet (markdown-filer) ska vara likvärdigt men följa den nya hierarkin.

### `utils/rattssystem_graf.py`
- `taxonomi()` returnerar det rekursiva trädet (topp-grenar).
- `bygg_taxonomigraf()` rekurserar: `niva` = djup, `gren` (topp-grenens id) ärvs nedåt
  på varje nod och driver färg. Lagnoder behåller `url` och skopat id (`lag::<gren>::<förk>`).
- `alla_lagar()` rekurserar.

### `utils/taxonomi_ui.py`
- Färg per **topp-gren**: Offentlig rätt = en färg, Civilrätt = en annan; lag = guld,
  rot = bläck (som i dag). Ersätt `AVDELNINGSFARGER` med `GRENFARGER` (2 grenar).
- `render_farglegend()` visar de två grenarna.

### `sidor/16_Rattskartan.py`
- Rendera trädet rekursivt (grenar som nästlade expanders där Streamlit tillåter;
  lag-kort på lövnivå). Ta bort AVD-etiketterna. Ingen Juridisk metod-nod.
- **Återställningsknapp** överst: tömmer `falltyp_sok`, `begrepp_sok`, `begrepp_omrade`
  ur `st.session_state` och kör `st.rerun()`. Expandrar fälls då ihop automatiskt,
  eftersom deras `expanded` styrs av om ett filter är aktivt.

### `utils/nyckelbegrepp.py`
- Uppdatera `begrepp_per_omrade()` och valideringen att läsa löv-grenarna via
  `delomraden()` i stället för `omrade.underomraden`. Id:na är oförändrade, så
  begreppsdatat rörs inte.

## Tester

Skrivs om/utökas: `test_rattskarta.py`, `test_rattssystem_graf.py` (+ `test_graf.py`),
`test_taxonomi_ui.py`, `test_avdelningar.py` (blir `test_grenar.py` eller tas bort),
`test_nyckelbegrepp.py` (id-bevarande), `test_rattskartan_sida.py` (återställningsknapp),
och Obsidian-exportens tester (`test_obsidian.py` om relevant).

Nya invarianter att vakta:
- Alla 14 delområdes-id finns kvar som löv-grenar (regression mot begreppskopplingen).
- Straffrätt och process-/exekutionsrätt ligger under `offentlig_ratt`.
- Köp-/konsumenträtt och arbetsrätt ligger under speciell avtalsrätt under obligationsrätt.
- Grafen är fortfarande ett strikt träd (kanter = noder , 1).
- Ingen nod har `gren`-färg utanför {offentlig_ratt, civilratt} utom rot/lag.
- Juridisk metod förekommer inte i grafen.

## Utanför omfånget
- **Projekt D** (kapitel-/momentnedbrytning av varje lag) är separat.
- Ingen ändring av begreppsdatat eller lagrumsregistret.
- Ingen ändring av modulsidorna eller övningsflödena.
