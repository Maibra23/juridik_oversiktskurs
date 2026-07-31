"""Läs lagens kapitel- och momentrubriker ur källans HTML.

Riksdagens öppna data bär författningens egen disposition: <h3> är
kapitelrubriker ("3 kap. Näringsidkarens dröjsmål") och <h4> är
momentrubriker ("Påföljder vid dröjsmål"). scripts/hamta_lagtext.py kastar
dem eftersom den bara letar paragrafankare. Här plockas de fram, så att
nedbrytningen i lagkortet blir lagens egen och inte något vi hittat på.

Ren modul: ingen nätverkskod, inget filsystem, inget Streamlit-beroende.
Det gör den testbar mot sparade fixturer i stället för mot lagen.nu.

Modulen upprepar medvetet två små hjälpare från scripts/hamta_lagtext.py
(taggrensning och paragrafnyckel). Att bryta ut dem ur hämtaren vore en
ändring av fungerande kod utan nytta för det här projektet.
"""

from __future__ import annotations

import re
from html import unescape

# Rubriker och paragrafankare plockas i dokumentordning ur samma svep, så att
# varje rubrik kan äga de paragrafer som följer på den. Skiljer man på svepen
# tappar man ordningen, och därmed kopplingen rubrik -> paragraf.
_RUBRIK_ELLER_PARAGRAF = re.compile(
    r"<h(?P<niva>[34])[^>]*>(?P<rubrik>.*?)</h(?P=niva)>"
    r'|<a[^>]*class="paragraf"[^>]*name="(?P<ankare>K?\d*P\d+[a-z]?)"',
    re.DOTALL,
)

# "3 kap. Näringsidkarens dröjsmål" -> nummer 3, rubrik "Näringsidkarens
# dröjsmål". Det som inte matchar är brus: "Innehåll:", "Övergångsbestämmelser".
_KAPITELRUBRIK = re.compile(r"^(?P<nummer>\d+)\s*kap\.\s*(?P<rubrik>.*)$")

# Formen "1 a §" får ankaret "K4P1a" och avvisas: kursavsnitten refererar
# bara hela paragrafnummer, och en bokstavsparagraf hör till grundparagrafen.
_ANKARE = re.compile(r"^(?:K(?P<kapitel>\d+))?P(?P<paragraf>\d+)$")

_TAGG = re.compile(r"<[^>]+>")


def rensa_html(html: str) -> str:
    """Ta bort taggar och normalisera blanktecken i en rubrik."""
    return re.sub(r"\s+", " ", unescape(_TAGG.sub("", html))).strip()


def paragrafnyckel(ankarnamn: str, *, kapitelindelad: bool = True) -> str | None:
    """Ankarnamnet som paragrafnyckel, eller None för bokstavsparagrafer.

    Nyckeln har samma form som data/lagtext/: "3:2" för kapitelindelade
    lagar och "12" för lagar med löpande numrering.

    ``kapitelindelad`` måste komma från lagrumsregistret och inte gissas ur
    ankaret. AvtL märker sina paragrafer "K2P10" trots att numreringen löper
    obruten 1-41 genom hela lagen; registret säger ``kapitelindelad: false``
    och korpusen nycklar dem platt. Läser man kapitlet ur ankaret ändå får
    strukturen nycklar som inte går att foga ihop med vare sig korpusen eller
    kursavsnitten.
    """
    traff = _ANKARE.match(ankarnamn)
    if traff is None:
        return None
    kapitel = traff.group("kapitel")
    if kapitel is None or not kapitelindelad:
        return traff.group("paragraf")
    return f"{kapitel}:{traff.group('paragraf')}"


def _ny_post(**falt: object) -> dict:
    return {**falt, "paragrafer": []}


def extrahera_struktur(
    html: str, *, kapitelindelad: bool
) -> tuple[list[dict], list[dict]]:
    """Plocka ut (kapitel, moment) ur källans HTML.

    Båda listorna är i dokumentordning och kan var för sig vara tomma --
    aldrig båda, eftersom varje lag har minst en rubriknivå.

    ``kapitelindelad`` styr paragrafnyckelns form och hämtas ur
    lagrumsregistret. Kapitelrubrikerna behålls oavsett: AvtL har fyra
    kapitel att gruppera under men platta paragrafnycklar, eftersom lagens
    numrering löper obruten genom dem.
    """
    kapitel: list[dict] = []
    moment: list[dict] = []
    aktivt_kapitel: dict | None = None
    aktivt_moment: dict | None = None

    for trav in _RUBRIK_ELLER_PARAGRAF.finditer(html):
        ankare = trav.group("ankare")
        if ankare is not None:
            nyckel = paragrafnyckel(ankare, kapitelindelad=kapitelindelad)
            if nyckel is None:
                continue
            for post in (aktivt_kapitel, aktivt_moment):
                if post is not None and nyckel not in post["paragrafer"]:
                    post["paragrafer"].append(nyckel)
            continue

        rubrik = rensa_html(trav.group("rubrik"))
        if trav.group("niva") == "3":
            traff = _KAPITELRUBRIK.match(rubrik)
            if traff is None:
                # Brus. Nollställ ändå: paragrafer under
                # "Övergångsbestämmelser" hör inte till senaste kapitlet.
                aktivt_kapitel = None
                aktivt_moment = None
                continue
            aktivt_kapitel = _ny_post(
                nummer=traff.group("nummer"),
                rubrik=traff.group("rubrik").strip(),
            )
            kapitel.append(aktivt_kapitel)
            aktivt_moment = None
        else:
            aktivt_moment = _ny_post(
                rubrik=rubrik,
                kapitel=aktivt_kapitel["nummer"] if aktivt_kapitel else None,
            )
            moment.append(aktivt_moment)

    # En rubrik utan egna paragrafer är en mellanrubrik, inte ett moment.
    return (
        [k for k in kapitel if k["paragrafer"]],
        [m for m in moment if m["paragrafer"]],
    )
