"""Tester för Obsidianexporten: noter, wikilänkar, frontmatter och valv-zip.

Testar de rena funktionerna i utils.obsidian utan Streamlit. Valvet packas upp
i minnet (ZipFile över BytesIO) och kontrolleras: notstruktur, att varje
wikilänk matchar en verklig lagrumsnot (inga brutna länkar), frontmatter,
repetitionskort och att även overifierade lagrum får en not. Fail fast-stil
som test_export.py.
"""

from __future__ import annotations

import re
from io import BytesIO
from zipfile import ZipFile

from utils.obsidian import (
    CaseAnalys,
    bygg_valv,
    lagrumsnot,
    modulnot,
    notnamn,
    rattsfallsnot,
)
from utils.scenarier import Case, CaseFacit

# --- Testdata ---------------------------------------------------------------

FACIT = CaseFacit(
    rattsfraga="Har Anna och Bo ingått ett bindande avtal?",
    lagrum=("1 § AvtL", "6 § AvtL"),
    tillampningspunkter=("Anbud avgivet", "Ren och rättidig accept"),
    slutsats="Ja, ett avtal har slutits enligt 1 § AvtL.",
)
CASE = Case(
    id="avt-case-1",
    rubrik="Anbud och accept",
    svarighetsgrad="grund",
    uppskattad_tid_min=10,
    scenariotext="Anna skickar ett skriftligt anbud till Bo som svarar ja i tid.",
    facit=FACIT,
)
SVAR = {
    "rattsfragan": "Har parterna ingått avtal?",
    "norm": "1 § AvtL och 6 § AvtL reglerar anbud och accept.",
    "tillampning": "Anbudet var bindande enligt löftesprincipen.",
    "slutsats": "Avtal föreligger.",
}

# Studentsvar med ett påhittat lagrum (okänd lag) för att testa overifierat fall.
SVAR_MED_FEL = {
    **SVAR,
    "norm": "Detta regleras av 3 § FejkL enligt min mening.",
}

ANALYS = CaseAnalys(modul="Avtalsrätt", case=CASE, svar=SVAR)


def _wikilankar(text: str) -> set[str]:
    """Länkmål ur [[...]], normaliserade som Obsidian slår upp dem.

    "[[Not#Rubrik|alias]]" pekar på noten "Not"; rubrik- och aliasdelarna
    påverkar inte vilken fil länken leder till.
    """
    mal = set()
    for rå in re.findall(r"\[\[([^\]]+)\]\]", text):
        not_del = rå.split("#", 1)[0].split("|", 1)[0].strip()
        if not_del:
            mal.add(not_del)
    return mal


# --- notnamn ----------------------------------------------------------------

def test_notnamn_behaller_paragraftecken():
    assert notnamn("3 kap. 1 § SkL") == "3 kap. 1 § SkL"


def test_notnamn_sanerar_forbjudna_tecken():
    smutsigt = 'a/b:c*d?e"f<g>h|i#j'
    rensat = notnamn(smutsigt)
    for tecken in '/:*?"<>|#':
        assert tecken not in rensat


# --- lagrumsnot -------------------------------------------------------------

def test_lagrumsnot_har_frontmatter_och_tagg():
    not_ = lagrumsnot("36 § AvtL")
    assert not_.startswith("---")
    assert "juridik/lagrum" in not_


def test_lagrumsnot_verifierat_har_lagen_nu_lank():
    not_ = lagrumsnot("36 § AvtL")
    assert "lagen.nu" in not_
    assert "VERIFIERAD" in not_


def test_lagrumsnot_overifierat_kraschar_inte_och_markeras():
    not_ = lagrumsnot("3 § FejkL")
    assert "3 § FejkL" in not_
    assert "VERIFIERAD" not in not_.split("taggar")[0] or "OKAND" in not_


# --- rattsfallsnot ----------------------------------------------------------

def test_rattsfallsnot_innehaller_studentsvar_och_facit():
    not_ = rattsfallsnot(ANALYS)
    assert "Avtal föreligger." in not_  # studentens slutsats
    # Facit finns med; lagrummet i slutsatsen har wikilänkats.
    assert "Ja, ett avtal har slutits enligt [[1 § AvtL]]." in not_


def test_rattsfallsnot_wikilankar_lagrum():
    not_ = rattsfallsnot(ANALYS)
    lankar = _wikilankar(not_)
    assert "1 § AvtL" in lankar
    assert "6 § AvtL" in lankar


def test_rattsfallsnot_har_repetitionskort():
    not_ = rattsfallsnot(ANALYS)
    assert "## Repetition" in not_
    assert "::" in not_
    # Facit-baserat: rättsfrågan på framsidan.
    assert FACIT.rattsfraga in not_


# --- modulnot ---------------------------------------------------------------

def test_modulnot_ar_moc_med_lankar():
    not_ = modulnot("Avtalsrätt", ("Anbud och accept",), ("1 § AvtL",))
    assert "[[Anbud och accept]]" in not_
    assert "[[1 § AvtL]]" in not_


# --- bygg_valv --------------------------------------------------------------

def _las_valv(poster) -> dict[str, str]:
    data = bygg_valv(poster)
    with ZipFile(BytesIO(data)) as z:
        return {namn: z.read(namn).decode("utf-8") for namn in z.namelist()}


def test_valv_har_forvantad_struktur():
    filer = _las_valv([ANALYS])
    assert "Juridik/Start.md" in filer
    assert any(n.startswith("Juridik/Moduler/") for n in filer)
    assert any(n.startswith("Juridik/Rattsfall/") for n in filer)
    assert any(n.startswith("Juridik/Lagrum/") for n in filer)


def test_valv_skapar_lagrumnot_endast_for_refererade():
    filer = _las_valv([ANALYS])
    lagrumfiler = {n for n in filer if n.startswith("Juridik/Lagrum/")}
    assert "Juridik/Lagrum/1 § AvtL.md" in lagrumfiler
    assert "Juridik/Lagrum/6 § AvtL.md" in lagrumfiler
    # Inga föräldralösa lagrum ur hela registret.
    assert len(lagrumfiler) <= 4


def test_valv_har_inga_brutna_wikilankar():
    filer = _las_valv([ANALYS])
    notnamn_i_valvet = {
        n.rsplit("/", 1)[-1].removesuffix(".md") for n in filer
    }
    for innehall in filer.values():
        for mal in _wikilankar(innehall):
            assert mal in notnamn_i_valvet, f"Bruten wikilänk: [[{mal}]]"


def test_valv_skapar_not_for_overifierat_lagrum():
    analys = CaseAnalys(modul="Avtalsrätt", case=CASE, svar=SVAR_MED_FEL)
    filer = _las_valv([analys])
    assert "Juridik/Lagrum/3 § FejkL.md" in filer
    # Wikilänken finns i rättsfallsnoten trots att lagrummet är påhittat.
    rattsfall = next(v for n, v in filer.items() if n.startswith("Juridik/Rattsfall/"))
    assert "[[3 § FejkL]]" in rattsfall


def test_valv_tom_input_ger_giltig_zip_med_start():
    filer = _las_valv([])
    assert "Juridik/Start.md" in filer
