"""Granska ett tutorsvar innan studenten ser det.

Garden i utils.lagrum svarar på om ett lagrum FINNS. Den här modulen svarar
på om svaret som helhet går att lita på tillräckligt för att visas.

DEN AVGÖRANDE INSIKTEN
======================

Mätningarna visade att **det bästa tutorsvaret innehöll ett påhittat
lagrum**. När en student citerade det obefintliga "87 § AvtL" var rätt svar
att nämna paragrafen och avvisa den:

    "87 § AvtL finns inte i lagrumslistan. Detta är ett allvarligt fel."

En gard som bara letade efter overifierade lagrum hade stoppat exakt det
svaret, och släppt igenom det sämre som i stället påstod att "Rätt norm är
87 § AvtL".

Avgörande är alltså inte OM ett lagrum nämns, utan i vilken ROLL. Ett lagrum
utanför uppgiftens underlag måste avvisas i texten för att svaret ska
godkännas.

KONSERVATIV VID TVEKSAMHET
==========================

Går rollen inte att avgöra godkänns svaret, och UI:t varnar som förut. Ett
tveksamt svar som släpps igenom kostar en varningsruta. Ett korrekt svar som
stoppas kostar undervisning, och studenten får aldrig veta vad hen missade.
Den avvägningen är medveten.

Ren modul: inga LLM-anrop, ingen Streamlit, allt testbart.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from utils.lagrum import STATUS_VERIFIERAD, Lagrumsref, _som_ref, verify_lagrum

# Ord som visar att ett lagrum avvisas snarare än framhålls. Listan är
# medvetet bred: en missad avvisning stoppar ett korrekt svar, medan en
# felaktigt upptäckt avvisning bara släpper igenom ett svar som ändå får
# varningsruta.
_AVVISANDE = (
    "inte tillämplig",
    "inte är tillämplig",
    "icke tillämplig",
    "ej tillämplig",
    "gäller inte",
    "finns inte",
    "existerar inte",
    "saknas i",
    "utanför",
    "inte i lagrumslistan",
    "inte i lagrumsvitlistan",
    "inte med i",
    "felaktig",
    "felaktigt",
    "fel lagrum",
    "är fel",
    "allvarligt fel",
    "aldrig",
    "inte använda",
    "undvik",
    "inte hänvisa",
    "påhittad",
    "obefintlig",
)

# Meningsgräns. Punkt följd av blanksteg, eller radbrytning.
#
# Undantagen är nödvändiga: "12 kap. 4 § AvtL" innehåller en punkt följd av
# blanksteg mitt i lagrummet. Utan undantaget delas referensen från sin egen
# avvisande sats, och ett korrekt svar underkänns. Det inträffade på riktigt
# under utvecklingen av den här modulen.
_MENINGSSLUT = re.compile(
    r"(?<=[.!?:])(?<!kap\.)(?<!t\.ex\.)(?<!m\.m\.)(?<!bl\.a\.)\s+|\n+"
)


@dataclass(frozen=True)
class Granskning:
    """Utfallet av en granskning."""

    godkand: bool
    skal: str
    ovarifierade: tuple[str, ...] = ()
    utanfor_underlag: tuple[str, ...] = ()


def _kanonisk(ref: Lagrumsref) -> str:
    """Jämförbar form oavsett hur referensen skrevs i texten."""
    kapitel = f"{ref.kapitel}:" if ref.kapitel else ""
    return f"{ref.forkortning.lower()}|{kapitel}{ref.paragraf}"


def _underlagsnycklar(underlag: Iterable[str]) -> set[str]:
    nycklar = set()
    for post in underlag:
        parsad = _som_ref(post)
        if parsad is not None:
            nycklar.add(_kanonisk(parsad))
    return nycklar


def _meningar(text: str) -> list[str]:
    return [m for m in _MENINGSSLUT.split(text) if m.strip()]


def _avvisas(ra: str, text: str) -> bool:
    """Sant om lagrummet nämns i en avvisande mening.

    Tittar bara i de meningar där lagrummet faktiskt förekommer, så att en
    avvisning av ETT lagrum inte råkar frita ett annat i samma svar.
    """
    for mening in _meningar(text):
        if ra in mening and any(ord_ in mening.lower() for ord_ in _AVVISANDE):
            return True
    return False


def granska_tutorsvar(text: str | None, underlag: Iterable[str] = ()) -> Granskning:
    """Avgör om ett tutorsvar kan visas för studenten.

    ``underlag`` är uppgiftens kända korrekta lagrum (facits lagrum för ett
    rättsfall, alternativens för en quizfråga, begreppets egna för en
    fördjupning). Tomt underlag betyder att bara påhitt kan stoppas.
    """
    innehall = text or ""
    if not innehall.strip():
        return Granskning(False, "Tomt svar från tutorn.")

    kanda = _underlagsnycklar(underlag)

    ovarifierade: list[str] = []
    utanfor: list[str] = []
    problem: list[str] = []

    for traff in verify_lagrum(innehall):
        parsad = _som_ref(traff.ra)
        i_underlaget = parsad is not None and _kanonisk(parsad) in kanda

        if traff.status != STATUS_VERIFIERAD:
            ovarifierade.append(traff.ra)
            if not _avvisas(traff.ra, innehall):
                problem.append(
                    f"{traff.ra} kunde inte verifieras och framhålls som gällande"
                )
        elif kanda and not i_underlaget:
            utanfor.append(traff.ra)
            if not _avvisas(traff.ra, innehall):
                problem.append(
                    f"{traff.ra} ligger utanför uppgiftens lagrum och framhålls "
                    "som tillämpligt"
                )

    if problem:
        return Granskning(
            godkand=False,
            skal="; ".join(dict.fromkeys(problem)),
            ovarifierade=tuple(dict.fromkeys(ovarifierade)),
            utanfor_underlag=tuple(dict.fromkeys(utanfor)),
        )

    return Granskning(
        godkand=True,
        skal="",
        ovarifierade=tuple(dict.fromkeys(ovarifierade)),
        utanfor_underlag=tuple(dict.fromkeys(utanfor)),
    )
