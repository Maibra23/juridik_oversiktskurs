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

# Alla textbärande filtyper i repot. Tidigare saknades .txt, .js och .yml,
# och då slank både appnamn och en synlig grafetikett igenom vakten.
_GRANSKADE_SUFFIX = {".py", ".json", ".md", ".toml", ".txt", ".js", ".mjs", ".yml"}
_GRANSKADE_KATALOGER = (
    "utils",
    "sidor",
    "tests",
    "data",
    ".streamlit",
    ".github",
)

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
_GLYFUNDANTAG = ("streamlit_app.py",)
_GLYFUNDANTAG_KATALOGER: tuple[str, ...] = ()


def _glyfundantagen(fil: Path) -> bool:
    """Sant om filen är undantagen från glyfvakten."""
    relativ = fil.relative_to(ROT).as_posix()
    if relativ in _GLYFUNDANTAG:
        return True
    return any(relativ.startswith(f"{k}/") for k in _GLYFUNDANTAG_KATALOGER)


@pytest.mark.parametrize(
    "fil", _granskade_filer(), ids=lambda p: str(p.relative_to(ROT))
)
def test_inga_ikoner_eller_emoji(fil: Path) -> None:
    """Ingen emoji eller dekorativ glyf i kod, data eller dokumentation.

    Hierarki och tillstånd bärs av indrag, storlek, färgstyrka och CSS-form.
    """
    if _glyfundantagen(fil):
        pytest.skip("dokumenterat undantag, se _GLYFUNDANTAG")
    text = fil.read_text(encoding="utf-8", errors="replace")
    for glyf in _FORBJUDNA_GLYFER:
        assert glyf not in text, f"{fil}: förbjuden glyf {glyf!r}"
    traff = _EMOJI.search(text)
    assert traff is None, f"{fil}: emoji {traff.group()!r} på position {traff.start()}"


# Tankstreck och dekorativa avdelare läses som maskinskriven text. Prosan ska
# i stället bäras av punkt, komma, kolon och parentes. Skrivna som
# escapesekvenser så att den här filen inte flaggar sig själv.
_FORBJUDNA_SKILJETECKEN = {
    "—": "tankstreck (em dash)",
    "–": "kort tankstreck (en dash)",
    "·": "mittpunkt",
    "−": "minustecken",
}

# data/lagtext/ bär ordagrann författningstext från Riksdagens öppna data.
# Den citeras, inte skrivs, och får därför aldrig normaliseras: ett ändrat
# tecken i lagtext är ett sakfel, inte en stilfråga.
_SKILJETECKENUNDANTAG_KATALOGER = (
    "data/lagtext",
    "data/lagstruktur",
)
_SKILJETECKENUNDANTAG_FILER = ("tests/test_sprak.py",)

_DUBBELT_BINDESTRECK = re.compile(r'[a-zåäöA-ZÅÄÖ0-9"] -- [a-zåäöA-ZÅÄÖ0-9"]')


def _undantagen_katalog(fil: Path, kataloger: tuple[str, ...]) -> bool:
    """Sant om filen ligger i någon av de undantagna katalogerna."""
    relativ = fil.relative_to(ROT).as_posix()
    return any(relativ.startswith(f"{k}/") for k in kataloger)


@pytest.mark.parametrize(
    "fil", _granskade_filer(), ids=lambda p: str(p.relative_to(ROT))
)
def test_inga_tankstreck(fil: Path) -> None:
    """Ingen tankstrecksinterpunktion i kod, data eller dokumentation."""
    if fil.relative_to(ROT).as_posix() in _SKILJETECKENUNDANTAG_FILER:
        pytest.skip("vakten namnger det den förbjuder, se _SKILJETECKENUNDANTAG_FILER")
    if _undantagen_katalog(fil, _SKILJETECKENUNDANTAG_KATALOGER):
        pytest.skip("ordagrann lagtext eller historiskt dokument")
    text = fil.read_text(encoding="utf-8", errors="replace")
    # Dubbelt bindestreck mellan två ord är ett tankstreck någon skrivit för
    # hand. Mönstret kräver blanksteg och tecken runtom, så CLI-flaggor
    # (--fix, --test) och markdownlinjer (---) inte träffas.
    dubbla = [
        nr
        for nr, rad in enumerate(text.splitlines(), 1)
        if _DUBBELT_BINDESTRECK.search(rad)
    ]
    assert not dubbla, f"{fil}: skrivet tankstreck (--) på rad {dubbla[:5]}"
    for tecken, namn in _FORBJUDNA_SKILJETECKEN.items():
        rader = [
            nr for nr, rad in enumerate(text.splitlines(), 1) if tecken in rad
        ]
        assert not rader, f"{fil}: {namn} på rad {rader[:5]}"


# Appen är ett fristående övningsverktyg utan koppling till någon namngiven
# kurs eller lärobok. Vakten hindrar att sådana referenser kryper tillbaka in.
# Ordgränserna gör att sammansättningar som "konkursen" och "valutakursen"
# inte träffas: de är vanlig svenska och förekommer i lagtext.
_KURSORD = re.compile(
    r"\b(?:kurs|kursen|kursens|kurser|kursbok\w*|kursmodul\w*|kursavsnitt\w*|"
    r"delkurs\w*|kursansvarig\w*|översiktskurs\w*|tentam\w*|JÖK\w*)\b",
    re.IGNORECASE,
)

# data/lagtext/ och data/lagstruktur/ bär ordagrann författningstext och
# kapitelrubriker från Riksdagens öppna data. Där betyder "kursen" växelkurs,
# och texten citeras, inte skrivs.
# Den här filen undantar sig själv: en vakt måste kunna namnge det den
# förbjuder, precis som glyfvakten ovan.
_KURSORDUNDANTAG_KATALOGER = ("data/lagtext", "data/lagstruktur")
_KURSORDUNDANTAG_FILER = ("tests/test_sprak.py",)


@pytest.mark.parametrize(
    "fil", _granskade_filer(), ids=lambda p: str(p.relative_to(ROT))
)
def test_inga_kursreferenser(fil: Path) -> None:
    """Ingen referens till en namngiven kurs, lärobok eller examination."""
    if fil.relative_to(ROT).as_posix() in _KURSORDUNDANTAG_FILER:
        pytest.skip("vakten namnger det den förbjuder, se _KURSORDUNDANTAG_FILER")
    if _undantagen_katalog(fil, _KURSORDUNDANTAG_KATALOGER):
        pytest.skip("ordagrann lagtext eller historiskt dokument")
    text = fil.read_text(encoding="utf-8", errors="replace")
    traffar = [
        (nr, _KURSORD.search(rad).group())
        for nr, rad in enumerate(text.splitlines(), 1)
        if _KURSORD.search(rad)
    ]
    assert not traffar, f"{fil}: kursreferens {traffar[:5]}"


# Avstavade sammansättningar ("Köp- och konsumenträtt") bär ett bindestreck som
# svensk grammatik kräver men som ändå läses som maskinskriven text. Lösningen
# är att skriva ut båda leden ("Köprätt och konsumenträtt"), inte att stryka
# strecket. Mönstret är avsiktligt snävt: det träffar bara bindestreck följt av
# " och ", aldrig markdownlistor, CSS-egenskaper eller SFS-nummer.
_AVSTAVNING = re.compile(r"[A-Za-zÅÄÖåäö]+- och ")

# Undantag med sakskäl: dessa bindestreck sitter i officiella författningsnamn
# och i en fast grundlagsterm. "Offentlighets- och sekretesslagen" och
# "Plan- och bygglagen" är EN lag var, inte två, och "fri- och rättigheter" är
# regeringsformens egen ordalydelse (2 kap. RF). Att skriva ut leden var för sig
# skulle uppfinna författningar som inte finns, vilket är ett sakfel och värre
# än ett bindestreck.
_AVSTAVNING_TILLATEN = (
    "Offentlighets- och sekretesslagen",
    "Plan- och bygglagen",
    "fri- och rättigheter",
)

_AVSTAVNINGSUNDANTAG_KATALOGER = (
    "data/lagtext",
    "data/lagstruktur",
)
_AVSTAVNINGSUNDANTAG_FILER = ("tests/test_sprak.py",)


@pytest.mark.parametrize(
    "fil", _granskade_filer(), ids=lambda p: str(p.relative_to(ROT))
)
def test_inga_avstavade_sammansattningar(fil: Path) -> None:
    """Inga bindestreck i samordnade sammansättningar i egen text."""
    if fil.relative_to(ROT).as_posix() in _AVSTAVNINGSUNDANTAG_FILER:
        pytest.skip("vakten namnger det den förbjuder")
    if _undantagen_katalog(fil, _AVSTAVNINGSUNDANTAG_KATALOGER):
        pytest.skip("ordagrann lagtext eller historiskt dokument")
    text = fil.read_text(encoding="utf-8", errors="replace")
    traffar = []
    for nr, rad in enumerate(text.splitlines(), 1):
        rensad = rad
        for tillaten in _AVSTAVNING_TILLATEN:
            rensad = rensad.replace(tillaten, "")
        traff = _AVSTAVNING.search(rensad)
        if traff:
            traffar.append((nr, traff.group()))
    assert not traffar, f"{fil}: avstavad sammansättning {traffar[:5]}"
