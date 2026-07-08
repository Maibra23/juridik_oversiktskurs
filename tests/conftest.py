"""Delade pytest-fixturer.

Streamlit läser .streamlit/secrets.toml första gången st.secrets används,
vilket kan läcka in en lokal token i env-baserade tester. Autouse-fixturen
nedan tömmer den in-memory-secrets-dicten före varje test. Tester som
uttryckligen vill ha secrets kan fylla på den igen.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolera_streamlit_secrets(monkeypatch):
    try:
        import streamlit as st
    except ImportError:
        return
    try:
        st.secrets._secrets = {}
        st.secrets._file_watchers = []
    except Exception:
        monkeypatch.setattr(st, "secrets", {}, raising=False)
