"""Tester för navigeringsträdet i sidopanelen.

Vaktar den enda invariant som gör trädet trovärdigt: varje modul i trädet
pekar antingen på en sida som faktiskt finns i sidor/, eller saknar sida
och visas som "(kommer)". Ett stavfel i en sökväg ska fångas här och inte
som en trasig länk i UI:t.

Kontrollerar dessutom att trädet och st.Page-registret i streamlit_app.py
hålls i synk, eftersom sidopanelen känner igen den öppna sidan på titeln.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from utils.navigation import (
    NAV_TRAD,
    Grupp,
    Modul,
    alla_moduler,
    byggda_namn,
    byggda_sidor,
    sida_finns,
)

ROT = Path(__file__).resolve().parent.parent
MODULER = tuple(alla_moduler())


def test_tradet_har_moduler():
    assert len(MODULER) >= 10, "Navigeringsträdet ser oväntat tomt ut."


@pytest.mark.parametrize("modul", MODULER, ids=lambda m: m.namn)
def test_modul_pekar_pa_befintlig_sida_eller_ar_planerad(modul: Modul):
    """Varje modul pekar på en fil som finns, eller är märkt som planerad."""
    if modul.planerad:
        assert modul.sida is None
        return
    assert modul.sida is not None
    assert sida_finns(modul.sida), (
        f"{modul.namn!r} pekar på {modul.sida!r} som inte finns i projektet."
    )


def test_planerade_moduler_har_ingen_sida():
    """Planerad och byggd är varandras motsatser, aldrig något mittemellan."""
    for modul in MODULER:
        assert modul.planerad == (modul.sida is None), (
            f"{modul.namn!r} är inkonsekvent märkt."
        )


def test_inga_dubbletter_av_sidor():
    sidor = byggda_sidor()
    assert len(sidor) == len(set(sidor)), "Samma sida förekommer flera gånger."


def test_inga_dubbletter_av_modulnamn():
    namn = [m.namn for m in MODULER]
    assert len(namn) == len(set(namn)), f"Dubblerade modulnamn: {namn}"


def test_alla_grupper_har_barn():
    """En tom rubriknivå ska aldrig ritas ut i panelen."""

    def granska(noder):
        for nod in noder:
            if isinstance(nod, Grupp):
                assert nod.barn, f"Gruppen {nod.namn!r} saknar barn."
                granska(nod.barn)

    granska(NAV_TRAD)


def test_alla_modulsidor_finns_med_i_tradet():
    """Ingen sida i sidor/ får sakna plats i navigeringen.

    Utan den här kontrollen kan en ny modulsida bli oåtkomlig, eftersom
    Streamlits egen sidlista är avstängd (position="hidden").
    """
    pa_disk = {
        f"sidor/{p.name}" for p in (ROT / "sidor").glob("*.py") if p.name != "__init__.py"
    }
    i_tradet = set(byggda_sidor())
    assert pa_disk == i_tradet, (
        f"Sidor utanför trädet: {sorted(pa_disk - i_tradet)}. "
        f"Träd utan fil: {sorted(i_tradet - pa_disk)}."
    )


def test_tradets_namn_matchar_sidregistret():
    """Modulnamnen i trädet ska vara identiska med titlarna i st.Page.

    Sidopanelen fäller ut rätt sektion genom att jämföra den öppna sidans
    titel med modulnamnet, så de två listorna måste hållas i synk.
    """
    kalla = (ROT / "streamlit_app.py").read_text(encoding="utf-8")
    titlar = set(re.findall(r'st\.Page\("[^"]+",\s*title="([^"]+)"', kalla))
    assert set(byggda_namn()) == titlar, (
        f"Bara i trädet: {sorted(set(byggda_namn()) - titlar)}. "
        f"Bara i registret: {sorted(titlar - set(byggda_namn()))}."
    )
