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
_GRANSKADE_KATALOGER = ("utils", "sidor", "tests", "data", "docs", ".streamlit")

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


# Ikonförbudet i design_system.md 4.1 gäller hela appen. Vakten fångar emoji och
# de dekorativa glyfer som tidigare läckt in (tärning, rundpil, statusprickar,
# stepperikoner). Skrivna som escapesekvenser så att den här filen inte flaggar
# sig själv.
_FORBJUDNA_GLYFER = (
    "\U0001f7e2",  # grön cirkel
    "\u26aa",  # vit cirkel
    "\U0001f3b2",  # tärning
    "\u21ba",  # rundpil moturs
    "\u25cf",  # fylld cirkel
    "\u2713",  # bock
)
_EMOJI = re.compile("[\U0001f300-\U0001faff\u2600-\u27bf\U0001f1e6-\U0001f1ff]")

# Två undantag, båda avsiktliga:
#   streamlit_app.py bär page_icon, webbläsarflikens identitet. Det är inte
#   appkrom, och det är det enda undantaget design_system.md 4.1 medger.
#   docs/superpowers/ är historiska design- och planeringsdokument. De beskriver
#   vad appen var vid en viss tidpunkt och ska inte skrivas om i efterhand;
#   granskningsdokumentet måste dessutom kunna citera de glyfer det avskaffar.
_GLYFUNDANTAG = ("streamlit_app.py",)
_GLYFUNDANTAG_KATALOGER = ("docs/superpowers",)


def _glyfundantagen(fil: Path) -> bool:
    """Sant om filen är undantagen från glyfvakten."""
    relativ = fil.relative_to(ROT).as_posix()
    if relativ in _GLYFUNDANTAG:
        return True
    return any(relativ.startswith(f"{k}/") for k in _GLYFUNDANTAG_KATALOGER)


@pytest.mark.parametrize("fil", _granskade_filer(), ids=lambda p: str(p))
def test_inga_ikoner_eller_emoji(fil: Path) -> None:
    """Ingen emoji eller dekorativ glyf i kod, data eller dokumentation.

    Hierarki och tillstånd bärs av indrag, storlek, färgstyrka och CSS-form.
    """
    if _glyfundantagen(fil):
        pytest.skip("dokumenterat undantag, se _GLYFUNDANTAG")
    text = fil.read_text(encoding="utf-8")
    for glyf in _FORBJUDNA_GLYFER:
        assert glyf not in text, f"{fil}: förbjuden glyf {glyf!r}"
    traff = _EMOJI.search(text)
    assert traff is None, f"{fil}: emoji {traff.group()!r} på position {traff.start()}"
