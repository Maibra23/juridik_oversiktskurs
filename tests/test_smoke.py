"""Röktester för hela flödet.

Verifierar att:
- alla sidor i pages/ kan importeras (körs i Streamlits bare mode utan token),
- alla scenariofiler i data/scenarier laddas och strukturvalideras,
- varje lagrum i case-facit, quizalternativ och lagrumsjakt verifieras mot
  lagrum.json,
- varje flervalsfråga har exakt ett rätt svar.

Detta är sista säkringen innan innehåll läggs till: en trasig referens eller
en felmärkt fråga fångas här i stället för i UI:t.
"""

from __future__ import annotations

import importlib.util
import warnings
from pathlib import Path

import pytest

from utils.lagrum import STATUS_VERIFIERAD, validera_lagrum
from utils.quiz import ratt_alternativ_index
from utils.scenarier import (
    SCENARIER_DIR,
    alla_lagrum,
    fragor_utan_exakt_ett_ratt,
    ladda_fil,
    ogiltiga_lagrum,
)

PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"

SCENARIOFILER = sorted(SCENARIER_DIR.glob("*.json"))
SIDFILER = sorted(PAGES_DIR.glob("*.py"))


@pytest.mark.parametrize("sidfil", SIDFILER, ids=lambda p: p.name)
def test_alla_sidor_kan_importeras(sidfil: Path):
    """Varje sida i pages/ ska kunna köras utan att krascha (bare mode)."""
    spec = importlib.util.spec_from_file_location(f"page_{sidfil.stem}", sidfil)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        spec.loader.exec_module(mod)


@pytest.mark.parametrize("scenariofil", SCENARIOFILER, ids=lambda p: p.name)
def test_alla_scenariofiler_laddas(scenariofil: Path):
    """Varje scenariofil ska strukturvalideras utan fel."""
    modul = ladda_fil(scenariofil)
    assert modul.modul


@pytest.mark.parametrize("scenariofil", SCENARIOFILER, ids=lambda p: p.name)
def test_alla_lagrum_i_facit_verifieras(scenariofil: Path):
    """Alla lagrum i facit, alternativ och lagrumsjakt måste finnas i registret."""
    modul = ladda_fil(scenariofil)
    ogiltiga = ogiltiga_lagrum(modul)
    assert ogiltiga == (), f"Overifierade lagrum i {scenariofil.name}: {ogiltiga}"


@pytest.mark.parametrize("scenariofil", SCENARIOFILER, ids=lambda p: p.name)
def test_varje_mc_har_exakt_ett_ratt(scenariofil: Path):
    """Varje flervalsfråga ska ha exakt ett rätt svar."""
    modul = ladda_fil(scenariofil)
    dåliga = fragor_utan_exakt_ett_ratt(modul)
    assert dåliga == (), f"Frågor utan exakt ett rätt svar i {scenariofil.name}: {dåliga}"
    # Dubbelkontroll via quiz-modulens rättningslogik.
    for fraga in modul.flervalsfragor:
        ratt_alternativ_index(fraga)


def test_minst_tre_moduler_spelbara():
    """Definition of done Dag 2: minst tre moduler har fullt övningsinnehåll."""
    spelbara = 0
    for fil in SCENARIOFILER:
        modul = ladda_fil(fil)
        if modul.case and modul.flervalsfragor and modul.lagrumsjakt:
            spelbara += 1
    assert spelbara >= 3, f"Endast {spelbara} moduler är fullt spelbara, kräver minst 3."


def test_lagrum_facit_faktiskt_verifierade_status():
    """Stickprov: varje enskilt facit-lagrum ger status VERIFIERAD."""
    for fil in SCENARIOFILER:
        modul = ladda_fil(fil)
        for ref in alla_lagrum(modul):
            assert validera_lagrum(ref) == STATUS_VERIFIERAD, (
                f"{ref} i {fil.name} verifierades inte"
            )
