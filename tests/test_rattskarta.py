"""Tester för utils/rattskarta.py: Obsidiankarta över det svenska rättssystemet.

Kartan är ett rekursivt träd av grenar (Obsidian-callouts med wikilänkar) som
visar hur rättsområdena hänger ihop och när varje lag ska övervägas.
Grundningsprincipen gäller: varje lag i kartan måste finnas i kursens
lagrumsregister — kartan får aldrig nämna påhittade lagar.
"""

from __future__ import annotations

import io
import zipfile

import pytest

from utils.lagrum import lagrum_register
from utils.rattskarta import (
    delomraden,
    ladda_rattssystem,
    lagnot,
    omradesnot,
    rattskarta_filer,
    rattskarta_not,
    toppgrenar,
)

# --- Datamodell och grundning ------------------------------------------------

def test_rattssystemet_laddar_med_toppgrenar():
    grenar = ladda_rattssystem()
    assert len(grenar) == 3
    namn = [g.namn for g in grenar]
    assert "Civilrätt" in namn
    assert "Offentlig rätt" in namn
    assert "Internationell rätt & EU-rätt" in namn


def test_alla_kurslagar_i_kartan_finns_i_registret():
    """Kurslagar (ej referenslagar) måste finnas i registret — grundningen.

    Referenslagar är per definition utanför registret; grundningsprincipen
    gäller bara kursens egna lagar.
    """
    register = lagrum_register()
    for lov in delomraden():
        for lag in lov.lagar:
            if lag.ar_referens:
                continue
            assert lag.forkortning in register, (
                f"{lag.forkortning} i kartan saknas i lagrumsregistret"
            )


def test_referenslagar_star_utanfor_registret():
    """Motsatsen: en referenslag får aldrig råka finnas i kursregistret."""
    register = lagrum_register()
    referens = [
        lag
        for lov in delomraden()
        for lag in lov.lagar
        if lag.ar_referens
    ]
    assert referens, "Inga referenslagar hittades i kartan"
    for lag in referens:
        assert lag.forkortning not in register, (
            f"{lag.forkortning} är referenslag men finns i kursregistret"
        )
        assert lag.namn, f"{lag.forkortning} saknar namn"
        assert lag.url, f"{lag.forkortning} saknar klicklänk"


def test_kartan_tacker_hela_lagrumsregistret():
    """Varje lag i kursens register ska ha en plats i kartan."""
    i_kartan = {
        lag.forkortning for lov in delomraden() for lag in lov.lagar
    }
    saknas = set(lagrum_register()) - i_kartan
    assert not saknas, f"Lagar utan plats i rättskartan: {sorted(saknas)}"


def test_relaterade_lagar_pekar_pa_kanda_forkortningar():
    kanda = set(lagrum_register())
    for lov in delomraden():
        for lag in lov.lagar:
            for rel in lag.relaterade:
                assert rel in kanda, f"{lag.forkortning} relaterar till okänd {rel}"


def test_alla_grenar_har_beskrivning():
    for topp in toppgrenar():
        _kontrollera_beskrivning(topp)


def _kontrollera_beskrivning(gren):
    assert gren.beskrivning, f"{gren.id} saknar beskrivning"
    for lag in gren.lagar:
        # Referenslagar är överblick och behöver ingen "När?"-text.
        if lag.ar_referens:
            assert lag.beskrivning, lag.forkortning
        else:
            assert lag.beskrivning and lag.nar, lag.forkortning
    for barn in gren.grenar:
        _kontrollera_beskrivning(barn)


# --- Kartnoten (dashboard) ---------------------------------------------------

def test_rattskarta_not_har_hopfallbara_callouts():
    not_md = rattskarta_not()
    assert "> [!" in not_md          # callout = färgad ruta
    assert "]- " in not_md           # "-" = hopfällbar


def test_rattskarta_not_lankar_grenar_och_lagar():
    not_md = rattskarta_not()
    assert "[[Civilrätt" in not_md
    assert "[[AvtL" in not_md
    assert "[[BrB" in not_md


def test_rattskarta_not_har_falltypsguide():
    """Snabbguiden fall -> lag hjälper studenten hitta rätt lag direkt."""
    not_md = rattskarta_not()
    assert "Vilken lag gäller" in not_md


def test_rattskarta_not_fargkodar_per_toppgren():
    """De två toppgrenarna ska få var sin callouttyp (färg)."""
    not_md = rattskarta_not()
    typer = {
        rad.split("[!")[1].split("]")[0]
        for rad in not_md.splitlines()
        if "[!" in rad and "]- " in rad
    }
    # quote (offentlig rätt) och info (civilrätt).
    assert {"quote", "info"} <= typer


# --- Lag- och områdesnoter ---------------------------------------------------

def test_lagnot_innehaller_beskrivning_nar_och_lagen_nu():
    md = lagnot("AvtL")
    assert "AvtL" in md
    assert "När ska lagen övervägas" in md
    assert "lagen.nu/1915:218" in md


def test_lagnot_lankar_relaterade_lagar():
    md = lagnot("KöpL")
    assert "[[KKöpL]]" in md or "[[KKöpL|" in md


def test_lagnot_deep_lankar_till_toppgrenens_note():
    """Lagnoten pekar tillbaka in i toppgrenens note via en rubrik."""
    md = lagnot("AvtL")
    assert "[[Civilrätt#" in md


def test_lagnot_okand_forkortning_ger_fel():
    with pytest.raises(KeyError):
        lagnot("PåhittL")


def test_omradesnot_renderar_subtrad_med_rubriker():
    civilratt = next(g for g in ladda_rattssystem() if g.namn == "Civilrätt")
    md = omradesnot(civilratt)
    assert "[[AvtL" in md
    assert "## " in md  # grenar som rubriker (nås via [[Civilrätt#...]])
    # Doktrinen ska synas i rubrikerna.
    assert "Obligationsrätt" in md and "Sakrätt" in md


# --- Valvintegration ---------------------------------------------------------

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
