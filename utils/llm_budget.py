"""Serverbaserad daglig LLM-anropsbudget.

Sessionstaket dör med sessionen, så på en publik deploy skulle någon
kunna tömma HF-tokenbudgeten genom att ladda om sidan. Denna modul
för en filbaserad daglig räknare (data/.llm_daily_usage.json) som delas
av alla sessioner på värden och inte kan nollställas från UI:t.

Räknaren är rådgivande, inte faktureringskritisk: vid filsystemfel
öppnar vi hellre (appen fortsätter fungera) och loggar problemet.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_DAILY_CALL_CAP = 300

DAILY_CAP_MESSAGE = (
    "Dagens gemensamma budget för förklaringar är förbrukad. "
    "Rättning, quiz, lagrumslänkar och export fungerar som vanligt. "
    "Förklaringarna är tillgängliga igen i morgon."
)


def get_daily_cap() -> int:
    """Dagligt tak från inställningen LLM_DAILY_CAP, annars standardvärdet."""
    raw = os.environ.get("LLM_DAILY_CAP")
    if raw is None:
        try:
            import streamlit as st

            if "LLM_DAILY_CAP" in st.secrets:
                raw = str(st.secrets["LLM_DAILY_CAP"])
        except Exception:
            raw = None
    if raw is None:
        return DEFAULT_DAILY_CALL_CAP
    try:
        value = int(str(raw).strip())
    except ValueError:
        logger.warning("Ogiltigt LLM_DAILY_CAP %r, använder standardvärdet", raw)
        return DEFAULT_DAILY_CALL_CAP
    return max(0, value)


def _usage_file() -> Path:
    """Sökväg till budgetfilen.

    LLM_BUDGET_FILE har högst prioritet (används i test och som /tmp-fallback
    på deployer där data/ är skrivskyddad).
    """
    custom = os.environ.get("LLM_BUDGET_FILE")
    if custom:
        return Path(custom)
    return Path(__file__).resolve().parent.parent / "data" / ".llm_daily_usage.json"


def _read_usage() -> dict:
    """Läs dagens användning. Gammalt datum och korrupt fil nollställs."""
    today = date.today().isoformat()
    fresh = {"date": today, "calls": 0}
    path = _usage_file()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return fresh
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.warning("Kunde inte läsa budgetfilen %s: %s", path, exc)
        return fresh
    if not isinstance(raw, dict) or raw.get("date") != today:
        return fresh
    try:
        calls = max(0, int(raw.get("calls", 0)))
    except (TypeError, ValueError):
        return fresh
    return {"date": today, "calls": calls}


def get_daily_calls_used() -> int:
    """Antal LLM-anrop som registrerats idag över alla sessioner."""
    return _read_usage()["calls"]


def get_daily_calls_remaining() -> int:
    """Anrop kvar i dagens gemensamma budget. Aldrig negativt."""
    return max(0, get_daily_cap() - get_daily_calls_used())


def record_daily_call() -> None:
    """Registrera ett LLM-anrop i dagens gemensamma räknare.

    Fail open vid filsystemfel: budgeten skyddar kostnad, den får aldrig
    ta ner appen.
    """
    usage = _read_usage()
    usage = {"date": usage["date"], "calls": usage["calls"] + 1}
    path = _usage_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(usage), encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        logger.warning("Kunde inte skriva budgetfilen %s: %s", path, exc)
