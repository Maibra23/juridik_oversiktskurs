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

    Ligger den där försvinner den vid nästa rerun. Knappblockets kropp ska
    bara sätta flaggan; själva rättningen och facit hör hemma i det block som
    grindas av flaggan, så att de överlever att studenten klickar någon
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
    facit = next(i for i, r in enumerate(rader) if "Visa facit" in r)
    assert grind < facit, "Facit ska ligga efter grinden, inte före"
    assert _indrag(rader[facit]) > _indrag(rader[grind]), (
        "Facitexpandern ligger utanför rättad-blocket och visas utan försök"
    )
