"""Förbered kursavsnitten för visning i lagkortet.

Registret bär avsnitten platt, medan lagen är indelad i kapitel. Den här
modulen slår ihop de två: avsnitten grupperas under lagens egna
kapitelrubriker, och lagar utan kapitelindelning får en enda ogrupperad
lista. Vyn slipper därmed veta något om lagstrukturen.

Ren modul utan Streamlit-beroende: all formatering är testbar utan att
rendera något.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.lagrum import Kursavsnitt, Lag
from utils.lagstruktur import antal_kapitel, kapitelrubrik


@dataclass(frozen=True)
class Avsnittsrad:
    """En rad i lagkortets avsnittslista."""

    spann: str
    rubrik: str
    url: str


@dataclass(frozen=True)
class Kapitelgrupp:
    """Ett kapitel med sina kursavsnitt. ``kapitel`` är None för platta lagar."""

    kapitel: str | None
    rubrik: str
    avsnitt: tuple[Avsnittsrad, ...]


def formatera_spann(fran: int, till: int) -> str:
    """Paragrafspannet på svensk form: "36 §" för en, "1–9 §§" för flera.

    Paragraftecknet dubbleras bara vid flertal, och skiljetecknet är
    tankstreck. Ett "36 §§" läser studenten som slarv i just den detalj
    kursen ska lära ut.
    """
    if fran == till:
        return f"{fran} §"
    return f"{fran}–{till} §§"


def _rad(lag: Lag, avsnitt: Kursavsnitt) -> Avsnittsrad:
    return Avsnittsrad(
        spann=formatera_spann(avsnitt.paragraf_fran, avsnitt.paragraf_till),
        rubrik=avsnitt.beskrivning,
        url=avsnitt.lagen_nu_url or lag.lagen_nu_bas_url,
    )


def _sorteringsnyckel(avsnitt: Kursavsnitt) -> tuple[int, int]:
    """Lagens egen ordning: kapitel först, sedan paragraf."""
    kapitel = avsnitt.kapitel
    return (int(kapitel) if kapitel and kapitel.isdigit() else 0, avsnitt.paragraf_fran)


def gruppera_kursavsnitt(lag: Lag) -> tuple[Kapitelgrupp, ...]:
    """Gruppera lagens kursavsnitt under lagens egna kapitelrubriker.

    Lagar utan kapitelindelning ger exakt en grupp utan kapitel och utan
    rubrik, så att vyn kan rendera båda formerna med samma slinga.

    Ordningen är lagens, inte registrets. Registret är redaktionellt sorterat
    och kan lägga 6 kap. före 3 kap., vilket i ett lagkort läser som ett
    slarvfel: en student som letar efter 3 kap. förväntar sig den mellan 2
    och 4, precis som i författningen.
    """
    if not lag.kursavsnitt:
        return ()

    ordnade = sorted(lag.kursavsnitt, key=_sorteringsnyckel)

    if not lag.kapitelindelad:
        return (
            Kapitelgrupp(
                kapitel=None,
                rubrik="",
                avsnitt=tuple(_rad(lag, a) for a in ordnade),
            ),
        )

    ordning: list[str] = []
    per_kapitel: dict[str, list[Avsnittsrad]] = {}
    for avsnitt in ordnade:
        nyckel = avsnitt.kapitel or ""
        if nyckel not in per_kapitel:
            per_kapitel[nyckel] = []
            ordning.append(nyckel)
        per_kapitel[nyckel].append(_rad(lag, avsnitt))

    return tuple(
        Kapitelgrupp(
            kapitel=nyckel or None,
            rubrik=kapitelrubrik(lag.forkortning, nyckel) or "",
            avsnitt=tuple(per_kapitel[nyckel]),
        )
        for nyckel in ordning
    )


def tackningstext(lag: Lag) -> str:
    """Hur stor del av lagen kursen berör, eller tom sträng.

    Raden är lagkortets ärlighetskrav. Utan den läser studenten
    avsnittslistan som om lagen tog slut där -- kursen berör sex av
    konsumentköplagens nio kapitel och sex av brottsbalkens trettioåtta.
    Saknar lagen kapitel finns inget att räkna, och då ska raden utebli helt
    hellre än att gissa.
    """
    totalt = antal_kapitel(lag.forkortning)
    if not totalt:
        return ""
    berorda = len({a.kapitel for a in lag.kursavsnitt if a.kapitel})
    if not berorda:
        return ""
    return f"kursen täcker {berorda} av lagens {totalt} kapitel"
