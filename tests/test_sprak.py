"""Språk-QA: automatiska kontroller av svenskan innan den når UI:t.

Fångar den klass av fel som annars slinker igenom kodgranskning:
- inbäddade icke-latinska tecken som ser ut som latinska bokstäver
  (t.ex. ett kyrilliskt s-tecken mitt i ett svenskt ord)
- trasiga svenska tecken (ersättningstecknet U+FFFD efter felaktig kodning)

Kontrollen omfattar appens källkod, scenariodata och dokumentation —
allt som kan nå en användare eller utvecklare.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROT = Path(__file__).resolve().parent.parent

_GRANSKADE_SUFFIX = {".py", ".json", ".md", ".toml"}
_GRANSKADE_KATALOGER = ("utils", "pages", "tests", "data", "docs", ".streamlit")

# Skrivna som escapesekvenser så att den här filen inte flaggar sig själv.
_KYRILLISKA = re.compile("[\u0400-\u04ff]")
_ERSATTNINGSTECKEN = "\ufffd"


def _granskade_filer() -> list[Path]:
    filer = [p for p in ROT.glob("*") if p.is_file() and p.suffix in _GRANSKADE_SUFFIX]
    for katalog in _GRANSKADE_KATALOGER:
        filer += [
            p
            for p in (ROT / katalog).rglob("*")
            if p.is_file() and p.suffix in _GRANSKADE_SUFFIX
        ]
    return filer


@pytest.mark.parametrize("fil", _granskade_filer(), ids=lambda p: str(p.relative_to(ROT)))
def test_inga_kyrilliska_tecken(fil: Path):
    text = fil.read_text(encoding="utf-8", errors="replace")
    traffar = [
        (nr, rad)
        for nr, rad in enumerate(text.splitlines(), 1)
        if _KYRILLISKA.search(rad)
    ]
    assert not traffar, f"Kyrilliska tecken i {fil.name}: {traffar[:3]}"


@pytest.mark.parametrize("fil", _granskade_filer(), ids=lambda p: str(p.relative_to(ROT)))
def test_ingen_trasig_teckenkodning(fil: Path):
    text = fil.read_text(encoding="utf-8", errors="replace")
    assert _ERSATTNINGSTECKEN not in text, f"Trasig teckenkodning i {fil.name}"
