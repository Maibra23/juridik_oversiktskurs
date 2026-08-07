"""RNTS-stegen och vilken aktivitet som tränar vilket steg.

RNTS är appens ryggrad, inte ett formulär. Den här modulen är den enda platsen
i koden där stegens namn definieras, och den enda platsen där kopplingen
aktivitet -> steg definieras, så att UI:t kan märka varje övning med vad den
faktiskt bygger. Stegens namn står med rätta även i löptext på flera ställen
(t.ex. utils/prompts.py, utils/obsidian.py, utils/modulvy.py) — det är bara
koden som ska ha en enda källa.

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
