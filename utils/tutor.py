"""On demand-tutorhjälpare.

Centraliserar mönstret som varje sida använder: tutorförklaringen körs
ENDAST när studenten trycker på knappen, aldrig vid rerun. Genererad
text cachas i st.session_state tillsammans med en hash av de inputs som
producerade den; vid oförändrad hash återges texten gratis, vid ändrad
hash markeras den som inaktuell och knappen byter etikett till
"Uppdatera förklaringen".

Skillnad mot ekonomistyrning: efter varje generering renderas texten med
utils.ui.render_tutortext, som kör utils.lagrum.verify_lagrum och byter ut
verifierade lagrum mot klickbara chips och varnar för overifierade.
Felhantering: LLMSessionCapError -> sessionstakskort,
LLMDailyCapError -> dagsbudgetkort, LLMUnavailableError -> svenskt infokort.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

# --- Cachemodell (immutabel) ------------------------------------------------


@dataclass(frozen=True)
class Tutorsvar:
    """Ett cachat tutorsvar med hashen av de inputs som skapade det."""

    text: str
    input_hash: str


def _hash_inputs(system_prompt: str, user_prompt: str) -> str:
    """Stabil hash av (system, user) som identifierar en tutorgenerering."""
    payload = f"{system_prompt}\n||\n{user_prompt}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cache() -> dict:
    """Hämta (eller skapa) tutorcachen i session_state."""
    import streamlit as st

    return st.session_state.setdefault("tutor_cache", {})


def hamta_cachat(nyckel: str) -> Tutorsvar | None:
    """Returnera ett cachat tutorsvar för nyckeln, eller None."""
    try:
        return _cache().get(nyckel)
    except Exception:
        return None


def ar_inaktuell(nyckel: str, system_prompt: str, user_prompt: str) -> bool:
    """True om det finns ett cachat svar men dess inputs har ändrats."""
    cachat = hamta_cachat(nyckel)
    if cachat is None:
        return False
    return cachat.input_hash != _hash_inputs(system_prompt, user_prompt)


def _spara(nyckel: str, svar: Tutorsvar) -> None:
    """Lägg ett tutorsvar i cachen (ny dict, ingen mutation av gammalt svar)."""
    try:
        _cache()[nyckel] = svar
    except Exception:
        pass


def generera_tutorsvar(
    nyckel: str,
    system_prompt: str,
    user_prompt: str,
) -> Tutorsvar:
    """Anropa LLM:en och cachea svaret under ``nyckel``.

    Anropas endast när studenten uttryckligen begär en förklaring (knapptryck).
    Kastar vidare LLM-felhierarkin så att anroparen kan visa rätt infokort.
    """
    from utils.llm import cached_chat

    text = cached_chat(system_prompt, user_prompt)
    svar = Tutorsvar(text=text, input_hash=_hash_inputs(system_prompt, user_prompt))
    _spara(nyckel, svar)
    return svar


def tutorknapp(
    nyckel: str,
    system_prompt: str,
    user_prompt: str,
    etikett: str = "Be tutorn granska min analys",
    knappnyckel: str | None = None,
) -> None:
    """Rita tutorknappen, hantera generering, cache och rendering.

    Beteende:
    - Utan cachat svar: en knapp med ``etikett``. Genererar vid tryck.
    - Med aktuellt cachat svar: rendera det direkt (gratis, ingen ny LLM).
    - Med inaktuellt svar (inputs ändrade): visa det gamla svaret plus en
      knapp "Uppdatera förklaringen".
    - Fångar LLM-felhierarkin och visar svenska infokort i stället för att krascha.
    """
    import streamlit as st

    from utils.llm import LLMSessionCapError, LLMUnavailableError, LLMDailyCapError
    from utils.ui import (
        render_daily_cap_card,
        render_info,
        render_session_cap_card,
        render_tutortext,
    )

    cachat = hamta_cachat(nyckel)
    inaktuell = ar_inaktuell(nyckel, system_prompt, user_prompt)
    knappnyckel = knappnyckel or f"tutorknapp_{nyckel}"

    knapptext = etikett if cachat is None else "Uppdatera förklaringen"
    tryckt = st.button(knapptext, key=knappnyckel, type="primary")

    if tryckt:
        try:
            with st.spinner("Tutorn läser ditt svar …"):
                cachat = generera_tutorsvar(nyckel, system_prompt, user_prompt)
                inaktuell = False
        except LLMSessionCapError:
            render_session_cap_card()
            return
        except LLMDailyCapError:
            render_daily_cap_card()
            return
        except LLMUnavailableError:
            render_info(
                "Tutorn är inte tillgänglig just nu (ingen modell konfigurerad "
                "eller tillfälligt fel). Rättning, quiz, lagrumslänkar och facit "
                "fungerar som vanligt – prova tutorn igen om en stund."
            )
            return

    if cachat is not None:
        if inaktuell:
            render_info(
                "Ditt svar har ändrats sedan förklaringen skapades. Tryck på "
                "\"Uppdatera förklaringen\" för en ny granskning."
            )
        render_tutortext(cachat.text)
