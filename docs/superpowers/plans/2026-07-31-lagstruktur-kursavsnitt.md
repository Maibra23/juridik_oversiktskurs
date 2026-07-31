# Lagstruktur och kursavsnitt i lagkortet — implementationsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Visa kursavsnitten i Rättskartans lagkort, grupperade under lagens verkliga kapitel, efter att samtliga 105 avsnitt verifierats mot lagens faktiska struktur.

**Architecture:** En ny hämtare läser kapitel- och momentrubriker ur Riksdagens öppna data till `data/lagstruktur/<sfs>.json`. Ett läsande lager i `utils/` slår ihop den strukturen med de kursavsnitt som redan finns i `data/lagrum.json`. Ett kontrollager jämför de två och rapporterar avvikelser, vilket driver rättningen av de 78 flaggade avsnitten. Först därefter renderas avsnitten i lagkortet.

**Tech Stack:** Python 3.11, Streamlit, pytest. Inga nya beroenden. Endast standardbiblioteket (`re`, `json`, `urllib.request`, `dataclasses`, `functools.lru_cache`).

## Global Constraints

- **Kör alltid tester med `python3.11 -m pytest`.** Streamlits interpreter är 3.11; bar `python3` saknar beroenden. Se minnesnoteringen `llm-otillganglig-python-mismatch`.
- **Appen rör aldrig nätet.** All hämtning sker i `scripts/`, körs manuellt, och resultatet committas. `utils/` och `sidor/` läser bara committad data.
- **Hämta aldrig lagen.nu:s egna kommentarer.** Endast författningstext (rubriker och paragrafer), undantagen upphovsrätt enligt 9 § upphovsrättslagen.
- **Hitta aldrig på juridiskt innehåll.** Rubriker kommer ur källan, aldrig ur modellen. Kursavsnittens gränser beslutas av användaren i Task 5, inte av en implementatör.
- **Immutabla datamodeller.** Alla dataklasser är `@dataclass(frozen=True)` med `tuple` i stället för `list`, enligt projektets kodstil.
- **Svenska genomgående** i kod, kommentarer, docstrings, commit-meddelanden och gränssnittstext. Å, ä och ö skrivs ut.
- **Paragrafnyckelns form är `"3:2"` för kapitelindelade lagar och `"12"` för övriga**, identisk med `data/lagtext/`.
- `scripts/` är **inget Python-paket** (saknar `__init__.py`) och kan inte importeras av tester. All logik som ska testas ligger därför i `utils/`; skripten är tunna CLI-skal.

## Filstruktur

| Fil | Ansvar |
|---|---|
| `utils/lagstruktur_extrahering.py` (ny) | Ren parser: källans HTML → kapitel- och momentlistor. Ingen nätverkskod, inget filsystem. |
| `scripts/hamta_lagstruktur.py` (ny) | Tunt CLI-skal: hämtar HTML, anropar parsern, skriver `data/lagstruktur/<sfs>.json`. |
| `utils/lagstruktur.py` (ny) | Läser och validerar `data/lagstruktur/`. Frusna dataklasser, cachad laddning, uppslag. |
| `utils/kursavsnitt_kontroll.py` (ny) | Jämför registrets kursavsnitt mot strukturen och producerar avvikelser. |
| `scripts/verifiera_kursavsnitt.py` (ny) | Tunt CLI-skal som skriver ut avvikelserapporten. |
| `utils/ui.py` (ändras) | `render_lagkort` får kursavsnitten och renderar dem grupperade. |
| `sidor/16_Rattskartan.py` (ändras) | Skickar avsnitten till lagkortet. |
| `data/lagstruktur/*.json` (ny) | 21 strukturfiler, committade. |
| `tests/fixtures/*.html` (ny) | Tre källfixturer, en per källform. |

---

### Task 1: Strukturparser med fixturer

**Files:**
- Create: `utils/lagstruktur_extrahering.py`
- Create: `tests/test_lagstruktur_extrahering.py`
- Create: `tests/fixtures/kkopl-2022-260.html`, `tests/fixtures/avtl-1915-218.html`, `tests/fixtures/preskl-1981-130.html`

**Interfaces:**
- Consumes: inget (första uppgiften).
- Produces:
  - `rensa_html(html: str) -> str`
  - `paragrafnyckel(ankarnamn: str) -> str | None`
  - `extrahera_struktur(html: str) -> tuple[list[dict], list[dict]]` som returnerar `(kapitel, moment)`. Varje kapitel är `{"nummer": str, "rubrik": str, "paragrafer": list[str]}`. Varje moment är `{"rubrik": str, "kapitel": str | None, "paragrafer": list[str]}`.

- [ ] **Step 1: Spara fixturerna**

De tre formerna måste finnas som fixturer innan parsern skrivs. Kör en gång, med nätverk:

```bash
mkdir -p tests/fixtures && python3.11 - <<'PY'
import sys
sys.path.insert(0, "scripts")
from pathlib import Path
from hamta_lagtext import hamta_riksdagen_html

for sfs, namn in [("2022:260", "kkopl"), ("1915:218", "avtl"), ("1981:130", "preskl")]:
    mal = Path(f"tests/fixtures/{namn}-{sfs.replace(':', '-')}.html")
    mal.write_text(hamta_riksdagen_html(sfs), encoding="utf-8")
    print(mal, mal.stat().st_size, "byte")
PY
```

Förväntat: tre filer, ungefär 69 kB, 25 kB och 8 kB.

- [ ] **Step 2: Skriv de fallerande testerna**

```python
"""Tester för strukturparsern (utils.lagstruktur_extrahering).

Fixturerna är sparad HTML från Riksdagens öppna data, en per källform:
KKöpL har både kapitel- och momentrubriker, AvtL har bara kapitelrubriker
(med löpande paragrafnumrering), PreskL har bara momentrubriker. Parsern
får aldrig anta en form; den läser de nivåer som finns.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from utils.lagstruktur_extrahering import (
    extrahera_struktur,
    paragrafnyckel,
    rensa_html,
)

FIXTURER = Path(__file__).parent / "fixtures"


def _las(namn: str) -> str:
    return (FIXTURER / namn).read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def kkopl():
    return extrahera_struktur(_las("kkopl-2022-260.html"))


@pytest.fixture(scope="module")
def avtl():
    return extrahera_struktur(_las("avtl-1915-218.html"))


@pytest.fixture(scope="module")
def preskl():
    return extrahera_struktur(_las("preskl-1981-130.html"))


def test_rensa_html_tar_bort_taggar_och_normaliserar():
    assert rensa_html("<em>3 kap.</em>  Om\n fullmakt") == "3 kap. Om fullmakt"


def test_paragrafnyckel_kapitelindelad():
    assert paragrafnyckel("K3P2") == "3:2"


def test_paragrafnyckel_oindelad():
    assert paragrafnyckel("P12") == "12"


def test_paragrafnyckel_avvisar_bokstavsparagraf():
    """Kursavsnitten refererar bara hela paragrafnummer, aldrig "1 a §"."""
    assert paragrafnyckel("K4P1a") is None


def test_kkopl_ger_bade_kapitel_och_moment(kkopl):
    kapitel, moment = kkopl
    assert kapitel, "KKöpL ska ge kapitel"
    assert moment, "KKöpL ska ge moment"


def test_kkopl_kapitelrubrik_ar_uppdelad_i_nummer_och_text(kkopl):
    kapitel, _ = kkopl
    tredje = next(k for k in kapitel if k["nummer"] == "3")
    assert tredje["rubrik"] == "Näringsidkarens dröjsmål"


def test_kkopl_moment_arver_sitt_kapitel(kkopl):
    _, moment = kkopl
    pafoljder = next(m for m in moment if m["rubrik"] == "Påföljder vid dröjsmål")
    assert pafoljder["kapitel"] == "3"
    assert all(p.startswith("3:") for p in pafoljder["paragrafer"])


def test_kkopl_kapitel_bar_sina_paragrafer_i_ordning(kkopl):
    kapitel, _ = kkopl
    forsta = next(k for k in kapitel if k["nummer"] == "1")
    assert forsta["paragrafer"][:3] == ["1:1", "1:2", "1:3"]


def test_avtl_ger_kapitel_utan_moment(avtl):
    kapitel, moment = avtl
    assert [k["rubrik"] for k in kapitel] == [
        "Om slutande av avtal",
        "Om fullmakt",
        "Om rättshandlingars ogiltighet",
        "Allmänna bestämmelser",
    ]
    assert moment == []


def test_avtl_har_platta_paragrafnycklar(avtl):
    """AvtL har kapitelrubriker men löpande numrering: "10", inte "2:10"."""
    kapitel, _ = avtl
    fullmakt = next(k for k in kapitel if k["rubrik"] == "Om fullmakt")
    assert "10" in fullmakt["paragrafer"]
    assert not any(":" in p for p in fullmakt["paragrafer"])


def test_preskl_ger_moment_utan_kapitel(preskl):
    kapitel, moment = preskl
    assert kapitel == []
    assert "Preskriptionstid" in [m["rubrik"] for m in moment]
    assert all(m["kapitel"] is None for m in moment)


def test_innehallsforteckning_blir_inte_ett_kapitel(kkopl):
    """h3-bruset "Innehåll:" och "Övergångsbestämmelser" ska filtreras bort."""
    kapitel, _ = kkopl
    rubriker = [k["rubrik"] for k in kapitel]
    assert "Innehåll:" not in rubriker
    assert "Övergångsbestämmelser" not in rubriker


def test_rubriker_utan_paragrafer_utelamnas(preskl):
    """En rubrik som inte äger någon paragraf är en mellanrubrik, inte ett moment."""
    _, moment = preskl
    assert all(m["paragrafer"] for m in moment)


def test_paragrafer_forekommer_bara_en_gang_per_rubrik(kkopl):
    kapitel, moment = kkopl
    for post in [*kapitel, *moment]:
        assert len(post["paragrafer"]) == len(set(post["paragrafer"]))
```

- [ ] **Step 3: Kör testerna och se dem falla**

Kör: `python3.11 -m pytest tests/test_lagstruktur_extrahering.py -v`
Förväntat: FAIL med `ModuleNotFoundError: No module named 'utils.lagstruktur_extrahering'`

- [ ] **Step 4: Skriv parsern**

```python
"""Läs lagens kapitel- och momentrubriker ur källans HTML.

Riksdagens öppna data bär författningens egen disposition: <h3> är
kapitelrubriker ("3 kap. Näringsidkarens dröjsmål") och <h4> är
momentrubriker ("Påföljder vid dröjsmål"). scripts/hamta_lagtext.py kastar
dem eftersom den bara letar paragrafankare. Här plockas de fram, så att
nedbrytningen i lagkortet blir lagens egen och inte något vi hittat på.

Ren modul: ingen nätverkskod, inget filsystem, inget Streamlit-beroende.
Det gör den testbar mot sparade fixturer i stället för mot lagen.nu.

Modulen upprepar medvetet två små hjälpare från scripts/hamta_lagtext.py
(taggrensning och paragrafnyckel). Att bryta ut dem ur hämtaren vore en
ändring av fungerande kod utan nytta för det här projektet.
"""

from __future__ import annotations

import re
from html import unescape

# Rubriker och paragrafankare plockas i dokumentordning ur samma svep, så att
# varje rubrik kan äga de paragrafer som följer på den. Skiljer man på svepen
# tappar man ordningen, och därmed kopplingen rubrik → paragraf.
_RUBRIK_ELLER_PARAGRAF = re.compile(
    r"<h(?P<niva>[34])[^>]*>(?P<rubrik>.*?)</h(?P=niva)>"
    r'|<a[^>]*class="paragraf"[^>]*name="(?P<ankare>K?\d*P\d+[a-z]?)"',
    re.DOTALL,
)

# "3 kap. Näringsidkarens dröjsmål" → nummer 3, rubrik "Näringsidkarens
# dröjsmål". Det som inte matchar är brus: "Innehåll:", "Övergångsbestämmelser".
_KAPITELRUBRIK = re.compile(r"^(?P<nummer>\d+)\s*kap\.\s*(?P<rubrik>.*)$")

# Formen "1 a §" får ankaret "K4P1a" och avvisas: kursavsnitten refererar
# bara hela paragrafnummer, och en bokstavsparagraf hör till grundparagrafen.
_ANKARE = re.compile(r"^(?:K(?P<kapitel>\d+))?P(?P<paragraf>\d+)$")

_TAGG = re.compile(r"<[^>]+>")


def rensa_html(html: str) -> str:
    """Ta bort taggar och normalisera blanktecken i en rubrik."""
    return re.sub(r"\s+", " ", unescape(_TAGG.sub("", html))).strip()


def paragrafnyckel(ankarnamn: str) -> str | None:
    """Ankarnamnet som paragrafnyckel, eller None för bokstavsparagrafer.

    Nyckeln har samma form som data/lagtext/: "3:2" för kapitelindelade
    lagar och "12" för lagar med löpande numrering.
    """
    m = _ANKARE.match(ankarnamn)
    if m is None:
        return None
    kapitel = m.group("kapitel")
    return f"{kapitel}:{m.group('paragraf')}" if kapitel else m.group("paragraf")


def _ny_post(**falt: object) -> dict:
    return {**falt, "paragrafer": []}


def extrahera_struktur(html: str) -> tuple[list[dict], list[dict]]:
    """Plocka ut (kapitel, moment) ur källans HTML.

    Båda listorna är i dokumentordning och kan var för sig vara tomma —
    aldrig båda, eftersom varje lag har minst en rubriknivå. Paragrafnyckelns
    form styrs av lagens numrering, aldrig av om en kapitelrubrik råkar finnas:
    AvtL har kapitelrubriker men löpande numrering och får platta nycklar.
    """
    kapitel: list[dict] = []
    moment: list[dict] = []
    aktivt_kapitel: dict | None = None
    aktivt_moment: dict | None = None

    for trav in _RUBRIK_ELLER_PARAGRAF.finditer(html):
        ankare = trav.group("ankare")
        if ankare is not None:
            nyckel = paragrafnyckel(ankare)
            if nyckel is None:
                continue
            for post in (aktivt_kapitel, aktivt_moment):
                if post is not None and nyckel not in post["paragrafer"]:
                    post["paragrafer"].append(nyckel)
            continue

        rubrik = rensa_html(trav.group("rubrik"))
        if trav.group("niva") == "3":
            traff = _KAPITELRUBRIK.match(rubrik)
            if traff is None:
                # Brus. Nollställ ändå: paragrafer under
                # "Övergångsbestämmelser" hör inte till senaste kapitlet.
                aktivt_kapitel = None
                aktivt_moment = None
                continue
            aktivt_kapitel = _ny_post(
                nummer=traff.group("nummer"),
                rubrik=traff.group("rubrik").strip(),
            )
            kapitel.append(aktivt_kapitel)
            aktivt_moment = None
        else:
            aktivt_moment = _ny_post(
                rubrik=rubrik,
                kapitel=aktivt_kapitel["nummer"] if aktivt_kapitel else None,
            )
            moment.append(aktivt_moment)

    # En rubrik utan egna paragrafer är en mellanrubrik, inte ett moment.
    return (
        [k for k in kapitel if k["paragrafer"]],
        [m for m in moment if m["paragrafer"]],
    )
```

- [ ] **Step 5: Kör testerna och se dem passera**

Kör: `python3.11 -m pytest tests/test_lagstruktur_extrahering.py -v`
Förväntat: PASS, 14 tester.

- [ ] **Step 6: Committa**

```bash
git add utils/lagstruktur_extrahering.py tests/test_lagstruktur_extrahering.py tests/fixtures/
git commit -m "feat: läs lagens kapitel- och momentrubriker ur källans HTML

Riksdagens öppna data bär författningens egen disposition i h3 och h4.
Parsern plockar den i dokumentordning så varje rubrik äger sina paragrafer.
Testad mot tre sparade fixturer, en per källform: KKöpL (kapitel och
moment), AvtL (bara kapitel, löpande numrering) och PreskL (bara moment)."
```

---

### Task 2: Hämtare som skriver data/lagstruktur/

**Files:**
- Create: `scripts/hamta_lagstruktur.py`
- Create: `data/lagstruktur/*.json` (21 filer, genereras i steg 4)

**Interfaces:**
- Consumes: `utils.lagstruktur_extrahering.extrahera_struktur`.
- Produces: `data/lagstruktur/<sfs med bindestreck>.json` med nycklarna `forkortning`, `sfs`, `kalla`, `kallnamn`, `hamtad`, `licens`, `kapitel`, `moment`.

- [ ] **Step 1: Skriv hämtaren**

```python
#!/usr/bin/env python3
"""Hämta lagarnas kapitel- och momentrubriker till data/lagstruktur/.

Syskon till scripts/hamta_lagtext.py och lyder samma regler: körs manuellt,
aldrig av appen, och resultatet committas så att appen fungerar offline.

    python3.11 scripts/hamta_lagstruktur.py              # allt som saknas
    python3.11 scripts/hamta_lagstruktur.py --uppdatera  # hämta om allt
    python3.11 scripts/hamta_lagstruktur.py --lag AvtL   # bara en lag

VAD SOM HÄMTAS
==============

Endast författningens egen disposition: kapitelrubriker, momentrubriker och
paragrafnummer. Ingen paragraftext (den ligger i data/lagtext/) och aldrig
lagen.nu:s egna kommentarer. Rubrikerna är författningstext och undantagna
upphovsrätt enligt 9 § upphovsrättslagen.

HELA LAGEN, INTE BARA KURSENS DEL
=================================

Till skillnad från hamta_lagtext.py sparas strukturen för hela lagen, inte
bara för kursavsnitten. Det är förutsättningen för täckningsraden i
lagkortet ("kursen täcker 6 av lagens 8 kapitel"). Utan den läser studenten
avsnittslistan som om lagen tog slut där. Datat är litet: bara rubriker och
paragrafnummer, inga texter.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROT))

from utils.lagstruktur_extrahering import extrahera_struktur  # noqa: E402

sys.path.insert(0, str(ROT / "scripts"))

from hamta_lagtext import (  # noqa: E402
    PAUS_SEKUNDER,
    hamta_riksdagen_html,
    riksdagen_url,
)

LAGRUM_PATH = ROT / "data" / "lagrum.json"
STRUKTUR_DIR = ROT / "data" / "lagstruktur"

LICENSNOT = (
    "Författningstext, undantagen upphovsrätt enligt 9 § upphovsrättslagen. "
    "Hämtad från Riksdagens öppna data. Källa: Sveriges riksdag."
)


def filnamn_for(sfs: str) -> Path:
    return STRUKTUR_DIR / f"{sfs.replace(':', '-')}.json"


def bygg_strukturfil(lag: dict, kapitel: list[dict], moment: list[dict]) -> dict:
    return {
        "forkortning": lag["forkortning"],
        "namn": lag["namn"],
        "sfs": lag["sfs"],
        "kalla": riksdagen_url(lag["sfs"]),
        "kallnamn": "Riksdagens öppna data",
        "hamtad": date.today().isoformat(),
        "licens": LICENSNOT,
        "kapitel": kapitel,
        "moment": moment,
    }


def hamta_lag(lag: dict, *, tyst: bool = False) -> tuple[int, int]:
    """Hämta och spara en lags struktur. Returnerar (antal kapitel, antal moment)."""
    html = hamta_riksdagen_html(lag["sfs"])
    kapitel, moment = extrahera_struktur(html)

    STRUKTUR_DIR.mkdir(parents=True, exist_ok=True)
    filnamn_for(lag["sfs"]).write_text(
        json.dumps(bygg_strukturfil(lag, kapitel, moment), ensure_ascii=False, indent=1)
        + "\n",
        encoding="utf-8",
    )

    if not tyst:
        form = _form(kapitel, moment)
        print(
            f"{lag['forkortning']:8s} {len(kapitel):3d} kapitel  "
            f"{len(moment):4d} moment   [{form}]"
        )
    return len(kapitel), len(moment)


def _form(kapitel: list[dict], moment: list[dict]) -> str:
    """Vilken av källans tre former lagen visade sig ha.

    Specen klassificerade sju lagar empiriskt och lämnade fjorton öppna.
    Utskriften bekräftar eller korrigerar den klassificeringen med data.
    """
    if kapitel and moment:
        return "kapitel och moment"
    if kapitel:
        return "bara kapitel"
    if moment:
        return "bara moment"
    return "INGEN STRUKTUR — undersök"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--uppdatera", action="store_true", help="hämta om allt")
    parser.add_argument("--lag", help="bara denna förkortning")
    parser.add_argument("--tyst", action="store_true", help="ingen utskrift")
    args = parser.parse_args(argv)

    import time

    lagar = json.loads(LAGRUM_PATH.read_text(encoding="utf-8"))["lagar"]
    if args.lag:
        lagar = [l for l in lagar if l["forkortning"] == args.lag]
        if not lagar:
            print(f"Okänd lag: {args.lag}", file=sys.stderr)
            return 1

    fel = 0
    for i, lag in enumerate(lagar):
        if not args.uppdatera and filnamn_for(lag["sfs"]).exists():
            continue
        try:
            hamta_lag(lag, tyst=args.tyst)
        except Exception as e:  # noqa: BLE001
            fel += 1
            print(f"{lag['forkortning']:8s} FEL: {type(e).__name__}: {e}", file=sys.stderr)
        if i < len(lagar) - 1:
            time.sleep(PAUS_SEKUNDER)

    return 1 if fel else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Kör hämtaren för en lag och granska utfallet**

Kör: `python3.11 scripts/hamta_lagstruktur.py --lag KKöpL`
Förväntat: `KKöpL     8 kapitel    56 moment   [kapitel och moment]`

Öppna `data/lagstruktur/2022-260.json` och kontrollera att `kapitel[2]` är
`{"nummer": "3", "rubrik": "Näringsidkarens dröjsmål", "paragrafer": ["3:1", ...]}`.

- [ ] **Step 3: Hämta samtliga 21 lagar**

Kör: `python3.11 scripts/hamta_lagstruktur.py --uppdatera`
Förväntat: 21 rader, ingen med `INGEN STRUKTUR`. Hämtningen tar drygt 20 sekunder på grund av pausen mellan anropen.

Anteckna vilken form varje lag fick. Specen klassificerade sju lagar empiriskt (KKöpL, BrB, UB, AvtL, KöpL, LAS, PreskL) och lämnade fjorton öppna — den här körningen avgör dem. Får någon lag `INGEN STRUKTUR`, stanna och undersök källan innan du går vidare; den lagen kan behöva en egen form i parsern.

- [ ] **Step 4: Committa**

```bash
git add scripts/hamta_lagstruktur.py data/lagstruktur/
git commit -m "feat: hämta lagarnas kapitel- och momentstruktur till data/lagstruktur

Hela lagens disposition sparas, inte bara kursens avsnitt, eftersom
täckningsraden i lagkortet ska kunna säga hur stor del av lagen kursen
faktiskt berör. Endast rubriker och paragrafnummer, ingen paragraftext."
```

---

### Task 3: Läsande lager utils/lagstruktur.py

**Files:**
- Create: `utils/lagstruktur.py`
- Create: `tests/test_lagstruktur.py`

**Interfaces:**
- Consumes: `data/lagstruktur/*.json` från Task 2, `utils.lagrum.lagrum_register`.
- Produces:
  - `Kapitel(nummer: str, rubrik: str, paragrafer: tuple[str, ...])`
  - `Moment(rubrik: str, kapitel: str | None, paragrafer: tuple[str, ...])`
  - `Lagstruktur(forkortning, namn, sfs, kalla, kallnamn, hamtad, licens, kapitel: tuple[Kapitel, ...], moment: tuple[Moment, ...])`
  - `ladda_lagstruktur() -> dict[str, Lagstruktur]`
  - `kapitelrubrik(forkortning: str, nummer: str) -> str | None`
  - `antal_kapitel(forkortning: str) -> int`
  - `paragrafnycklar(forkortning: str) -> frozenset[str]`

- [ ] **Step 1: Skriv de fallerande testerna**

```python
"""Tester för läsningen av lagstrukturen (utils.lagstruktur).

Strukturen är appens enda källa till lagens egen disposition. Den valideras
strikt vid inläsning: hellre ett tydligt fel vid uppstart än ett halvt
kapitel i lagkortet.
"""

from __future__ import annotations

import json

import pytest

from utils.lagrum import lagrum_register
from utils.lagstruktur import (
    DATA_DIR,
    antal_kapitel,
    kapitelrubrik,
    ladda_lagstruktur,
    paragrafnycklar,
    _bygg_struktur,
)


@pytest.fixture(scope="module")
def strukturer():
    return ladda_lagstruktur()


def test_alla_lagar_i_registret_har_en_strukturfil(strukturer):
    saknas = sorted(set(lagrum_register()) - set(strukturer))
    assert saknas == [], f"Saknar strukturfil för: {saknas}"


def test_ingen_lag_saknar_bada_rubriknivaerna(strukturer):
    tomma = [f for f, s in strukturer.items() if not s.kapitel and not s.moment]
    assert tomma == []


def test_moment_pekar_alltid_pa_ett_existerande_kapitel(strukturer):
    for forkortning, struktur in strukturer.items():
        nummer = {k.nummer for k in struktur.kapitel}
        for moment in struktur.moment:
            if moment.kapitel is not None:
                assert moment.kapitel in nummer, (
                    f"{forkortning}: momentet {moment.rubrik!r} pekar på "
                    f"kapitel {moment.kapitel} som inte finns"
                )


def test_paragrafnycklarna_har_samma_form_som_lagtextkorpusen(strukturer):
    for forkortning, struktur in strukturer.items():
        for kapitel in struktur.kapitel:
            for nyckel in kapitel.paragrafer:
                delar = nyckel.split(":")
                assert all(d.isdigit() for d in delar), f"{forkortning}: {nyckel}"
                assert len(delar) <= 2


def test_strukturen_ar_immutabel(strukturer):
    struktur = strukturer["KKöpL"]
    assert isinstance(struktur.kapitel, tuple)
    with pytest.raises(Exception):
        struktur.kapitel = ()


def test_kapitelrubrik_slar_upp_pa_nummer():
    assert kapitelrubrik("KKöpL", "3") == "Näringsidkarens dröjsmål"


def test_kapitelrubrik_ger_none_for_okant_kapitel():
    assert kapitelrubrik("KKöpL", "99") is None


def test_kapitelrubrik_ger_none_for_okand_lag():
    assert kapitelrubrik("Påhittad", "1") is None


def test_antal_kapitel_raknar_hela_lagen():
    assert antal_kapitel("KKöpL") >= 6


def test_antal_kapitel_ar_noll_for_kapitellos_lag():
    assert antal_kapitel("PreskL") == 0


def test_paragrafnycklar_samlar_bade_kapitel_och_moment():
    nycklar = paragrafnycklar("KKöpL")
    assert "3:1" in nycklar
    assert "99:1" not in nycklar


def test_trasig_fil_kastar_vid_inlasning():
    """Fail fast: hellre ett fel vid uppstart än ett halvt kapitel i vyn."""
    rad = {"forkortning": "X", "namn": "X", "sfs": "1:1", "kapitel": "inte en lista"}
    with pytest.raises(ValueError):
        _bygg_struktur(rad)


def test_fil_utan_rubriknivaer_kastar():
    rad = {
        "forkortning": "X", "namn": "X", "sfs": "1:1",
        "kalla": "", "kallnamn": "", "hamtad": "", "licens": "",
        "kapitel": [], "moment": [],
    }
    with pytest.raises(ValueError):
        _bygg_struktur(rad)


def test_datakatalogen_ar_committad():
    assert DATA_DIR.exists()
    assert len(list(DATA_DIR.glob("*.json"))) == 21
```

- [ ] **Step 2: Kör testerna och se dem falla**

Kör: `python3.11 -m pytest tests/test_lagstruktur.py -v`
Förväntat: FAIL med `ModuleNotFoundError: No module named 'utils.lagstruktur'`

- [ ] **Step 3: Skriv modulen**

```python
"""Läs-API mot lagstrukturen i data/lagstruktur/.

Strukturen är lagens egen disposition — kapitelrubriker, momentrubriker och
vilka paragrafer som hör till vad — hämtad ur Riksdagens öppna data av
scripts/hamta_lagstruktur.py och committad så att appen fungerar offline.

Den fyller två roller. Dels ger den lagkortet en ryggrad att gruppera
kursavsnitten under, dels är den facit när kursavsnittens paragrafgränser
ska verifieras (utils.kursavsnitt_kontroll).

Till skillnad från utils.lagtext, som får degradera tyst när en paragraf
saknas, validerar den här modulen strikt vid inläsning. Skälet är att en
trasig struktur inte ger en tom lucka utan ett felaktigt påstående om hur
lagen är uppbyggd. En saknad fil är däremot inte ett fel här; det hanteras
av anroparen, och ett test vaktar att ingen fil saknas.

Ren modul utan Streamlit-beroende.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "lagstruktur"


@dataclass(frozen=True)
class Kapitel:
    """Ett kapitel i lagen med sin egen rubrik och sina paragrafer."""

    nummer: str
    rubrik: str
    paragrafer: tuple[str, ...]


@dataclass(frozen=True)
class Moment:
    """En momentrubrik i lagen. ``kapitel`` är None för kapitellösa lagar."""

    rubrik: str
    kapitel: str | None
    paragrafer: tuple[str, ...]


@dataclass(frozen=True)
class Lagstruktur:
    """Hela lagens disposition. Minst en av kapitel och moment är ifylld."""

    forkortning: str
    namn: str
    sfs: str
    kalla: str
    kallnamn: str
    hamtad: str
    licens: str
    kapitel: tuple[Kapitel, ...]
    moment: tuple[Moment, ...]


def _krav_lista(rad: dict, nyckel: str) -> list:
    varde = rad.get(nyckel, [])
    if not isinstance(varde, list):
        raise ValueError(
            f"{rad.get('forkortning', '?')}: '{nyckel}' måste vara en lista, "
            f"fick {type(varde).__name__}"
        )
    return varde


def _bygg_struktur(rad: dict) -> Lagstruktur:
    """Validera en inläst rad och bygg den immutabla modellen."""
    forkortning = str(rad["forkortning"])

    kapitel = tuple(
        Kapitel(
            nummer=str(k["nummer"]),
            rubrik=str(k["rubrik"]),
            paragrafer=tuple(str(p) for p in k.get("paragrafer", ())),
        )
        for k in _krav_lista(rad, "kapitel")
    )
    moment = tuple(
        Moment(
            rubrik=str(m["rubrik"]),
            kapitel=None if m.get("kapitel") is None else str(m["kapitel"]),
            paragrafer=tuple(str(p) for p in m.get("paragrafer", ())),
        )
        for m in _krav_lista(rad, "moment")
    )

    if not kapitel and not moment:
        raise ValueError(
            f"{forkortning}: strukturen saknar både kapitel och moment. "
            "Varje lag har minst en rubriknivå — hämta om lagen."
        )

    nummer = {k.nummer for k in kapitel}
    for m in moment:
        if m.kapitel is not None and m.kapitel not in nummer:
            raise ValueError(
                f"{forkortning}: momentet {m.rubrik!r} pekar på kapitel "
                f"{m.kapitel}, som inte finns i strukturen."
            )

    return Lagstruktur(
        forkortning=forkortning,
        namn=str(rad["namn"]),
        sfs=str(rad["sfs"]),
        kalla=str(rad.get("kalla", "")),
        kallnamn=str(rad.get("kallnamn", "")),
        hamtad=str(rad.get("hamtad", "")),
        licens=str(rad.get("licens", "")),
        kapitel=kapitel,
        moment=moment,
    )


@lru_cache(maxsize=1)
def ladda_lagstruktur() -> dict[str, Lagstruktur]:
    """Läs och cachea alla strukturfiler, nycklade på lagförkortning."""
    if not DATA_DIR.exists():
        return {}

    ut: dict[str, Lagstruktur] = {}
    for fil in sorted(DATA_DIR.glob("*.json")):
        struktur = _bygg_struktur(json.loads(fil.read_text(encoding="utf-8")))
        ut[struktur.forkortning] = struktur
    return ut


def kapitelrubrik(forkortning: str, nummer: str) -> str | None:
    """Rubriken för ett kapitel, eller None om lagen eller kapitlet är okänt."""
    struktur = ladda_lagstruktur().get(forkortning)
    if struktur is None:
        return None
    for kapitel in struktur.kapitel:
        if kapitel.nummer == nummer:
            return kapitel.rubrik
    return None


def antal_kapitel(forkortning: str) -> int:
    """Antal kapitel i hela lagen. Noll för lagar utan kapitelindelning."""
    struktur = ladda_lagstruktur().get(forkortning)
    return 0 if struktur is None else len(struktur.kapitel)


def paragrafnycklar(forkortning: str) -> frozenset[str]:
    """Alla paragrafnycklar lagen faktiskt har, enligt källan."""
    struktur = ladda_lagstruktur().get(forkortning)
    if struktur is None:
        return frozenset()
    return frozenset(
        nyckel
        for post in (*struktur.kapitel, *struktur.moment)
        for nyckel in post.paragrafer
    )
```

- [ ] **Step 4: Kör testerna och se dem passera**

Kör: `python3.11 -m pytest tests/test_lagstruktur.py -v`
Förväntat: PASS, 14 tester.

- [ ] **Step 5: Kör hela sviten så inget annat gått sönder**

Kör: `python3.11 -m pytest -q`
Förväntat: alla tester passerar (630 före den här grenen, plus de nya).

- [ ] **Step 6: Committa**

```bash
git add utils/lagstruktur.py tests/test_lagstruktur.py
git commit -m "feat: läs-API mot lagstrukturen med strikt validering

Till skillnad från lagtextkorpusen, som degraderar tyst när en paragraf
saknas, kastar den här modulen vid trasig fil. En trasig struktur ger inte
en tom lucka utan ett felaktigt påstående om hur lagen är uppbyggd."
```

---

### Task 4: Kontrollager och överskjutandetestet

**Files:**
- Create: `utils/kursavsnitt_kontroll.py`
- Create: `scripts/verifiera_kursavsnitt.py`
- Create: `tests/test_kursavsnitt_kontroll.py`

**Interfaces:**
- Consumes: `utils.lagrum.lagrum_register`, `utils.lagrum.Lag`, `utils.lagrum.Kursavsnitt`, `utils.lagstruktur.Lagstruktur`, `utils.lagstruktur.ladda_lagstruktur`.
- Produces:
  - `TYP_OVERSKJUTANDE`, `TYP_FOR_SNAV`, `TYP_RUBRIKAVVIKELSE`, `TYP_SPANNER_OVER_MOMENT` (str-konstanter)
  - `Avvikelse(forkortning: str, avsnitt: str, typ: str, detalj: str)`
  - `avsnittsnycklar(lag: Lag, avsnitt: Kursavsnitt) -> tuple[str, ...]`
  - `kontrollera_lag(lag: Lag, struktur: Lagstruktur) -> tuple[Avvikelse, ...]`
  - `kontrollera_alla() -> tuple[Avvikelse, ...]`

**Denna uppgift lämnar sviten RÖD med avsikt.** Överskjutandetestet mäter 25 kända avvikelser. Rättningen sker i Task 5 och är användarens beslut, inte implementatörens.

- [ ] **Step 1: Skriv de fallerande testerna**

```python
"""Tester för försoningen mellan kursavsnitt och lagens struktur.

Bakgrund: data/lagrum.json bär 105 kursavsnitt, varav 78 flaggade med
"verifiera": true — osäkra paragrafgränser som skulle kontrolleras mot
lagen.nu. Så länge avsnitten bara matade validering och prompter var en
oskarp gräns billig. När de visas i lagkortet blir den ett påstående
studenten läser som sant.

Korpusen i data/lagtext/ kan inte användas som facit: den härleddes ur
kursavsnitten (scripts/hamta_lagtext.py sparar bara paragrafer inom dem),
så den fångar bara för vida gränser, aldrig för snäva. Lagens egen struktur
fångar båda.
"""

from __future__ import annotations

import pytest

from utils.kursavsnitt_kontroll import (
    TYP_FOR_SNAV,
    TYP_OVERSKJUTANDE,
    Avvikelse,
    avsnittsnycklar,
    kontrollera_alla,
    kontrollera_lag,
)
from utils.lagrum import Kursavsnitt, Lag
from utils.lagstruktur import Kapitel, Lagstruktur, Moment


def _lag(kapitelindelad: bool, avsnitt: tuple[Kursavsnitt, ...]) -> Lag:
    return Lag(
        forkortning="TestL",
        namn="Testlagen",
        sfs="2026:1",
        kapitelindelad=kapitelindelad,
        lagen_nu_bas_url="https://lagen.nu/2026:1",
        kursavsnitt=avsnitt,
    )


def _avsnitt(beskrivning, kapitel, fran, till, verifiera=True) -> Kursavsnitt:
    return Kursavsnitt(
        beskrivning=beskrivning,
        kapitel=kapitel,
        paragraf_fran=fran,
        paragraf_till=till,
        lagen_nu_url="https://lagen.nu/2026:1",
        verifiera=verifiera,
    )


def _struktur(kapitel=(), moment=()) -> Lagstruktur:
    return Lagstruktur(
        forkortning="TestL", namn="Testlagen", sfs="2026:1",
        kalla="", kallnamn="", hamtad="", licens="",
        kapitel=kapitel, moment=moment,
    )


def test_avsnittsnycklar_expanderar_kapitelindelat_intervall():
    lag = _lag(True, ())
    assert avsnittsnycklar(lag, _avsnitt("x", "3", 1, 3)) == ("3:1", "3:2", "3:3")


def test_avsnittsnycklar_expanderar_platt_intervall():
    lag = _lag(False, ())
    assert avsnittsnycklar(lag, _avsnitt("x", None, 10, 12)) == ("10", "11", "12")


def test_overskjutande_gräns_upptacks():
    """Avsnittet påstår paragrafer som inte finns i lagen."""
    lag = _lag(True, (_avsnitt("Talan", "13", 1, 9),))
    struktur = _struktur(
        kapitel=(Kapitel("13", "Om talan", ("13:1", "13:2", "13:3")),)
    )
    avvikelser = kontrollera_lag(lag, struktur)
    overskjutande = [a for a in avvikelser if a.typ == TYP_OVERSKJUTANDE]
    assert len(overskjutande) == 1
    assert "13:4" in overskjutande[0].detalj


def test_ingen_avvikelse_nar_gransen_stammer():
    lag = _lag(True, (_avsnitt("Talan", "13", 1, 3),))
    struktur = _struktur(
        kapitel=(Kapitel("13", "Om talan", ("13:1", "13:2", "13:3")),)
    )
    assert [a for a in kontrollera_lag(lag, struktur) if a.typ == TYP_OVERSKJUTANDE] == []


def test_for_snav_gräns_upptacks():
    """Momentet sträcker sig utanför avsnittet — korpusen kunde aldrig se detta."""
    lag = _lag(True, (_avsnitt("Påföljder", "5", 1, 2),))
    struktur = _struktur(
        kapitel=(Kapitel("5", "Påföljder", ("5:1", "5:2", "5:3")),),
        moment=(Moment("Påföljder vid fel", "5", ("5:1", "5:2", "5:3")),),
    )
    avvikelser = [a for a in kontrollera_lag(lag, struktur) if a.typ == TYP_FOR_SNAV]
    assert len(avvikelser) == 1
    assert "5:3" in avvikelser[0].detalj


def test_avvikelser_ar_immutabla():
    a = Avvikelse("TestL", "Talan", TYP_OVERSKJUTANDE, "13:4")
    with pytest.raises(Exception):
        a.typ = TYP_FOR_SNAV


def test_kontrollera_alla_taeker_hela_registret():
    """Kontrollen ska köras mot alla lagar, inte bara dem som råkar ha avvikelser."""
    avvikelser = kontrollera_alla()
    assert isinstance(avvikelser, tuple)
    assert all(isinstance(a, Avvikelse) for a in avvikelser)


def test_inga_kursavsnitt_pekar_utanfor_lagen():
    """Bärande invariant: inget kursavsnitt får påstå paragrafer som inte finns.

    RÖD tills de 78 flaggade avsnitten gåtts igenom (25 kända avvikelser).
    Därefter en permanent spärr mot att nästa lagändring smyger in samma fel.
    """
    fel = [a for a in kontrollera_alla() if a.typ == TYP_OVERSKJUTANDE]
    assert fel == [], "\n".join(f"{a.forkortning}: {a.avsnitt} — {a.detalj}" for a in fel)
```

- [ ] **Step 2: Kör testerna och se dem falla**

Kör: `python3.11 -m pytest tests/test_kursavsnitt_kontroll.py -v`
Förväntat: FAIL med `ModuleNotFoundError: No module named 'utils.kursavsnitt_kontroll'`

- [ ] **Step 3: Skriv kontrollagret**

```python
"""Jämför kursavsnitten i data/lagrum.json mot lagens faktiska struktur.

Registret bär 105 kursavsnitt, varav 78 flaggade med "verifiera": true —
osäkra paragrafgränser eller osäkert kursomfång. Den här modulen är facit:
den säger vad som avviker, i fyra sorter.

Vad modulen INTE gör: den rättar aldrig registret. Om ett avsnitt ska
omfatta 13:1–13:7 eller 13:1–13:5 är en bedömning av kursens omfång, inte
en textjämförelse. Modulen rapporterar; människan beslutar.

Ren modul utan Streamlit-beroende.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.lagrum import Kursavsnitt, Lag, lagrum_register
from utils.lagstruktur import Lagstruktur, ladda_lagstruktur

TYP_OVERSKJUTANDE = "OVERSKJUTANDE"
TYP_FOR_SNAV = "FOR_SNAV"
TYP_RUBRIKAVVIKELSE = "RUBRIKAVVIKELSE"
TYP_SPANNER_OVER_MOMENT = "SPANNER_OVER_MOMENT"

FORKLARING = {
    TYP_OVERSKJUTANDE: "Avsnittet anger paragrafer som inte finns i lagen.",
    TYP_FOR_SNAV: "Momentets paragrafer sträcker sig utanför avsnittet.",
    TYP_RUBRIKAVVIKELSE: "Beskrivningen skiljer sig från lagens egen rubrik.",
    TYP_SPANNER_OVER_MOMENT: "Avsnittet skär genom flera moment.",
}


@dataclass(frozen=True)
class Avvikelse:
    """En skillnad mellan ett kursavsnitt och lagens struktur."""

    forkortning: str
    avsnitt: str
    typ: str
    detalj: str


def avsnittsnycklar(lag: Lag, avsnitt: Kursavsnitt) -> tuple[str, ...]:
    """Paragrafnycklarna ett kursavsnitt gör anspråk på.

    Samma expansion som scripts/hamta_lagtext.kursens_nycklar, men på
    registrets modell i stället för på råa dictar.
    """
    kapitel = avsnitt.kapitel if lag.kapitelindelad else None
    return tuple(
        f"{kapitel}:{nr}" if kapitel else str(nr)
        for nr in range(avsnitt.paragraf_fran, avsnitt.paragraf_till + 1)
    )


def _moment_som_overlappar(
    struktur: Lagstruktur, nycklar: frozenset[str]
) -> tuple:
    return tuple(m for m in struktur.moment if nycklar & set(m.paragrafer))


def kontrollera_lag(lag: Lag, struktur: Lagstruktur) -> tuple[Avvikelse, ...]:
    """Alla avvikelser mellan en lags kursavsnitt och dess struktur."""
    finns = frozenset(
        nyckel
        for post in (*struktur.kapitel, *struktur.moment)
        for nyckel in post.paragrafer
    )

    avvikelser: list[Avvikelse] = []
    for avsnitt in lag.kursavsnitt:
        anspråk = frozenset(avsnittsnycklar(lag, avsnitt))

        saknade = sorted(anspråk - finns, key=_sortering)
        if saknade:
            avvikelser.append(
                Avvikelse(
                    lag.forkortning, avsnitt.beskrivning, TYP_OVERSKJUTANDE,
                    f"finns inte i lagen: {', '.join(saknade)}",
                )
            )

        overlappande = _moment_som_overlappar(struktur, anspråk)
        for moment in overlappande:
            utanfor = sorted(set(moment.paragrafer) - anspråk, key=_sortering)
            if utanfor:
                avvikelser.append(
                    Avvikelse(
                        lag.forkortning, avsnitt.beskrivning, TYP_FOR_SNAV,
                        f"momentet {moment.rubrik!r} har även: "
                        f"{', '.join(utanfor)}",
                    )
                )

        if len(overlappande) > 1:
            rubriker = ", ".join(repr(m.rubrik) for m in overlappande)
            avvikelser.append(
                Avvikelse(
                    lag.forkortning, avsnitt.beskrivning,
                    TYP_SPANNER_OVER_MOMENT, f"berör momenten: {rubriker}",
                )
            )

        if len(overlappande) == 1:
            rubrik = overlappande[0].rubrik
            if rubrik.casefold() != avsnitt.beskrivning.casefold():
                avvikelser.append(
                    Avvikelse(
                        lag.forkortning, avsnitt.beskrivning,
                        TYP_RUBRIKAVVIKELSE, f"lagens rubrik lyder {rubrik!r}",
                    )
                )

    return tuple(avvikelser)


def _sortering(nyckel: str) -> tuple[int, int]:
    if ":" in nyckel:
        kap, par = nyckel.split(":", 1)
        return (int(kap), int(par))
    return (0, int(nyckel))


def kontrollera_alla() -> tuple[Avvikelse, ...]:
    """Kontrollera hela registret mot alla strukturfiler."""
    strukturer = ladda_lagstruktur()
    avvikelser: list[Avvikelse] = []
    for forkortning, lag in sorted(lagrum_register().items()):
        struktur = strukturer.get(forkortning)
        if struktur is None:
            continue
        avvikelser.extend(kontrollera_lag(lag, struktur))
    return tuple(avvikelser)
```

- [ ] **Step 4: Skriv rapportskriptet**

```python
#!/usr/bin/env python3
"""Skriv ut avvikelser mellan kursavsnitten och lagarnas faktiska struktur.

    python3.11 scripts/verifiera_kursavsnitt.py            # alla avvikelser
    python3.11 scripts/verifiera_kursavsnitt.py --typ OVERSKJUTANDE
    python3.11 scripts/verifiera_kursavsnitt.py --lag RB

Skriptet RÄTTAR ALDRIG data/lagrum.json. Om ett avsnitt ska sluta vid 13:5
eller 13:7 är en bedömning av kursens omfång, inte en textjämförelse.
Rapporten är underlag; beslutet är människans.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.kursavsnitt_kontroll import FORKLARING, kontrollera_alla  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--typ", help="visa bara denna avvikelsetyp")
    parser.add_argument("--lag", help="visa bara denna lag")
    args = parser.parse_args(argv)

    avvikelser = kontrollera_alla()
    if args.typ:
        avvikelser = tuple(a for a in avvikelser if a.typ == args.typ)
    if args.lag:
        avvikelser = tuple(a for a in avvikelser if a.forkortning == args.lag)

    for avvikelse in avvikelser:
        print(f"{avvikelse.forkortning:8s} [{avvikelse.typ}]")
        print(f"         {avvikelse.avsnitt}")
        print(f"         {avvikelse.detalj}")
        print()

    rakning = Counter(a.typ for a in avvikelser)
    print("SAMMANFATTNING")
    for typ, antal in sorted(rakning.items()):
        print(f"  {antal:4d}  {typ}: {FORKLARING.get(typ, '')}")
    print(f"  {len(avvikelser):4d}  totalt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Kör testerna — enhetstesterna passerar, invarianten faller**

Kör: `python3.11 -m pytest tests/test_kursavsnitt_kontroll.py -v`
Förväntat: alla tester PASS **utom** `test_inga_kursavsnitt_pekar_utanfor_lagen`, som FAIL med en lista över de kursavsnitt som pekar utanför lagen (omkring 25 stycken, mätta mot korpusen; siffran kan skilja något mot strukturen som täcker hela lagen).

Detta är den avsedda röda fasen. Gå inte vidare genom att ändra testet.

- [ ] **Step 6: Skriv ut rapporten och spara den som underlag**

Kör: `python3.11 scripts/verifiera_kursavsnitt.py > /tmp/kursavsnitt-rapport.txt; tail -8 /tmp/kursavsnitt-rapport.txt`
Förväntat: en sammanfattning med antal per avvikelsetyp.

- [ ] **Step 7: Committa**

```bash
git add utils/kursavsnitt_kontroll.py scripts/verifiera_kursavsnitt.py tests/test_kursavsnitt_kontroll.py
git commit -m "feat: försona kursavsnitten mot lagens faktiska struktur

Fyra avvikelsetyper: överskjutande och för snäva gränser, rubrikavvikelse
och avsnitt som spänner över flera moment. Överskjutandetestet är rött med
avsikt: det mäter de kursavsnitt som pekar utanför lagen och driver
rättningen. Kontrollen rättar aldrig registret själv — gränserna är en
bedömning av kursens omfång, inte en textjämförelse."
```

---

### Task 5: Rättning av de flaggade kursavsnitten (användarens beslut)

**Files:**
- Modify: `data/lagrum.json`

**Interfaces:**
- Consumes: rapporten från Task 4.
- Produces: ett register där inget kursavsnitt bär `verifiera: true` och överskjutandetestet är grönt.

**Detta är projektets mänskliga grind.** En implementatör får inte tysta flaggorna på egen hand. Juridiskt innehåll får inte hittas på, och kursens omfång är kursansvarigs beslut.

- [ ] **Step 1: Gå igenom rapporten avsnitt för avsnitt**

För varje avvikelse, avgör vilket som gäller:
- Gränsen är fel → rätta `paragraf_fran`/`paragraf_till` i `data/lagrum.json`.
- Gränsen är rätt och avvikelsen är avsiktlig (t.ex. ett avsnitt som medvetet spänner över flera moment) → lämna gränsen, notera skälet i lagens `not`-fält.
- Rubriken är fel → rätta `beskrivning`.

Sätt `"verifiera": false` på varje avsnitt som gåtts igenom.

- [ ] **Step 2: Kör kontrollen igen tills överskjutandelistan är tom**

Kör: `python3.11 scripts/verifiera_kursavsnitt.py --typ OVERSKJUTANDE`
Förväntat: `0 totalt`

Kvarvarande avvikelser av typen `FOR_SNAV`, `RUBRIKAVVIKELSE` och `SPANNER_OVER_MOMENT` är inte fel i sig — de är underlag. Bara överskjutande gränser är alltid fel.

- [ ] **Step 3: Kör hela sviten**

Kör: `python3.11 -m pytest -q`
Förväntat: alla tester passerar, inklusive `test_inga_kursavsnitt_pekar_utanfor_lagen`.

- [ ] **Step 4: Committa**

```bash
git add data/lagrum.json
git commit -m "fix: rätta kursavsnittens paragrafgränser mot lagarnas struktur

De flaggade avsnitten är genomgångna mot lagens egen disposition och
verifiera-flaggan är nollställd. Inget avsnitt pekar längre på paragrafer
som inte finns."
```

---

### Task 6: Kursavsnitt i lagkortet

**Files:**
- Modify: `utils/ui.py:525-551` (`render_lagkort`)
- Modify: `utils/ui.py:212-227` (CSS för `.jok-lagkort`)
- Create: `utils/lagkort_avsnitt.py`
- Create: `tests/test_lagkort_avsnitt.py`
- Modify: `tests/test_ui.py`

**Interfaces:**
- Consumes: `utils.lagstruktur.kapitelrubrik`, `utils.lagstruktur.antal_kapitel`, `utils.lagrum.Lag`.
- Produces:
  - `formatera_spann(fran: int, till: int) -> str`
  - `Avsnittsrad(spann: str, rubrik: str, url: str)`
  - `Kapitelgrupp(kapitel: str | None, rubrik: str, avsnitt: tuple[Avsnittsrad, ...])`
  - `gruppera_kursavsnitt(lag: Lag) -> tuple[Kapitelgrupp, ...]`
  - `tackningstext(lag: Lag) -> str`
  - `render_lagkort(..., kursavsnitt: tuple[Kapitelgrupp, ...] = (), tackning: str = "")`

- [ ] **Step 1: Skriv de fallerande testerna för grupperingen**

```python
"""Tester för grupperingen av kursavsnitt inför lagkortet."""

from __future__ import annotations

from utils.lagkort_avsnitt import (
    formatera_spann,
    gruppera_kursavsnitt,
    tackningstext,
)
from utils.lagrum import lagrum_register


def test_ett_enda_paragrafnummer_far_enkelt_paragraftecken():
    """36 §, aldrig 36 §§. Pluralfel i lagrum läser studenten som slarv."""
    assert formatera_spann(36, 36) == "36 §"


def test_intervall_far_dubbelt_paragraftecken():
    assert formatera_spann(1, 9) == "1–9 §§"


def test_intervall_anvander_tankstreck_inte_bindestreck():
    assert "–" in formatera_spann(1, 9)
    assert "-" not in formatera_spann(1, 9)


def test_kapitelindelad_lag_grupperas_under_sina_kapitel():
    grupper = gruppera_kursavsnitt(lagrum_register()["KKöpL"])
    assert all(g.kapitel is not None for g in grupper)
    assert all(g.rubrik for g in grupper)


def test_kapitellos_lag_ger_en_enda_ogrupperad_grupp():
    grupper = gruppera_kursavsnitt(lagrum_register()["KöpL"])
    assert len(grupper) == 1
    assert grupper[0].kapitel is None
    assert grupper[0].rubrik == ""
    assert len(grupper[0].avsnitt) == len(lagrum_register()["KöpL"].kursavsnitt)


def test_avsnittsraden_bar_spann_rubrik_och_lank():
    grupper = gruppera_kursavsnitt(lagrum_register()["AvtL"])
    rad = grupper[0].avsnitt[0]
    assert rad.spann.endswith("§") or rad.spann.endswith("§§")
    assert rad.rubrik
    assert rad.url.startswith("https://lagen.nu/")


def test_tackningstext_for_kapitelindelad_lag():
    text = tackningstext(lagrum_register()["KKöpL"])
    assert "av lagens" in text
    assert "kapitel" in text


def test_tackningstext_ar_tom_for_kapitellos_lag():
    """Utan kapitel finns inget att räkna, och raden ska då utebli helt."""
    assert tackningstext(lagrum_register()["KöpL"]) == ""
```

- [ ] **Step 2: Kör och se dem falla**

Kör: `python3.11 -m pytest tests/test_lagkort_avsnitt.py -v`
Förväntat: FAIL med `ModuleNotFoundError: No module named 'utils.lagkort_avsnitt'`

- [ ] **Step 3: Skriv grupperingen**

```python
"""Förbered kursavsnitten för visning i lagkortet.

Registret bär avsnitten platt, medan lagen är indelad i kapitel. Den här
modulen slår ihop de två: avsnitten grupperas under lagens egna
kapitelrubriker, och lagar utan kapitelindelning får en enda ogrupperad
lista. Vyn slipper därmed veta något om lagstrukturen.

Ren modul utan Streamlit-beroende: all formatering är testbar utan att
rendera något.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.lagrum import Lag
from utils.lagstruktur import antal_kapitel, kapitelrubrik


@dataclass(frozen=True)
class Avsnittsrad:
    """En rad i lagkortets avsnittslista."""

    spann: str
    rubrik: str
    url: str


@dataclass(frozen=True)
class Kapitelgrupp:
    """Ett kapitel med sina kursavsnitt. ``kapitel`` är None för platta lagar."""

    kapitel: str | None
    rubrik: str
    avsnitt: tuple[Avsnittsrad, ...]


def formatera_spann(fran: int, till: int) -> str:
    """Paragrafspannet på svensk form: "36 §" för en, "1–9 §§" för flera.

    Paragraftecknet dubbleras bara vid flertal, och skiljetecknet är
    tankstreck. Ett "36 §§" läser studenten som slarv i just den detalj
    kursen ska lära ut.
    """
    if fran == till:
        return f"{fran} §"
    return f"{fran}–{till} §§"


def _rad(lag: Lag, avsnitt) -> Avsnittsrad:
    return Avsnittsrad(
        spann=formatera_spann(avsnitt.paragraf_fran, avsnitt.paragraf_till),
        rubrik=avsnitt.beskrivning,
        url=avsnitt.lagen_nu_url or lag.lagen_nu_bas_url,
    )


def gruppera_kursavsnitt(lag: Lag) -> tuple[Kapitelgrupp, ...]:
    """Gruppera lagens kursavsnitt under lagens egna kapitelrubriker.

    Lagar utan kapitelindelning ger exakt en grupp utan kapitel och utan
    rubrik, så att vyn kan rendera båda formerna med samma slinga.
    """
    if not lag.kursavsnitt:
        return ()

    if not lag.kapitelindelad:
        return (
            Kapitelgrupp(
                kapitel=None,
                rubrik="",
                avsnitt=tuple(_rad(lag, a) for a in lag.kursavsnitt),
            ),
        )

    ordning: list[str] = []
    per_kapitel: dict[str, list[Avsnittsrad]] = {}
    for avsnitt in lag.kursavsnitt:
        nyckel = avsnitt.kapitel or ""
        if nyckel not in per_kapitel:
            per_kapitel[nyckel] = []
            ordning.append(nyckel)
        per_kapitel[nyckel].append(_rad(lag, avsnitt))

    return tuple(
        Kapitelgrupp(
            kapitel=nyckel or None,
            rubrik=kapitelrubrik(lag.forkortning, nyckel) or "",
            avsnitt=tuple(per_kapitel[nyckel]),
        )
        for nyckel in ordning
    )


def tackningstext(lag: Lag) -> str:
    """Hur stor del av lagen kursen berör, eller tom sträng.

    Raden är lagkortets ärlighetskrav. Utan den läser studenten
    avsnittslistan som om lagen tog slut där. Saknar lagen kapitel finns
    inget att räkna, och då ska raden utebli helt hellre än att gissa.
    """
    totalt = antal_kapitel(lag.forkortning)
    if not totalt:
        return ""
    berorda = len({a.kapitel for a in lag.kursavsnitt if a.kapitel})
    if not berorda:
        return ""
    return f"kursen täcker {berorda} av lagens {totalt} kapitel"
```

- [ ] **Step 4: Kör och se dem passera**

Kör: `python3.11 -m pytest tests/test_lagkort_avsnitt.py -v`
Förväntat: PASS, 8 tester.

- [ ] **Step 5: Skriv de fallerande testerna för renderingen**

Lägg till i `tests/test_ui.py`:

```python
def test_lagkortet_renderar_kursavsnitt_med_kapitelrubrik():
    from utils.lagkort_avsnitt import Avsnittsrad, Kapitelgrupp
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="KKöpL", namn="Konsumentköplag", sfs="2022:260",
        beskrivning="B", nar="N", url="https://lagen.nu/2022:260",
        kursavsnitt=(
            Kapitelgrupp("3", "Näringsidkarens dröjsmål", (
                Avsnittsrad("1–6 §§", "Påföljder vid dröjsmål",
                            "https://lagen.nu/2022:260#K3P1"),
            )),
        ),
        tackning="kursen täcker 6 av lagens 8 kapitel",
    )
    assert "3 kap. Näringsidkarens dröjsmål" in html
    assert "1–6 §§" in html
    assert "Påföljder vid dröjsmål" in html
    assert "kursen täcker 6 av lagens 8 kapitel" in html


def test_lagkortet_utan_kursavsnitt_ser_ut_som_forr():
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="X", namn="X", sfs="1:1", beskrivning="B", nar="N",
        url="https://lagen.nu/1:1",
    )
    assert "KURSAVSNITT" not in html


def test_lagkortet_escapar_avsnittsrubriker():
    from utils.lagkort_avsnitt import Avsnittsrad, Kapitelgrupp
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="X", namn="X", sfs="1:1", beskrivning="B", nar="N",
        url="https://lagen.nu/1:1",
        kursavsnitt=(
            Kapitelgrupp(None, "", (
                Avsnittsrad("1 §", "<script>alert(1)</script>", "https://lagen.nu/1:1"),
            )),
        ),
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_kapitellos_grupp_renderar_ingen_kapitelrubrik():
    from utils.lagkort_avsnitt import Avsnittsrad, Kapitelgrupp
    from utils.ui import render_lagkort

    html = render_lagkort(
        forkortning="KöpL", namn="Köplag", sfs="1990:931", beskrivning="B",
        nar="N", url="https://lagen.nu/1990:931",
        kursavsnitt=(
            Kapitelgrupp(None, "", (
                Avsnittsrad("22–29 §§", "Påföljder vid dröjsmål",
                            "https://lagen.nu/1990:931#P22"),
            )),
        ),
    )
    assert "kap." not in html
    assert "22–29 §§" in html
```

- [ ] **Step 6: Kör och se dem falla**

Kör: `python3.11 -m pytest tests/test_ui.py -k lagkort -v`
Förväntat: FAIL med `TypeError: render_lagkort() got an unexpected keyword argument 'kursavsnitt'`

- [ ] **Step 7: Utöka renderaren**

Ersätt `render_lagkort` i `utils/ui.py` (rad 525-551) med:

```python
def render_lagkort(
    forkortning: str,
    namn: str,
    sfs: str,
    beskrivning: str,
    nar: str,
    url: str,
    relaterade: tuple[str, ...] = (),
    kursavsnitt: tuple = (),
    tackning: str = "",
) -> str:
    """Kort för en lag i områdesträdet: vad den täcker och när den övervägs.

    ``kursavsnitt`` är Kapitelgrupp-poster från utils.lagkort_avsnitt. Är den
    tom renderas kortet precis som förr, utan tom avsnittsrubrik.
    """
    rel = ""
    if relaterade:
        rel = (
            '<div class="nar"><strong>Relaterade lagar:</strong> '
            f"{html.escape(', '.join(relaterade))}</div>"
        )
    return (
        '<div class="jok-lagkort">'
        f"<h4>{html.escape(forkortning)}: {html.escape(namn)}</h4>"
        f'<div class="sfs">SFS {html.escape(sfs)}</div>'
        f"<p>{html.escape(beskrivning)}</p>"
        f'<div class="nar"><strong>När övervägs den?</strong> {html.escape(nar)}</div>'
        f"{rel}"
        f"{_avsnittsblock(kursavsnitt, tackning)}"
        f'<div class="nar"><a href="{html.escape(url)}" target="_blank">'
        f"Öppna {html.escape(forkortning)} på lagen.nu</a></div>"
        "</div>"
    )


def _avsnittsblock(grupper: tuple, tackning: str) -> str:
    """Kursavsnitten grupperade under lagens egna kapitelrubriker.

    Guld är reserverat för lagrum, så spannet får paragrafguld medan
    kapitelrubriken bär bläck. Se design_system.md avsnitt 1 och 4.
    """
    if not grupper:
        return ""

    tack = (
        f'<span class="tackning">{html.escape(tackning)}</span>' if tackning else ""
    )
    delar = [
        f'<div class="avsnitt"><div class="avsnittsrubrik">KURSAVSNITT{tack}</div>'
    ]
    for grupp in grupper:
        if grupp.kapitel:
            rubrik = f"{grupp.kapitel} kap."
            if grupp.rubrik:
                rubrik = f"{rubrik} {grupp.rubrik}"
            delar.append(f'<div class="kapitelrad">{html.escape(rubrik)}</div>')
        for rad in grupp.avsnitt:
            delar.append(
                '<div class="avsnittsrad">'
                f'<a class="spann" href="{html.escape(rad.url)}" target="_blank">'
                f"{html.escape(rad.spann)}</a>"
                f'<span class="avsnittstext">{html.escape(rad.rubrik)}</span>'
                "</div>"
            )
    delar.append(
        '<div class="avsnittsnot">Urvalet följer kursen, inte hela lagen.</div></div>'
    )
    return "".join(delar)
```

- [ ] **Step 8: Lägg till CSS**

Lägg till efter `.jok-lagkort .nar strong` (rad 227 i `utils/ui.py`), inne i samma f-sträng — dubbla klammerparenteser eftersom blocket är en f-sträng:

```python
        .jok-lagkort .avsnitt {{
            margin-top: .7rem; padding-top: .6rem;
            border-top: 1px solid rgba(107, 100, 89, .18);
        }}
        .jok-lagkort .avsnittsrubrik {{
            font-size: 11px; letter-spacing: .08em; text-transform: uppercase;
            color: #6B6459; display: flex; justify-content: space-between;
            gap: 1rem; margin-bottom: .35rem;
        }}
        .jok-lagkort .tackning {{ text-transform: none; letter-spacing: 0; }}
        .jok-lagkort .kapitelrad {{
            font-size: 13px; font-weight: 600; color: var(--bla);
            margin: .45rem 0 .2rem 0;
        }}
        .jok-lagkort .avsnittsrad {{
            display: flex; gap: .6rem; font-size: 14px; line-height: 1.5;
            padding: .1rem 0 .1rem .6rem;
        }}
        .jok-lagkort .avsnittsrad .spann {{
            flex: 0 0 6.5rem; color: var(--guld); font-variant-numeric: tabular-nums;
            text-decoration: none; font-weight: 600;
        }}
        .jok-lagkort .avsnittsrad .spann:hover {{ text-decoration: underline; }}
        .jok-lagkort .avsnittstext {{ color: #4A453D; }}
        .jok-lagkort .avsnittsnot {{
            font-size: 12px; color: #6B6459; margin-top: .5rem; font-style: italic;
        }}
```

`--guld` och `--bla` är definierade i `:root` på rad 50-52 i samma f-sträng och kan användas som de står.

- [ ] **Step 9: Kör testerna och se dem passera**

Kör: `python3.11 -m pytest tests/test_ui.py tests/test_lagkort_avsnitt.py -v`
Förväntat: PASS.

- [ ] **Step 10: Committa**

```bash
git add utils/lagkort_avsnitt.py utils/ui.py tests/test_lagkort_avsnitt.py tests/test_ui.py
git commit -m "feat: visa kursavsnitten i lagkortet, grupperade per kapitel

Avsnitten fanns redan i lagrumsregistret men syntes bara för modellen.
Nu grupperas de under lagens egna kapitelrubriker, med paragrafspann i
guld och djuplänk per avsnitt. Täckningsraden säger hur stor del av lagen
kursen berör, så att listan inte läses som hela lagen."
```

---

### Task 7: Koppla in på Rättskartan och stäng grinden

**Files:**
- Modify: `sidor/16_Rattskartan.py:126-135`
- Modify: `tests/test_rattskartan_sida.py`
- Modify: `tests/test_lagrum.py`
- Modify: `APPGUIDE.md`, `design_system.md`

**Interfaces:**
- Consumes: `utils.lagkort_avsnitt.gruppera_kursavsnitt`, `utils.lagkort_avsnitt.tackningstext`.
- Produces: inget nytt API.

- [ ] **Step 1: Skriv de fallerande testerna**

Lägg till i `tests/test_rattskartan_sida.py`:

```python
def test_lagkorten_visar_kursavsnitt(sida):
    """Avsnitten ska nå studenten, inte bara modellen.

    st.html-element saknar .value i AppTest (Streamlit 1.55); innehållet
    ligger i el.proto.body.
    """
    allt = " ".join(el.proto.body for el in sida.get("html"))
    assert "KURSAVSNITT" in allt
    assert "Urvalet följer kursen, inte hela lagen." in allt
```

Lägg till i `tests/test_lagrum.py`:

```python
def test_inget_kursavsnitt_ar_overifierat():
    """Slutgrind: allt som visas för studenten ska vara genomgånget.

    Flaggan betyder enligt registrets egen beskrivning osäkra
    paragrafgränser eller osäkert kursomfång. Sådant får inte renderas som
    ett påstående i lagkortet.
    """
    from utils.lagrum import lagrum_register

    oflaggade = [
        f"{lag.forkortning}: {a.beskrivning}"
        for lag in lagrum_register().values()
        for a in lag.kursavsnitt
        if a.verifiera
    ]
    assert oflaggade == [], "\n".join(oflaggade)
```

- [ ] **Step 2: Kör och se dem falla**

Kör: `python3.11 -m pytest tests/test_rattskartan_sida.py -k kursavsnitt tests/test_lagrum.py -k overifierat -v`
Förväntat: FAIL — sidan renderar ännu inte avsnitten. (Grindtestet i `test_lagrum.py` passerar redan om Task 5 är utförd.)

- [ ] **Step 3: Koppla in avsnitten på sidan**

I `sidor/16_Rattskartan.py`, ersätt anropet till `render_lagkort` (rad ~126-135):

```python
            for lag in lov.lagar:
                info = register[lag.forkortning]
                st.html(
                    render_lagkort(
                        forkortning=lag.forkortning,
                        namn=info.namn,
                        sfs=info.sfs,
                        beskrivning=lag.beskrivning,
                        nar=lag.nar,
                        url=info.lagen_nu_bas_url,
                        kursavsnitt=gruppera_kursavsnitt(info),
                        tackning=tackningstext(info),
                    )
                )
```

Lägg till importen bland de befintliga importerna överst i filen:

```python
from utils.lagkort_avsnitt import gruppera_kursavsnitt, tackningstext
```

- [ ] **Step 4: Kör testerna och se dem passera**

Kör: `python3.11 -m pytest tests/test_rattskartan_sida.py tests/test_lagrum.py -v`
Förväntat: PASS.

- [ ] **Step 5: Kör hela sviten**

Kör: `python3.11 -m pytest -q`
Förväntat: alla tester passerar.

- [ ] **Step 6: Granska i appen**

Kör: `python3.11 -m streamlit run Hem.py`

Öppna Rättskartan, fäll ut ett delområde och kontrollera:
- Kapitelindelad lag (KKöpL, BrB) visar kapitelrubriker med avsnitten under.
- Kapitellös lag (KöpL, LAS) visar en platt avsnittslista utan "kap.".
- Paragrafspannet är guld och länkar till rätt ställe på lagen.nu.
- Täckningsraden syns för kapitelindelade lagar, saknas för kapitellösa.
- Noten "Urvalet följer kursen, inte hela lagen." står under varje lista.

- [ ] **Step 7: Uppdatera dokumentationen**

I `APPGUIDE.md`, avsnitt 9 ("Flik 1 — Systemet"), lägg till efter stycket om områdesträdet:

```markdown
Varje lagkort visar lagens **kursavsnitt**: vilka paragrafintervall kursen
omfattar, med lagens egen rubrik för varje avsnitt och en djuplänk till
lagen.nu. För kapitelindelade lagar grupperas avsnitten under lagens egna
kapitelrubriker, hämtade ur `data/lagstruktur/`, och en täckningsrad anger
hur stor del av lagen kursen berör. Urvalet följer kursen, inte hela lagen,
och det står utskrivet under varje lista.
```

I `design_system.md`, avsnitt om taxonomigrafens visuella kanaler, lägg till:

```markdown
**Lagkortets kursavsnitt.** Paragrafspannet bär paragrafguld eftersom det är
ett lagrum; kapitelrubriken bär bläck eftersom den är struktur. Det är samma
regel som i avsnitt 1: guld betyder alltid lagrum, och kopplingen får inte
brytas av navigeringsfärger.
```

- [ ] **Step 8: Committa**

```bash
git add sidor/16_Rattskartan.py tests/test_rattskartan_sida.py tests/test_lagrum.py APPGUIDE.md design_system.md
git commit -m "feat: visa kursavsnitten på Rättskartan och stäng verifieringsgrinden

Lagkorten på Rättskartan visar nu kursens paragrafintervall per lag.
Ett grindtest vaktar att inget kursavsnitt bär verifiera-flaggan, så att
inget overifierat påstående kan nå studenten."
```

---

## Självgranskning

**Spec-täckning**

| Spec-krav | Uppgift |
|---|---|
| `scripts/hamta_lagstruktur.py`, återanvänder befintliga hämtningshjälpare | Task 2 |
| `data/lagstruktur/<sfs>.json`, hela lagen, två parallella listor | Task 2 |
| Positionell scan, h3-brus filtrerat på `^\d+ kap\.` | Task 1 |
| AvtL-specialfallet: kapitelrubriker med platta paragrafnycklar | Task 1, steg 2 (`test_avtl_har_platta_paragrafnycklar`) |
| Klassificeringen av de fjorton oinspekterade lagarna bekräftas av data | Task 2, steg 3 (`_form`-utskriften) |
| `utils/lagstruktur.py` med frusna dataklasser och strikt validering | Task 3 |
| Saknad fil degraderar, trasig fil kastar | Task 3 (`ladda_lagstruktur` returnerar tomt vid saknad katalog; `_bygg_struktur` kastar) |
| `verifiera_kursavsnitt.py`, fyra avvikelsetyper, rättar aldrig själv | Task 4 |
| Överskjutandetestet RED, sedan permanent spärr | Task 4, steg 5 |
| Mänsklig grind för de 78 flaggade avsnitten | Task 5 |
| `render_lagkort` med kursavsnitt, kapitelgruppering, täckningsrad | Task 6 |
| `§`/`§§`-regeln med eget test | Task 6, steg 1 |
| Guld enbart för lagrum | Task 6, steg 8 (CSS) |
| `html.escape` genomgående | Task 6, steg 5 (`test_lagkortet_escapar_avsnittsrubriker`) |
| Sidan skickar avsnitten | Task 7 |
| Grindtest: inget `verifiera: true` | Task 7, steg 1 |
| Fixturer, aldrig nätverk i tester | Task 1, steg 1 |

**Platshållare:** inga. Varje steg har körbara kommandon eller fullständig kod.

**Typkonsistens:** `Kapitelgrupp` och `Avsnittsrad` definieras i Task 6 och används i Task 6-7. `Avvikelse` och typkonstanterna definieras i Task 4 och används i Task 4-5. `Lagstruktur`, `Kapitel` och `Moment` definieras i Task 3 och används i Task 4. `extrahera_struktur` definieras i Task 1 och används i Task 2. Parsern returnerar `list[dict]` (skrivs direkt till JSON), medan läslagret returnerar frusna dataklasser med `tuple` — gränsen går vid filen och är avsiktlig.

**Känd risk:** Task 4:s överskjutandetest mättes till 25 avvikelser mot lagtextkorpusen. Strukturen täcker hela lagen, så siffran kan bli något annorlunda — färre om korpusen saknade paragrafer som faktiskt finns, fler om något avsnitt pekar på ett kapitel som inte existerar. Avvikelsen i siffran är inte ett fel i planen; listan i testutskriften är facit.
