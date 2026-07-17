"""Central texthjälp för användarsynliga strängar.

Samlar språklogik som annars dupliceras (och blir fel) ute i sidorna,
t.ex. svensk kongruensböjning av räknade enheter ("1 genomfört rättsfall"
men "3 genomförda rättsfall"). Språk-QA:n i tests/test_sprak.py och
tests/test_texter.py granskar texterna innan de når UI:t.
"""

from __future__ import annotations


def antal_med_enhet(antal: int, singular: str, plural: str) -> str:
    """Formatera ett antal med rätt böjd enhet: "1 genomfört rättsfall".

    ``singular`` används endast för exakt 1; 0 och alla andra antal får
    ``plural`` (svensk kongruens). Negativa antal är ett programfel.
    """
    if antal < 0:
        raise ValueError(f"Antal kan inte vara negativt: {antal}")
    enhet = singular if antal == 1 else plural
    return f"{antal} {enhet}"
