"""Generering av nya rättsfall för Kunskapsutmaningen.

Studenten kan be om ett färskt, fiktivt rättsfall att testa sin förmåga på.
Fallet genereras av LLM men grundas deterministiskt: varje lagrum i facit
måste verifieras mot lagrumsregistret innan scenariot visas. Klarar inte
modellen det (påhitt, trasig JSON eller otillgänglig LLM) faller vi tillbaka
på ett kuraterat statiskt case ur modulen – appen är alltid användbar.

LLM-klienten injiceras (Protocol ChatKlient) så att logiken kan enhetstestas
helt utan nätverk.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from typing import Protocol

from utils.lagrum import STATUS_VERIFIERAD, validera_lagrum
from utils.llm import LLMUnavailableError
from utils.prompts import build_generate_prompt
from utils.scenarier import (
    Case,
    Modulscenarier,
    bygg_case_fran_dict,
    ladda_modul,
    lista_moduler,
)

MAX_FORSOK = 2

LLM_EJ_TILLGANGLIG_NOTIS = (
    "LLM är inte tillgänglig just nu – här är ett kuraterat rättsfall i stället."
)
GRUNDNING_MISSLYCKADES_NOTIS = (
    "Kunde inte generera ett grundat fall den här gången – här är ett kuraterat "
    "rättsfall i stället."
)

_FENCE_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class ChatKlient(Protocol):
    """Minsta gränssnitt generatorn behöver av en LLM-klient.

    Endast de två positionsargumenten används; en riktig LLMClient får ha fler
    defaultade parametrar och är ändå kompatibel.
    """

    def chat(self, system_prompt: str, user_prompt: str) -> str: ...


@dataclass(frozen=True)
class GenereratResultat:
    """Utfallet av en generering: ett case och varifrån det kom."""

    case: Case
    kalla: str  # "genererad" eller "fallback"
    notis: str | None = None


# --- Hjälpare ---------------------------------------------------------------

def _forkortningar_for_modul(modul: Modulscenarier) -> tuple[str, ...]:
    """Förkortningarna som modulens kuraterade innehåll faktiskt använder."""
    ordnade: list[str] = []
    for case in modul.case:
        for ref in case.facit.lagrum:
            fk = ref.split()[-1] if ref.split() else ""
            if fk and fk not in ordnade:
                ordnade.append(fk)
    return tuple(ordnade)


def _extrahera_json(svar: str) -> str:
    """Plocka ut JSON-kroppen ur ett svar, även om det är inbäddat i fences."""
    traff = _FENCE_PATTERN.search(svar)
    if traff:
        return traff.group(1).strip()
    return svar.strip()


def _case_ar_grundat(case: Case) -> bool:
    """Alla lagrum i facit måste verifieras – och minst ett måste finnas."""
    if not case.facit.lagrum:
        return False
    return all(validera_lagrum(ref) == STATUS_VERIFIERAD for ref in case.facit.lagrum)


def _forsok_bygg_grundat_case(svar: str) -> Case | None:
    """Parsa svaret till ett grundat Case, eller None vid fel/ogrundat."""
    try:
        rad = json.loads(_extrahera_json(svar))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(rad, dict):
        return None
    try:
        case = bygg_case_fran_dict(rad)
    except (KeyError, ValueError, TypeError):
        return None
    return case if _case_ar_grundat(case) else None


def _fallback_case(modul: Modulscenarier, rng: random.Random) -> Case:
    """Ett slumpat kuraterat case ur modulen (alltid grundat och validerat)."""
    return rng.choice(modul.case)


def _standardklient() -> ChatKlient | None:
    """Skapa en riktig LLM-klient, eller None om ingen token finns."""
    try:
        from utils.llm import LLMClient

        return LLMClient()
    except LLMUnavailableError:
        return None


# --- Publikt API ------------------------------------------------------------

def valj_slumpmodul(rng: random.Random | None = None) -> str:
    """Välj en slumpmässig modul för 'Överraska mig'."""
    rng = rng or random.Random()
    return rng.choice(lista_moduler())


def generera_case(
    modul_namn: str,
    klient: ChatKlient | None = None,
    rng: random.Random | None = None,
) -> GenereratResultat:
    """Generera ett grundat rättsfall för modulen, med fallback vid problem.

    Försöker upp till ``MAX_FORSOK`` gånger. Ett scenario returneras endast om
    varje lagrum i facit verifieras mot registret; annars faller vi tillbaka på
    ett kuraterat case ur modulen.
    """
    modul = ladda_modul(modul_namn)
    rng = rng or random.Random()
    forkortningar = _forkortningar_for_modul(modul)

    if klient is None:
        klient = _standardklient()
    if klient is None:
        return GenereratResultat(
            _fallback_case(modul, rng), "fallback", LLM_EJ_TILLGANGLIG_NOTIS
        )

    for forsok in range(MAX_FORSOK):
        system_prompt, user_prompt = build_generate_prompt(
            modul_namn, forkortningar, striktare=forsok > 0
        )
        try:
            svar = klient.chat(system_prompt, user_prompt)
        except LLMUnavailableError:
            return GenereratResultat(
                _fallback_case(modul, rng), "fallback", LLM_EJ_TILLGANGLIG_NOTIS
            )

        case = _forsok_bygg_grundat_case(svar)
        if case is not None:
            return GenereratResultat(case, "genererad")

    return GenereratResultat(
        _fallback_case(modul, rng), "fallback", GRUNDNING_MISSLYCKADES_NOTIS
    )
