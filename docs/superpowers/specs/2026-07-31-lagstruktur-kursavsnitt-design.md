# Lagstruktur och kursavsnitt i lagkortet (projekt D)

**Datum:** 2026-07-31
**Status:** Genomförd 2026-08-03 (commit c5541c3,f88dfa3). Samtliga komponenter nedan
finns, alla tre faser är avslutade och grindtestet är grönt. En avvikelse mot
designen: `kursavsnitt_grupperade` ligger inte i `utils/lagstruktur.py` utan i egna
`utils/lagkort_avsnitt.py` (`gruppera_kursavsnitt`, `tackningstext`,
`formatera_spann`), enligt projektets regel om många små moduler.
**Omfång:** Projekt D av fyra. A (svårighetsgrad) och B+C (Rättskartans ombyggnad) är klara.

## Problem

Roadmapen formulerade projekt D som "kapitel-/momentnedbrytning av de 21 lagarna" och
antog att kapitelrubrikerna måste författas, eftersom `data/lagtext/*.json` bara bär
paragrafnummer och paragraftext. Två undersökningar under designarbetet kullkastade
den premissen:

1. **Nedbrytningen finns redan författad.** `data/lagrum.json` bär 105 `kursavsnitt`
   över de 21 lagarna, vart och ett med rubrik, kapitel, paragrafintervall och
   djuplänk till lagen.nu. De används av `utils/lagrum.py` (validering av tutorns
   citat) och `utils/prompts.py` (LAGRUMSVITLISTAN), men **visas aldrig för studenten**.
   Lagkortet i Rättskartan (`utils/ui.py:525`) visar namn, SFS, beskrivning och en
   länk till lagen som helhet.
2. **Lagens egna rubriker finns i källan.** Riksdagens öppna data bär både
   kapitelrubriker och momentrubriker i HTML-fältet. `scripts/hamta_lagtext.py`
   kastar dem, den letar bara paragrafankare. Rubrikerna är författningstext och
   omfattas av samma upphovsrättsundantag (9 § URL) som paragraftexten som redan
   lagras. **Inget titellager behöver författas.**

Kvarstår ett kvalitetsproblem som blockerar visning: **78 av 105 kursavsnitt bär
`verifiera: true`**, vilket enligt filens egen beskrivning betyder osäkra
paragrafgränser eller osäkert kursomfång som ska kontrolleras mot lagen.nu innan de
betraktas som fastställda. Så länge avsnitten bara matade validering och prompter var
en oskarp gräns billig. På ett lagkort blir den ett påstående studenten läser som sant.

En korskörning av alla 105 avsnitt mot korpusen visar att oron var befogad:
**25 avsnitt anger paragrafer som inte finns i den hämtade lagtexten** (68 nummer
totalt). RB "Väckande av talan och rättegångshinder" anger 13:1 till 13:15 när bara
13:1 till 13:7 existerar; KKöpL "Påföljder vid fel" anger 5:1 till 5:20 mot verkliga 5:1 till 5:11.

Korpusen kan inte verifiera sig själv: `scripts/hamta_lagtext.py` sparar endast
paragrafer *inom* kursavsnitten, så korpusen är härledd ur det den skulle kontrollera.
Den fångar bara för vida gränser, aldrig för snäva. Lagens egen struktur fångar båda.

## Mål

Visa kursavsnitten i lagkortet, grupperade under lagens verkliga kapitel, med
paragrafintervall och djuplänk per avsnitt, och verifiera samtliga 105 avsnitt mot
lagens faktiska struktur först, så att inget overifierat påstående når studenten.

## Valda beslut

- **Syfte: orientering i lagkortet.** Inte en lagläsare i appen, inte en koppling
  mellan moment och övningar. Båda övervägdes och valdes bort som separata projekt.
- **Verifiera allt före visning.** Alla 78 flaggade avsnitt gås igenom och
  `verifiera` sätts till `false` innan nedbrytningen visas. Alternativen, visa med
  förbehållsmärkning, eller visa bara de 27 verifierade, valdes bort.
- **Strukturen lagras som egen data.** Alternativet att bara producera en
  engångsrapport valdes bort: verifieringen ska kunna köras om som ett test när
  lagarna ändras, offline och utan nätverk.

## Källans tre former

Samtliga 21 lagar är hämtade och uppmätta (Task 2). De fördelar sig på tre former:

| Form | Lagar | `<h3>` | `<h4>` |
|---|---|---|---|
| Kapitel **och** moment | BrB, JB, HBL, UB, KonkL, ÄktB, FB, RB, ABL, KKöpL | `3 kap. Näringsidkarens dröjsmål` | `Påföljder vid dröjsmål` |
| Bara kapitel | AvtL, SkbrL, ÄB, SkL | `2 kap. Om fullmakt` | saknas |
| Bara moment | LAS, KöpL, SamboL, MFL, GFL, LFF, PreskL | saknas | `Påföljder vid säljarens dröjsmål` |

Tre lagar föll inte ut som designarbetets gissning: **SkL och ÄB saknar
momentrubriker** (de klassificerades som "kapitel och moment"), och **SkbrL har
kapitelrubriker** trots att den klassificerades som kapitellös.

Hämtaren förutsätter därför ingen form per lag: den läser vilka rubriknivåer som
finns och skriver de listor som faktiskt fylls. Ingen lag saknade båda nivåerna.

`<h3>` innehåller även brus (`Innehåll:`, `Övergångsbestämmelser`) som filtreras på
mönstret `^\d+ kap\.`.

**AvtL är specialfallet.** Lagen har kapitelrubriker men löpande paragrafnumrering,
vilket registret redan noterar (`kapitelindelad: false` med förklarande `not`-fält).
Dess `kapitel[].nummer` blir alltså `"2"` medan `kapitel[].paragrafer` är platta
nycklar (`"10"`, `"11"`, …), inte `"2:10"`. Paragrafnyckelns form styrs av lagens
numrering, aldrig av om en kapitelrubrik råkar finnas.

**SkbrL är samma fall** och upptäcktes i Task 2: fyra kapitelrubriker
(`Om löpande skuldebrev` osv.) med löpande numrering 1 till 38 tvärs igenom dem.

Uppmätt vid implementationen av Task 1, och tvärtemot vad den här specen först
antog: **källan märker AvtL:s paragrafer `K2P10`**, med kapitelprefix, trots att
numreringen löper obruten 1 till 41 genom hela lagen. Formen kan därför inte läsas ur
ankaret. Parsern tar `kapitelindelad` som argument och hämtar värdet ur
lagrumsregistret, som är sanningskällan för den frågan. Gör den inte det får AvtL
nycklar som varken korpusen (`data/lagtext/1915-218.json`, platta nycklar) eller
kursavsnitten (`kapitel: null`) går att foga ihop med, och samtliga AvtL-avsnitt
skulle se överskjutande ut i kontrollen.

## Datamodell: `data/lagstruktur/<sfs>.json`

```json
{
  "forkortning": "KKöpL",
  "sfs": "2022:260",
  "kalla": "https://data.riksdagen.se/dokument/sfs-2022-260",
  "kallnamn": "Riksdagens öppna data",
  "hamtad": "2026-07-31",
  "licens": "Författningstext, undantagen upphovsrätt enligt 9 § upphovsrättslagen.",
  "kapitel": [
    {"nummer": "3", "rubrik": "Näringsidkarens dröjsmål",
     "paragrafer": ["3:1", "3:2", "3:3", "3:4", "3:5", "3:6"]}
  ],
  "moment": [
    {"rubrik": "Påföljder vid dröjsmål", "kapitel": "3", "paragrafer": ["3:2", "3:3"]}
  ]
}
```

Två parallella ordnade listor. Var för sig får de vara tomma, aldrig båda, varje lag
har minst en rubriknivå. `moment.kapitel` är `null` för kapitellösa lagar.
Paragrafnycklarna har exakt samma form som `data/lagtext/` (`"3:2"` för kapitelindelade,
`"12"` för övriga), så de kan slås ihop utan översättning.

**Hela lagens struktur lagras, inte bara kursens kapitel.** Endast rubriker och
paragrafnummer, ingen paragraftext, BrB:s 588 paragrafer blir några kilobyte. Det är
förutsättningen för täckningsraden i gränssnittet ("kursen täcker 6 av lagens 8
kapitel"), som är projektets ärlighetskrav: utan den läser studenten avsnittslistan
som om lagen tog slut där.

## Komponenter

### `scripts/hamta_lagstruktur.py` (nytt)

Syskon till `hamta_lagtext.py` och lyder samma regler: körs manuellt, aldrig av appen;
hämtar från Riksdagens öppna data med samma användaragent och paus; hämtar **aldrig**
lagen.nu:s egna kommentarer. Återanvänder `hamta_sida`, `riksdagen_url` och `_rensa`
ur den befintliga hämtaren i stället för att duplicera dem.

Extraheringen är en positionell scan: rubriker och paragrafankare plockas i
dokumentordning, och varje rubrik äger paragraferna fram till nästa rubrik på samma
eller högre nivå. Verifierat mot KKöpL under designarbetet.

Flaggor speglar den befintliga hämtaren: `--uppdatera`, `--lag <FÖRKORTNING>`, `--tyst`.

### `utils/lagstruktur.py` (nytt)

Läsande lager, samma form som `utils/lagtext.py`:

- Frusna dataklasser `Lagstruktur`, `Kapitel`, `Moment`.
- `ladda_lagstruktur() -> dict[str, Lagstruktur]`, cachad, nyckel = förkortning.
- `kapitelrubrik(forkortning, nummer) -> str | None`.
- `antal_kapitel(forkortning) -> int` för täckningsraden.
- `kursavsnitt_grupperade(forkortning)` som slår ihop registrets `kursavsnitt` med
  strukturens kapitel och ger de rader vyn ska rendera.

Inläsningen validerar strikt och kastar på trasig fil. En **saknad** fil är däremot
inte ett fel i vyn: kortet degraderar då till en platt avsnittslista. Ett test vaktar
att alla 21 lagar har en strukturfil, så en saknad fil aldrig kan nå produktion tyst.

### `scripts/verifiera_kursavsnitt.py` (nytt)

Jämför varje kursavsnitt i `lagrum.json` mot strukturen och rapporterar fyra
avvikelsetyper:

- **Överskjutande gräns**, avsnittet anger paragrafer som inte finns i lagen.
- **För snäv gräns**, momentets paragrafer sträcker sig utanför avsnittet.
- **Rubrikavvikelse**, `beskrivning` skiljer sig från lagens rubrik för de paragrafer
  avsnittet täcker.
- **Spänner över moment**, avsnittet skär genom flera moment. Kan vara medvetet.

**Skriptet rättar aldrig `lagrum.json`.** Om ett avsnitt ska omfatta 13:1 till 13:7 eller
13:1 till 13:5 är en bedömning av kursens omfång, inte en textjämförelse. Skriptet
producerar rapporten; människan fattar besluten och sätter `verifiera: false`.

### `utils/ui.py`, `render_lagkort`

Ny valfri parameter `kursavsnitt`. Renderas under de befintliga fälten:

```
KURSAVSNITT                    kursen täcker 6 av lagens 8 kapitel
  1 kap. Grundläggande bestämmelser
     1 till 9 §§    Lagens tillämpningsområde och tvingande verkan   ↗
  3 kap. Näringsidkarens dröjsmål
     1 till 6 §§    Påföljder vid säljarens dröjsmål                 ↗
```

Kapitelraden kommer ur strukturfilen, avsnittsraden ur `lagrum.json`. För kapitellösa
lagar faller kapitelnivån bort och avsnitten listas platt, samma renderare, ingen
gren i vyn.

- `§` för ett enda paragrafnummer, `§§` för ett intervall. `36 §`, aldrig `36 §§`.
- Djuplänkarna använder paragrafguld, aldrig navigeringsfärg (`design_system.md`
  avsnitt 1 och 4: guld betyder alltid lagrum).
- All text går genom `html.escape`, som resten av funktionen.

### `sidor/16_Rattskartan.py`

Anropet till `render_lagkort` (rad ~127) får avsnitten. `info = register[...]` bär dem
redan, så inget nytt behöver hämtas i vyn.

## Dataflöde

```
Riksdagens öppna data
   │  scripts/hamta_lagstruktur.py   (manuellt, nätverk)
   ▼
data/lagstruktur/<sfs>.json          (committad, rubriker + paragrafnummer)
   │
   ├─► scripts/verifiera_kursavsnitt.py ──► rapport ──► människa rättar data/lagrum.json
   │
   └─► utils/lagstruktur.py ──► sidor/16_Rattskartan.py ──► utils.ui.render_lagkort
                  ▲
                  └── data/lagrum.json (kursavsnitt: rubrik, spann, djuplänk)
```

Appen rör aldrig nätet. All visning sker mot committad data, som resten av korpusen.

## Felhantering

- **Trasig strukturfil**, `ladda_lagstruktur` kastar vid inläsning. Fail fast.
- **Saknad strukturfil**, vyn degraderar till platt avsnittslista. Test vaktar att
  ingen saknas.
- **Lag utan kursavsnitt**, kortet ser ut som i dag, ingen tom rubrik renderas.
- **Hämtningsfel**, skriptet rapporterar per lag och fortsätter, som `hamta_lagtext.py`.
- **Moment som pekar på okänt kapitel**, valideringsfel vid inläsning, inte tyst nod.

## Tester

Extraheringen testas mot sparade HTML-fixturer under `tests/fixtures/`, aldrig mot
nätet, en fixtur per källform: KKöpL (kapitel + moment), AvtL (bara kapitel),
PreskL (bara moment).

Bärande invariant, `tests/test_lagstruktur.py`:

- **Överskjutandetestet**, varje kursavsnitts paragrafspann finns i lagens struktur.
  Testet är RED från början med de 25 uppmätta avvikelserna. Det är avsiktligt: det är
  den röda fas som driver rättningsarbetet, och det som blir kvar är en permanent
  spärr mot att nästa lagändring smyger in samma fel.
- Alla 21 lagar i registret har en strukturfil.
- `moment.kapitel` pekar alltid på ett existerande kapitel.
- Kapitelindelning och momentlistorna är aldrig båda tomma.
- Paragrafnycklarna har samma form som `data/lagtext/`.

Gränssnittstester (`tests/test_ui.py`, `tests/test_rattskartan_sida.py`): lagkortet
renderar avsnitten, grupperar under kapitel, escapar HTML, väljer `§`/`§§` rätt, visar
täckningsraden och degraderar utan strukturfil.

Slutgiltigt grindtest i `tests/test_lagrum.py`: inget kursavsnitt bär `verifiera: true`.

## Faser och överlämning

Grindtestet kan bli grönt först efter den mänskliga genomgången, vilket ger tre faser:

1. **Bygga och mäta**, hämtare, datamodell, läsande lager, verifieringsskript,
   överskjutandetestet i RED. Utförs av kodassistenten.
2. **Besluta om gränserna**, de 78 flaggade avsnitten gås igenom mot rapporten,
   `lagrum.json` rättas, `verifiera` sätts till `false`. Utförs av användaren, med
   förslag per avsnitt från kodassistenten. Juridiskt innehåll får inte hittas på.
3. **Visa**, lagkortet, sidan, gränssnittstesterna. Utförs av kodassistenten.

## Utanför omfånget

- Lagläsare i appen (bläddra paragraftext per moment), övervägt, valt bort.
- Koppling mellan moment och övningar eller nyckelbegrepp, övervägt, valt bort.
  `utils.lagrum._matchande_avsnitt` finns redan om det blir aktuellt senare.
- Ändringar i taxonomin, begreppsdatat eller Rättskartans graf.
- Utökning av kursens omfång. Verifieringen rättar gränser mot lagen som den ser ut,
  den lägger inte till nya avsnitt.
