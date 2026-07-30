"""Nyckelbegrepp per delområde: inläsning, validering och uppslag.

Läser data/nyckelbegrepp.json, kursens deterministiska begreppsbank. Varje
begrepp har fyra obligatoriska fält (definition, förklaring, exempel och
igenkänning i scenario) och kan dessutom bära lagrum, en modullänk och en
kort skillnadsrad för kontrastpar (behörighet vs befogenhet och liknande).

Grundningsprincipen är densamma som i utils.rattskarta: varje lagrum i filen
måste kunna verifieras mot lagrumsregistret, och varje begrepp måste höra
till ett delområde som finns i data/rattssystem.json. Inläsningen vägrar
annars, så att appen aldrig visar ett begrepp som pekar på en paragraf som
inte finns.

Ren modul utan Streamlit-beroende.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from utils.lagrum import STATUS_VERIFIERAD, validera_lagrum

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nyckelbegrepp.json"

# De fyra fasta fälten som varje begrepp måste fylla i.
OBLIGATORISKA_FALT = ("definition", "forklaring", "exempel", "igenkanning")


@dataclass(frozen=True)
class Begrepp:
    """Ett nyckelbegrepp med sina fyra fasta fält och sina kopplingar."""

    id: str
    term: str
    omrade_id: str
    kapitel: str
    definition: str
    forklaring: str
    exempel: str
    igenkanning: str
    skillnaden: str = ""
    lagrum: tuple[str, ...] = ()
    modul_sida: str | None = None
    se_aven: tuple[str, ...] = ()


def _giltiga_omraden() -> set[str]:
    """Alla delområdes-id:n (löv-grenar) ur rättssystemkartan."""
    from utils.rattskarta import delomraden

    return {lov.id for lov in delomraden()}


def _bygg_begrepp(rad: dict, giltiga_omraden: set[str]) -> Begrepp:
    """Bygg och validera ett begrepp ur en JSON-rad. Fail fast vid fel."""
    bid = str(rad.get("id", "")).strip()
    if not bid:
        raise ValueError("Ett begrepp saknar id i data/nyckelbegrepp.json.")

    for falt in OBLIGATORISKA_FALT:
        if not str(rad.get(falt, "")).strip():
            raise ValueError(
                f"Begreppet {bid!r} saknar det obligatoriska fältet {falt!r}. "
                "Alla fyra fälten (definition, forklaring, exempel, "
                "igenkanning) måste vara ifyllda."
            )

    omrade_id = str(rad.get("omrade_id", ""))
    if omrade_id not in giltiga_omraden:
        raise ValueError(
            f"Begreppet {bid!r} pekar på delområdet {omrade_id!r} som inte "
            "finns i data/rattssystem.json."
        )

    lagrum = tuple(str(r) for r in rad.get("lagrum", ()))
    for ref in lagrum:
        status = validera_lagrum(ref)
        if status != STATUS_VERIFIERAD:
            raise ValueError(
                f"Begreppet {bid!r} hänvisar till {ref!r} som inte kunde "
                f"verifieras mot lagrumsregistret (status {status}). "
                "Begreppsbanken får aldrig innehålla ogrundade lagrum."
            )

    sida = rad.get("modul_sida")
    return Begrepp(
        id=bid,
        term=str(rad["term"]),
        omrade_id=omrade_id,
        kapitel=str(rad.get("kapitel", "")),
        definition=str(rad["definition"]).strip(),
        forklaring=str(rad["forklaring"]).strip(),
        exempel=str(rad["exempel"]).strip(),
        igenkanning=str(rad["igenkanning"]).strip(),
        skillnaden=str(rad.get("skillnaden", "")).strip(),
        lagrum=lagrum,
        modul_sida=str(sida) if sida else None,
        se_aven=tuple(str(s) for s in rad.get("se_aven", ())),
    )


@lru_cache(maxsize=1)
def ladda_begrepp() -> tuple[Begrepp, ...]:
    """Läs, validera och cachea hela begreppsbanken."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Hittar inte begreppsdatat: {DATA_PATH}")

    rad = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    giltiga = _giltiga_omraden()

    begrepp = tuple(
        _bygg_begrepp(b, giltiga) for b in rad.get("begrepp", ())
    )
    if not begrepp:
        raise ValueError("Begreppsbanken innehåller inga begrepp.")

    ider = [b.id for b in begrepp]
    dubbletter = {i for i in ider if ider.count(i) > 1}
    if dubbletter:
        raise ValueError(f"Dubblerade begrepps-id: {sorted(dubbletter)}")

    return begrepp


def begrepp_per_omrade() -> dict[str, tuple[Begrepp, ...]]:
    """Gruppera begreppen per delområde, i rättssystemkartans ordning."""
    from utils.rattskarta import delomraden

    alla = ladda_begrepp()
    ut: dict[str, tuple[Begrepp, ...]] = {}
    for lov in delomraden():
        traffar = tuple(b for b in alla if b.omrade_id == lov.id)
        if traffar:
            ut[lov.id] = traffar
    return ut


def hamta_begrepp(bid: str) -> Begrepp | None:
    """Slå upp ett begrepp på id, eller None."""
    return next((b for b in ladda_begrepp() if b.id == bid), None)


def sok_begrepp(fras: str) -> tuple[Begrepp, ...]:
    """Fritextsök över term, definition och igenkänningsfältet."""
    q = (fras or "").strip().lower()
    if not q:
        return ladda_begrepp()
    return tuple(
        b
        for b in ladda_begrepp()
        if q in b.term.lower()
        or q in b.definition.lower()
        or q in b.igenkanning.lower()
        or any(q in r.lower() for r in b.lagrum)
    )
