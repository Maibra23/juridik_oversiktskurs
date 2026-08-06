# Avtalsrätten i Rättskartan: särskild avtalsrätt bryts ned i sina avtalstyper

**Datum:** 2026-08-06
**Status:** Design, ej implementerad.
**Omfång:** `data/rattssystem.json` under grenen `speciell_avtalsratt` samt den
befintliga toppgrenen `fastighetsratt`. Rör inte taxonomigrafens rendering
(`utils/taxonomigraf.js`, `utils/taxonomi_ui.py`, `utils/rattssystem_graf.py`) —
dessa läser trädet generiskt och kräver inga ändringar. Rör inte quiz, kunskapstest,
svårighetsgrad eller lagrumsverifiering.

## Problem

En skärmdump (kursmaterial, "Avtalsrätt") visar hur ämnet doktrinärt delas i två
skikt: **Allmän avtalsrätt** (ingående, fullmakt, ogiltighet, tolkning — dagens
`avtalsratt`-nod) och **Särskild avtalsrätt**, som i sin tur rymmer sju
avtalstyper: köp av lös egendom, köp av fast egendom, hyra av fast egendom,
transportavtal, leasing, anställningsavtal och licensavtal.

Dagens `speciell_avtalsratt`-gren (`data/rattssystem.json`, `civilratt →
formogenhetsratt → obligationsratt → speciell_avtalsratt`) har bara två av de
sju: `kop_och_konsumentratt` och `arbetsratt`. Två luckor väger tyngst:

- **Köp och hyra av fast egendom saknas som egna noder.** Innehållet finns —
  `Fastighetsrätt` (JB) är redan en nod i kartan — men den ligger som en fristående
  toppgren under Civilrätt, inte under Avtalsrätt. Kartan visar alltså inte att
  fastighetsköp och fastighetshyra *är* särskild avtalsrätt.
- **Transportavtal, leasing och licensavtal saknas helt.** Ingen nod, ingen text.

## Mål

Kartans `speciell_avtalsratt`-gren ska ha alla sju avtalstyper som barn, i samma
ordning som förlagan. De två som redan har lagstöd i kursens register (köp och
hyra av fast egendom) får fullständiga noder med lagrum. De tre som saknar
lagstöd i registret (transportavtal, leasing, licensavtal) får ändå kartnoder med
rätt lagnamn i beskrivningen — men utan att röra registret, quiz eller
svårighetsgrad. Se "Tekniska förutsättningar" för varför den gränsen finns.

## Tekniska förutsättningar

- **En gren har antingen `grenar` eller `lagar`, aldrig båda/ingetdera**
  (`utils/rattskarta.py:106–110`, `_bygg_gren`). En tom lista `"lagar": []`
  uppfyller kravet — det är exakt mönstret `statsratt`/`forvaltningsratt` redan
  använder för "(kommer)"-ämnen (`data/rattssystem.json:12–17`).
- **`lagar[].forkortning` valideras mot `data/lagrum.json`** via
  `lagrum_register()` (`utils/rattskarta.py:81–99`). En förkortning som inte
  finns där stoppar hela inläsningen.
- **Att lägga till en förkortning i `data/lagrum.json` är inte en isolerad
  ändring.** `tests/test_lagstruktur.py` och `tests/test_lagtext.py` kräver då
  matchande filer i `data/lagstruktur/<sfs>.json` respektive
  `data/lagtext/<sfs>.json` — Riksdagens kapitel/paragrafstruktur och full
  lagtext, normalt hämtade med `scripts/hamta_lagstruktur.py`. Det är fullt
  förarbete som inte är beställt här.
- **Samma lag i flera grenar ger distinkta grafnoder.** `lag_id(gren_id,
  forkortning)` (`utils/rattssystem_graf.py:93`) namnrymder lagnoder per
  förälder. Testet `test_samma_lag_i_tva_grenar_ger_tva_distinkta_noder`
  (`tests/test_rattssystem_graf.py:140`) bevisar mönstret redan fungerar för
  andra lagar. JB kan alltså återanvändas i tre grenar utan kollision.
- **Kvar-check:** `assert lagnoder == set(lagrum_register())`
  (`tests/test_rattssystem_graf.py:123`) kräver att *varje* förkortning i
  registret har minst en nod i trädet, och tvärtom. Så länge inga nya
  förkortningar läggs i `data/lagrum.json` påverkas inte det testet.
- **Registrets `kursavsnitt` för JB bekräftar gränsdragningen oberoende av den
  här designen.** `data/lagrum.json`, JB-postens `kursavsnitt`, delar redan
  kapitlen i precis samma två grupper: kap. 4 "Köp av fast egendom
  (formkrav)"/"Fel i fastighet" och kap. 12 "Hyra (bostadshyra)" mot kap. 1–2,
  6–7 (fastighetsgräns, tillbehör, panträtt, nyttjanderätt/servitut). Den
  obligationsrättsliga/sakrättsliga delningen i "Valda beslut" är alltså inte
  en ny tolkning — den följer en gränsdragning kursens eget lagrumsregister
  redan gör.

## Valda beslut

- **Transportavtal, leasing och licensavtal förblir lagfria kartnoder.**
  `"lagar": []`, precis som `statsratt`/`forvaltningsratt`. De verkliga lagarna
  (identifierade nedan, källor bifogade) skrivs in i `beskrivning`/`nar` som
  fri text i stället för strukturerade `lagar[]`-poster. Det ger studenten rätt
  lagnamn utan att trigga registerkravet, lagstruktur-scraping eller att
  ämnena plötsligt dyker upp i quiz/svårighetsgrad — ingen av de delarna läser
  fri text, bara `lagar[].forkortning`.
- **Fastighetsrätt delas efter sin egen redan skrivna gränsdragning.**
  Nodens nuvarande beskrivning säger redan att JB "Spänner över både
  obligationsrätt (fastighetsköpet) och sakrätt (panträtt och servitut)".
  Den obligationsrättsliga halvan (köp, formkrav, fel, hyra) flyttar till två
  nya noder under `speciell_avtalsratt`; den sakrättsliga halvan
  (fastighetstillbehör, servitut, panträtt) blir kvar på `fastighetsratt`,
  som förblir en egen toppgren under Civilrätt (den är inte ett avtal, den är
  ett förmögenhetsobjekt — sakrätt hör inte hemma under Avtalsrätt).
- **JB citeras tre gånger, med olika kapitel i varje nod.** Köp av fast
  egendom pekar på 4 kap. JB, hyra av fast egendom på 12 kap. JB
  ("hyreslagen"), och kvarvarande `fastighetsratt` på de sakrättsliga kapitlen
  (tillbehör, servitut, panträtt). Ingen ny förkortning krävs — bara tre noder
  som delar `forkortning: "JB"` men har olika `beskrivning`/`nar`.
- **Ordningen i `speciell_avtalsratt.grenar` följer förlagan:** köp av lös
  egendom, köp av fast egendom, hyra av fast egendom, transportavtal, leasing,
  anställningsavtal, licensavtal.

## Nya och ändrade noder

### `kop_av_fast_egendom` (ny, under `speciell_avtalsratt`)

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
}
```

### `hyra_av_fast_egendom` (ny, under `speciell_avtalsratt`)

```json
{
  "id": "hyra_av_fast_egendom",
  "namn": "Hyra av fast egendom",
  "beskrivning": "Hyra av bostad och lokal: besittningsskydd, uppsägning och hyresvillkor. Regleras i jordabalkens 12 kap., den s.k. hyreslagen.",
  "nar": "Frågan gäller ett hyresförhållande för fast egendom — besittningsskydd, uppsägning eller villkoren i hyresavtalet.",
  "lagar": [
    {
      "forkortning": "JB",
      "beskrivning": "Jordabalkens 12 kap. (hyreslagen) reglerar hyra av bostad och lokal: besittningsskydd, uppsägning och hyresvillkor.",
      "nar": "Frågan rör ett hyresförhållande: besittningsskydd, uppsägning av hyresgäst eller hyresvillkorens giltighet.",
      "relaterade": ["AvtL"]
    }
  ]
}
```

### `transportavtal` (ny, under `speciell_avtalsratt`, lagfri)

```json
{
  "id": "transportavtal",
  "namn": "Transportavtal",
  "beskrivning": "Avtal om godsbefordran. Vilken lag som gäller beror på transportslag: väg (lagen (1974:610) om inrikes vägtransport, internationellt CMR-lagen (1969:12)), sjö (sjölagen, 1994:1009), järnväg (järnvägstrafiklagen, 1985:192) och luft (luftfartslagen, 2010:500).",
  "nar": "Frågan gäller ansvar för gods under transport. Avgör transportslaget först — det styr vilken lag som är tillämplig. Inga lagrum ur kursens register. Kartan pekar bara ut området.",
  "lagar": []
}
```

### `leasing` (ny, under `speciell_avtalsratt`, lagfri)

```json
{
  "id": "leasing",
  "namn": "Leasing",
  "beskrivning": "Ingen särskild leasinglag finns i Sverige. Avtalet bedöms utifrån allmänna avtalsrättsliga principer, med försiktig analogi till köplagen eller konsumentköplagen. Konsumentkreditlagen (2010:1846) kan bli tillämplig om leasingen i realiteten är ett avbetalningsköp.",
  "nar": "Frågan gäller ett leasingavtal. Utgångspunkten är avtalet självt och allmänna avtalsrättsliga principer — det finns ingen dedikerad lagstiftning att falla tillbaka på. Inga lagrum ur kursens register. Kartan pekar bara ut området.",
  "lagar": []
}
```

### `licensavtal` (ny, under `speciell_avtalsratt`, lagfri)

```json
{
  "id": "licensavtal",
  "namn": "Licensavtal",
  "beskrivning": "Avtal om rätt att använda någon annans immateriella rättighet. Vilken lag som styr beror på vad som licensieras: upphovsrättslagen (1960:729), patentlagen (1967:837) eller varumärkeslagen (2010:1877). Själva avtalet regleras i övrigt av allmän avtalsrätt.",
  "nar": "Frågan gäller rätten att nyttja någon annans immateriella rättighet. Avgör vilken rättighetstyp som licensieras — det styr vilken speciallag som är relevant. Inga lagrum ur kursens register. Kartan pekar bara ut området.",
  "lagar": []
}
```

### `fastighetsratt` (ändrad, kvar som toppgren under Civilrätt)

Beskrivning och `nar` renodlas till den sakrättsliga halvan; JB-postens text
byts ut på samma sätt. `relaterade` tappar `AvtL` (den relationen hör nu hemma
i de två nya avtalsnoderna) och behåller `ÄktB` (makars samtycke vid
förfogande över fastighet är fortsatt en sakrättslig fråga).

```json
{
  "id": "fastighetsratt",
  "namn": "Fastighetsrätt",
  "beskrivning": "Fast egendom som sakrättsligt objekt: fastighetstillbehör, servitut och panträtt.",
  "nar": "Frågan gäller vad som räknas som fastighetstillbehör, eller en rättighet som belastar fastigheten genom servitut eller panträtt — inte själva köpet eller hyresförhållandet.",
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

### `kop_och_konsumentratt` och `arbetsratt`

Oförändrade. De motsvarar redan "Köp av lös egendom" respektive
"Anställningsavtal" i förlagan.

## Testning

- `tests/test_rattssystem_graf.py`: nya asserts att `speciell_avtalsratt` har
  sju barn i rätt ordning; att JB nu ger tre distinkta noder
  (`lag_id("fastighetsratt","JB")`, `lag_id("kop_av_fast_egendom","JB")`,
  `lag_id("hyra_av_fast_egendom","JB")`); att `transportavtal`/`leasing`/
  `licensavtal` är löv utan lagnoder (`ar_lov == True`, `lagar == ()`), samma
  mönster som redan testas för `statsratt`/`forvaltningsratt`.
- `tests/test_rattskarta.py`: `_bygg_gren`-invarianten (antingen `grenar`
  eller `lagar`) täcker redan de nya lagfria noderna generiskt, men lägg till
  ett explicit fall om inget redan finns.
- Ingen ändring väntas i `tests/test_taxonomi_ui.py` (inga hårdkodade
  nodantal), `tests/test_quiz.py`, `tests/test_lagrum.py` eller
  `tests/test_lagstruktur.py`/`tests/test_lagtext.py` — de nya noderna
  tillför inga nya förkortningar till `data/lagrum.json`.
- Full `pytest`-körning efter ändringen ska fortsatt vara grön (798 tester
  innan denna ändring).

## Dokumentation

`APPGUIDE.md` rad ~337 nämner exempelvägen "Obligationsrätt → Speciell
avtalsrätt → Köp- och konsumenträtt → KöpL" som illustration av grafens djup.
Lägg till en rad som nämner att Särskild avtalsrätt nu har sju avtalstyper,
inklusive de tre lagfria "(kommer)"-ämnena.

## Utanför omfånget

- Att registrera CMR-lagen, Vägtransportlagen, Sjölagen,
  Järnvägstrafiklagen, Luftfartslagen, Konsumentkreditlagen,
  Upphovsrättslagen, Patentlagen eller Varumärkeslagen i
  `data/lagrum.json` — det kräver lagstruktur- och lagtext-filer och gör
  transportavtal/leasing/licensavtal quizbara, vilket inte är beställt.
- Ändringar i taxonomigrafens rendering, layout eller interaktion.
- Nytt quizinnehåll för någon av de sju avtalstyperna.

## Källor (lagnamn/SFS-nummer, verifierade 2026-08-06)

- Lag (1974:610) om inrikes vägtransport; lag (1969:12) med anledning av
  Sveriges tillträde till konventionen om fraktavtalet vid internationell
  godsbefordran på väg (CMR-lagen) — [riksdagen.se](https://www.riksdagen.se)
- Sjölag (1994:1009) — [lagen.nu/1994:1009](https://lagen.nu/1994:1009)
- Järnvägstrafiklagen (1985:192); lag (1985:193) om internationell
  järnvägstrafik — [riksdagen.se](https://www.riksdagen.se)
- Luftfartslag (2010:500) — [lagen.nu/2010:500](https://lagen.nu/2010:500)
- Konsumentkreditlag (2010:1846) —
  [lagen.nu/2010:1846](https://lagen.nu/2010:1846)
- Lag (1960:729) om upphovsrätt till litterära och konstnärliga verk;
  patentlagen (1967:837); varumärkeslagen (2010:1877) — riksdagen.se,
  branschöversikter (Digitala Juristerna, Lavendla)
