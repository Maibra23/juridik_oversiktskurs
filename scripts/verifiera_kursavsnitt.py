#!/usr/bin/env python3
"""Skriv ut avvikelser mellan kursavsnitten och lagarnas faktiska struktur.

    python3.11 scripts/verifiera_kursavsnitt.py            # alla avvikelser
    python3.11 scripts/verifiera_kursavsnitt.py --typ OVERSKJUTANDE
    python3.11 scripts/verifiera_kursavsnitt.py --lag RB

Skriptet RÄTTAR ALDRIG data/lagrum.json. Om ett avsnitt ska sluta vid 13:5
eller 13:7 är en bedömning av kursens omfång, inte en textjämförelse.
Rapporten är underlag; beslutet är människans.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.kursavsnitt_kontroll import FORKLARING, kontrollera_alla  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--typ", help="visa bara denna avvikelsetyp")
    parser.add_argument("--lag", help="visa bara denna lag")
    args = parser.parse_args(argv)

    avvikelser = kontrollera_alla()
    if args.typ:
        avvikelser = tuple(a for a in avvikelser if a.typ == args.typ)
    if args.lag:
        avvikelser = tuple(a for a in avvikelser if a.forkortning == args.lag)

    for avvikelse in avvikelser:
        print(f"{avvikelse.forkortning:8s} [{avvikelse.typ}]")
        print(f"         {avvikelse.avsnitt}")
        print(f"         {avvikelse.detalj}")
        print()

    rakning = Counter(a.typ for a in avvikelser)
    print("SAMMANFATTNING")
    for typ, antal in sorted(rakning.items()):
        print(f"  {antal:4d}  {typ}: {FORKLARING.get(typ, '')}")
    print(f"  {len(avvikelser):4d}  totalt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
