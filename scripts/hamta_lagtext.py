#!/usr/bin/env python3
"""Hämta författningstext för kursens lagar från lagen.nu till data/lagtext/.

Körs manuellt, aldrig av appen. Korpusen ligger i git så att appen fungerar
offline, deterministiskt och utan att belasta lagen.nu vid varje tutorsvar.

    python3 scripts/hamta_lagtext.py              # hämta allt som saknas
    python3 scripts/hamta_lagtext.py --uppdatera  # hämta om allt, visa diff
    python3 scripts/hamta_lagtext.py --lag AvtL   # bara en lag

VAD SOM HÄMTAS, OCH VAD SOM INTE GÖR DET
========================================

Endast **författningstexten**. Den är undantagen upphovsrätt enligt 9 §
upphovsrättslagen och fri att lagra och sprida.

lagen.nu:s **egna kommentarer** (sektionerna "Kommentar", "Rättsfall",
"Lagrumshänvisningar") är författade verk med namngivna upphovsmän och
hämtas ALDRIG. Strukturen gör det enkelt att hålla isär: författningstexten
ligger i ``<section id="P4" class="col-sm-7">`` medan kommentaren ligger i en
syskon-``<div class="panel-group col-sm-5">``. Extraheraren läser bara
section-elementet.

Utöka aldrig den här hämtaren till att ta med kommentarerna. Det vore både
ett upphovsrättsintrång och en pedagogisk försämring: kursen ska lära
studenten läsa lagtext, inte andras sammanfattningar av den.

BARA KURSENS PARAGRAFER
=======================

Endast paragrafer inom ``kursavsnitt`` i data/lagrum.json sparas (cirka 1089
stycken). Det håller korpusen liten och speglar exakt det garden redan
släpper igenom.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import date
from html import unescape
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
LAGRUM_PATH = ROT / "data" / "lagrum.json"
LAGTEXT_DIR = ROT / "data" / "lagtext"

ANVANDARAGENT = (
    "juridik-oversiktskurs/0.1 (utbildningsprojekt; hämtar författningstext)"
)
PAUS_SEKUNDER = 1.0

# Under den här täckningsgraden litar vi inte på lagen.nu för lagen, utan
# hämtar om från Riksdagens öppna data. Bakgrund: lagen.nu:s sida för UB
# (1981:774) renderar bara kapitelrubriker för kapitel 2-16, inga paragrafer,
# trots att sidans egna länkar pekar på dem. Det gav 2 av 39 paragrafer.
MINSTA_TACKNING = 0.6

KALLA_LAGEN_NU = "lagen.nu"
KALLA_RIKSDAGEN = "riksdagen"

_LICENS_BAS = (
    "Författningstext, undantagen upphovsrätt enligt 9 § upphovsrättslagen."
)
LICENSNOT = {
    KALLA_LAGEN_NU: (
        f"{_LICENS_BAS} Hämtad från lagen.nu. Innehåller ingen av lagen.nu:s "
        "egna kommentarer."
    ),
    KALLA_RIKSDAGEN: (
        f"{_LICENS_BAS} Hämtad från Riksdagens öppna data. "
        "Källa: Sveriges riksdag."
    ),
}


# --- Hämtning ---------------------------------------------------------------


def hamta_sida(url: str) -> str:
    """Hämta en lagsida som text."""
    req = urllib.request.Request(url, headers={"User-Agent": ANVANDARAGENT})
    with urllib.request.urlopen(req, timeout=60) as svar:  # noqa: S310
        return svar.read().decode("utf-8", "replace")


def riksdagen_url(sfs: str) -> str:
    """JSON-dokumentet för en SFS hos Riksdagens öppna data."""
    return f"https://data.riksdagen.se/dokument/sfs-{sfs.replace(':', '-')}.json"


def hamta_riksdagen_html(sfs: str) -> str:
    """Hämta lagens HTML-fält ur Riksdagens öppna data."""
    dok = json.loads(hamta_sida(riksdagen_url(sfs)))
    return dok["dokumentstatus"]["dokument"].get("html") or ""


# --- Extrahering ------------------------------------------------------------

# Ett paragrafblock: <section id="P4" class="col-sm-7"> ... </section>.
# Kapitelindelade lagar använder id="K2P1". Kommentaren ligger utanför
# section-elementet och kan därför aldrig råka följa med.
_SEKTION = re.compile(
    r'<section id="(?P<id>K?\d*P\d+)"[^>]*class="[^"]*col-sm-7[^"]*"[^>]*>'
    r"(?P<kropp>.*?)</section>",
    re.DOTALL,
)
_STYCKE = re.compile(r"<p[^>]*id=\"[^\"]*S\d+\"[^>]*>(?P<text>.*?)</p>", re.DOTALL)
_PARAGRAFBETECKNING = re.compile(
    r'<a[^>]*class="paragrafbeteckning"[^>]*>.*?</a>', re.DOTALL
)
_TAGG = re.compile(r"<[^>]+>")
_ID = re.compile(r"^(?:K(?P<kapitel>\d+))?P(?P<paragraf>\d+)$")


def _rensa(html: str) -> str:
    """Ta bort taggar och normalisera blanktecken i ett stycke."""
    # Paragrafbeteckningen ("4 §") är en etikett, inte en del av lagtexten.
    utan_beteckning = _PARAGRAFBETECKNING.sub("", html)
    ren = _TAGG.sub("", utan_beteckning)
    return re.sub(r"\s+", " ", unescape(ren)).strip()


# Riksdagens HTML märker paragrafer med <a class="paragraf" name="K4P1">.
# Texten löper fram till nästa sådan ankare. Formen "1 a §" får ankaret
# "K4P1a" och faller bort i _ID nedan, vilket är rätt: kursavsnitten
# refererar bara till hela paragrafnummer.
_RIKSDAGEN_ANKARE = re.compile(
    r'<a[^>]*class="paragraf"[^>]*name="(?P<id>K?\d*P\d+[a-z]?)"[^>]*>.*?</a>',
    re.DOTALL,
)


def extrahera_paragrafer_riksdagen(html: str) -> dict[str, str]:
    """Plocka ut {paragrafnyckel: text} ur Riksdagens HTML-fält.

    Reservväg för lagar där lagen.nu:s sida saknar paragrafinnehåll.
    """
    traffar = list(_RIKSDAGEN_ANKARE.finditer(html))
    ut: dict[str, str] = {}
    for i, match in enumerate(traffar):
        m = _ID.match(match.group("id"))
        if not m:
            continue
        kapitel = m.group("kapitel")
        nyckel = f"{kapitel}:{m.group('paragraf')}" if kapitel else m.group("paragraf")

        slut = traffar[i + 1].start() if i + 1 < len(traffar) else len(html)
        text = _rensa(html[match.end() : slut])
        if text:
            ut[nyckel] = text
    return ut


def extrahera_paragrafer(html: str) -> dict[str, str]:
    """Plocka ut {paragrafnyckel: text} ur en lagsida.

    Nyckeln är ``"4"`` för oindelade lagar och ``"2:1"`` för kapitelindelade,
    samma form som ``utils.lagtext`` slår upp på.
    """
    ut: dict[str, str] = {}
    for match in _SEKTION.finditer(html):
        m = _ID.match(match.group("id"))
        if not m:
            continue
        kapitel = m.group("kapitel")
        nyckel = f"{kapitel}:{m.group('paragraf')}" if kapitel else m.group("paragraf")

        stycken = [
            _rensa(s.group("text")) for s in _STYCKE.finditer(match.group("kropp"))
        ]
        text = "\n\n".join(s for s in stycken if s)
        if text:
            ut[nyckel] = text
    return ut


# --- Urval mot kursavsnitten ------------------------------------------------


def kursens_nycklar(lag: dict) -> set[str]:
    """Alla paragrafnycklar som ligger inom lagens kursavsnitt."""
    nycklar: set[str] = set()
    for avsnitt in lag.get("kursavsnitt", ()):
        fran = int(avsnitt["paragraf_fran"])
        till = int(avsnitt["paragraf_till"])
        kapitel = avsnitt.get("kapitel")
        for nr in range(fran, till + 1):
            nycklar.add(f"{kapitel}:{nr}" if kapitel else str(nr))
    return nycklar


# --- Skrivning --------------------------------------------------------------


def filnamn_for(sfs: str) -> Path:
    return LAGTEXT_DIR / f"{sfs.replace(':', '-')}.json"


def bygg_lagfil(lag: dict, paragrafer: dict[str, str], kalla: str) -> dict:
    url = (
        lag["lagen_nu_bas_url"]
        if kalla == KALLA_LAGEN_NU
        else riksdagen_url(lag["sfs"])
    )
    return {
        "forkortning": lag["forkortning"],
        "namn": lag["namn"],
        "sfs": lag["sfs"],
        "kalla": url,
        "kallnamn": kalla,
        "hamtad": date.today().isoformat(),
        "licens": LICENSNOT[kalla],
        # Studenten läser alltid lagen på lagen.nu, oavsett var texten hämtats.
        "lagen_nu_url": lag["lagen_nu_bas_url"],
        "paragrafer": dict(sorted(paragrafer.items(), key=_sorteringsnyckel)),
    }


def _sorteringsnyckel(post: tuple[str, str]) -> tuple[int, int]:
    nyckel = post[0]
    if ":" in nyckel:
        kap, par = nyckel.split(":", 1)
        return (int(kap), int(par))
    return (0, int(nyckel))


def hamta_lag(lag: dict, *, tyst: bool = False) -> tuple[int, int]:
    """Hämta och spara en lag. Returnerar (sparade, förväntade).

    Hämtar i första hand från lagen.nu. Ger den för dålig täckning mot
    kursavsnitten hämtas lagen om från Riksdagens öppna data, och den bästa
    av de två sparas. Se MINSTA_TACKNING för bakgrunden.
    """
    onskade = kursens_nycklar(lag)

    alla = extrahera_paragrafer(hamta_sida(lag["lagen_nu_bas_url"]))
    valda = {n: t for n, t in alla.items() if n in onskade}
    kalla = KALLA_LAGEN_NU

    if onskade and len(valda) / len(onskade) < MINSTA_TACKNING:
        if not tyst:
            print(
                f"{lag['forkortning']:8s} lagen.nu gav {len(valda)}/{len(onskade)}"
                " paragrafer, hämtar om från Riksdagen …"
            )
        try:
            reserv_alla = extrahera_paragrafer_riksdagen(
                hamta_riksdagen_html(lag["sfs"])
            )
            reserv = {n: t for n, t in reserv_alla.items() if n in onskade}
            if len(reserv) > len(valda):
                valda, kalla = reserv, KALLA_RIKSDAGEN
        except Exception as exc:  # noqa: BLE001 (behåll lagen.nu-resultatet)
            if not tyst:
                print(f"{lag['forkortning']:8s} Riksdagen misslyckades: {exc}")

    saknade = sorted(onskade - set(valda), key=lambda n: _sorteringsnyckel((n, "")))

    LAGTEXT_DIR.mkdir(parents=True, exist_ok=True)
    filnamn_for(lag["sfs"]).write_text(
        json.dumps(bygg_lagfil(lag, valda, kalla), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )

    if not tyst:
        status = (
            f"{lag['forkortning']:8s} {len(valda):4d}/{len(onskade):4d} paragrafer"
            f"  [{kalla}]"
        )
        if saknade:
            # Vanligt och oproblematiskt: kursavsnitt anges som intervall och
            # alla nummer i intervallet finns inte alltid som egna paragrafer.
            visa = ", ".join(saknade[:6]) + ("…" if len(saknade) > 6 else "")
            status += f"  (ej funna: {visa})"
        print(status)
    return len(valda), len(onskade)


# --- CLI --------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--uppdatera",
        action="store_true",
        help="hämta om även lagar som redan finns i data/lagtext/",
    )
    parser.add_argument("--lag", help="hämta endast denna förkortning, t.ex. AvtL")
    args = parser.parse_args(argv)

    lagar = json.loads(LAGRUM_PATH.read_text(encoding="utf-8"))["lagar"]
    if args.lag:
        lagar = [lag for lag in lagar if lag["forkortning"] == args.lag]
        if not lagar:
            print(f"Okänd lag: {args.lag}", file=sys.stderr)
            return 1

    totalt = 0
    hoppade = 0
    for i, lag in enumerate(lagar):
        if not args.uppdatera and filnamn_for(lag["sfs"]).exists():
            hoppade += 1
            continue
        try:
            sparade, _onskade = hamta_lag(lag)
            totalt += sparade
        except Exception as exc:  # noqa: BLE001 (ett fel får inte stoppa resten)
            print(f"{lag['forkortning']:8s} MISSLYCKADES: {exc}", file=sys.stderr)
        if i < len(lagar) - 1:
            time.sleep(PAUS_SEKUNDER)

    print(f"\n{totalt} paragrafer sparade i {LAGTEXT_DIR.relative_to(ROT)}/")
    if hoppade:
        print(f"{hoppade} lagar hoppades över (fanns redan). --uppdatera hämtar om.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
