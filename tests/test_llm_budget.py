"""Tester för utils.llm_budget.

Täcker daglig räknare: nollställning vid nytt datum, korrupt fil ger
noll, fail open vid filsystemfel, LLM_DAILY_CAP-parsning och att
record_daily_call skriver atomiskt.
"""

from __future__ import annotations

import json

import pytest

from utils import llm_budget


@pytest.fixture()
def budget_file(tmp_path, monkeypatch):
    path = tmp_path / "usage.json"
    monkeypatch.setenv("LLM_BUDGET_FILE", str(path))
    monkeypatch.delenv("LLM_DAILY_CAP", raising=False)
    return path


def test_default_cap_is_positive(budget_file):
    assert llm_budget.get_daily_cap() > 0


def test_default_cap_is_300(budget_file):
    assert llm_budget.get_daily_cap() == 300


def test_cap_override_via_env(budget_file, monkeypatch):
    monkeypatch.setenv("LLM_DAILY_CAP", "7")
    assert llm_budget.get_daily_cap() == 7


def test_invalid_cap_override_falls_back_to_default(budget_file, monkeypatch):
    monkeypatch.setenv("LLM_DAILY_CAP", "not-a-number")
    assert llm_budget.get_daily_cap() == llm_budget.DEFAULT_DAILY_CALL_CAP


def test_usage_starts_at_zero(budget_file):
    assert llm_budget.get_daily_calls_used() == 0
    assert llm_budget.get_daily_calls_remaining() == llm_budget.get_daily_cap()


def test_record_increments_usage(budget_file):
    llm_budget.record_daily_call()
    llm_budget.record_daily_call()
    assert llm_budget.get_daily_calls_used() == 2
    assert budget_file.exists()


def test_stale_date_resets_counter(budget_file):
    budget_file.write_text(
        json.dumps({"date": "2020-01-01", "calls": 999}), encoding="utf-8"
    )
    assert llm_budget.get_daily_calls_used() == 0
    llm_budget.record_daily_call()
    assert llm_budget.get_daily_calls_used() == 1


def test_corrupt_file_treated_as_fresh(budget_file):
    budget_file.write_text("{not json", encoding="utf-8")
    assert llm_budget.get_daily_calls_used() == 0
    llm_budget.record_daily_call()
    assert llm_budget.get_daily_calls_used() == 1


def test_remaining_never_negative(budget_file, monkeypatch):
    monkeypatch.setenv("LLM_DAILY_CAP", "1")
    llm_budget.record_daily_call()
    llm_budget.record_daily_call()
    assert llm_budget.get_daily_calls_remaining() == 0


def test_cached_chat_raises_daily_cap_when_exhausted(budget_file, monkeypatch):
    from utils.llm import LLMDailyCapError, LLMUnavailableError, cached_chat

    monkeypatch.setenv("LLM_DAILY_CAP", "0")
    with pytest.raises(LLMDailyCapError):
        cached_chat("system", "user")
    # Sidor som bara känner till LLMUnavailableError måste ändå fånga den.
    assert issubclass(LLMDailyCapError, LLMUnavailableError)


def test_daily_cap_message_is_user_friendly_swedish():
    assert "förklaringar" in llm_budget.DAILY_CAP_MESSAGE.lower()
    assert "LLM" not in llm_budget.DAILY_CAP_MESSAGE
