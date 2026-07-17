"""Tester för utils/rattskarta.py: Obsidiankarta över det svenska rättssystemet.

Kartan är en hierarkisk, hopfällbar och klickbar trädvy (Obsidian-callouts med
wikilänkar) som visar hur rättsområdena hänger ihop och när varje lag ska
övervägas. Grundningsprincipen gäller även här: varje lag i kartan måste
finnas i kursens lagrumsregister — kartan får aldrig nämna påhittade lagar.
"""

from __future__ import annotations

import io
import zipfile

from utils.lagrum import lagrum_register
from utils.rattskarta import (
    ladda_rattssystem,
    lagnot,
    omradesnot,
    rattskarta_filer,
    rattskarta_not,
)


# --- Datamodell och grundning -------------------------------------------------

def test_rattssystemet_laddar_med_omraden():
    omraden = ladda_rattssystem()
    assert len(omraden) >= 3
    namn = [o.namn for o in omraden]
    assert "Civilrätt" in namn


def test_alla_lagar_i_kartan_finns_i_registret():
    register = lagrum_register()
    for omrade in ladda_rattssystem():
        for under in omrade.underomraden:
            for lag in under.lagar:
                assert lag.forkortning in register, (
                    f"{lag.forkortning} i kartan saknas i lagrumsregistret"
                )


def test_kartan_tacker_hela_lagrumsregistret():
    """Varje lag i kursens register ska ha en plats i kartan."""
    i_kartan = {
        lag.forkortning
        for omrade in ladda_rattssystem()
        for under in omrade.underomraden
        for lag in under.lagar
    }
    saknas = set(lagrum_register()) - i_kartan
    assert not saknas, f"Lagar utan plats i rättskartan: {sorted(saknas)}"


def test_relaterade_lagar_pekar_pa_kanda_forkortningar():
    kanda = set(lagrum_register())
    for omrade in ladda_rattssystem():
        for under in omrade.underomraden:
            for lag in under.lagar:
                for rel in lag.relaterade:
                    assert rel in kanda, f"{lag.forkortning} relaterar till okänd {rel}"


def test_alla_noder_har_beskrivning_och_nar():
    for omrade in ladda_rattssystem():
        assert omrade.beskrivning and omrade.nar
        for under in omrade.underomraden:
            assert under.beskrivning and under.nar, under.namn
            for lag in under.lagar:
                assert lag.beskrivning and lag.nar, lag.forkortning


# --- Kartnoten (dashboard) ------------------------------------------------------

def test_rattskarta_not_har_hopfallbara_callouts():
    not_md = rattskarta_not()
    assert "> [!" in not_md          # callout = färgad ruta
    assert "]- " in not_md           # "-" = hopfällbar


def test_rattskarta_not_lankar_omraden_och_lagar():
    not_md = rattskarta_not()
    assert "[[Civilrätt" in not_md
    assert "[[AvtL" in not_md
    assert "[[BrB" in not_md


def test_rattskarta_not_har_falltypsguide():
    """Snabbguiden fall -> lag hjälper studenten hitta rätt lag direkt."""
    not_md = rattskarta_not()
    assert "Vilken lag gäller" in not_md


def test_rattskarta_not_anvander_olika_callouttyper():
    """Olika toppområden ska få olika färger (olika callouttyper)."""
    not_md = rattskarta_not()
    typer = {rad.split("[!")[1].split("]")[0] for rad in not_md.splitlines() if "[!" in rad}
    assert len(typer) >= 3, f"För få callouttyper för färgkodning: {typer}"


# --- Lag- och områdesnoter ------------------------------------------------------

def test_lagnot_innehaller_beskrivning_nar_och_lagen_nu():
    md = lagnot("AvtL")
    assert "AvtL" in md
    assert "När ska lagen övervägas" in md
    assert "lagen.nu/1915:218" in md


def test_lagnot_lankar_relaterade_lagar():
    md = lagnot("KöpL")
    assert "[[KKöpL]]" in md or "[[KKöpL|" in md


def test_lagnot_okand_forkortning_ger_fel():
    import pytest

    with pytest.raises(KeyError):
        lagnot("PåhittL")


def test_omradesnot_lankar_sina_lagar():
    omrade = next(o for o in ladda_rattssystem() if o.namn == "Civilrätt")
    md = omradesnot(omrade)
    assert "[[AvtL" in md
    assert "## " in md  # underområden som rubriker (nås via [[Civilrätt#...]])


# --- Valvintegration -------------------------------------------------------------

def test_rattskarta_filer_har_dashboard_och_lagnoter():
    filer = rattskarta_filer()
    assert "Juridik/Rättskartan.md" in filer
    assert any(n.startswith("Juridik/Lagar/") for n in filer)
    assert any(n.startswith("Juridik/Rättssystemet/") for n in filer)


def test_valv_innehaller_rattskartan_aven_utan_analyser():
    from utils.obsidian import bygg_valv

    zf = zipfile.ZipFile(io.BytesIO(bygg_valv(())))
    namn = zf.namelist()
    assert "Juridik/Rättskartan.md" in namn
    start = zf.read("Juridik/Start.md").decode("utf-8")
    assert "[[Rättskartan]]" in start
