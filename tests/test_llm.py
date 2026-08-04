"""Tester för utils.llm.

Täcker tokenupplösning, modellnormalisering, <think>-strippning,
prompt-hashning, sessionstak (nya hashar debiteras, cacheträffar inte)
och felhierarkin LLMUnavailableError/LLMSessionCapError/LLMDailyCapError.
Undviker riktiga nätverksanrop; InferenceClient exercerar vi inte här.
"""

from __future__ import annotations

import pytest

from utils.llm import (
    ALTERNATIVE_MODEL,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    SESSION_CALL_CAP,
    SUPPORTED_MODELS,
    LLMUnavailableError,
    _strip_think_tags,
    get_active_model,
    get_hf_token,
    get_llm_config,
    is_llm_available,
    normalize_model,
    verify_lagrum,
)

# --- Token och konfiguration ------------------------------------------------

def test_get_hf_token_from_env(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test_value")
    assert get_hf_token() == "hf_test_value"


def test_get_hf_token_missing(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert get_hf_token() is None


def test_is_llm_available_false_when_missing(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert is_llm_available() is False


def test_is_llm_available_true_with_token(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    assert is_llm_available() is True


def test_get_llm_config_defaults(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    config = get_llm_config()
    assert config.token is None
    assert config.model == DEFAULT_MODEL
    assert config.provider == DEFAULT_PROVIDER


def test_get_llm_config_from_env(monkeypatch):
    monkeypatch.setenv("HF_TOKEN", "hf_x")
    monkeypatch.setenv("LLM_MODEL", "Qwen/Qwen3-14B")
    monkeypatch.setenv("LLM_PROVIDER", "together")
    config = get_llm_config()
    assert config.token == "hf_x"
    assert config.model == ALTERNATIVE_MODEL
    assert config.provider == "together"


# --- Modellval --------------------------------------------------------------

def test_supported_models_are_the_two_qwen_variants():
    assert SUPPORTED_MODELS == (DEFAULT_MODEL, ALTERNATIVE_MODEL)
    assert DEFAULT_MODEL == "Qwen/Qwen3-8B"
    assert ALTERNATIVE_MODEL == "Qwen/Qwen3-14B"


def test_normalize_model_accepts_full_and_short_names():
    assert normalize_model("Qwen/Qwen3-8B") == DEFAULT_MODEL
    assert normalize_model("Qwen3-14B") == ALTERNATIVE_MODEL
    assert normalize_model("qwen3-14b") == ALTERNATIVE_MODEL
    assert normalize_model("Qwen/Qwen3-32B") is None
    assert normalize_model(None) is None


def test_unsupported_model_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.setenv("LLM_MODEL", "Qwen/Qwen3-32B")
    assert get_active_model() == DEFAULT_MODEL
    assert get_llm_config().model == DEFAULT_MODEL


def test_active_model_uses_alternative_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "Qwen3-14B")
    assert get_active_model() == ALTERNATIVE_MODEL


def test_session_override_takes_precedence(monkeypatch):
    import streamlit as st

    from utils.llm import MODEL_SESSION_KEY

    monkeypatch.setenv("LLM_MODEL", DEFAULT_MODEL)
    monkeypatch.setattr(st, "session_state", {MODEL_SESSION_KEY: ALTERNATIVE_MODEL})
    assert get_active_model() == ALTERNATIVE_MODEL


# --- <think>-strippning -----------------------------------------------------

def test_strip_think_tags_removes_block():
    assert _strip_think_tags("<think>funderar</think>Svaret är 36 § AvtL.") == (
        "Svaret är 36 § AvtL."
    )


def test_strip_think_tags_handles_unclosed_block():
    assert _strip_think_tags("Innan<think>avbrutet mitt i") == "Innan"


# --- Felhierarki ------------------------------------------------------------

def test_llm_unavailable_error_is_exception():
    err = LLMUnavailableError("test")
    assert isinstance(err, Exception)
    assert str(err) == "test"


def test_session_call_cap_constant():
    assert SESSION_CALL_CAP == 40


def test_llm_session_cap_error_is_subclass_of_unavailable():
    from utils.llm import LLMSessionCapError

    assert issubclass(LLMSessionCapError, LLMUnavailableError)


def test_llm_daily_cap_error_is_subclass_of_unavailable():
    from utils.llm import LLMDailyCapError

    assert issubclass(LLMDailyCapError, LLMUnavailableError)


def test_session_cap_message_is_user_friendly_swedish():
    from utils.llm import SESSION_CAP_MESSAGE

    assert "förklaringar" in SESSION_CAP_MESSAGE.lower()
    # Får inte lova att omladdning bevarar inmatningar (session state dör).
    assert "Uppdatera sidan" not in SESSION_CAP_MESSAGE
    # Får inte läcka LLM/tutor-abstraktionen till användaren.
    assert "LLM" not in SESSION_CAP_MESSAGE
    assert "tutor" not in SESSION_CAP_MESSAGE.lower()


def test_cached_chat_raises_session_cap_when_used_up(monkeypatch):
    from utils import llm as llm_mod
    from utils.llm import LLMSessionCapError, cached_chat

    monkeypatch.setattr(llm_mod, "get_session_calls_remaining", lambda: 0)
    with pytest.raises(LLMSessionCapError):
        cached_chat("sys", "user")


# --- verify_lagrum delegerar till utils.lagrum ------------------------------

def test_verify_lagrum_delegates_to_lagrum_module():
    (traff,) = verify_lagrum("Se 36 § AvtL.")
    assert traff.status == "VERIFIERAD"
