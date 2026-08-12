"""Lagrumsregister och verifiering av lagrumshänvisningar.

Juridikappens motsvarighet till ekonomistyrnings verify_grounding, men
för lagrum i stället för siffror. Ansvarar för:
- Inläsning och validering av data/lagrum.json (SFS-nummer, lagnamn,
  vedertagen förkortning, paragrafer och kort beskrivning per lagrum)
- extrahera_lagrum(text): parsa hänvisningar ur text, t.ex.
  "36 § AvtL", "3 kap. 1 § SkL", "28 till 30 §§ AvtL"
- validera_lagrum(ref): slå upp mot registret och returnera en status
  (VERIFIERAD, OKAND_PARAGRAF, OKAND_LAG)
- lagen_nu_url(ref): bygg korrekt djuplänk till lagen.nu
- verify_lagrum(text): helhetsrapport där varje träff klassificeras,
  inklusive rättsfall (NJA) som markeras EJ_VALIDERBAR

All juridisk verifiering sker deterministiskt mot registret, aldrig via
LLM. Detta är appens hallucinationsskydd.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# --- Statuskonstanter -------------------------------------------------------

STATUS_VERIFIERAD = "VERIFIERAD"
STATUS_OKAND_PARAGRAF = "OKAND_PARAGRAF"
STATUS_OKAND_LAG = "OKAND_LAG"
STATUS_EJ_VALIDERBAR = "EJ_VALIDERBAR"

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "lagrum.json"


# --- Datamodeller (immutabla) ----------------------------------------------

@dataclass(frozen=True)
class Kursavsnitt:
    """Ett paragrafintervall som ingår i kursen för en viss lag."""

    beskrivning: str
    kapitel: str | None
    paragraf_fran: int
    paragraf_till: int
    lagen_nu_url: str
    verifiera: bool


@dataclass(frozen=True)
class Lag:
    """En lag i registret med sina kursrelevanta avsnitt."""

    forkortning: str
    namn: str
    sfs: str
    kapitelindelad: bool
    lagen_nu_bas_url: str
    kursavsnitt: tuple[Kursavsnitt, ...]
    aliaser: tuple[str, ...] = ()


@dataclass(frozen=True)
class Lagrumsref:
    """En parsad lagrumshänvisning på kanonisk form."""

    forkortning: str
    paragraf: str
    kapitel: str | None = None
    paragraf_till: str | None = None
    ra: str = ""  # råtext som matchades i källan


@dataclass(frozen=True)
class Lagrumstraff:
    """En klassificerad träff i en verifieringsrapport."""

    ra: str
    status: str
    ref: Lagrumsref | None = None
    url: str | None = None
    beskrivning: str | None = None


# --- Regex ------------------------------------------------------------------

# Paragraf- och kapitelmarkörer accepteras både som tecken och utskrivna, för
# att § inte ska krävas (tecknet är svårt att skriva på många tangentbord).
# Utskrivna former: "paragrafen", "paragraf" och den säkra förkortningen
# "par." (med punkt). Bart "p" utelämnas medvetet — det förväxlas för lätt med
# vanlig text och skulle urholka hallucinationsspärren. Längsta alternativet
# först så att t.ex. "paragrafen" matchar före "paragraf". Kapitel på samma
# sätt: "kapitlet"/"kapitel" utöver "kap."/"kap".
# (?i:...) gör bara markörorden skiftlägesokänsliga (Paragrafen/PARAGRAFEN),
# i linje med att lagnamnen redan matchas oberoende av skiftläge. Resten av
# mönstret förblir skiftlägeskänsligt. Den avslutande (?![a-zåäö]) på ordformerna
# hindrar att "paragraf" nafsar ett prefix av "paragrafen" och lämnar "en"/"EN"
# kvar som en påhittad förkortning; §-tecknet får däremot gränsa direkt mot
# lagnamnet ("36 §AvtL") och har därför ingen sådan spärr.
_PARAGRAF_MARKOR = r"(?i:§{1,2}|par\.|paragraf(?:erna|en)?(?![a-zåäö]))"
_KAPITEL_MARKOR = r"(?i:kap\.|kapitlet|kapitel|kap(?![a-zåäö]))"

# Fångar svenska lagrumshänvisningar:
#   "36 § AvtL", "3 kap. 1 § SkL", "7 kap 1 § ÄktB", "28 till 30 §§ AvtL"
#   "3 paragrafen SkbrL", "3 kapitlet 1 paragrafen skadeståndslagen"
# Förkortningen består av bokstäver i valfritt skiftläge (t.ex. AvtL, avtl,
# AVTL) och normaliseras till registrets kanoniska skiftläge i
# _ref_fran_match. Verifiering av att den finns i registret sker separat i
# validera_lagrum.
LAGRUM_PATTERN = re.compile(
    r"(?:(?P<kapitel>\d+)\s*" + _KAPITEL_MARKOR + r"\s*)?"
    r"(?P<paragraf>\d+)\s*[a-z]?\s*"
    r"(?:(?:till|–|-)\s*(?P<paragraf_till>\d+)\s*)?"
    + _PARAGRAF_MARKOR + r"\s*"
    r"(?P<forkortning>[A-Za-zÅÄÖåäö]+)"
)

# Omvänd ordning där modellen skriver förkortningen först, t.ex.
# "AvtL 36 §", "AvtL 28–30 §§", "SkL 3 kap. 1 §", "skuldebrevslagen 3 paragrafen".
# Denna form är tvetydig (vilket ord som helst kan föregå ett paragrafnummer),
# så träffar accepteras endast om förkortningen finns i registret
# (skiftlägesokänsligt). Se extrahera_lagrum för den filtreringen.
LAGRUM_PATTERN_OMVAND = re.compile(
    r"(?P<forkortning>[A-Za-zÅÄÖåäö]+)\s+"
    r"(?:(?P<kapitel>\d+)\s*" + _KAPITEL_MARKOR + r"\s*)?"
    r"(?P<paragraf>\d+)\s*[a-z]?\s*"
    r"(?:(?:till|–|-)\s*(?P<paragraf_till>\d+)\s*)?"
    + _PARAGRAF_MARKOR
)

# Rättsfallshänvisningar (NJA, RH, AD, MÖD) kan inte valideras lokalt i v1.
RATTSFALL_PATTERN = re.compile(
    r"(?P<ra>(?:NJA|RH|AD|MÖD)\s+\d{4}\s+s\.?\s*\d+)",
    re.IGNORECASE,
)


# --- Registerinläsning ------------------------------------------------------

def _validera_ra_lag(rad: dict) -> Lag:
    """Validera en råpost ur lagrum.json och bygg en immutabel Lag.

    Kastar ValueError vid saknade fält eller icke-numeriska paragrafer så
    att fel i datafilen upptäcks direkt (fail fast).
    """
    for falt in ("forkortning", "namn", "sfs", "kapitelindelad", "lagen_nu_bas_url"):
        if falt not in rad:
            raise ValueError(f"Lagpost saknar fältet '{falt}': {rad!r}")

    avsnitt: list[Kursavsnitt] = []
    for a in rad.get("kursavsnitt", []):
        fran = str(a.get("paragraf_fran", "")).strip()
        till = str(a.get("paragraf_till", "")).strip()
        if not fran.isdigit() or not till.isdigit():
            raise ValueError(
                f"Icke-numeriskt paragrafintervall i {rad['forkortning']}: {a!r}"
            )
        avsnitt.append(
            Kursavsnitt(
                beskrivning=a.get("beskrivning", ""),
                kapitel=(str(a["kapitel"]) if a.get("kapitel") is not None else None),
                paragraf_fran=int(fran),
                paragraf_till=int(till),
                lagen_nu_url=a.get("lagen_nu_url", ""),
                verifiera=bool(a.get("verifiera", False)),
            )
        )

    ra_aliaser = rad.get("aliaser", [])
    if not isinstance(ra_aliaser, list):
        raise ValueError(
            f"'aliaser' måste vara en lista i {rad['forkortning']}: {ra_aliaser!r}"
        )
    for a in ra_aliaser:
        if not isinstance(a, str) or not re.fullmatch(r"[A-Za-zÅÄÖåäö]+", a):
            raise ValueError(
                f"Alias måste vara ett enda ord med bokstäver i {rad['forkortning']}: {a!r}"
            )

    return Lag(
        forkortning=rad["forkortning"],
        namn=rad["namn"],
        sfs=rad["sfs"],
        kapitelindelad=bool(rad["kapitelindelad"]),
        lagen_nu_bas_url=rad["lagen_nu_bas_url"],
        kursavsnitt=tuple(avsnitt),
        aliaser=tuple(ra_aliaser),
    )


@lru_cache(maxsize=1)
def lagrum_register() -> dict[str, Lag]:
    """Läs och cachea lagrumsregistret, nyckelat på förkortning."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Hittar inte lagrumsregistret: {DATA_PATH}")

    with DATA_PATH.open(encoding="utf-8") as f:
        data = json.load(f)

    lagar = data.get("lagar")
    if not isinstance(lagar, list) or not lagar:
        raise ValueError("lagrum.json saknar en icke-tom lista 'lagar'.")

    register: dict[str, Lag] = {}
    for rad in lagar:
        lag = _validera_ra_lag(rad)
        register[lag.forkortning] = lag
    return register


def giltiga_forkortningar() -> frozenset[str]:
    """Vitlistan av förkortningar som appen kan verifiera."""
    return frozenset(lagrum_register().keys())


def _bygg_alias_karta(register: dict[str, Lag]) -> dict[str, str]:
    """Bygg en gemena-till-kanonisk-karta ur ett register.

    Nyckel är förkortningen eller ett alias i gemener, värdet lagens
    kanoniska förkortning. Kastar ValueError om två lagar delar samma
    sökord (skiftlägesokänsligt) i stället för att tyst låta
    registrets iterationsordning avgöra vilken lag som "vinner".
    """
    karta: dict[str, str] = {}
    for lag in register.values():
        for ord_ in (lag.forkortning, *lag.aliaser):
            nyckel = ord_.lower()
            if nyckel in karta and karta[nyckel] != lag.forkortning:
                raise ValueError(
                    f"Alias '{ord_}' är tvetydigt: pekar på både "
                    f"'{karta[nyckel]}' och '{lag.forkortning}'."
                )
            karta[nyckel] = lag.forkortning
    return karta


@lru_cache(maxsize=1)
def _forkortning_gemener_karta() -> dict[str, str]:
    """Karta från gemener (förkortning eller alias) till kanonisk förkortning."""
    return _bygg_alias_karta(lagrum_register())


def _normalisera_forkortning(rå: str) -> str:
    """Normalisera en tolkad förkortning till registrets skiftläge.

    Studenter skriver ibland förkortningen i fel skiftläge ("skl", "AVTL").
    Finns en skiftlägesokänslig träff i registret används dess kanoniska
    form; annars returneras texten oförändrad så att genuint okända lagar
    fortfarande flaggas OKAND_LAG i stället för att tyst passera.
    """
    return _forkortning_gemener_karta().get(rå.lower(), rå)


# --- Extrahering ------------------------------------------------------------

def _ref_fran_match(m: re.Match[str]) -> Lagrumsref:
    """Bygg en Lagrumsref ur en regexträff (samma grupper i båda mönstren)."""
    return Lagrumsref(
        forkortning=_normalisera_forkortning(m.group("forkortning")),
        paragraf=m.group("paragraf"),
        kapitel=m.group("kapitel"),
        paragraf_till=m.group("paragraf_till"),
        ra=m.group(0).strip(),
    )


def extrahera_lagrum(text: str) -> tuple[Lagrumsref, ...]:
    """Parsa alla lagrumshänvisningar ur en text till kanonisk form.

    Fångar både kanonisk ordning ("36 § AvtL", "36 § avtl") och omvänd
    ordning där förkortningen står först ("AvtL 36 §"). En kandidat
    accepteras om förkortningen antingen finns i registret (oavsett
    skiftläge, t.ex. "avtl"/"AVTL"/"AvtL") eller är versalinledd — det
    senare bevarar hallucinationsskyddet för påhittade lagnamn ("Pizzalagen")
    utan att öppna för att ett vanligt gement ord efter "§" ("är", "reglerar")
    tolkas som en förkortning.

    Kanoniska träffar har företräde: en omvänd träff hoppas över om den
    överlappar en kanonisk.
    """
    if not text:
        return ()

    kanda_gemener = _forkortning_gemener_karta()

    def _godtagen(forkortning: str) -> bool:
        return forkortning.lower() in kanda_gemener or forkortning[:1].isupper()

    traffar: list[tuple[int, Lagrumsref]] = []
    upptagna: list[tuple[int, int]] = []

    for m in LAGRUM_PATTERN.finditer(text):
        if not _godtagen(m.group("forkortning")):
            continue
        traffar.append((m.start(), _ref_fran_match(m)))
        upptagna.append((m.start(), m.end()))

    for m in LAGRUM_PATTERN_OMVAND.finditer(text):
        if m.group("forkortning").lower() not in kanda_gemener:
            continue
        start, slut = m.start(), m.end()
        if any(start < o_slut and o_start < slut for o_start, o_slut in upptagna):
            continue  # överlappar en kanonisk träff
        traffar.append((start, _ref_fran_match(m)))

    traffar.sort(key=lambda t: t[0])
    return tuple(ref for _start, ref in traffar)


# --- Validering och länkning ------------------------------------------------

def _som_ref(ref: Lagrumsref | str) -> Lagrumsref | None:
    """Normalisera indata till en Lagrumsref, eller None om inget lagrum hittas."""
    if isinstance(ref, Lagrumsref):
        return ref
    traffar = extrahera_lagrum(ref)
    return traffar[0] if traffar else None


def _matchande_avsnitt(lag: Lag, ref: Lagrumsref) -> Kursavsnitt | None:
    """Hitta det kursavsnitt som täcker referensens paragraf (och kapitel)."""
    if not ref.paragraf.isdigit():
        return None
    paragraf = int(ref.paragraf)

    # En lag utan kapitelindelning har inga kapitel att träffa. Ett angivet
    # kapitel är då alltid påhittat, och kapitelledet får inte tyst ignoreras:
    # då skulle "99 kap. 1 § AvtL" verifieras på styrkan av att AvtL har en 1 §.
    if not lag.kapitelindelad and ref.kapitel is not None:
        return None

    for avsnitt in lag.kursavsnitt:
        if lag.kapitelindelad:
            if ref.kapitel is None or avsnitt.kapitel != ref.kapitel:
                continue
        if avsnitt.paragraf_fran <= paragraf <= avsnitt.paragraf_till:
            return avsnitt
    return None


def validera_lagrum(ref: Lagrumsref | str) -> str:
    """Slå upp en referens mot registret och returnera en status."""
    parsad = _som_ref(ref)
    if parsad is None:
        return STATUS_EJ_VALIDERBAR

    lag = lagrum_register().get(parsad.forkortning)
    if lag is None:
        return STATUS_OKAND_LAG

    return STATUS_VERIFIERAD if _matchande_avsnitt(lag, parsad) else STATUS_OKAND_PARAGRAF


def lagen_nu_url(ref: Lagrumsref | str) -> str | None:
    """Bygg en djuplänk till lagen.nu, eller None om lagen är okänd."""
    parsad = _som_ref(ref)
    if parsad is None:
        return None

    lag = lagrum_register().get(parsad.forkortning)
    if lag is None:
        return None

    if lag.kapitelindelad:
        if parsad.kapitel is None:
            return lag.lagen_nu_bas_url
        return f"{lag.lagen_nu_bas_url}#K{parsad.kapitel}P{parsad.paragraf}"
    return f"{lag.lagen_nu_bas_url}#P{parsad.paragraf}"


# --- Helhetsrapport ---------------------------------------------------------

def verify_lagrum(text: str) -> tuple[Lagrumstraff, ...]:
    """Klassificera samtliga lagrums- och rättsfallshänvisningar i en text.

    Varje lagrum får status VERIFIERAD, OKAND_PARAGRAF eller OKAND_LAG.
    Rättsfall (NJA m.fl.) kan inte valideras lokalt och markeras
    EJ_VALIDERBAR så att UI:t kan varna i stället för att visa dem som fakta.
    """
    if not text:
        return ()

    traffar: list[Lagrumstraff] = []

    for ref in extrahera_lagrum(text):
        status = validera_lagrum(ref)
        lag = lagrum_register().get(ref.forkortning)
        avsnitt = _matchande_avsnitt(lag, ref) if lag else None
        traffar.append(
            Lagrumstraff(
                ra=ref.ra,
                status=status,
                ref=ref,
                url=lagen_nu_url(ref) if status == STATUS_VERIFIERAD else None,
                beskrivning=avsnitt.beskrivning if avsnitt else None,
            )
        )

    for m in RATTSFALL_PATTERN.finditer(text):
        traffar.append(
            Lagrumstraff(ra=m.group("ra").strip(), status=STATUS_EJ_VALIDERBAR)
        )

    return tuple(traffar)
