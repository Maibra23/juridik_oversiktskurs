"""Läs-API mot lagtextkorpusen i data/lagtext/.

Korpusen finns för att tutorn ska kunna **läsa** lagen i stället för att
minnas den. Mätt mot Qwen3-8B är skillnaden avgörande: modellen vet vilka
lagrum som gäller när de står i prompten, men påstår fel saker om vad de
innehåller. Den hävdade att 36 § AvtL reglerar avtals ingående (paragrafen är
generalklausulen om jämkning) och myntade termer som "proxim
meningskausalitet". Båda felen kommer av att den gissar ur egna vikter.

Bärande regel: **den här modulen gissar aldrig.** Saknas en paragraf
returneras ``None``, och promptbyggarna utelämnar då lagtexten hellre än att
skicka något påhittat. En tom lucka är alltid bättre än en trovärdig lögn.

Korpusen byggs av scripts/hamta_lagtext.py och ligger i git, så appen
fungerar offline. Ren modul utan Streamlit-beroende.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from utils.lagrum import Lagrumsref, _som_ref, lagrum_register

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "lagtext"


@dataclass(frozen=True)
class Lagtext:
    """Författningstexten för en lag, paragraf för paragraf."""

    forkortning: str
    namn: str
    sfs: str
    kalla: str
    hamtad: str
    licens: str
    # Nyckel: "4" för oindelade lagar, "2:1" för kapitelindelade.
    paragrafer: dict[str, str]


def _nyckel_for(ref: Lagrumsref) -> str:
    """Paragrafnyckeln för en parsad referens."""
    return f"{ref.kapitel}:{ref.paragraf}" if ref.kapitel else str(ref.paragraf)


@lru_cache(maxsize=1)
def ladda_lagtext() -> dict[str, Lagtext]:
    """Läs och cachea hela korpusen, nycklad på lagförkortning.

    Lagar utan fil hoppas tyst över: korpusen får byggas ut stegvis, och en
    saknad lag ska degradera till "ingen lagtext" i prompten, inte till ett
    kraschande appstart.
    """
    if not DATA_DIR.exists():
        return {}

    ut: dict[str, Lagtext] = {}
    for fil in sorted(DATA_DIR.glob("*.json")):
        rad = json.loads(fil.read_text(encoding="utf-8"))
        forkortning = str(rad["forkortning"])
        ut[forkortning] = Lagtext(
            forkortning=forkortning,
            namn=str(rad["namn"]),
            sfs=str(rad["sfs"]),
            kalla=str(rad["kalla"]),
            hamtad=str(rad["hamtad"]),
            licens=str(rad.get("licens", "")),
            paragrafer={str(k): str(v) for k, v in rad.get("paragrafer", {}).items()},
        )
    return ut


def hamta_paragraftext(ref: Lagrumsref | str) -> str | None:
    """Författningstexten för ett lagrum, eller None.

    None betyder alltid "vet inte" och aldrig "tom paragraf". Anroparen ska
    utelämna lagtexten i det läget, inte fylla i något eget.
    """
    parsad = _som_ref(ref)
    if parsad is None:
        return None
    if parsad.forkortning not in lagrum_register():
        return None

    lag = ladda_lagtext().get(parsad.forkortning)
    if lag is None:
        return None
    return lag.paragrafer.get(_nyckel_for(parsad))


def har_lagtext(ref: Lagrumsref | str) -> bool:
    """Sant om korpusen har text för lagrummet."""
    return hamta_paragraftext(ref) is not None


def lagtext_block(refs: Iterable[Lagrumsref | str]) -> str:
    """Bygg promptblocket med ordagrann lagtext för angivna lagrum.

    Lagrum utan text hoppas över helt. Finns inget att visa returneras en tom
    sträng, så att prompten slipper en rubrik utan innehåll.

    Ordningen följer anroparens, med dubbletter borttagna: facits lagrum bör
    komma före studentens egna.
    """
    sedda: set[str] = set()
    rader: list[str] = []
    for ref in refs:
        parsad = _som_ref(ref)
        if parsad is None:
            continue
        etikett = parsad.ra.strip() or _kanonisk_etikett(parsad)
        if etikett in sedda:
            continue
        text = hamta_paragraftext(parsad)
        if not text:
            continue
        sedda.add(etikett)
        rader.append(f"{etikett}:\n{text}")

    if not rader:
        return ""

    return (
        "LAGTEXT (ordagrann, hämtad ur författningen):\n"
        + "\n\n".join(rader)
        + "\n\nBygg din bedömning på lagtexten ovan. Påstå aldrig något om vad "
        "en paragraf innehåller som inte står i texten. Skriv lagrummen exakt "
        "som rubrikerna ovan, med paragrafnumret först."
    )


def _kanonisk_etikett(ref: Lagrumsref) -> str:
    """Skriv referensen på standardform: "2 kap. 1 § SkL"."""
    if ref.kapitel:
        return f"{ref.kapitel} kap. {ref.paragraf} § {ref.forkortning}"
    return f"{ref.paragraf} § {ref.forkortning}"
