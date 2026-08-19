#!/usr/bin/env python3
"""Hämta lagarnas kapitelrubriker och momentrubriker till data/lagstruktur/.

Syskon till scripts/hamta_lagtext.py och lyder samma regler: körs manuellt,
aldrig av appen, och resultatet committas så att appen fungerar offline.

    python3.11 scripts/hamta_lagstruktur.py              # allt som saknas
    python3.11 scripts/hamta_lagstruktur.py --uppdatera  # hämta om allt
    python3.11 scripts/hamta_lagstruktur.py --lag AvtL   # bara en lag

VAD SOM HÄMTAS
==============

Endast författningens egen disposition: kapitelrubriker, momentrubriker och
paragrafnummer. Ingen paragraftext (den ligger i data/lagtext/) och aldrig
lagen.nu:s egna kommentarer. Rubrikerna är författningstext och undantagna
upphovsrätt enligt 9 § upphovsrättslagen.

HELA LAGEN, INTE BARA APPENS DEL
=================================

Till skillnad från hamta_lagtext.py sparas strukturen för hela lagen, inte
bara för lagavsnitten. Det är förutsättningen för täckningsraden i
lagkortet ("appen behandlar 6 av lagens 8 kapitel"). Utan den läser studenten
avsnittslistan som om lagen tog slut där. Datat är litet: bara rubriker och
paragrafnummer, inga texter.

PARAGRAFNYCKELNS FORM
=====================

``kapitelindelad`` hämtas ur lagrumsregistret och skickas vidare till
parsern. Den får inte gissas ur källans ankare: AvtL märker sina paragrafer
"K2P10" trots att numreringen löper obruten 1-41, och registret säger
kapitelindelad: false. Läser man kapitlet ur ankaret ändå blir nycklarna
omöjliga att foga ihop med korpusen och lagavsnitten.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

ROT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROT))
sys.path.insert(0, str(ROT / "scripts"))

from hamta_lagtext import (  # noqa: E402
    PAUS_SEKUNDER,
    hamta_riksdagen_html,
    riksdagen_url,
)

from utils.lagstruktur_extrahering import extrahera_struktur  # noqa: E402

LAGRUM_PATH = ROT / "data" / "lagrum.json"
STRUKTUR_DIR = ROT / "data" / "lagstruktur"

LICENSNOT = (
    "Författningstext, undantagen upphovsrätt enligt 9 § upphovsrättslagen. "
    "Hämtad från Riksdagens öppna data. Källa: Sveriges riksdag."
)


def filnamn_for(sfs: str) -> Path:
    return STRUKTUR_DIR / f"{sfs.replace(':', '-')}.json"


def bygg_strukturfil(lag: dict, kapitel: list[dict], moment: list[dict]) -> dict:
    return {
        "forkortning": lag["forkortning"],
        "namn": lag["namn"],
        "sfs": lag["sfs"],
        "kalla": riksdagen_url(lag["sfs"]),
        "kallnamn": "Riksdagens öppna data",
        "hamtad": date.today().isoformat(),
        "licens": LICENSNOT,
        "kapitelindelad": bool(lag["kapitelindelad"]),
        "kapitel": kapitel,
        "moment": moment,
    }


def _form(kapitel: list[dict], moment: list[dict]) -> str:
    """Vilken av källans tre former lagen visade sig ha.

    Specen klassificerade sju lagar empiriskt och lämnade fjorton öppna.
    Utskriften bekräftar eller korrigerar den klassificeringen med data.
    """
    if kapitel and moment:
        return "kapitel och moment"
    if kapitel:
        return "bara kapitel"
    if moment:
        return "bara moment"
    return "INGEN STRUKTUR - undersök"


def hamta_lag(lag: dict, *, tyst: bool = False) -> tuple[int, int]:
    """Hämta och spara en lags struktur. Returnerar (antal kapitel, antal moment)."""
    html = hamta_riksdagen_html(lag["sfs"])
    kapitel, moment = extrahera_struktur(
        html, kapitelindelad=bool(lag["kapitelindelad"])
    )

    STRUKTUR_DIR.mkdir(parents=True, exist_ok=True)
    filnamn_for(lag["sfs"]).write_text(
        json.dumps(bygg_strukturfil(lag, kapitel, moment), ensure_ascii=False, indent=1)
        + "\n",
        encoding="utf-8",
    )

    if not tyst:
        antal_paragrafer = len(
            {p for post in (*kapitel, *moment) for p in post["paragrafer"]}
        )
        print(
            f"{lag['forkortning']:8s} {len(kapitel):3d} kapitel  "
            f"{len(moment):4d} moment  {antal_paragrafer:4d} paragrafer   "
            f"[{_form(kapitel, moment)}]"
        )
    return len(kapitel), len(moment)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--uppdatera", action="store_true", help="hämta om allt")
    parser.add_argument("--lag", help="bara denna förkortning")
    parser.add_argument("--tyst", action="store_true", help="ingen utskrift")
    args = parser.parse_args(argv)

    lagar = json.loads(LAGRUM_PATH.read_text(encoding="utf-8"))["lagar"]
    if args.lag:
        lagar = [rad for rad in lagar if rad["forkortning"] == args.lag]
        if not lagar:
            print(f"Okänd lag: {args.lag}", file=sys.stderr)
            return 1

    fel = 0
    for i, lag in enumerate(lagar):
        if not args.uppdatera and filnamn_for(lag["sfs"]).exists():
            continue
        try:
            hamta_lag(lag, tyst=args.tyst)
        except Exception as e:  # noqa: BLE001
            fel += 1
            print(
                f"{lag['forkortning']:8s} FEL: {type(e).__name__}: {e}",
                file=sys.stderr,
            )
        if i < len(lagar) - 1:
            time.sleep(PAUS_SEKUNDER)

    return 1 if fel else 0


if __name__ == "__main__":
    raise SystemExit(main())
