# UX-omdesign, etapp 1 (hög effekt / låg insats) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Genomför de tolv åtgärderna i avsnitt 9, "Hög effekt / låg insats", i
`docs/superpowers/specs/2026-08-06-ux-omdesign-design.md` — så att appen ger
studenten ett sant nästa steg, gör RNTS synligt, och slutar läcka ikoner,
död kod och tysta datafel.

**Architecture:** Ingen omstrukturering av informationsarkitekturen i den här
etappen. Allt arbete sker i befintliga moduler: ren logik läggs i `utils/navigation.py`
(Streamlit-fritt, enhetstestbart), presentation i `utils/ui.py`, och sidflödet i
`utils/modulvy.py` och `sidor/`. Nya funktioner är rena funktioner som tar sitt
tillstånd som argument i stället för att läsa `st.session_state` direkt, så att de
kan testas utan Streamlit-runtime.

**Tech Stack:** Python 3.11+, Streamlit ≥1.37, pytest, ruff. Inga nya beroenden.

## Global Constraints

- **Inga nya beroenden.** `requirements.txt` ändras inte. Enbart Streamlit.
- **Inga ikoner, emoji eller dekorativa glyfer** någonstans i appen. Enda
dokumenterade undantag: `page_icon="⚖️"` i `streamlit_app.py` (webbläsarflikens
identitet). Nivåer och tillstånd bärs av indrag, storlek, färgstyrka och CSS-form.
- **Guld (**`--guld`**,** `#B8860B`**) betyder alltid lagrum**, aldrig något annat. Aldrig i
navigering.
- **All användarsynlig text på svenska**, du-tilltal, inga utropstecken i
bedömningar. Fel formuleras handlingsorienterat, aldrig skuldbeläggande.
- **Maxbredd 46rem** för löptext. Brödtext 17px/1.65.
- **Deterministiskt först:** ingen ändring får göra en LLM nödvändig för något som
i dag fungerar utan den.
- **Filstorlek:** håll filer under 800 rader. `utils/ui.py` är i dag 768 rader —
växer den över 800 i en task, bryt ut den CSS-strängen enligt Task 5.
- **Testkommando:** `python3 -m pytest -q`. Hela sviten (798 test vid start) ska
vara grön före varje commit.
- **Lintkommando:** `python3 -m ruff check .` enligt `ruff.toml`.
- **Committa efter varje grön task**, meddelandeformat `<type>: <beskrivning>` på
svenska (feat, fix, refactor, docs, test, chore).



## Filstruktur


| Fil                            | Ansvar                                                                        | Tasks          |
| ------------------------------ | ----------------------------------------------------------------------------- | -------------- |
| `utils/navigation.py`          | Navigeringsträd + kursordning + startsidans CTA-mål. Ren data.                | 1              |
| `utils/framsteg.py` (ny)       | Ren funktion: vilka moduler är påbörjade? Läser böckerna, inte session_state. | 1, 8           |
| `utils/ui.py`                  | Delade komponenter, CSS-tokens, sidopanel, statuspanel.                       | 4, 5, 6, 7, 10 |
| `utils/rnts.py` (ny)           | RNTS-stegens namn och vilken aktivitet som tränar vilket steg.                | 9              |
| `utils/modulvy.py`             | Modulsidans tre flikar, facitgrindar, TRÄNAR-etiketter, ingress.              | 2, 3, 9, 10    |
| `sidor/0_Hem.py`               | Startsidans CTA, framsteg, tomt tillstånd.                                    | 1, 8           |
| `sidor/11_Kunskapsutmaning.py` | Glyf bort, justeringshack bort.                                               | 4              |
| `sidor/16_Rattskartan.py`      | Glyfer bort i två Rensa-knappar.                                              | 4              |
| `tests/test_sprak.py`          | Språk-QA. Utökas med glyfvakt och `sidor/`.                                   | 4              |
| `tests/test_navigation.py`     | Kursordning, nästa modul, CTA-mål.                                            | 1              |
| `tests/test_framsteg.py` (ny)  | Påbörjade moduler.                                                            | 1              |
| `tests/test_rnts.py` (ny)      | RNTS-etiketter per aktivitet.                                                 | 9              |
| `tests/test_ui.py`             | Tokens, statuspanel, aktiv rubrikkedja.                                       | 5, 6, 7        |
| `tests/test_modulvy.py` (ny)   | Facitgrindar.                                                                 | 2, 3           |
| `design_system.md`             | Uppdateras i den task som ändrar en dokumenterad regel.                       | 4, 5, 6, 9     |


**Ordning.** Task 1 och 4 först (de bär mest värde och minst risk). Task 5 före 6
och 7, eftersom de senare använder tokens. Task 9 sist av de funktionella, eftersom
den rör flest anropsställen.

---



## Task 1: Kursordning och ett sant nästa steg

Spec: avsnitt 9 punkt 1, avsnitt 3 punkt 3, invändning 11.6.

I dag pekar `cta_mal()` mot senast besökta modul. En student som råkar öppna
Associationsrätt skickas dit för alltid. Kursordningen finns redan i `NAV_TRAD` men
används aldrig.

**Files:**

- Modify: `utils/navigation.py` (dataklassen `Modul` rad 26–40, `cta_mal` rad 227–240)
- Create: `utils/framsteg.py`
- Create: `tests/test_framsteg.py`
- Modify: `tests/test_navigation.py` (befintliga `cta_mal`-test rad 149–172)
- Modify: `sidor/0_Hem.py` (`_render_cta` rad 72–92)

**Interfaces:**

- Produces: `Modul.kursmodul: bool` (default `False`); `kursmoduler() -> tuple[Modul, ...]`;
`nasta_kursmodul(pabborjade: frozenset[str]) -> Modul | None`;
`cta_mal(senast_besokt: str | None, pabborjade: frozenset[str] = frozenset()) -> CtaMal`
där `CtaMal` får det nya fältet `skal: str`;
`utils.framsteg.pabborjade_moduler() -> frozenset[str]`.
- Consumes: `utils.quiz.alla_resultat() -> dict[str, tuple[int, int]]` och
`utils.export.genomforda_case() -> dict[str, tuple[str, ...]]`. Båda är nycklade på
modulens **visningsnamn** ("Avtalsrätt"), identiskt med `byggda_namn()`.

- [ ] **Step 1: Skriv det failande testet för kursmoduler och ordning**

Lägg till i `tests/test_navigation.py`:

```python
from utils.navigation import kursmoduler, nasta_kursmodul


def test_kursmoduler_foljer_tradets_ordning():
    namn = [m.namn for m in kursmoduler()]
    assert namn[0] == "Juridisk metod"
    assert namn.index("Personrätt") < namn.index("Avtalsrätt")
    assert namn.index("Avtalsrätt") < namn.index("Skadeståndsrätt")


def test_kursmoduler_utesluter_verktygssidor():
    namn = {m.namn for m in kursmoduler()}
    for verktyg in ("Hem", "Rättskartan", "Kunskapstest", "Kunskapskarta",
                    "Kunskapsutmaning"):
        assert verktyg not in namn


def test_kursmoduler_matchar_scenariodatan():
    """Vakt mot drift: varje kursmodul måste ha övningsinnehåll, och omvänt."""
    from utils.scenarier import ladda_modul, lista_moduler

    ur_data = {ladda_modul(stem).modul for stem in lista_moduler()}
    ur_tradet = {m.namn for m in kursmoduler()}
    assert ur_tradet == ur_data


def test_nasta_kursmodul_utan_framsteg_ger_forsta():
    assert nasta_kursmodul(frozenset()).namn == "Juridisk metod"


def test_nasta_kursmodul_hoppar_over_paborjade():
    nasta = nasta_kursmodul(frozenset({"Juridisk metod", "Personrätt"}))
    assert nasta.namn == "Allmän förmögenhetsrätt"


def test_nasta_kursmodul_alla_paborjade_ger_none():
    alla = frozenset(m.namn for m in kursmoduler())
    assert nasta_kursmodul(alla) is None
```

- [ ] **Step 2: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_navigation.py -q -k "kursmodul or nasta_kursmodul"`
Expected: FAIL med `ImportError: cannot import name 'kursmoduler'`

- [ ] **Step 3: Lägg till fältet och funktionerna**

I `utils/navigation.py`, utöka `Modul`:

```python
@dataclass(frozen=True)
class Modul:
    """Ett löv i trädet: en modulsida, byggd eller planerad.

    ``sida`` är sökvägen relativt projektroten, t.ex. "sidor/2_Avtalsratt.py".
    None betyder att modulen är planerad men ännu inte byggd.

    ``kursmodul`` skiljer kursens rättsområden (de som har övningsinnehåll i
    data/scenarier och därmed en plats i kursordningen) från verktygssidor som
    Hem, Rättskartan och Kunskapskarta. Startsidans "nästa steg" rör sig bara
    genom kursmoduler; tests/test_navigation.py vaktar att mängden är exakt
    densamma som scenariodatans moduler.
    """

    namn: str
    sida: str | None = None
    kursmodul: bool = False
```

Sätt `kursmodul=True` på exakt dessa tolv i `NAV_TRAD` (låt övriga vara orörda):
Juridisk metod, Personrätt, Allmän förmögenhetsrätt, Avtalsrätt,
Köp- och konsumenträtt, Fastighetsrätt, Skadeståndsrätt, Arbetsrätt,
Associationsrätt, Familje- och successionsrätt, Straff- och processrätt,
Fordringsrätt. Exempel på formen:

```python
            Modul("Juridisk metod", "sidor/1_Juridisk_metod.py", kursmodul=True),
```

Lägg till efter `sida_for_namn`:

```python
def kursmoduler(noder: tuple[Nod, ...] = NAV_TRAD) -> tuple[Modul, ...]:
    """Kursens rättsområdesmoduler i trädets ordning.

    Trädets ordning är kursbokens kapitelordning, så den här tupeln ÄR
    kursordningen. Verktygssidor (Hem, Rättskartan, Kunskapstest,
    Kunskapskarta, Kunskapsutmaning) ingår inte.
    """
    return tuple(m for m in alla_moduler(noder) if m.kursmodul and m.sida)


def nasta_kursmodul(pabborjade: frozenset[str]) -> Modul | None:
    """Första kursmodulen studenten ännu inte börjat på, i kursordning.

    None betyder att alla kursmoduler är påbörjade — då har startsidan inget
    nytt att föreslå och faller tillbaka på att återuppta.
    """
    for modul in kursmoduler():
        if modul.namn not in pabborjade:
            return modul
    return None
```

- [ ] **Step 4: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_navigation.py -q -k "kursmodul or nasta_kursmodul"`
Expected: PASS (6 test)

- [ ] **Step 5: Skriv det failande testet för påbörjade moduler**

Skapa `tests/test_framsteg.py`:

```python
"""Test för utils.framsteg: vilka kursmoduler studenten har börjat på.

Funktionen är ren och tar böckerna som argument, så den kan testas utan
Streamlit-runtime. Wrappern som läser session_state testas inte här.
"""

from __future__ import annotations

from utils.framsteg import pabborjade_ur_bocker


def test_tom_bok_ger_tom_mangd():
    assert pabborjade_ur_bocker({}, {}) == frozenset()


def test_quizresultat_raknas_som_paborjad():
    assert pabborjade_ur_bocker({"Avtalsrätt": (2, 3)}, {}) == frozenset({"Avtalsrätt"})


def test_genomfort_case_raknas_som_paborjad():
    assert pabborjade_ur_bocker({}, {"Personrätt": ("p-1",)}) == frozenset({"Personrätt"})


def test_bada_kallorna_slas_samman():
    resultat = pabborjade_ur_bocker(
        {"Avtalsrätt": (1, 1)}, {"Personrätt": ("p-1",)}
    )
    assert resultat == frozenset({"Avtalsrätt", "Personrätt"})


def test_tomma_poster_raknas_inte():
    """En modul med noll besvarade frågor och noll fall är inte påbörjad."""
    assert pabborjade_ur_bocker({"Avtalsrätt": (0, 0)}, {"Personrätt": ()}) == frozenset()
```

- [ ] **Step 6: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_framsteg.py -q`
Expected: FAIL med `ModuleNotFoundError: No module named 'utils.framsteg'`

- [ ] **Step 7: Skriv utils/framsteg.py**

```python
"""Studentens framsteg, sammanställt ur sessionens två böcker.

Ansvarar för en enda fråga: vilka kursmoduler har studenten börjat på? Svaret
driver startsidans "nästa steg" (utils.navigation.nasta_kursmodul).

Den rena funktionen ``pabborjade_ur_bocker`` tar böckerna som argument och kan
därför enhetstestas utan Streamlit. ``pabborjade_moduler`` är det tunna skalet
som hämtar dem ur session_state.

Framstegen är sessionsbundna: stänger studenten fliken är de borta. Det sägs
rent ut i UI:t (sidor/0_Hem.py) i stället för att antydas i en rubrik.
"""

from __future__ import annotations


def pabborjade_ur_bocker(
    quizresultat: dict[str, tuple[int, int]],
    case_bok: dict[str, tuple[str, ...]],
) -> frozenset[str]:
    """Modulnamnen studenten har registrerat något arbete på.

    ``quizresultat`` är utils.quiz.alla_resultat(): modulnamn -> (rätt, besvarade).
    ``case_bok`` är utils.export.genomforda_case(): modulnamn -> case-id.
    Båda är nycklade på modulens visningsnamn, identiskt med
    utils.navigation.byggda_namn().

    En post med noll besvarade frågor eller noll genomförda fall räknas inte:
    böckerna kan innehålla tomma poster efter en avbruten interaktion, och de
    ska inte få startsidan att hoppa över en modul studenten inte gjort.
    """
    paborjade = {modul for modul, (_ratt, besvarade) in quizresultat.items() if besvarade}
    paborjade |= {modul for modul, ids in case_bok.items() if ids}
    return frozenset(paborjade)


def pabborjade_moduler() -> frozenset[str]:
    """Påbörjade moduler i den här sessionen. Tom mängd om något går fel."""
    from utils.export import genomforda_case
    from utils.quiz import alla_resultat

    try:
        return pabborjade_ur_bocker(alla_resultat(), genomforda_case())
    except Exception:  # noqa: BLE001 (startsidan ska aldrig krascha på framsteg)
        return frozenset()
```

- [ ] **Step 8: Kör testet och se att det passerar**



Run: `python3 -m pytest tests/test_framsteg.py -q`
Expected: PASS (5 test)

- [ ] **Step 9: Skriv om cta_mal-testen till det nya beteendet**

Ersätt de befintliga `cta_mal`-testen i `tests/test_navigation.py` (rad 149–172).
Beteendet ändras avsiktligt: nästa modul i kursordning väger tyngre än senast
besökta, och `CtaMal` bär ett skäl som startsidan visar.

```python
# --- cta_mal -------------------------------------------------------------------

def test_cta_mal_ny_session_ger_kursens_forsta_modul():
    mal = cta_mal(None)
    assert mal.titel == "Juridisk metod"
    assert mal.sida == "sidor/1_Juridisk_metod.py"
    assert mal.ateruppta is False
    assert mal.skal


def test_cta_mal_foredrar_nasta_i_kursordning_framfor_senast_besokt():
    """Kärnan i ändringen: senast besökta modul får inte låsa studenten."""
    mal = cta_mal("Associationsrätt", pabborjade=frozenset({"Juridisk metod"}))
    assert mal.titel == "Personrätt"
    assert mal.ateruppta is False


def test_cta_mal_alla_kursmoduler_paborjade_ger_ateruppta():
    from utils.navigation import kursmoduler

    alla = frozenset(m.namn for m in kursmoduler())
    mal = cta_mal("Avtalsrätt", pabborjade=alla)
    assert mal.titel == "Avtalsrätt"
    assert mal.ateruppta is True


def test_cta_mal_okand_senast_besokt_faller_tillbaka_pa_kursordning():
    alla = frozenset(m.namn for m in kursmoduler())
    mal = cta_mal("Modul som inte längre finns", pabborjade=alla)
    assert mal.titel == FALLBACK_CTA_TITEL
    assert mal.sida == FALLBACK_CTA_SIDA
    assert mal.ateruppta is False
```

Säkerställ att `kursmoduler`, `FALLBACK_CTA_TITEL` och `FALLBACK_CTA_SIDA` är
importerade högst upp i filen.

- [ ] **Step 10: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_navigation.py -q -k cta_mal`
Expected: FAIL — `cta_mal() got an unexpected keyword argument 'pabborjade'`

- [ ] **Step 11: Skriv om cta_mal**

Ersätt `CtaMal` och `cta_mal` i `utils/navigation.py`:

```python
@dataclass(frozen=True)
class CtaMal:
    """Startsidans call-to-action: vart den pekar och varför.

    ``skal`` är en mening som visas i kortet, så att en student som vill något
    annat gör ett informerat val i stället för att känna sig olydig.
    """

    titel: str
    sida: str
    ateruppta: bool
    skal: str = ""


def cta_mal(
    senast_besokt: str | None,
    pabborjade: frozenset[str] = frozenset(),
) -> CtaMal:
    """Bestäm startsidans call-to-action.

    Föredrar **nästa ej påbörjade kursmodul i kursordning**, eftersom det är den
    enda av de två signalerna som faktiskt leder studenten framåt: senast
    besökta modul kan vara en modul studenten råkade öppna, och pekar man dit
    varje gång låses studenten fast där. Kursordningen är trädets ordning i
    NAV_TRAD, som följer kursbokens kapitelordning.

    Är alla kursmoduler påbörjade finns inget nytt att föreslå, och vi återupptar
    den senast besökta modulen i stället. Går den inte att slå upp (ny session,
    eller ett sparat namn som inte längre finns efter en ombyggnad av trädet)
    faller vi tillbaka på FALLBACK_CTA_TITEL/-SIDA.
    """
    nasta = nasta_kursmodul(pabborjade)
    if nasta is not None and nasta.sida:
        return CtaMal(
            nasta.namn,
            nasta.sida,
            False,
            "Nästa i kursen efter det du redan gjort.",
        )

    if senast_besokt:
        sida = sida_for_namn(senast_besokt)
        if sida:
            return CtaMal(
                senast_besokt,
                sida,
                True,
                "Du har varit inne i alla kursmoduler. Fortsätt där du var.",
            )

    return CtaMal(
        FALLBACK_CTA_TITEL,
        FALLBACK_CTA_SIDA,
        False,
        "Kursens första modul. Börja här om du är ny.",
    )
```

Notera: `nasta_kursmodul` definieras ovanför `cta_mal` i filen, så ingen
framåtreferens uppstår.

- [ ] **Step 12: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_navigation.py tests/test_framsteg.py -q`
Expected: PASS

- [ ] **Step 13: Koppla in det på startsidan**

Ersätt `_render_cta` i `sidor/0_Hem.py`:

```python
def _render_cta() -> None:
    """Startsidans enda call-to-action: ett kort som svarar på vad och varför.

    Modulerna nås i övrigt uteslutande via sidopanelen: en andra länklista
    här skulle bara upprepa den, i en annan ordning, med olika omfattning.
    """
    try:
        senast = st.session_state.get(SENAST_BESOKT_NYCKEL)
    except Exception:
        senast = None
    mal = cta_mal(senast, pabborjade_moduler())

    st.html(
        section_heading(
            "NÄSTA STEG",
            "Fortsätt där du var" if mal.ateruppta else "Kom igång",
        )
    )
    if mal.skal:
        st.caption(mal.skal)
    prefix = "Fortsätt" if mal.ateruppta else "Börja med"
    if st.button(f"{prefix}: {mal.titel} →", type="primary"):
        st.switch_page(mal.sida)

    # Den sekundära vägen: har studenten en pågående modul som inte är målet,
    # ska den vara nåbar utan att konkurrera med den primära knappen.
    if not mal.ateruppta and senast and senast != mal.titel:
        sida = sida_for_namn(senast)
        if sida:
            st.page_link(sida, label=f"Fortsätt där du var: {senast}")
```

Uppdatera importerna i `sidor/0_Hem.py`:

```python
from utils.framsteg import pabborjade_moduler
from utils.navigation import SENAST_BESOKT_NYCKEL, cta_mal, sida_for_namn
```

- [ ] **Step 14: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS, inga lintfel

- [ ] **Step 15: Commit**

```bash
git add utils/navigation.py utils/framsteg.py sidor/0_Hem.py \
        tests/test_navigation.py tests/test_framsteg.py
git commit -m "feat: startsidans nästa steg följer kursordningen i stället för senaste besök"
```

---



## Task 2: Facitexpandern i lagrumsjakten försvinner (verklig bugg)

Spec: avsnitt 5 "Lagrumsjakten", avsnitt 9 punkt 3.

`with st.expander("Visa facit")` ligger inuti `if st.button("Rätta")`-blocket
(`utils/modulvy.py:472`). Facit renderas därför bara i den rerun där knappen
trycktes och försvinner vid nästa interaktion — studenten tappar facit genom att
klicka någon annanstans på sidan.

**Files:**

- Modify: `utils/modulvy.py` (`_rendera_jaktfraga` rad 450–474)
- Create: `tests/test_modulvy.py`

**Interfaces:**

- Consumes: `utils.scenarier.Lagrumsjakt`, `utils.quiz.ratta_lagrumsjakt`.
- Produces: `_jakt_ratta_nyckel(modul: str, jakt_id: str) -> str` — sessionsnyckeln
som minns att studenten har rättat. Task 3 använder samma mönster.

- [ ] **Step 1: Skriv det failande testet**

Skapa `tests/test_modulvy.py`:

```python
"""Test för modulsidans grindar: facit ska överleva en rerun och kosta ett försök.

Testen läser källkoden i stället för att köra Streamlit, eftersom felet är
strukturellt: expanderns indrag avgör om den bara renderas i den rerun där
knappen trycktes. AppTest hade inte fångat det utan en andra interaktion.
"""

from __future__ import annotations

import inspect

from utils import modulvy


def test_jaktfacit_ligger_inte_i_knappblocket():
    """Facit får inte renderas inuti `if st.button("Rätta")`.

    Ligger den där försvinner den vid nästa rerun. Vi kontrollerar att
    expanderraden har mindre indrag än knappblockets kropp.
    """
    kalla = inspect.getsource(modulvy._rendera_jaktfraga)
    rader = kalla.splitlines()
    knapprad = next(i for i, r in enumerate(rader) if 'st.button("Rätta"' in r)
    knappindrag = len(rader[knapprad]) - len(rader[knapprad].lstrip())
    facitrad = next(i for i, r in enumerate(rader) if 'Visa facit' in r)
    facitindrag = len(rader[facitrad]) - len(rader[facitrad].lstrip())
    assert facitindrag <= knappindrag, (
        "Facitexpandern ligger i knappblocket och försvinner vid nästa rerun"
    )
```

- [ ] **Step 2: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_modulvy.py -q`
Expected: FAIL med "Facitexpandern ligger i knappblocket och försvinner vid nästa rerun"

- [ ] **Step 3: Flytta expandern ut ur blocket och kom ihåg rättningen**

Ersätt `_rendera_jaktfraga` i `utils/modulvy.py`:

```python
def _jakt_ratta_nyckel(modul: str, jakt_id: str) -> str:
    """Sessionsnyckel som minns att studenten har rättat en jaktfråga."""
    return f"jakt_rattad_{modul}_{jakt_id}"


def _rendera_jaktfraga(modul: str, nr: int, jakt: Lagrumsjakt) -> None:
    st.markdown(f"**{nr}.** {jakt.situation}")
    svar = st.text_input(
        "Ditt lagrum",
        key=f"jakt_svar_{modul}_{jakt.id}",
        placeholder="T.ex. 4 § AvtL eller 2 kap. 1 § SkL",
    )
    rattad_nyckel = _jakt_ratta_nyckel(modul, jakt.id)
    if st.button("Rätta", key=f"jakt_ratta_{modul}_{jakt.id}"):
        st.session_state[rattad_nyckel] = True

    # Rättningen renderas utanför knappblocket: den ska överleva att studenten
    # klickar någon annanstans på sidan. Streamlit kör om hela skriptet vid
    # varje interaktion, och det som bara ritas i knappens egen rerun försvinner.
    if st.session_state.get(rattad_nyckel):
        res = ratta_lagrumsjakt(jakt, svar)
        if res.korrekt:
            st.success("Rätt lagrum!")
            for ref in res.traffade:
                _lagrum_chip_rad(ref)
        else:
            if res.status == STATUS_OKAND_LAG:
                st.error("Den lagen finns inte i kursens lagrumslista. Försök igen.")
            elif not svar.strip():
                st.warning("Skriv ett lagrum först.")
            else:
                st.error("Inte rätt lagrum ännu.")
            if jakt.ledtrad:
                st.caption(f"Ledtråd: {jakt.ledtrad}")
        with st.expander("Visa facit"):
            for ref in jakt.facit_lagrum:
                _lagrum_chip_rad(ref)
```

- [ ] **Step 4: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_modulvy.py -q`
Expected: PASS

- [ ] **Step 5: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add utils/modulvy.py tests/test_modulvy.py
git commit -m "fix: lagrumsjaktens facit försvinner inte längre vid nästa rerun"
```

---



## Task 3: Facit bakom ett försök

Spec: avsnitt 7.4, avsnitt 9 punkt 9.

Facitexpandern ligger i dag direkt under tutorknappen och är öppen för ett klick
innan studenten skrivit något. Generationseffekten är appens hela premiss och kan
kringgås gratis. Grinden ska vara en avsiktsbekräftelse, inte ett lås.

**Files:**

- Modify: `utils/modulvy.py` (`rendera_case_ovning` rad 264–265, `_rendera_jaktfraga`)
- Modify: `tests/test_modulvy.py`

**Interfaces:**

- Consumes: `_jakt_ratta_nyckel` från Task 2, `RNTS_FALT`.
- Produces: `facit_upplast(nyckel: str, session_state: Mapping[str, object]) -> bool`
— ren funktion som avgör om facit får visas; och
`_rendera_facitgrind(nyckel: str, rubrik: str = ...) -> bool` som ritar knappen.

- [ ] **Step 1: Skriv det failande testet**

Lägg till i `tests/test_modulvy.py`:

```python
from utils.modulvy import facit_upplast


def test_facit_ar_last_fran_borjan():
    assert facit_upplast("case_x", {}) is False


def test_facit_oppnas_av_uttryckligt_val():
    assert facit_upplast("case_x", {"facit_upplast_case_x": True}) is True


def test_facit_las_ar_per_uppgift():
    """Att låsa upp ett facit får inte låsa upp alla andra."""
    state = {"facit_upplast_case_a": True}
    assert facit_upplast("case_a", state) is True
    assert facit_upplast("case_b", state) is False
```

- [ ] **Step 2: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_modulvy.py -q -k facit`
Expected: FAIL med `ImportError: cannot import name 'facit_upplast'`

- [ ] **Step 3: Lägg till grindfunktionen och knappen**

Lägg till i `utils/modulvy.py`, nära `_jakt_ratta_nyckel`:

Lägg till importen `from typing import Mapping` högst upp i filen om den saknas.

```python
def facit_upplast(nyckel: str, session_state: Mapping[str, object]) -> bool:
    """Har studenten uttryckligen valt att se facit för den här uppgiften?

    En grind, inte ett lås: ett klick räcker. Poängen är att facit inte ska vara
    gratis *innan* studenten försökt, eftersom generationseffekten är hela skälet
    att appen låter dem skriva själva först. Låset är per uppgift, så att ett
    öppnat facit inte avslöjar alla andra.
    """
    return bool(session_state.get(f"facit_upplast_{nyckel}"))


def _rendera_facitgrind(nyckel: str, rubrik: str = "Jag har försökt — visa facit") -> bool:
    """Rita upplåsningsknappen och returnera True när facit får visas."""
    if facit_upplast(nyckel, st.session_state):
        return True
    if st.button(rubrik, key=f"facit_knapp_{nyckel}"):
        st.session_state[f"facit_upplast_{nyckel}"] = True
        return True
    return False
```

I `rendera_case_ovning`, ersätt de två raderna

```python
    with st.expander("Visa facit (utan tutor)"):
        _rendera_facit(case)
```

med

```python
    # Facit efter försök, inte före: en jämförelse är bara lärorik om studenten
    # har något eget att jämföra med.
    if _rendera_facitgrind(f"case_{modul}_{case.id}"):
        with st.expander("Facit (utan tutor)", expanded=True):
            _rendera_facit(case)
```

I `_rendera_jaktfraga`, ersätt facitexpandern från Task 2 med

```python
        if _rendera_facitgrind(
            f"jakt_{modul}_{jakt.id}", "Jag har försökt — visa facit"
        ):
            with st.expander("Facit", expanded=True):
                for ref in jakt.facit_lagrum:
                    _lagrum_chip_rad(ref)
```

- [ ] **Step 4: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_modulvy.py -q`
Expected: PASS

- [ ] **Step 5: Uppdatera tutorknappens reservhänvisning**

I `rendera_case_ovning` pekar `reservhanvisning` mot en expander som nu ligger
bakom en grind. Ändra strängen till:

```python
        reservhanvisning="Tryck på **Jag har försökt — visa facit** nedan så länge.",
```

- [ ] **Step 6: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS. Failar något test som antar att facitexpandern alltid ritas, ändra
testet: det nya beteendet är avsiktligt.

- [ ] **Step 7: Commit**

```bash
git add utils/modulvy.py tests/test_modulvy.py
git commit -m "feat: facit visas efter ett eget försök i stället för före"
```

---



## Task 4: Fäll ikonläckorna och sätt en vakt

Spec: avsnitt 6 "Ikoner", avsnitt 9 punkt 4, ändring av `design_system.md` §4.1.

Ikonförbudet i §4.1 gäller bara navigeringen. Fyra glyfer har läckt in:
`🟢`/`⚪` (`utils/ui.py:679`), `🎲` (`sidor/11_Kunskapsutmaning.py:65`), `↺`
(`sidor/16_Rattskartan.py:154` och `:303`), och stepperns `●`/`✓`/`!`
(`utils/ui.py:326–331`). Dessutom scannar språkvakten katalogen `pages` som inte
finns — appens sidor ligger i `sidor/` och är därför **helt ogranskade** av
språk-QA:n i dag.

**Files:**

- Modify: `tests/test_sprak.py` (`_GRANSKADE_KATALOGER`, ny glyfvakt)
- Modify: `utils/ui.py` (`_RNTS_IKONER` rad 326–331, CSS för `.jok-rnts .ikon`,
`render_statuspanel` rad 679)
- Modify: `utils/obsidian.py` (rad 132)
- Modify: `sidor/11_Kunskapsutmaning.py` (rad 62–65)
- Modify: `sidor/16_Rattskartan.py` (rad 154, rad 303)
- Modify: `APPGUIDE.md` (knappetiketten "🎲 Överraska mig")
- Modify: `design_system.md` (§4.1)

**Interfaces:**

- Produces: inget nytt publikt API. `_RNTS_IKONER` ersätts av CSS-klasser, så
`render_rnts_steg` behåller sin signatur `tuple[tuple[str, str], ...] -> str`.

- [ ] **Step 1: Utöka språkvakten till sidor/ och lägg till glyfvakten**

I `tests/test_sprak.py`, ändra katalogtupeln (notera att `pages` inte finns):

```python
_GRANSKADE_KATALOGER = ("utils", "sidor", "tests", "data", "docs", ".streamlit")
```

Lägg till i samma fil. `_granskade_filer()` är redan en modulnivåfunktion som
returnerar en lista, så den kan anropas direkt i dekoratorn — följ filens
befintliga parametriseringsmönster.

```python
# Ikonförbudet i design_system.md 4.1 gäller hela appen. Vakten fångar emoji och
# de dekorativa glyfer som tidigare läckt in (tärning, rundpil, statusprickar,
# stepperikoner). Skrivna som escapesekvenser så att den här filen inte flaggar
# sig själv.
_FORBJUDNA_GLYFER = (
    "\U0001f7e2",  # grön cirkel
    "⚪",      # vit cirkel
    "\U0001f3b2",  # tärning
    "↺",      # rundpil moturs
    "●",      # fylld cirkel
    "✓",      # bock
)
_EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿\U0001f1e6-\U0001f1ff]")

# Två undantag, båda avsiktliga:
#   streamlit_app.py bär page_icon, webbläsarflikens identitet. Det är inte
#   appkrom, och det är det enda undantaget design_system.md 4.1 medger.
#   docs/superpowers/ är historiska design- och planeringsdokument. De beskriver
#   vad appen var vid en viss tidpunkt och ska inte skrivas om i efterhand;
#   granskningsdokumentet måste dessutom kunna citera de glyfer det avskaffar.
_GLYFUNDANTAG = ("streamlit_app.py",)
_GLYFUNDANTAG_KATALOGER = ("docs/superpowers",)


def _glyfundantagen(fil: Path) -> bool:
    """Sant om filen är undantagen från glyfvakten."""
    relativ = fil.relative_to(ROT).as_posix()
    if relativ in _GLYFUNDANTAG:
        return True
    return any(relativ.startswith(f"{k}/") for k in _GLYFUNDANTAG_KATALOGER)


@pytest.mark.parametrize("fil", _granskade_filer(), ids=lambda p: str(p))
def test_inga_ikoner_eller_emoji(fil: Path) -> None:
    """Ingen emoji eller dekorativ glyf i kod, data eller dokumentation.

    Hierarki och tillstånd bärs av indrag, storlek, färgstyrka och CSS-form.
    """
    if _glyfundantagen(fil):
        pytest.skip("dokumenterat undantag, se _GLYFUNDANTAG")
    text = fil.read_text(encoding="utf-8")
    for glyf in _FORBJUDNA_GLYFER:
        assert glyf not in text, f"{fil}: förbjuden glyf {glyf!r}"
    traff = _EMOJI.search(text)
    assert traff is None, f"{fil}: emoji {traff.group()!r} på position {traff.start()}"
```

Notera att `☀-➿` täcker bocken och varningstriangeln men **inte**
högerpilen `→` (U+2192), som används i knappetiketter och är typografi, inte ikon.

- [ ] **Step 2: Kör vakten och se att den failar**

Run: `python3 -m pytest tests/test_sprak.py -q -k ikoner`
Expected: FAIL på exakt fem filer, uppmätta före planen skrevs:
`utils/ui.py` (`🟢`, `⚪`, `✓`), `utils/obsidian.py` (`⚠️`),
`sidor/11_Kunskapsutmaning.py` (`🎲`), `sidor/16_Rattskartan.py` (`↺` × 2) och
`APPGUIDE.md` (`🎲`). Flaggas något annat har appen ändrats sedan dess — fäll
glyfen i stället för att utöka undantagslistan.

- [ ] **Step 3: Ersätt stepperns glyfer med CSS-form**

I `utils/ui.py`, ersätt `_RNTS_IKONER` och `render_rnts_steg`:

```python
# Tillstånden ritas med CSS (fyllning, ram, en ren bockform), inte med
# teckenglyfer: ikonförbudet i design_system.md 4.1 gäller hela appen. Klassen
# på .steg styr utseendet; ikonelementet är avsiktligt tomt.
_RNTS_TILLSTAND = (
    RNTS_STATUS_EJ_PABORJAD,
    RNTS_STATUS_PAGAR,
    RNTS_STATUS_GODKAND,
    RNTS_STATUS_BEHOVER_MER,
)


def render_rnts_steg(steg: tuple[tuple[str, str], ...]) -> str:
    """Vertikal RNTS-stepper: (etikett, status) per steg.

    Status måste vara en av RNTS_STATUS_*-konstanterna; annars ValueError
    (fail fast så att en felstavad status inte renderas tyst som tom cirkel).
    """
    rader = []
    for etikett, status in steg:
        if status not in _RNTS_TILLSTAND:
            raise ValueError(
                f"Okänd RNTS-status {status!r} för steget {etikett!r}. "
                f"Tillåtna: {sorted(_RNTS_TILLSTAND)}"
            )
        rader.append(
            f'<div class="steg {status}"><span class="ikon"></span>'
            f"<span>{html.escape(etikett)}</span></div>"
        )
    return f'<div class="jok-rnts">{"".join(rader)}</div>'
```

I `inject_css()`, ersätt de fyra `.jok-rnts`-reglerna för tillstånd med:

```css
        .jok-rnts .steg.pagar .ikon {{
            border-color: var(--bla); background: var(--bla);
        }}
        .jok-rnts .steg.godkand .ikon {{
            border-color: var(--gron); background: var(--gron);
        }}
        /* Bocken ritas som två kanter roterade 45 grader, inte som tecknet ✓. */
        .jok-rnts .steg.godkand .ikon::after {{
            content: ""; display: block; width: .3rem; height: .55rem;
            margin: .12rem auto 0 auto; transform: rotate(45deg);
            border-right: 2px solid #fff; border-bottom: 2px solid #fff;
        }}
        .jok-rnts .steg.behover-mer .ikon {{
            border-color: var(--varn-mork); background: var(--varn-bg);
        }}
        /* Utropstecknet som stapel och punkt, av samma skäl som bocken. */
        .jok-rnts .steg.behover-mer .ikon::after {{
            content: ""; display: block; width: 2px; height: .45rem;
            margin: .2rem auto 0 auto; background: var(--varn-mork);
            box-shadow: 0 .18rem 0 0 var(--varn-mork);
        }}
```

- [ ] **Step 4: Ta bort de tre återstående glyferna**

`utils/ui.py`, i `render_statuspanel`:

```python
    prick = "Tillgänglig" if tillganglig else "Ej konfigurerad"
```

`sidor/11_Kunskapsutmaning.py` rad 62–65 — ta bort både glyfen och
justeringshacket (spec avsnitt 5, "Justeringshack"):

```python
kol_val, kol_slump = st.columns([3, 1], vertical_alignment="bottom")
with kol_val:
    vald_stem = st.selectbox(
        "Rättsområde",
        options=moduler,
        format_func=lambda s: visningsnamn.get(s, s),
        key="utmaning_val",
    )
with kol_slump:
    overraska = st.button("Överraska mig", use_container_width=True)
```

`sidor/16_Rattskartan.py` rad 154 och 303:

```python
    if st.button("Rensa sökningen", help="Töm sökrutan ovan."):
```

```python
    if st.button("Rensa filtren", help="Töm sökrutan och områdesfiltret."):
```

- [ ] **Step 5: Fäll varningsglyfen i Obsidianexporten**

`utils/obsidian.py:132` skriver `⚠️` i den genererade noten. Exporten är
användarsynlig, och appen har redan ett ord för samma sak — chipsprefixet
"Ej verifierad:". Ersätt:

```python
            f"Ej verifierad: kunde inte verifieras mot kursens lagrumsregister "
            f"(status {status}). "
```

Kontrollera den omgivande f-strängen så att meningen fortfarande börjar med stor
bokstav och att raden inte överskrider radlängdsgränsen i `ruff.toml`.

- [ ] **Step 6: Uppdatera APPGUIDE.md**

`APPGUIDE.md` dokumenterar knappen "🎲 Överraska mig" som i Step 4 blev
"Överraska mig". Ta bort glyfen där också, så att dokumentationen beskriver den
knapp som faktiskt finns.

- [ ] **Step 7: Uppdatera design_system.md §4.1**



Ersätt regelraden om ikoner:

```markdown
* Nivåerna får inte skiljas åt med emoji eller ikoner. Hierarkin bärs av indrag
  och färgstyrka. **Förbudet gäller hela appen**, inte bara navigeringen: inga
  emoji, inga dekorativa glyfer (tärningar, rundpilar, statusprickar) och inga
  teckenbaserade ikoner i komponenter. Tillstånd ritas med CSS-form, som
  RNTS-steppern gör. Enda dokumenterade undantaget är `page_icon` i
  `streamlit_app.py`: webbläsarflikens identitet är inte appkrom, och där gör en
  ikon något ett ord inte kan. `tests/test_sprak.py` vaktar regeln.
```

- [ ] **Step 8: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add tests/test_sprak.py utils/ui.py utils/obsidian.py \
        sidor/11_Kunskapsutmaning.py sidor/16_Rattskartan.py \
        APPGUIDE.md design_system.md
git commit -m "refactor: ikonförbudet gäller hela appen och vaktas av språk-QA

Språkvakten granskade katalogen pages som inte finns; appens sidor ligger i
sidor/ och var därmed helt ogranskade. Fyra glyfläckor fällda: statusprickar,
tärning, två rundpilar och stepperns teckenikoner, som nu ritas med CSS."
```

---



## Task 5: Typ- och spacingtokens

Spec: avsnitt 6 "Typografi" och "Spacing", avsnitt 9 punkt 5, nya §2.1 och §2.2.

Typskalan har hål och dubbletter (28/22/19/18/16, och etikettrollen i tre
storlekar: 14, 12, 11px). Marginalerna är handsatta i tretton olika rem-värden, så
avstånden signalerar ingen gruppering.

**Files:**

- Modify: `utils/ui.py` (`inject_css`, `:root`-blocket rad 50–55)
- Modify: `tests/test_ui.py`
- Modify: `design_system.md` (nya §2.1 och §2.2)

**Interfaces:**

- Produces: CSS-variablerna `--t-hero`, `--t-h2`, `--t-h3`, `--t-brod`, `--t-ui`,
`--t-etikett`, `--s1`…`--s7` i `:root`. Ingen Python-signatur ändras.

- [ ] **Step 1: Skriv det failande testet**

Lägg till i `tests/test_ui.py`:

```python
import re

from utils.ui import inject_css


def _css() -> str:
    """Plocka ut CSS-strängen ur inject_css utan att köra Streamlit."""
    import inspect
    return inspect.getsource(inject_css)


def test_alla_tokens_ar_deklarerade():
    css = _css()
    for token in ("--t-hero", "--t-h2", "--t-h3", "--t-brod", "--t-ui",
                  "--t-etikett", "--s1", "--s2", "--s3", "--s4", "--s5",
                  "--s6", "--s7"):
        assert f"{token}:" in css, f"token {token} saknas i :root"


def test_inga_hardkodade_typstorlekar():
    """font-size ska referera en token, aldrig ett px-tal.

    Tokendeklarationerna i :root skrivs som `--t-hero: 28px`, inte som
    `font-size:`, så de matchas inte av mönstret och behöver inget undantag.
    """
    hardkodade = re.findall(r"font-size:\s*(\d+)px", _css())
    assert not hardkodade, f"hårdkodade typstorlekar kvar: {sorted(set(hardkodade))}"
```

- [ ] **Step 2: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_ui.py -q -k "token or typstorlekar"`
Expected: FAIL — "token --t-hero saknas i :root"

- [ ] **Step 3: Deklarera tokens**

I `inject_css()`, utöka `:root`:

```css
        :root {{
            --bl: {BLACK}; --perg: {PARCHMENT}; --panel: {PANEL};
            --ram: {BORDER}; --bla: {BLUE}; --guld: {GOLD};
            --gron: {GREEN}; --varn-fg: {WARN_FG}; --varn-bg: {WARN_BG};
            --varn-mork: {WARN_DARK}; --fel: {ERROR};

            /* Typskala (design_system.md 2.1). Sex steg, en roll var. */
            --t-hero: 28px;     /* sidrubrik, en per sida */
            --t-h2: 22px;       /* avsnittsrubrik */
            --t-h3: 18px;       /* kortrubrik */
            --t-brod: 17px;     /* brödtext, scenarier */
            --t-ui: 15px;       /* kontroller, kortmetadata */
            --t-etikett: 13px;  /* kapitäler, chips, metadata */

            /* Spacingskala, 4px-bas (design_system.md 2.2). Regeln: avstånd
               INOM en grupp är alltid mindre än avstånd MELLAN grupper. */
            --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px;
            --s5: 24px; --s6: 32px; --s7: 48px;
        }}
```

- [ ] **Step 4: Byt ut varje font-size mot en token**

Gå igenom CSS-strängen och ersätt varje `font-size: Npx` med närmaste token.
Avbildningen är:


| Var                                                                                                                                                                                                                | Från | Till               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---- | ------------------ |
| `.jok-hero h1`                                                                                                                                                                                                     | 28px | `var(--t-hero)`    |
| `.jok-section h2`                                                                                                                                                                                                  | 22px | `var(--t-h2)`      |
| `.jok-begrepp h3`                                                                                                                                                                                                  | 19px | `var(--t-h3)`      |
| `.jok-kort h3`, `.jok-case h3`                                                                                                                                                                                     | 18px | `var(--t-h3)`      |
| `.jok-hero p`, `.jok-case p`, `.jok-summary`                                                                                                                                                                       | 17px | `var(--t-brod)`    |
| `.jok-tutortext`, `.jok-begrepp .falt p`                                                                                                                                                                           | 16px | `var(--t-brod)`    |
| `.jok-lagkort h4`                                                                                                                                                                                                  | 16px | `var(--t-h3)`      |
| `.jok-varning`, `.jok-info`, `.jok-lagkort p`, `.jok-begrepp .skillnad`                                                                                                                                            | 15px | `var(--t-ui)`      |
| `.jok-hero .eyebrow`, `.jok-section .eyebrow`, `.jok-chip`, `.jok-pipeline span`, `.jok-status`, `.jok-legend`, `.jok-rnts .steg`, `.jok-lagkort .nar`, `.jok-lagkort .avsnittsrad`, `.jok-begrepp .falt .etikett` | 14px | `var(--t-etikett)` |
| `.jok-nav-kategori`, `.jok-nav-gren`, `.jok-lagkort .sfs`, `.jok-begrepp .kapitel`, `.jok-lagkort .avsnittsnot`                                                                                                    | 12px | `var(--t-etikett)` |
| `.jok-nav-under`, `.jok-nav-kommer`, `.jok-case .meta`, `.jok-footer`, `.jok-lagkort .kapitelrad`                                                                                                                  | 13px | `var(--t-etikett)` |
| `.jok-lagkort .avsnittsrubrik`                                                                                                                                                                                     | 11px | `var(--t-etikett)` |
| `.jok-rnts .ikon`                                                                                                                                                                                                  | 11px | `var(--t-etikett)` |


Notera att `.jok-begrepp h3` går från 19 till 18px och `.jok-lagkort h4` från 16
till 18px — det är avsiktligt: skalan har sex steg, inte nio.

- [ ] **Step 5: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_ui.py -q -k "token or typstorlekar"`
Expected: PASS

- [ ] **Step 6: Dokumentera skalorna**

Lägg till i `design_system.md` efter §2, före §3:

```markdown
### 2.1 Typskala

Sex steg, en roll var, deklarerade som CSS-variabler i `:root` i `utils/ui.py`.
Inga px-värden för `font-size` får förekomma utanför den deklarationen;
`tests/test_ui.py` vaktar det.

| Token | px | Roll |
|---|---|---|
| `--t-hero` | 28 | Sidrubrik, en per sida |
| `--t-h2` | 22 | Avsnittsrubrik |
| `--t-h3` | 18 | Kortrubrik |
| `--t-brod` | 17 | Brödtext, scenarier |
| `--t-ui` | 15 | Kontroller, kortmetadata |
| `--t-etikett` | 13 | Kapitäler, chips, metadata |

### 2.2 Spacingskala

4px-bas: `--s1` 4, `--s2` 8, `--s3` 12, `--s4` 16, `--s5` 24, `--s6` 32,
`--s7` 48. Regeln som gör skalan meningsfull: **avstånd inom en grupp är alltid
mindre än avstånd mellan grupper.** Närhet är den starkaste grupperingssignal
som finns, och den bär struktur utan att kräva ramar.
```

- [ ] **Step 7: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add utils/ui.py tests/test_ui.py design_system.md
git commit -m "refactor: typ- och spacingskala som CSS-tokens"
```

---



## Task 6: Statuspanelen till en rad, modellväljaren ut

Spec: avsnitt 4 "Statuspanel", avsnitt 9 punkt 7.

Fyra rader driftinformation ligger alltid utfällda i sidopanelen, med samma vikt
som navigeringen. "Anrop kvar i sessionen 40/40" betyder ingenting för en publik
besökare. Modellväljaren 8B/14B är utvecklaryta i en publik app.

**Files:**

- Modify: `utils/ui.py` (`render_statuspanel` rad 668–691, `_render_model_selector`
rad 694–712, `render_sidebar` rad 754–768)
- Modify: `tests/test_ui.py`
- Modify: `design_system.md` (§4, punkten om sidopanelen)

**Interfaces:**

- Produces: `statusrad(tillganglig: bool, sess: int, sess_tak: int, dag: int, dag_tak: int) -> tuple[str, bool]` — ren funktion som ger (text, ska_expanderas).
- `render_statuspanel()` behåller sin signatur (inga argument, returnerar None).

- [ ] **Step 1: Skriv det failande testet**

Lägg till i `tests/test_ui.py`:

```python
from utils.ui import statusrad


def test_statusrad_normalfall_ar_kort_och_inte_expanderad():
    text, expandera = statusrad(True, 40, 40, 300, 300)
    assert text == "Tutorn: tillgänglig"
    assert expandera is False


def test_statusrad_expanderar_nar_sessionen_narmar_sig_taket():
    _text, expandera = statusrad(True, 9, 40, 300, 300)
    assert expandera is True


def test_statusrad_expanderar_nar_dagsbudgeten_narmar_sig_taket():
    _text, expandera = statusrad(True, 40, 40, 70, 300)
    assert expandera is True


def test_statusrad_otillganglig_sager_vad_som_anda_fungerar():
    text, expandera = statusrad(False, 40, 40, 300, 300)
    assert "inte tillgänglig" in text
    assert expandera is True


def test_statusrad_tal_noll_tak_utan_division_med_noll():
    text, expandera = statusrad(True, 0, 0, 0, 0)
    assert text
    assert expandera is True
```

- [ ] **Step 2: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_ui.py -q -k statusrad`
Expected: FAIL med `ImportError: cannot import name 'statusrad'`

- [ ] **Step 3: Skriv statusrad och skriv om panelen**

Ersätt `render_statuspanel` i `utils/ui.py`:

```python
# Under den här andelen återstående anrop är budgeten värd att visa i detalj.
STATUS_TROSKEL = 0.25


def statusrad(
    tillganglig: bool, sess: int, sess_tak: int, dag: int, dag_tak: int
) -> tuple[str, bool]:
    """Sidopanelens statustext, och om detaljerna bör visas.

    Ren funktion så att tröskellogiken kan testas utan Streamlit. Detaljerna
    visas bara när de betyder något: när tutorn är otillgänglig, eller när
    mindre än en fjärdedel av något tak återstår. Driftinformation ska inte
    konkurrera med navigeringen i normalläget.
    """
    if not tillganglig:
        return (
            "Tutorn är inte tillgänglig. Quiz, lagrumslänkar och facit "
            "fungerar som vanligt.",
            True,
        )

    def _lagt(kvar: int, tak: int) -> bool:
        if tak <= 0:
            return True
        return kvar / tak < STATUS_TROSKEL

    if _lagt(sess, sess_tak) or _lagt(dag, dag_tak):
        return (f"Tutorn: {sess} anrop kvar i sessionen, {dag} i dag.", True)
    return ("Tutorn: tillgänglig", False)


def render_statuspanel() -> None:
    """LLM-status i sidopanelen: en rad, som utökas bara när den behöver det."""
    from utils.llm import (
        SESSION_CALL_CAP,
        get_active_model,
        get_session_calls_remaining,
        is_llm_available,
    )
    from utils.llm_budget import get_daily_calls_remaining, get_daily_cap

    text, expandera = statusrad(
        is_llm_available(),
        get_session_calls_remaining(),
        SESSION_CALL_CAP,
        get_daily_calls_remaining(),
        get_daily_cap(),
    )
    st.caption(text)
    if expandera:
        modell = get_active_model().split("/")[-1]
        st.caption(f"Modell: {modell}")
```

- [ ] **Step 4: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_ui.py -q -k statusrad`
Expected: PASS (5 test)

- [ ] **Step 5: Ta modellväljaren ur sidopanelen**

Ta bort `_render_model_selector` helt, och anropet till den i `render_sidebar`:

```python
def render_sidebar() -> None:
    """Sidopanelens innehåll: navigeringsträd och en rad LLM-status.

    Anropas en gång per körning från streamlit_app.py, som registrerar
    samma sidor i st.navigation med position="hidden" så att Streamlits
    egen platta sidlista inte ritas parallellt med trädet.

    Modellväljaren är borttagen: 8B/14B är ett val ingen student kan grunda,
    och mätningen i projektets historik visade att 14B inte var bättre — bara
    långsammare. Standardmodellen sätts i utils/llm.py.
    """
    with st.sidebar:
        st.html('<div class="jok-section"><h2>Juridisk översiktskurs</h2></div>')
        st.caption("Fallbaserad träning med RNTS-metoden.")
        st.divider()
        render_sidopanel()
        st.divider()
        render_statuspanel()
```

Kontrollera att `MODEL_SESSION_KEY` inte längre sätts någonstans, och att
`utils/llm.py:get_active_model()` faller tillbaka på `DEFAULT_MODEL` när nyckeln
saknas. Gör den inte det, är det en bugg som ska åtgärdas i den här taskens
commit.

- [ ] **Step 6: Uppdatera design_system.md §4**

Ersätt punkten om sidopanelen:

```markdown
* **Sidopanel**: modulnavigering överst, en rad LLM-status nederst. Statusraden
  utökas med detaljer först när något faktiskt är begränsat (under en fjärdedel
  av ett tak återstår, eller tutorn är otillgänglig): driftinformation ska inte
  konkurrera med navigeringen i normalläget. Ingen modellväljare — den var
  utvecklaryta i en app som vem som helst kan öppna.
```

- [ ] **Step 7: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS. Failar ett test som förväntar sig modellväljaren, ta bort testet:
kontrollen är avsiktligt borta.

- [ ] **Step 8: Commit**

```bash
git add utils/ui.py tests/test_ui.py design_system.md
git commit -m "refactor: statuspanelen till en rad, modellväljaren ut ur sidopanelen"
```

---



## Task 7: Aktiv rubrikkedja i sidopanelen

Spec: avsnitt 4 "Aktiv sida i sammanhang", avsnitt 9 punkt 8.

`st.page_link` markerar den aktiva sidan, men rubrikerna vet inget: inget säger
att *Förmögenhetsrätt → Kontraktsrätt* innehåller den öppna sidan. Datat finns
redan — `streamlit_app.py:63` lägger `_jok_aktiv_sida` i session_state och ingen
läser det.

**Files:**

- Modify: `utils/navigation.py` (ny ren funktion)
- Modify: `utils/ui.py` (`_render_nod`, `render_sidopanel`, CSS)
- Modify: `tests/test_navigation.py`

**Interfaces:**

- Produces: `rubrikkedja(namn: str, noder: tuple[Nod, ...] = NAV_TRAD) -> tuple[str, ...]`
— namnen på alla grupper som innehåller modulen, från yttersta till innersta.
- Consumes: `st.session_state["_jok_aktiv_sida"]` (satt av `streamlit_app.py`).

- [ ] **Step 1: Skriv det failande testet**

Lägg till i `tests/test_navigation.py`:

```python
from utils.navigation import rubrikkedja


def test_rubrikkedja_for_djupt_nastlad_modul():
    assert rubrikkedja("Avtalsrätt") == (
        "CIVILRÄTT", "Förmögenhetsrätt", "Kontraktsrätt",
    )


def test_rubrikkedja_for_modul_direkt_under_kategori():
    assert rubrikkedja("Juridisk metod") == ("START OCH METOD",)


def test_rubrikkedja_for_okand_modul_ar_tom():
    assert rubrikkedja("Modul som inte finns") == ()
```

- [ ] **Step 2: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_navigation.py -q -k rubrikkedja`
Expected: FAIL med `ImportError: cannot import name 'rubrikkedja'`

- [ ] **Step 3: Skriv rubrikkedja**

Lägg till i `utils/navigation.py`:

```python
def rubrikkedja(namn: str, noder: tuple[Nod, ...] = NAV_TRAD) -> tuple[str, ...]:
    """Namnen på grupperna som omsluter modulen, yttersta först.

    Sidopanelen använder kedjan för att ge den öppna sidans förfäder full
    bläckvikt, så att studenten hittar sin plats i ett träd som är fyra nivåer
    djupt. Tom tupel om modulnamnet inte finns i trädet.
    """
    for nod in noder:
        if isinstance(nod, Modul):
            continue
        if any(m.namn == namn for m in alla_moduler(nod.barn)):
            return (nod.namn,) + rubrikkedja(namn, nod.barn)
    return ()
```

- [ ] **Step 4: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_navigation.py -q -k rubrikkedja`
Expected: PASS (3 test)

- [ ] **Step 5: Använd kedjan när panelen ritas**

I `utils/ui.py`, ändra `_render_nod` och `render_sidopanel` så att kedjan skickas
med och lägger till klassen `aktiv`:

```python
def _render_nod(nod: "Nod", niva: int, aktiv_kedja: frozenset[str] = frozenset()) -> None:
    """Rita en nod i navigeringsträdet rekursivt.

    ``niva`` är djupet under huvudkategorin: 1 = underkategori, 2 och nedåt
    = undergren. Moduler ritas som länkar, planerade moduler som gråtonad
    text med "(kommer)". Grupper som omsluter den öppna sidan får klassen
    ``aktiv`` och full bläckvikt, så att studenten ser var i trädet den är.
    """
    if isinstance(nod, Modul):
        if nod.sida is None:
            st.html(
                f'<div class="jok-nav-kommer">{html.escape(nod.namn)} (kommer)</div>'
            )
        else:
            st.page_link(nod.sida, label=nod.namn)
        return

    klass = "jok-nav-under" if niva <= 1 else "jok-nav-gren"
    if nod.namn in aktiv_kedja:
        klass += " aktiv"
    st.html(f'<div class="{klass}">{html.escape(nod.namn)}</div>')
    for barn in nod.barn:
        _render_nod(barn, niva + 1, aktiv_kedja)


def render_sidopanel() -> None:
    """Rita hela navigeringsträdet som en sammanhållen lista.

    Speglar svensk rätts systematik enligt utils.navigation.NAV_TRAD i
    stället för en platt sidlista. Allt visas samtidigt: inga hopfällbara
    sektioner per huvudkategori, eftersom en panel som måste öppnas döljer
    kursens struktur i stället för att visa den. Nivåerna skiljs åt med
    indrag och färgstyrka enligt design_system.md 4.1.

    Rubrikerna ovanför den öppna sidan får full bläckvikt via klassen ``aktiv``.
    Ingen färg och ingen ikon: guld är reserverat för lagrum, och hierarkin ska
    bäras av vikt och indrag.
    """
    from utils.navigation import rubrikkedja

    try:
        aktiv = st.session_state.get("_jok_aktiv_sida") or ""
    except Exception:
        aktiv = ""
    aktiv_kedja = frozenset(rubrikkedja(aktiv)) if aktiv else frozenset()

    for kategori in NAV_TRAD:
        klass = "jok-nav-kategori"
        if kategori.namn in aktiv_kedja:
            klass += " aktiv"
        st.html(f'<div class="{klass}">{html.escape(kategori.namn)}</div>')
        for barn in kategori.barn:
            _render_nod(barn, niva=1, aktiv_kedja=aktiv_kedja)
```

Lägg till i `inject_css()`, efter `.jok-nav-kommer`:

```css
        /* Förfäderna till den öppna sidan får full bläckvikt, så att studenten
           hittar sin plats i ett fyra nivåer djupt träd. Ingen färg, ingen
           ikon: guld är reserverat för lagrum. */
        .jok-nav-under.aktiv, .jok-nav-gren.aktiv {{
            color: var(--bl); font-weight: 700;
        }}
        .jok-nav-kategori.aktiv {{ color: var(--bl); }}
```

- [ ] **Step 6: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add utils/navigation.py utils/ui.py tests/test_navigation.py
git commit -m "feat: sidopanelen visar var i trädet den öppna sidan ligger"
```

---



## Task 8: Startsidans tomma tillstånd och sessionens flyktighet

Spec: avsnitt 3 punkt 5, avsnitt 9 punkterna 6 och 10, ny §7 i `design_system.md`.

Utan resultat visar startsidan i dag: ett `st.info` om att inget finns, en
nedladdningsknapp för Obsidianvalvet och ett `st.info` som förklarar Obsidian.
Tillsammans med friskrivningen ger det tre informationskort och två knappar på en
sida vars uppgift är *börja här*. Och att framstegen försvinner när fliken stängs
sägs bara indirekt, i en rubrik.

**Files:**

- Modify: `sidor/0_Hem.py` (`_render_framsteg` rad 95–147, `render_landing` rad 36–69)
- Modify: `design_system.md` (ny §7)

**Interfaces:**

- Consumes: `utils.framsteg.pabborjade_moduler` (Task 1), `alla_resultat`,
`genomforda_case`, `bygg_valv`, `hamta_case_analyser`.

- [ ] **Step 1: Dämpa friskrivningen i render_landing**

I `sidor/0_Hem.py`, ersätt `render_info(...)`-anropet med en caption. Den
fullständiga texten står redan i `footer_note()`, så kravet i PRD 4 är uppfyllt —
kravet var synlighet, inte dominans.

```python
    st.caption(
        "Studieverktyg, inte juridisk rådgivning. Mata inte in personuppgifter."
    )
```

Ta bort `render_info` ur importlistan om inget annat i filen använder den.

- [ ] **Step 2: Skriv om framstegssektionen**

Ersätt `_render_framsteg` i `sidor/0_Hem.py`:

```python
def _render_framsteg() -> None:
    """Framstegssektion: tre tal, en ärlig rad om sessionen, och exporten.

    Tomt tillstånd visar ingenting alls utom en mening: en förstagångsbesökare
    ska mötas av exakt en handling, inte av nedladdningsknappar för en rapport
    som ännu är tom.
    """
    resultat = alla_resultat()
    case_bok = genomforda_case()

    if not resultat and not case_bok:
        st.caption(
            "När du börjat öva visas dina framsteg här."
        )
        return

    st.html(section_heading("FRAMSTEG", "Så här långt"))

    moduler = len(pabborjade_moduler())
    fall = sum(len(ids) for ids in case_bok.values())
    ratt = sum(r for r, _b in resultat.values())
    besvarade = sum(b for _r, b in resultat.values())

    delar = [
        antal_med_enhet(moduler, "modul påbörjad", "moduler påbörjade"),
        antal_med_enhet(fall, "rättsfall genomfört", "rättsfall genomförda"),
    ]
    if besvarade:
        delar.append(f"{ratt}/{besvarade} rätt på quiz")
    st.markdown(" · ".join(delar))

    st.caption(
        "Framstegen gäller den här sessionen. Stänger du fliken är de borta — "
        "ladda ner dem nedan för att behålla dem."
    )
    _render_export(resultat, case_bok)


def _render_export(
    resultat: dict[str, tuple[int, int]], case_bok: dict[str, tuple[str, ...]]
) -> None:
    """Exportknapparna: valvet primärt, rapporterna sekundära.

    Obsidianvalvet ligger först och får mest vikt eftersom det är den
    pedagogiskt intressanta exporten: Rättskartan följer alltid med, varje
    RNTS-analys blir en egen not, och noterna binds ihop av sina lagrum. Det
    är appens enda väg till repetition över tid.
    """
    st.html(section_heading("TA MED DIG", "Läs om det du gjort i morgon"))
    st.download_button(
        "Ladda ner Obsidianvalv med Rättskartan (zip)",
        data=bygg_valv(hamta_case_analyser()),
        file_name="juridik_valv.zip",
        mime="application/zip",
        type="primary",
    )
    st.caption(
        "Packa upp zipen och öppna mappen Juridik som ett valv i Obsidian. "
        "Rättskartan är en klickbar karta över rättssystemet, och varje "
        "genomförd RNTS-analys blir en egen not."
    )

    kol_md, kol_xlsx = st.columns(2)
    with kol_md:
        st.download_button(
            "Rapport (Markdown)",
            data=bygg_markdown_rapport(resultat_till_svar(), case_bok),
            file_name="studierapport.md",
            mime="text/markdown",
        )
    with kol_xlsx:
        st.download_button(
            "Rapport (Excel)",
            data=bygg_excel_rapport(resultat_till_svar(), case_bok),
            file_name="studierapport.xlsx",
            mime="application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet",
        )
```

Notera att `_render_framsteg` nu returnerar tidigt i det tomma fallet, så
Obsidianvalvet inte längre erbjuds på första skärmen. Det är fortfarande nåbart
så snart studenten gjort något — och i etapp 2 flyttar det till sidan *Framsteg
och samband*.

- [ ] **Step 3: Ta bort ARBETSGÅNG-sektionen**

Spec avsnitt 3 punkt 4: pipelinen och RNTS-panelen lär ut samma fyrstegsmodell i
olika vokabulär. RNTS-panelen byggs i etapp 2, men duplikatet ska bort redan nu
eftersom hero-texten redan räknar upp de fyra stegen. Ta bort dessa rader ur
`render_landing`:

```python
    st.html(section_heading("ARBETSGÅNG", "Så arbetar du i varje modul"))
    st.html(
        pipeline_steps(
            [
                "Läs scenariot",
                "Skriv din RNTS-analys",
                "Be tutorn granska",
                "Öva lagrum och quiz",
            ]
        )
    )
```

Ta bort `pipeline_steps` ur importlistan i `sidor/0_Hem.py`. Behåll funktionen i
`utils/ui.py`: `_norm_feedback` och `_rendera_facit` använder `.jok-pipeline` för
chiprader.

- [ ] **Step 4: Kontrollera importlistan**

`sidor/0_Hem.py` ska nu importera:

```python
from utils.export import (
    bygg_excel_rapport,
    bygg_markdown_rapport,
    genomforda_case,
)
from utils.framsteg import pabborjade_moduler
from utils.navigation import SENAST_BESOKT_NYCKEL, cta_mal, sida_for_namn
from utils.obsidian import bygg_valv, hamta_case_analyser
from utils.quiz import alla_resultat
from utils.texter import antal_med_enhet
from utils.ui import footer_note, hero, section_heading
```

- [ ] **Step 5: Verifiera sidan headless**

Run:

```bash
python3 -c "
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('streamlit_app.py', default_timeout=60).run()
assert not at.exception, at.exception
knappar = [b.label for b in at.button]
print('knappar:', knappar)
print('nedladdningar:', len(at.get('download_button')))
assert len(knappar) == 1, f'tomt tillstånd ska ha exakt en knapp, har {knappar}'
"
```

Expected: exakt en knapp (CTA:n), noll nedladdningsknappar.

Ser du `KeyError: 'url_pathname'` beror det på att session_state sattes före
första `at.run()` — kör en gång först, injicera tillstånd sedan.

- [ ] **Step 6: Dokumentera regeln**

Lägg till som nytt avsnitt sist i `design_system.md`:

```markdown
## 7. Framsteg och kontinuitet

Framstegen är sessionsbundna: allt ligger i `st.session_state` och försvinner när
fliken stängs. Målgruppen är publik och anonym, så det finns ingen inloggning och
därmed ingen ärlig serverlagring per student.

Regeln: **säg det rent ut, och peka på lösningen i samma andetag.** "Framstegen
gäller den här sessionen. Stänger du fliken är de borta — ladda ner dem nedan för
att behålla dem." Aldrig bara antytt i en rubrik. En student som förlorat en
timmes arbete utan varning kommer inte tillbaka, och tillit är en förutsättning
för ansträngning.

Obsidianvalvet är därför inte en teknisk detalj utan kursens repetitionsmekanism,
och framställs som det ("Läs om det du gjort i morgon"). Tomma tillstånd visar
aldrig nedladdningsknappar för innehåll som inte finns.
```

- [ ] **Step 7: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add sidor/0_Hem.py design_system.md
git commit -m "feat: startsidan säger att framstegen är sessionsbundna och tystnar när den är tom"
```

---



## Task 9: TRÄNAR-etiketter gör RNTS synligt

Spec: avsnitt 7.1, avsnitt 9 punkt 2.

Lagrumsjakten tränar *Norm*, quizet tränar *Tillämpning*, rättsfallet tränar alla
fyra. Ingen av dem säger det, så studenten samlar övningar utan att se att de
bygger samma förmåga.

**Files:**

- Create: `utils/rnts.py`
- Create: `tests/test_rnts.py`
- Modify: `utils/modulvy.py` (`RNTS_FALT` rad 61–66, de tre flikfunktionerna)
- Modify: `utils/ui.py` (ny komponent + CSS)
- Modify: `design_system.md` (§5)

**Interfaces:**

- Produces: `utils.rnts.RNTS_STEG: tuple[str, ...]`;
`utils.rnts.AKTIVITETSSTEG: dict[str, tuple[str, ...]]`;
`utils.rnts.tranar_etikett(aktivitet: str) -> str`;
`utils.ui.render_tranar(text: str) -> str`.
- Consumes: `RNTS_FALT` i `utils/modulvy.py` behåller sina fyra etiketter, men
hämtar stegnamnen från `utils.rnts.RNTS_STEG` så att de bara står på ett ställe.

- [ ] **Step 1: Skriv det failande testet**

Skapa `tests/test_rnts.py`:

```python
"""Test för utils.rnts: RNTS-stegen och vilken aktivitet som tränar vilket steg.

Ren data utan Streamlit-beroende, så avbildningen kan testas direkt.
"""

from __future__ import annotations

import pytest

from utils.rnts import AKTIVITETSSTEG, RNTS_STEG, tranar_etikett


def test_rnts_steg_har_de_fyra_i_ratt_ordning():
    assert RNTS_STEG == ("Rättsfrågan", "Norm", "Tillämpning", "Slutsats")


def test_varje_aktivitet_tranar_minst_ett_steg():
    assert AKTIVITETSSTEG
    for aktivitet, steg in AKTIVITETSSTEG.items():
        assert steg, f"{aktivitet} tränar inga steg"


def test_alla_angivna_steg_finns_i_rnts_steg():
    """Vakt mot stavfel: ett okänt stegnamn ska inte kunna smyga in."""
    for aktivitet, steg in AKTIVITETSSTEG.items():
        for s in steg:
            assert s in RNTS_STEG, f"{aktivitet} anger okänt steg {s!r}"


def test_lagrumsjakt_tranar_norm():
    assert AKTIVITETSSTEG["lagrumsjakt"] == ("Norm",)


def test_rattsfall_tranar_alla_fyra():
    assert AKTIVITETSSTEG["rattsfall"] == RNTS_STEG


def test_tranar_etikett_ar_versal_och_kommaseparerad():
    assert tranar_etikett("lagrumsjakt") == "TRÄNAR: NORM"
    assert tranar_etikett("quiz") == "TRÄNAR: NORM, TILLÄMPNING"


def test_tranar_etikett_okand_aktivitet_ger_valueerror():
    with pytest.raises(ValueError, match="Okänd aktivitet"):
        tranar_etikett("finns-inte")
```

- [ ] **Step 2: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_rnts.py -q`
Expected: FAIL med `ModuleNotFoundError: No module named 'utils.rnts'`

- [ ] **Step 3: Skriv utils/rnts.py**

```python
"""RNTS-stegen och vilken aktivitet som tränar vilket steg.

RNTS är appens ryggrad, inte ett formulär. Den här modulen är den enda platsen
där stegens namn står, och den enda platsen där kopplingen aktivitet -> steg
definieras, så att UI:t kan märka varje övning med vad den faktiskt bygger.

Poängen är pedagogisk: en student som ser "TRÄNAR: NORM" över lagrumsjakten
förstår att jakten och Normfältet i rättsfallsanalysen är samma förmåga. Utan
etiketten samlar de övningar utan att se sammanhanget.

Ren data utan Streamlit-beroende.
"""

from __future__ import annotations

RNTS_STEG: tuple[str, ...] = ("Rättsfrågan", "Norm", "Tillämpning", "Slutsats")

# Nyckeln är aktivitetens interna namn, inte dess rubrik i UI:t.
AKTIVITETSSTEG: dict[str, tuple[str, ...]] = {
    # Hela analysen, från rättsfråga till slutsats.
    "rattsfall": RNTS_STEG,
    # Frågorna prövar vilken norm som gäller och hur den faller ut i ett fall.
    "quiz": ("Norm", "Tillämpning"),
    # Jakten är ren normidentifiering: hitta paragrafen som styr situationen.
    "lagrumsjakt": ("Norm",),
    # Begreppen ger signalorden som avgör vilken fråga scenariot ställer.
    "nyckelbegrepp": ("Rättsfrågan",),
}


def tranar_etikett(aktivitet: str) -> str:
    """Kapitälsetiketten för en aktivitet, t.ex. "TRÄNAR: NORM".

    ValueError vid okänd aktivitet: en felstavad nyckel ska inte tyst ge en
    etikett som utelämnar stegen.
    """
    if aktivitet not in AKTIVITETSSTEG:
        raise ValueError(
            f"Okänd aktivitet {aktivitet!r}. Tillåtna: {sorted(AKTIVITETSSTEG)}"
        )
    steg = ", ".join(s.upper() for s in AKTIVITETSSTEG[aktivitet])
    return f"TRÄNAR: {steg}"
```

- [ ] **Step 4: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_rnts.py -q`
Expected: PASS (7 test)

- [ ] **Step 5: Lägg till komponenten i utils/ui.py**

```python
def render_tranar(text: str) -> str:
    """Kapitälsetikett som säger vilket RNTS-steg en aktivitet tränar.

    Dämpad med avsikt: den ska kunna läsas en gång och sedan ignoreras, inte
    konkurrera med uppgiften. Se utils.rnts för avbildningen.
    """
    return f'<div class="jok-tranar">{html.escape(text)}</div>'
```

Och i `inject_css()`:

```css
        /* Vilket RNTS-steg en aktivitet tränar. Dämpad kapitälrad: informativ
           en gång, därefter tyst. */
        .jok-tranar {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
            font-size: var(--t-etikett); letter-spacing: .1em;
            text-transform: uppercase; color: #6B6459;
            margin: var(--s3) 0 var(--s2) 0;
        }}
```

- [ ] **Step 6: Använd etiketten på de tre flikarna**

I `utils/modulvy.py`, importera och lägg etiketten först i varje flikfunktion:

```python
from utils.rnts import RNTS_STEG, tranar_etikett
from utils.ui import render_tranar
```

Först i `_rendera_rattsfall`:

```python
    st.html(render_tranar(tranar_etikett("rattsfall")))
```

Först i `_rendera_quiz`, efter tomhetskontrollen:

```python
    st.html(render_tranar(tranar_etikett("quiz")))
```

Först i `_rendera_lagrumsjakt`, efter tomhetskontrollen:

```python
    st.html(render_tranar(tranar_etikett("lagrumsjakt")))
```

- [ ] **Step 7: Låt RNTS_FALT hämta stegnamnen från en enda källa**

Ersätt `RNTS_FALT` i `utils/modulvy.py` så att etiketterna kommer ur
`utils.rnts.RNTS_STEG` och inte kan glida ifrån dem:

```python
# Etiketterna kommer ur utils.rnts.RNTS_STEG så att stegens namn står på exakt
# ett ställe i projektet. Normfältet bär ett tillägg eftersom formen ("4 § AvtL")
# är det studenten oftast fastnar på.
RNTS_FALT = (
    ("rattsfragan", RNTS_STEG[0], "Vilken rättslig fråga ska besvaras?"),
    ("norm", f"{RNTS_STEG[1]} (ange lagrum)", "T.ex. 4 § AvtL eller 2 kap. 1 § SkL"),
    ("tillampning", RNTS_STEG[2], "Hur tillämpas normen på omständigheterna?"),
    ("slutsats", RNTS_STEG[3], "Vad blir svaret på rättsfrågan?"),
)
```

Notera att Normfältets placeholder nu visar formen i stället för att förklara den
(spec avsnitt 8, minut 2:00).

- [ ] **Step 8: Dokumentera regeln**

Lägg till i `design_system.md` §5:

```markdown
* Varje övningsaktivitet inleds med en dämpad kapitälrad som säger vilket
  RNTS-steg den tränar ("TRÄNAR: NORM"). Avbildningen aktivitet -> steg ägs av
  `utils/rnts.py`, som också är den enda platsen där stegens namn står. Skälet är
  pedagogiskt: utan etiketten ser studenten fyra separata övningstyper i stället
  för fyra ingångar till samma förmåga.
```

- [ ] **Step 9: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add utils/rnts.py utils/ui.py utils/modulvy.py tests/test_rnts.py design_system.md
git commit -m "feat: varje aktivitet visar vilket RNTS-steg den tränar"
```

---



## Task 10: Död kod och modulingressen

Spec: avsnitt 5 "Kort och behållare", avsnitt 9 punkterna 11 och 12.

`render_kort` och `summary_box` refereras bara av `tests/test_ui.py`, och
`render_kort` tar dessutom en `ikon`-parameter som strider mot ikonregeln.
`_ingress()` i `utils/modulvy.py` tar ett `filnamn`-argument som den ignorerar och
ger samma mening på alla tolv modulsidor — en mening som är sann för alla moduler
bär ingen information om någon.

**Files:**

- Modify: `utils/ui.py` (`summary_box` rad 296–298, `render_kort` rad 301–307, docstring)
- Modify: `tests/test_ui.py` (ta bort testen för borttagen kod)
- Modify: `utils/scenarier.py` (`Modulscenarier`, `ladda_modul`)
- Modify: `utils/modulvy.py` (`_ingress`, `rendera_modulsida`)
- Modify: `tests/test_scenarier.py`

**Interfaces:**

- Produces: `Modulscenarier.ingress: str = ""` (nytt, valfritt fält);
`_ingress(modul: Modulscenarier) -> str`.
- Removes: `utils.ui.render_kort`, `utils.ui.summary_box`.

- [ ] **Step 1: Ta bort den döda koden**

Ta bort `summary_box` och `render_kort` ur `utils/ui.py`, och stryk dem ur
modulens docstring (raderna som nämner `summary_box` och `render_kort`). Ta bort
`test_render_kort_escapar_innehall` och importen av `render_kort` ur
`tests/test_ui.py`.

- [ ] **Step 2: Kontrollera att inget annat använde dem**

Run: `grep -rn "render_kort\|summary_box" --include=*.py --include=*.md .`
Expected: inga träffar i `utils/`, `sidor/` eller `tests/`. Träffar i
`design_system.md` §3 åtgärdas i Step 7.

- [ ] **Step 3: Skriv det failande testet för ingressen**

Lägg till i `tests/test_scenarier.py`:

```python
def test_modul_utan_ingress_far_tom_strang():
    """Fältet är valfritt: befintliga scenariofiler ska läsas oförändrat."""
    from utils.scenarier import ladda_modul

    modul = ladda_modul("avtalsratt")
    assert isinstance(modul.ingress, str)


def test_ingress_lases_in_nar_den_finns(tmp_path, monkeypatch):
    import json

    from utils import scenarier

    data = {
        "modul": "Testmodul",
        "ingress": "En mening om just den här modulen.",
        "case": [],
        "flervalsfragor": [],
        "lagrumsjakt": [],
    }
    fil = tmp_path / "testmodul.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(scenarier, "SCENARIER_DIR", tmp_path)
    assert scenarier.ladda_modul("testmodul").ingress == (
        "En mening om just den här modulen."
    )
```

- [ ] **Step 4: Kör testet och se att det failar**

Run: `python3 -m pytest tests/test_scenarier.py -q -k ingress`
Expected: FAIL med `AttributeError: 'Modulscenarier' object has no attribute 'ingress'`

- [ ] **Step 5: Lägg till fältet**

I `utils/scenarier.py`, utöka dataklassen:

```python
@dataclass(frozen=True)
class Modulscenarier:
    """Allt övningsinnehåll för en modul.

    ``ingress`` är en valfri mening om just den här modulen, som modulsidans
    hero visar. Saknas den faller sidan tillbaka på en generell formulering.
    Fältet är valfritt så att befintliga scenariofiler läses oförändrat.
    """

    modul: str
    case: tuple[Case, ...]
    flervalsfragor: tuple[Flervalsfraga, ...]
    lagrumsjakt: tuple[Lagrumsjakt, ...]
    ingress: str = ""
```

Konstruktionen sker i `ladda_fil` (rad 153–165), **inte** i `ladda_modul` — den
senare delegerar bara. Ersätt returraden i `ladda_fil`:

```python
    ingress = data.get("ingress", "")
    _krav(
        isinstance(ingress, str),
        f"Fältet 'ingress' i {path} måste vara en sträng, inte {type(ingress).__name__}.",
    )

    return Modulscenarier(
        modul=str(data.get("modul", path.stem)),
        case=tuple(_bygg_case(c) for c in data.get("case", [])),
        flervalsfragor=tuple(_bygg_fraga(q) for q in data.get("flervalsfragor", [])),
        lagrumsjakt=tuple(_bygg_lagrumsjakt(lj) for lj in data.get("lagrumsjakt", [])),
        ingress=ingress,
    )
```

Valideringen följer filens `_krav`-mönster: fail fast på trasig data i stället för
att tysta konvertera ett tal till en sträng.

- [ ] **Step 6: Kör testet och se att det passerar**

Run: `python3 -m pytest tests/test_scenarier.py -q -k ingress`
Expected: PASS

- [ ] **Step 7: Använd ingressen på modulsidan**

I `utils/modulvy.py`, ersätt `_ingress` och anropet i `rendera_modulsida`. Hero
ritas i dag *före* `ladda_modul`, så ordningen måste kastas om:

```python
def _ingress(modul: Modulscenarier) -> str:
    """Modulsidans ingress: modulens egen mening, annars en generell.

    Fallbacken är avsiktligt generell men säger något som gäller: att varje
    lagrum verifieras. Har modulen en egen ingress i data/scenarier väger den
    tyngre, eftersom en mening som är sann för alla moduler inte informerar om
    någon av dem.
    """
    if modul.ingress:
        return modul.ingress
    return (
        "Läs scenariot, skriv din egen RNTS-analys och be tutorn granska den. "
        "Varje lagrum du och tutorn anger kontrolleras mot kursens lagrumslista."
    )
```

I `rendera_modulsida`, flytta `st.html(hero(...))` så att den kommer *efter*
`ladda_modul`, och låt felvägarna rita sitt eget hero:

```python
def rendera_modulsida(filnamn: str, titel: str, undertitel: str = "") -> None:
    """Rendera en komplett modulsida från en scenariofil.

    ``filnamn`` är scenariofilens namn utan suffix, t.ex. "avtalsratt".
    ``titel``/``undertitel`` visas i sidhuvudet. CSS och sidopanel injiceras
    centralt av streamlit_app.py och upprepas inte här.
    """
    eyebrow = undertitel or "MODUL"
    try:
        modul = ladda_modul(filnamn)
    except Exception as exc:  # noqa: BLE001 (vi vill visa ett vänligt fel i UI:t)
        st.html(hero(eyebrow=eyebrow, title=titel, lead=""))
        render_varning(
            f"Kunde inte läsa övningsinnehållet för modulen ({exc}). "
            "Kontrollera scenariofilen."
        )
        st.html(footer_note())
        return

    st.html(hero(eyebrow=eyebrow, title=titel, lead=_ingress(modul)))

    if not (modul.case or modul.flervalsfragor or modul.lagrumsjakt):
        render_varning(
            "Den här modulen har inget övningsinnehåll ännu. Kom tillbaka senare."
        )
        st.html(footer_note())
        return

    flik_case, flik_quiz, flik_jakt = st.tabs(["Rättsfall", "Quiz", "Lagrumsjakt"])
    with flik_case:
        _rendera_rattsfall(filnamn, modul)
    with flik_quiz:
        _rendera_quiz(modul)
    with flik_jakt:
        _rendera_lagrumsjakt(modul)

    st.html(footer_note())
```

- [ ] **Step 8: Uppdatera design_system.md §3**

Ta bort raden om `render_kort` och lägg till en rad om att kortprimitiverna
dokumenteras i den kommande etappen. Ersätt punkten:

```markdown
* **render_case(rubrik, metadata, scenariotext)**: scenariokort med rubrik,
  faktatext, diskret metadatarad (svårighetsgrad, uppskattad tid) och en tunn
  guldlinje överst. Basen för alla innehållsblock. `render_kort` och
  `summary_box` är borttagna: de användes inte, och `render_kort` bar en
  ikonparameter som stred mot ikonförbudet i 4.1.
```

Ta även bort `render_quizfraga`-punkten eller markera den som ej byggd — den
implementeras i etapp 2, task-listan för hög effekt / medelinsats:

```markdown
* **render_quizfraga(fraga)**: ännu inte byggd. Quizfrågan ritas i dag direkt i
  `utils/modulvy.py` med fet markdown och en radio. Komponenten ligger i etapp 2.
```

- [ ] **Step 9: Kör hela sviten och linta**

Run: `python3 -m pytest -q && python3 -m ruff check .`
Expected: PASS

- [ ] **Step 10: Verifiera modulsidan headless**

Run:

```bash
python3 -c "
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('sidor/2_Avtalsratt.py', default_timeout=60).run()
assert not at.exception, at.exception
print('flikar:', len(at.tabs))
"
```

Expected: inget undantag.

- [ ] **Step 11: Commit**

```bash
git add utils/ui.py utils/scenarier.py utils/modulvy.py tests/test_ui.py \
        tests/test_scenarier.py design_system.md
git commit -m "refactor: ta bort död kod och ge modulingressen en egen datakälla"
```



---



## Slutkontroll

- [ ] **Step 1: Hela sviten, lint och typkontroll**

```bash
python3 -m pytest -q
python3 -m ruff check .
```

Expected: allt grönt, antalet test ≥ 798 + de nya.

- [ ] **Step 2: Manuell genomgång i appen**

```bash
python3 -m streamlit run streamlit_app.py
```

Kontrollera i ordning:

1. Startsidan i ny session: exakt **en** knapp, ingen nedladdning, friskrivningen
  som caption, skälet under NÄSTA STEG.
2. Klicka CTA:n → hamnar i Juridisk metod. Sidopanelen: START OCH METOD i
  bläckvikt.
3. Öppna Avtalsrätt. Varje flik har en TRÄNAR-rad. Sidopanelen: CIVILRÄTT,
  Förmögenhetsrätt och Kontraktsrätt i bläckvikt.
4. Lagrumsjakt: skriv fel lagrum, tryck Rätta, klicka sedan i en annan flik och
  tillbaka — rättningen ska fortfarande vara kvar.
5. Facit kräver ett klick på "Jag har försökt".
6. Fyll i alla fyra RNTS-fält → gå till Hem: framstegsraden visar tal, och raden
  om att sessionen är flyktig står där, med Obsidianvalvet under.
7. Inga emoji eller glyfer någonstans i UI:t.
8. Sidopanelen: en statusrad, ingen modellväljare.

- [ ] **Step 3: Uppdatera roadmapen i specen**

Markera punkterna 1–12 i avsnitt 9 som genomförda i
`docs/superpowers/specs/2026-08-06-ux-omdesign-design.md`, med en rad om att
etapp 1 är klar och var planen ligger.

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/2026-08-06-ux-omdesign-design.md
git commit -m "docs: etapp 1 av UX-omdesignen genomförd"
```

---



## Kvarstår till senare etapper

Ur specens avsnitt 9, **inte** i den här planen:

- **Etapp 2 (hög effekt / medelinsats), punkt 13–22:** RNTS-panelen på startsidan,
sidopanelen i tre plan, sammanslagningen Kunskapstest + Kunskapskarta →
*Framsteg och samband*, flikrampen, `render_quizfraga`, en enda
aviseringsuppsättning, vågrät stepper med sanna statusar, kortsystemet,
framstegsmarkering per modul, ett-steg-i-taget-läge.
- **Etapp 3 (hög effekt / stor insats), punkt 23–26:** författade worked examples
per modul, onboarding för anonym förstagångsbesökare, falltypsguiden som ingång.
Punkt 24 (framstegsmodell per RNTS-steg) bör **inte** byggas som en
kvalitetsmodell — se invändning 11.1 i specen.
- **Framtida idéer:** bokmärkbar framstegslänk via `st.query_params`
(invändning 11.7 — potentiellt den mest värdefulla åtgärden i hela specen),
tillgänglighetsgenomgång med riktiga hjälpmedel, tidsuppskattning per modul.

Varje etapp får sin egen plan enligt samma mönster.