"""Test för modulsidans grindar: facit ska överleva en rerun och kosta ett försök.

Testen läser källkoden i stället för att köra Streamlit, eftersom felet är
strukturellt: facitgrindens indrag avgör om den bara renderas i den rerun där
knappen trycktes. AppTest hade inte fångat det utan en andra interaktion.
"""

from __future__ import annotations

import inspect

from utils import modulvy
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


def test_jaktfacitgrinden_ligger_inte_i_knappblocket():
    """Facitgrinden får inte renderas inuti `if st.button("Rätta")`.

    Ligger den där försvinner den vid nästa rerun. Knappblockets kropp ska
    bara sätta flaggan; själva rättningen och facitgrinden (som i sin tur
    grindar facit bakom ett eget försök, se Task 3) hör hemma i det block
    som grindas av flaggan, så att de överlever att studenten klickar någon
    annanstans på sidan.
    """
    rader = inspect.getsource(modulvy._rendera_jaktfraga).splitlines()

    def _indrag(rad: str) -> int:
        return len(rad) - len(rad.lstrip())

    knapp = next(i for i, r in enumerate(rader) if 'st.button("Rätta"' in r)
    assert "st.session_state[rattad_nyckel] = True" in rader[knapp + 1], (
        "Knappblockets kropp ska bara sätta flaggan"
    )
    grind = next(
        i for i, r in enumerate(rader) if "st.session_state.get(rattad_nyckel)" in r
    )
    facit = next(i for i, r in enumerate(rader) if "_rendera_facitgrind(" in r)
    assert grind < facit, "Facitgrinden ska ligga efter rättad-grinden, inte före"
    assert _indrag(rader[facit]) > _indrag(rader[grind]), (
        "Facitgrinden ligger utanför rättad-blocket och visas utan försök"
    )
