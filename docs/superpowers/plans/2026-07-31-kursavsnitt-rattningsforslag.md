# Rättningsförslag för de 15 överskjutande kursavsnitten

**Datum:** 2026-07-31
**Underlag:** `python3.11 scripts/verifiera_kursavsnitt.py --typ OVERSKJUTANDE`
**Status:** Förslag. Varje rad kräver ditt godkännande innan `data/lagrum.json` ändras.

Alla fakta om vad ett kapitel heter och hur många paragrafer det har kommer ur
`data/lagstruktur/`, hämtat från Riksdagens öppna data. Inget juridiskt innehåll är
påhittat. Vad *kursen* ska omfatta är däremot inte en uppgift som går att läsa ur
lagen — den bedömningen är din.

## Grupp A — gränsjustering (12 avsnitt)

Här stämmer kapitlet och rubriken; bara den övre gränsen pekar förbi kapitlets sista
paragraf. Förslaget är att klämma gränsen till kapitlets slut.

| Lag | Avsnitt | Anger | Kapitlet har | Förslag |
|---|---|---|---|---|
| ABL | Inledande bestämmelser | 1 kap. 1–15 §§ | 1 kap. *Inledande bestämmelser*, 1–14 §§ | **1–14 §§** |
| ABL | Bildande av aktiebolag | 2 kap. 1–36 §§ | 2 kap. *Bildande av aktiebolag*, 1–31 §§ | **1–31 §§** |
| KonkL | Återvinning till konkursbo | 4 kap. 1–22 §§ | 4 kap. *Återvinning till konkursbo*, 1–21 §§ | **1–21 §§** |
| RB | Om rättegångskostnad | 18 kap. 1–18 §§ | 18 kap. *Om rättegångskostnad*, 1–16 §§ | **1–16 §§** |
| SkL | Principalansvar och det allmännas ansvar | 3 kap. 1–12 §§ | 3 kap. *Skadeståndsansvar för annans vållande och för det allmänna*, 1–11 §§ | **1–11 §§** |
| ÄB | Den legala arvsordningen | 2 kap. 1–5 §§ | 2 kap. *Om skyldemans arvsrätt*, 1–4 §§ | **1–4 §§** |
| ÄB | Laglott och bröstarvinges skydd | 7 kap. 1–9 §§ | 7 kap. *Om laglott*, 1–7 §§ | **1–7 §§** |
| ÄB | Formkrav för testamente | 10 kap. 1–10 §§ | 10 kap. *Om upprättande och återkallelse av testamente*, 1–7 §§ | **1–7 §§** |
| ÄktB | Andelar och lotter vid bodelning | 11 kap. 1–13 §§ | 11 kap. *Andelar och lotter*, 1–11 §§ | **1–11 §§** |
| KKöpL | Påföljder vid fel | 5 kap. 1–20 §§ | 5 kap. *Påföljder vid fel på varan*, 1–11 §§ | **1–11 §§** |
| BrB | Uppsåt, oaktsamhet och ansvarsfrihetsgrunder | 24 kap. 1–13 §§ | 24 kap. *Om allmänna grunder för ansvarsfrihet*, 1–9 §§ | **1–9 §§**, se not |
| RB | Väckande av talan och rättegångshinder | 13 kap. 1–17 §§ | 13 kap. *Om föremål för talan och talans väckande*, 1–7 §§ | **1–7 §§**, se not |

**Not, BrB 24 kap.** Gränsen är enkel, men rubriken lovar mer än kapitlet håller:
uppsåt och oaktsamhet regleras inte i 24 kap. utan i 1 kap. Antingen snävas rubriken
till *Ansvarsfrihetsgrunder*, eller så läggs ett eget avsnitt till för uppsåtsläran.

**Not, RB 13 kap.** Samma sak: rättegångshinder behandlas inte i 13 kap. Antingen
snävas rubriken till *Väckande av talan*, eller så kompletteras kursen med det kapitel
där rättegångshinder faktiskt regleras.

## Grupp B — pekar på fel kapitel (3 avsnitt)

Här räcker det **inte** att justera gränsen. Avsnittet pekar på ett kapitel vars ämne
är ett annat än rubriken anger, och en klämd gräns skulle tyst behålla fel innehåll.

### KKöpL — tre avsnitt är felmappade

Konsumentköplagen skrevs om 2022 och fick kapitelindelning; den gamla lagen
(1990:932) hade löpande paragrafnumrering. Tre av sex kursavsnitt pekar på kapitel
vars ämne inte motsvarar rubriken:

| Avsnittets rubrik | Pekar på | Det kapitlets ämne | Rätt kapitel enligt rubriken |
|---|---|---|---|
| Avlämnande och risken för varan | 3 kap. 1–6 §§ | *Näringsidkarens dröjsmål* | **2 kap.** *Varans avlämnande*, 1–6 §§ |
| Påföljder vid säljarens dröjsmål | 6 kap. 1–10 §§ | *Skadestånd vid näringsidkarens avtalsbrott* | **3 kap.** *Näringsidkarens dröjsmål*, 1–6 §§ |
| Skadestånd | 7 kap. 1–8 §§ | *Konsumentens betalningsskyldighet och dröjsmål* | **6 kap.** *Skadestånd vid näringsidkarens avtalsbrott*, 1–5 §§ |

Bara ett av de tre (`Påföljder vid säljarens dröjsmål`) syns som överskjutande, eftersom
de andra två råkar falla inom sina felaktiga kapitels paragrafintervall. **Det är det
allvarligaste fyndet i genomgången:** två avsnitt är fel utan att någon automatisk
kontroll klagar, och de har matat tutorns vitlista sedan de skrevs.

### ÄktB — två avsnitt spänner över fel eller flera kapitel

| Avsnittets rubrik | Pekar på | Det kapitlets ämne | Kommentar |
|---|---|---|---|
| Äktenskaps ingående och villkor | 2 kap. 1–6 §§ | *Äktenskapshinder*, 1–4 §§ | Äktenskaps ingående regleras i 1 kap. (*Äktenskap*), 3 kap. (*Prövning av äktenskapshinder*) och 4 kap. (*Vigsel*). Klämning till 2 kap. 1–4 §§ ger bara hindren. |
| Äktenskapsförord och gåvor mellan makar | 8 kap. 1–9 §§ | *Gåvor mellan makar*, 1–3 §§ | Äktenskapsförord regleras i 7 kap. 3 §, inte i 8 kap. Rubriken spänner över två kapitel. |

**Förslag för ÄktB:** dela avsnitten så att varje avsnitt motsvarar ett kapitel, eller
snäva rubrikerna till det som faktiskt ingår. Vilket som är rätt beror på vad kursen
ska pröva, och det avgör du.

## Vad som inte ingår i det här förslaget

- De 15 `FOR_SNAV`, 9 `RUBRIKAVVIKELSE` och 50 `SPANNER_OVER_MOMENT` är underlag, inte
  fel. De behöver ingen åtgärd för att överskjutandetestet ska bli grönt.
- `verifiera: false` sätts per avsnitt först när du gått igenom det, oavsett om det
  fanns i listan ovan. 78 avsnitt bär flaggan; bara 15 är överskjutande.
- 14 paragrafer saknas i `data/lagtext/` trots att de ingår i kursen och finns i lagen
  (ABL 8:6–8:7, BrB 1:7 och 8:3, FB 1:6 och 7:11, KonkL 2:23, LAS 24, RB 1:7, 1:9 och
  12:10, SkbrL 8, ÄB 7:6, ÄktB 2:2). Det är ett hämtningsproblem i korpusen, inte ett
  gränsproblem, och hanteras separat.
