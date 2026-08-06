# Lagrumsjakt: Alternativa sätt att ange lagrum — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let students write a lagrum using its full colloquial Swedish name or an established alternative abbreviation (e.g. `"36 § avtalslagen"`, `"3 § KKL"`), not just the registry's canonical abbreviation, and have it graded correctly in the lagrumsjakt tab and the Normfält direct-feedback.

**Architecture:** Add an explicit, hand-authored `aliaser` list to each of the 21 law entries in `data/lagrum.json`. Extend the existing case-insensitive abbreviation lookup in `utils/lagrum.py` to also index those aliases, with a fail-fast `ValueError` if two laws' aliases collide. No regex or UI changes: Swedish law names are single words, so they already fit the existing lagrum-citation patterns, and downstream code already normalizes to the canonical abbreviation before rendering.

**Tech Stack:** Python 3.11, pytest, no new dependencies.

## Global Constraints

- Aliases are **explicit, hand-authored data**, never derived by grammar rules (e.g. auto-appending `-en`/`-balken`) — 6 of the 21 laws are registered under a `"Lag om …"` title with no mechanical path to their real colloquial name. (Spec §"Design"/§"Icke-mål".)
- SFS-nummer (e.g. `"1915:218"`) is explicitly **out of scope** as a lagrum-citation form. (Spec §"Icke-mål".)
- Changing how `paragraf_till` ranges are compared in `ratta_lagrumsjakt` is explicitly **out of scope** — unrelated to alias matching. (Spec §"Icke-mål".)
- Alias collisions (two laws sharing an alias, or an alias equal to another law's abbreviation) must raise `ValueError` at the point the lookup map is built — fail fast, matching the existing pattern in `_validera_ra_lag`. (Spec §"Mål".)

---

## File Structure

- Modify `utils/lagrum.py`: `Lag` dataclass gets a new `aliaser: tuple[str, ...] = ()` field; `_validera_ra_lag` parses it; the abbreviation→canonical lookup (`_forkortning_gemener_karta`) is rebuilt on top of a new pure, directly-testable function `_bygg_alias_karta`.
- Modify `data/lagrum.json`: every law entry gets an `"aliaser"` array.
- Modify `tests/test_lagrum.py`: unit tests for alias parsing, alias-map collision detection, and end-to-end extraction/validation using real registry aliases.
- Modify `tests/test_quiz.py`: lagrumsjakt grading tests using alias-based answers.

---

### Task 1: `Lag.aliaser` field and parsing

**Files:**
- Modify: `utils/lagrum.py:51-60` (the `Lag` dataclass), `utils/lagrum.py:152-159` (`_validera_ra_lag`'s `return Lag(...)`)
- Test: `tests/test_lagrum.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `Lag.aliaser: tuple[str, ...]` (defaults to `()` when the raw JSON row has no `"aliaser"` key). `_validera_ra_lag(rad: dict) -> Lag` unchanged in signature, now also reads `rad.get("aliaser", [])`.

- [ ] **Step 1: Write the failing tests**

Add to the end of `tests/test_lagrum.py`:

```python
# --- Aliasfält på Lag ---------------------------------------------------

def test_validera_ra_lag_las_alias_falt():
    from utils.lagrum import _validera_ra_lag

    rad = {
        "forkortning": "TestL",
        "namn": "Testlag",
        "sfs": "2026:1",
        "kapitelindelad": False,
        "lagen_nu_bas_url": "https://lagen.nu/2026:1",
        "aliaser": ["testlagen", "TL"],
        "kursavsnitt": [],
    }
    lag = _validera_ra_lag(rad)
    assert lag.aliaser == ("testlagen", "TL")


def test_validera_ra_lag_alias_falt_default_tomt():
    from utils.lagrum import _validera_ra_lag

    rad = {
        "forkortning": "TestL",
        "namn": "Testlag",
        "sfs": "2026:1",
        "kapitelindelad": False,
        "lagen_nu_bas_url": "https://lagen.nu/2026:1",
        "kursavsnitt": [],
    }
    lag = _validera_ra_lag(rad)
    assert lag.aliaser == ()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_lagrum.py -k alias_falt -v`
Expected: FAIL with `TypeError: Lag.__init__() got an unexpected keyword argument` or `AttributeError: 'Lag' object has no attribute 'aliaser'` (the field doesn't exist yet).

- [ ] **Step 3: Add the field to the dataclass**

In `utils/lagrum.py`, replace:

```python
@dataclass(frozen=True)
class Lag:
    """En lag i registret med sina kursrelevanta avsnitt."""

    forkortning: str
    namn: str
    sfs: str
    kapitelindelad: bool
    lagen_nu_bas_url: str
    kursavsnitt: tuple[Kursavsnitt, ...]
```

with:

```python
@dataclass(frozen=True)
class Lag:
    """En lag i registret med sina kursrelevanta avsnitt."""

    forkortning: str
    namn: str
    sfs: str
    kapitelindelad: bool
    lagen_nu_bas_url: str
    kursavsnitt: tuple[Kursavsnitt, ...]
    aliaser: tuple[str, ...] = ()
```

- [ ] **Step 4: Parse the field in `_validera_ra_lag`**

In `utils/lagrum.py`, replace:

```python
    return Lag(
        forkortning=rad["forkortning"],
        namn=rad["namn"],
        sfs=rad["sfs"],
        kapitelindelad=bool(rad["kapitelindelad"]),
        lagen_nu_bas_url=rad["lagen_nu_bas_url"],
        kursavsnitt=tuple(avsnitt),
    )
```

with:

```python
    return Lag(
        forkortning=rad["forkortning"],
        namn=rad["namn"],
        sfs=rad["sfs"],
        kapitelindelad=bool(rad["kapitelindelad"]),
        lagen_nu_bas_url=rad["lagen_nu_bas_url"],
        kursavsnitt=tuple(avsnitt),
        aliaser=tuple(rad.get("aliaser", [])),
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_lagrum.py -k alias_falt -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Run full test suite to check for regressions**

Run: `pytest tests/test_lagrum.py tests/test_quiz.py -v`
Expected: all PASS (adding an optional field with a default doesn't change existing behavior)

- [ ] **Step 7: Commit**

```bash
git add utils/lagrum.py tests/test_lagrum.py
git commit -m "feat: lägg till aliaser-fält på Lag för alternativa lagrumsnamn"
```

---

### Task 2: Alias-aware lookup map with collision detection

**Files:**
- Modify: `utils/lagrum.py:187-190` (`_forkortning_gemener_karta`)
- Test: `tests/test_lagrum.py`

**Interfaces:**
- Consumes: `Lag.forkortning`, `Lag.aliaser` (from Task 1); `lagrum_register() -> dict[str, Lag]` (existing, unchanged).
- Produces: `_bygg_alias_karta(register: dict[str, Lag]) -> dict[str, str]` — pure function, new. Raises `ValueError` if an alias collides with another law's forkortning/alias. `_forkortning_gemener_karta() -> dict[str, str]` — same signature and `@lru_cache` as before, now built on top of `_bygg_alias_karta(lagrum_register())`. `_normalisera_forkortning` and `extrahera_lagrum`'s `_godtagen` (both already call `_forkortning_gemener_karta()`) get alias support automatically, no changes needed in either.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_lagrum.py`:

```python
# --- _bygg_alias_karta --------------------------------------------------

def test_bygg_alias_karta_loser_alias_till_forkortning():
    from utils.lagrum import Lag, _bygg_alias_karta

    register = {
        "AvtL": Lag(
            forkortning="AvtL",
            namn="Testnamn",
            sfs="1915:218",
            kapitelindelad=False,
            lagen_nu_bas_url="https://lagen.nu/1915:218",
            kursavsnitt=(),
            aliaser=("avtalslagen",),
        ),
    }
    karta = _bygg_alias_karta(register)
    assert karta["avtalslagen"] == "AvtL"
    assert karta["avtl"] == "AvtL"


def test_bygg_alias_karta_kastar_vid_kolliderande_alias():
    from utils.lagrum import Lag, _bygg_alias_karta

    register = {
        "AvtL": Lag(
            forkortning="AvtL",
            namn="Testnamn A",
            sfs="1915:218",
            kapitelindelad=False,
            lagen_nu_bas_url="https://lagen.nu/1915:218",
            kursavsnitt=(),
            aliaser=("dubbel",),
        ),
        "SkL": Lag(
            forkortning="SkL",
            namn="Testnamn B",
            sfs="1972:207",
            kapitelindelad=True,
            lagen_nu_bas_url="https://lagen.nu/1972:207",
            kursavsnitt=(),
            aliaser=("dubbel",),
        ),
    }
    with pytest.raises(ValueError, match="dubbel"):
        _bygg_alias_karta(register)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_lagrum.py -k bygg_alias_karta -v`
Expected: FAIL with `ImportError: cannot import name '_bygg_alias_karta'`

- [ ] **Step 3: Implement `_bygg_alias_karta` and rewire `_forkortning_gemener_karta`**

In `utils/lagrum.py`, replace:

```python
@lru_cache(maxsize=1)
def _forkortning_gemener_karta() -> dict[str, str]:
    """Karta från gemener till registrets kanoniska skiftläge, t.ex. 'skl' -> 'SkL'."""
    return {forkortning.lower(): forkortning for forkortning in giltiga_forkortningar()}
```

with:

```python
def _bygg_alias_karta(register: dict[str, Lag]) -> dict[str, str]:
    """Bygg en gemena-till-kanonisk-karta ur ett register.

    Nyckel är förkortningen eller ett alias i gemener, värdet lagens
    kanoniska förkortning. Kastar ValueError om två lagar delar samma
    sökord (skiftlägesokänsligt) i stället för att tyst låta
    registrets iterationsordning avgöra vilken lag som "vinner".
    """
    karta: dict[str, str] = {}
    for lag in register.values():
        for ord_ in (lag.forkortning, *lag.aliaser):
            nyckel = ord_.lower()
            if nyckel in karta and karta[nyckel] != lag.forkortning:
                raise ValueError(
                    f"Alias '{ord_}' är tvetydigt: pekar på både "
                    f"'{karta[nyckel]}' och '{lag.forkortning}'."
                )
            karta[nyckel] = lag.forkortning
    return karta


@lru_cache(maxsize=1)
def _forkortning_gemener_karta() -> dict[str, str]:
    """Karta från gemener (förkortning eller alias) till kanonisk förkortning."""
    return _bygg_alias_karta(lagrum_register())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_lagrum.py -k bygg_alias_karta -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Run full test suite to check for regressions**

Run: `pytest tests/test_lagrum.py tests/test_quiz.py -v`
Expected: all PASS. `data/lagrum.json` has no `aliaser` fields yet (Task 3 adds them), so `_bygg_alias_karta(lagrum_register())` runs with every `Lag.aliaser == ()` — behaviorally identical to the old one-liner.

- [ ] **Step 6: Commit**

```bash
git add utils/lagrum.py tests/test_lagrum.py
git commit -m "feat: alias-medveten lagrumsuppslagning med kollisionskontroll"
```

---

### Task 3: Add the alias table to `data/lagrum.json`

**Files:**
- Modify: `data/lagrum.json`

**Interfaces:**
- Consumes: `"aliaser"` key read by `_validera_ra_lag` (Task 1).
- Produces: real alias data consumed by Tasks 4 and 5's tests.

- [ ] **Step 1: Run this script once to inject the alias table**

This edits the file in place, inserting `"aliaser"` right after `"lagen_nu_bas_url"` in each of the 21 entries, preserving the existing field order and formatting otherwise. Run from the repo root:

```bash
python3 <<'PYEOF'
import json
from pathlib import Path

ALIASER = {
    "AvtL": ["avtalslagen"],
    "SkbrL": ["skuldebrevslagen"],
    "ÄB": ["ärvdabalken"],
    "BrB": ["brottsbalken"],
    "JB": ["jordabalken"],
    "SkL": ["skadeståndslagen"],
    "HBL": ["handelsbolagslagen"],
    "UB": ["utsökningsbalken"],
    "LAS": ["anställningsskyddslagen"],
    "KonkL": ["konkurslagen"],
    "ÄktB": ["äktenskapsbalken"],
    "KöpL": ["köplagen"],
    "FB": ["föräldrabalken"],
    "RB": ["rättegångsbalken"],
    "SamboL": ["sambolagen"],
    "ABL": ["aktiebolagslagen"],
    "MFL": ["marknadsföringslagen"],
    "KKöpL": ["konsumentköplagen", "KKL"],
    "GFL": ["godtrosförvärvslagen"],
    "LFF": ["framtidsfullmaktslagen"],
    "PreskL": ["preskriptionslagen", "PreskrL"],
}

path = Path("data/lagrum.json")
data = json.loads(path.read_text(encoding="utf-8"))

sedda = set()
for lag in data["lagar"]:
    fk = lag["forkortning"]
    if fk not in ALIASER:
        raise SystemExit(f"Saknar aliaser för {fk!r} i ALIASER-tabellen.")
    sedda.add(fk)
    ny_lag = {}
    for nyckel, varde in lag.items():
        ny_lag[nyckel] = varde
        if nyckel == "lagen_nu_bas_url":
            ny_lag["aliaser"] = ALIASER[fk]
    lag.clear()
    lag.update(ny_lag)

saknas = set(ALIASER) - sedda
if saknas:
    raise SystemExit(f"ALIASER innehåller okända förkortningar: {saknas}")

path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Klart:", len(sedda), "lagar uppdaterade.")
PYEOF
```

Expected output: `Klart: 21 lagar uppdaterade.`

- [ ] **Step 2: Sanity-check the diff**

Run: `git diff data/lagrum.json | head -40`

Expected: the `AvtL` entry gains a line `"aliaser": ["avtalslagen"],` immediately after its `"lagen_nu_bas_url"` line, with no other lines changed for that entry.

- [ ] **Step 3: Validate the file is still well-formed JSON**

Run: `python3 -m json.tool data/lagrum.json > /dev/null && echo OK`
Expected: `OK`

- [ ] **Step 4: Document the field**

In `data/lagrum.json`, append a sentence to the existing `"_beskrivning"` value (the long string at the top of the file), right after its current final sentence. Replace:

```
"...inte att kursens omfång är pedagogiskt rätt avvägt -- den bedömningen görs av kursansvarig."
```

with:

```
"...inte att kursens omfång är pedagogiskt rätt avvägt -- den bedömningen görs av kursansvarig. Fältet \"aliaser\" listar andra sätt studenter kan skriva lagen på (fullt vardagligt namn, etablerade alternativa förkortningar) och är handförfattat, inte grammatiskt härlett -- se docs/superpowers/specs/2026-08-06-lagrumsjakt-alias-matching-design.md."
```

(Use the Edit tool for this — it's a single string replacement inside the `_beskrivning` value.)

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/test_lagrum.py tests/test_quiz.py -v`
Expected: all PASS, including `test_register_laddas_med_21_lagar` (count unaffected) and the Task 2 collision test (real data has no colliding aliases — if this fails, it means two laws in `ALIASER` accidentally share a value; fix the table before proceeding).

- [ ] **Step 6: Commit**

```bash
git add data/lagrum.json
git commit -m "feat: alias-tabell för kursens 21 lagar (fulla namn och alt-förkortningar)"
```

---

### Task 4: End-to-end extraction/validation tests

**Files:**
- Test: `tests/test_lagrum.py`

**Interfaces:**
- Consumes: `extrahera_lagrum`, `validera_lagrum`, `lagen_nu_url` (all existing, unchanged signatures), real alias data from Task 3.

- [ ] **Step 1: Write the tests**

Add to `tests/test_lagrum.py`:

```python
# --- Alias: fulla lagnamn och alternativa förkortningar mot riktiga registret

@pytest.mark.parametrize(
    "text,forkortning",
    [
        ("36 § avtalslagen", "AvtL"),
        ("avtalslagen 36 §", "AvtL"),
        ("1 kap. 1 § brottsbalken", "BrB"),
        ("brottsbalken 1 kap. 1 §", "BrB"),
        ("3 § köplagen", "KöpL"),
        ("3 kap. 1 § KKL", "KKöpL"),
        ("10 § PreskrL", "PreskL"),
    ],
)
def test_extrahera_kant_alias_normaliseras_till_forkortning(text, forkortning):
    (ref,) = extrahera_lagrum(text)
    assert ref.forkortning == forkortning


@pytest.mark.parametrize(
    "text",
    ["36 § AVTALSLAGEN", "36 § Avtalslagen", "avtalslagen 36 §"],
)
def test_extrahera_alias_skiftlagesokansligt(text):
    (ref,) = extrahera_lagrum(text)
    assert ref.forkortning == "AvtL"


def test_validera_verifierad_med_fullt_lagnamn():
    assert validera_lagrum("36 § avtalslagen") == STATUS_VERIFIERAD


def test_validera_verifierad_med_alternativ_forkortning():
    assert validera_lagrum("3 kap. 1 § KKL") == STATUS_VERIFIERAD


def test_lagen_nu_url_med_fullt_lagnamn_ar_samma_som_forkortning():
    assert lagen_nu_url("36 § avtalslagen") == lagen_nu_url("36 § AvtL")
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_lagrum.py -k "alias" -v`
Expected: all PASS. If any FAIL with a mismatch, check the alias spelling in the Task 3 `ALIASER` table against the parametrized text (a stray capital or missing word is the usual cause — `_forkortning_gemener_karta` lookups are case-insensitive but must match on the full word).

- [ ] **Step 3: Run the full test suite**

Run: `pytest tests/ -v`
Expected: all PASS, no regressions.

- [ ] **Step 4: Commit**

```bash
git add tests/test_lagrum.py
git commit -m "test: extrahera/validera lagrum via fullt namn och alt-förkortning"
```

---

### Task 5: Lagrumsjakt grading with alias-based answers

**Files:**
- Test: `tests/test_quiz.py`

**Interfaces:**
- Consumes: `ratta_lagrumsjakt(jakt: Lagrumsjakt, studentens_svar: str) -> LagrumsjaktResultat` (existing, unchanged), `Lagrumsjakt` (existing), real alias data from Task 3.

- [ ] **Step 1: Write the tests**

Add to `tests/test_quiz.py`:

```python
def test_lagrumsjakt_accepterar_fullt_lagnamn_mot_forkortningsfacit():
    # Facit är skrivet med förkortning, studenten svarar med fullt namn.
    jakt = Lagrumsjakt(id="lj8", situation="?", facit_lagrum=("4 § AvtL",))
    res = ratta_lagrumsjakt(jakt, "Jag tror det är 4 § avtalslagen.")
    assert res.korrekt is True
    assert res.status == STATUS_VERIFIERAD


def test_lagrumsjakt_accepterar_alternativ_forkortning():
    jakt = Lagrumsjakt(id="lj9", situation="?", facit_lagrum=("3 kap. 1 § KKöpL",))
    res = ratta_lagrumsjakt(jakt, "3 kap. 1 § KKL")
    assert res.korrekt is True
    assert res.status == STATUS_VERIFIERAD
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_quiz.py -k alias -v`
Expected: both PASS. `ratta_lagrumsjakt` compares canonical keys (`forkortning, kapitel, paragraf`) via `utils.quiz._nyckel`, which already calls `extrahera_lagrum` — so it inherits alias support from Tasks 1–3 with no changes to `utils/quiz.py`.

- [ ] **Step 3: Run the full test suite**

Run: `pytest tests/ -v`
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_quiz.py
git commit -m "test: lagrumsjakt godkänner svar via alias mot förkortningsfacit"
```

---

## Final Verification

- [ ] Run `pytest tests/ -v` — full suite green.
- [ ] Manually open the Streamlit app (`streamlit run streamlit_app.py`), go to Juridisk metod → Lagrumsjakt tab, and answer question `jm-lj-1` ("Du vill visa att köplagen är dispositiv...") with `"3 § köplagen"` instead of `"3 § KöpL"` — confirm it's marked correct with a green, clickable lagen.nu chip.
