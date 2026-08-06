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
