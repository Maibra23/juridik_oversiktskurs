"""Läs-API mot lagstrukturen i data/lagstruktur/.

Strukturen är lagens egen disposition -- kapitelrubriker, momentrubriker och
vilka paragrafer som hör till vad -- hämtad ur Riksdagens öppna data av
scripts/hamta_lagstruktur.py och committad så att appen fungerar offline.

Den fyller två roller. Dels ger den lagkortet en ryggrad att gruppera
lagavsnitten under, dels är den facit när lagavsnittens paragrafgränser
ska verifieras (utils.lagavsnitt_kontroll).

Till skillnad från utils.lagtext, som får degradera tyst när en paragraf
saknas, validerar den här modulen strikt vid inläsning. Skälet är att en
trasig struktur inte ger en tom lucka utan ett felaktigt påstående om hur
lagen är uppbyggd. En saknad fil är däremot inte ett fel här; det hanteras
av anroparen, och ett test vaktar att ingen fil saknas.

Ren modul utan Streamlit-beroende.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "lagstruktur"


@dataclass(frozen=True)
class Kapitel:
    """Ett kapitel i lagen med sin egen rubrik och sina paragrafer."""

    nummer: str
    rubrik: str
    paragrafer: tuple[str, ...]


@dataclass(frozen=True)
class Moment:
    """En momentrubrik i lagen. ``kapitel`` är None för kapitellösa lagar."""

    rubrik: str
    kapitel: str | None
    paragrafer: tuple[str, ...]


@dataclass(frozen=True)
class Lagstruktur:
    """Hela lagens disposition. Minst en av kapitel och moment är ifylld."""

    forkortning: str
    namn: str
    sfs: str
    kalla: str
    kallnamn: str
    hamtad: str
    licens: str
    kapitel: tuple[Kapitel, ...]
    moment: tuple[Moment, ...]


def _krav_lista(rad: dict, nyckel: str) -> list:
    varde = rad.get(nyckel, [])
    if not isinstance(varde, list):
        raise ValueError(
            f"{rad.get('forkortning', '?')}: '{nyckel}' måste vara en lista, "
            f"fick {type(varde).__name__}"
        )
    return varde


def _bygg_struktur(rad: dict) -> Lagstruktur:
    """Validera en inläst rad och bygg den immutabla modellen."""
    forkortning = str(rad["forkortning"])

    kapitel = tuple(
        Kapitel(
            nummer=str(k["nummer"]),
            rubrik=str(k["rubrik"]),
            paragrafer=tuple(str(p) for p in k.get("paragrafer", ())),
        )
        for k in _krav_lista(rad, "kapitel")
    )
    moment = tuple(
        Moment(
            rubrik=str(m["rubrik"]),
            kapitel=None if m.get("kapitel") is None else str(m["kapitel"]),
            paragrafer=tuple(str(p) for p in m.get("paragrafer", ())),
        )
        for m in _krav_lista(rad, "moment")
    )

    if not kapitel and not moment:
        raise ValueError(
            f"{forkortning}: strukturen saknar både kapitel och moment. "
            "Varje lag har minst en rubriknivå -- hämta om lagen."
        )

    nummer = {k.nummer for k in kapitel}
    for m in moment:
        if m.kapitel is not None and m.kapitel not in nummer:
            raise ValueError(
                f"{forkortning}: momentet {m.rubrik!r} pekar på kapitel "
                f"{m.kapitel}, som inte finns i strukturen."
            )

    return Lagstruktur(
        forkortning=forkortning,
        namn=str(rad["namn"]),
        sfs=str(rad["sfs"]),
        kalla=str(rad.get("kalla", "")),
        kallnamn=str(rad.get("kallnamn", "")),
        hamtad=str(rad.get("hamtad", "")),
        licens=str(rad.get("licens", "")),
        kapitel=kapitel,
        moment=moment,
    )


@lru_cache(maxsize=1)
def ladda_lagstruktur() -> dict[str, Lagstruktur]:
    """Läs och cachea alla strukturfiler, nycklade på lagförkortning."""
    if not DATA_DIR.exists():
        return {}

    ut: dict[str, Lagstruktur] = {}
    for fil in sorted(DATA_DIR.glob("*.json")):
        struktur = _bygg_struktur(json.loads(fil.read_text(encoding="utf-8")))
        ut[struktur.forkortning] = struktur
    return ut


def kapitelrubrik(forkortning: str, nummer: str) -> str | None:
    """Rubriken för ett kapitel, eller None om lagen eller kapitlet är okänt."""
    struktur = ladda_lagstruktur().get(forkortning)
    if struktur is None:
        return None
    for kapitel in struktur.kapitel:
        if kapitel.nummer == nummer:
            return kapitel.rubrik
    return None


def antal_kapitel(forkortning: str) -> int:
    """Antal kapitel i hela lagen. Noll för lagar utan kapitelindelning."""
    struktur = ladda_lagstruktur().get(forkortning)
    return 0 if struktur is None else len(struktur.kapitel)


def paragrafnycklar_i(struktur: Lagstruktur) -> frozenset[str]:
    """Alla paragrafnycklar en struktur nämner, oavsett rubriknivå.

    Kapitel och moment slås ihop var för sig i stället för att packas upp i
    samma tupel: de är skilda typer utan gemensam bas, och en hopslagen tupel
    skulle bara vara ``object`` för typkontrollen.
    """
    return frozenset(
        {nyckel for kap in struktur.kapitel for nyckel in kap.paragrafer}
        | {nyckel for mom in struktur.moment for nyckel in mom.paragrafer}
    )


def paragrafnycklar(forkortning: str) -> frozenset[str]:
    """Alla paragrafnycklar lagen faktiskt har, enligt källan."""
    struktur = ladda_lagstruktur().get(forkortning)
    if struktur is None:
        return frozenset()
    return paragrafnycklar_i(struktur)
