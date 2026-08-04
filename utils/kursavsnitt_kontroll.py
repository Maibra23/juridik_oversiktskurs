"""Jämför kursavsnitten i data/lagrum.json mot lagens faktiska struktur.

Registret bär 105 kursavsnitt, varav 78 flaggade med "verifiera": true --
osäkra paragrafgränser eller osäkert kursomfång. Den här modulen är facit:
den säger vad som avviker, i fyra sorter.

Vad modulen INTE gör: den rättar aldrig registret. Om ett avsnitt ska
omfatta 13:1-13:7 eller 13:1-13:5 är en bedömning av kursens omfång, inte
en textjämförelse. Modulen rapporterar; människan beslutar.

Ren modul utan Streamlit-beroende.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.lagrum import Kursavsnitt, Lag, lagrum_register
from utils.lagstruktur import (
    Lagstruktur,
    Moment,
    ladda_lagstruktur,
    paragrafnycklar_i,
)

TYP_OVERSKJUTANDE = "OVERSKJUTANDE"
TYP_FOR_SNAV = "FOR_SNAV"
TYP_RUBRIKAVVIKELSE = "RUBRIKAVVIKELSE"
TYP_SPANNER_OVER_MOMENT = "SPANNER_OVER_MOMENT"

FORKLARING = {
    TYP_OVERSKJUTANDE: "Avsnittet anger paragrafer som inte finns i lagen.",
    TYP_FOR_SNAV: "Momentets paragrafer sträcker sig utanför avsnittet.",
    TYP_RUBRIKAVVIKELSE: "Beskrivningen skiljer sig från lagens egen rubrik.",
    TYP_SPANNER_OVER_MOMENT: "Avsnittet skär genom flera moment.",
}


@dataclass(frozen=True)
class Avvikelse:
    """En skillnad mellan ett kursavsnitt och lagens struktur."""

    forkortning: str
    avsnitt: str
    typ: str
    detalj: str


def avsnittsnycklar(lag: Lag, avsnitt: Kursavsnitt) -> tuple[str, ...]:
    """Paragrafnycklarna ett kursavsnitt gör anspråk på.

    Samma expansion som scripts/hamta_lagtext.kursens_nycklar, men på
    registrets modell i stället för på råa dictar. Kapitelledet används bara
    för kapitelindelade lagar: AvtL och SkbrL bär kapitelrubriker i
    strukturen men refererar platt i registret.
    """
    kapitel = avsnitt.kapitel if lag.kapitelindelad else None
    return tuple(
        f"{kapitel}:{nr}" if kapitel else str(nr)
        for nr in range(avsnitt.paragraf_fran, avsnitt.paragraf_till + 1)
    )


def _sortering(nyckel: str) -> tuple[int, int]:
    if ":" in nyckel:
        kap, par = nyckel.split(":", 1)
        return (int(kap), int(par))
    return (0, int(nyckel))


def _moment_som_overlappar(
    struktur: Lagstruktur, nycklar: frozenset[str]
) -> tuple[Moment, ...]:
    return tuple(m for m in struktur.moment if nycklar & set(m.paragrafer))


def kontrollera_lag(lag: Lag, struktur: Lagstruktur) -> tuple[Avvikelse, ...]:
    """Alla avvikelser mellan en lags kursavsnitt och dess struktur."""
    finns = paragrafnycklar_i(struktur)

    avvikelser: list[Avvikelse] = []
    for avsnitt in lag.kursavsnitt:
        anspraak = frozenset(avsnittsnycklar(lag, avsnitt))

        saknade = sorted(anspraak - finns, key=_sortering)
        if saknade:
            avvikelser.append(
                Avvikelse(
                    lag.forkortning,
                    avsnitt.beskrivning,
                    TYP_OVERSKJUTANDE,
                    f"finns inte i lagen: {', '.join(saknade)}",
                )
            )

        overlappande = _moment_som_overlappar(struktur, anspraak)
        for moment in overlappande:
            utanfor = sorted(set(moment.paragrafer) - anspraak, key=_sortering)
            if utanfor:
                avvikelser.append(
                    Avvikelse(
                        lag.forkortning,
                        avsnitt.beskrivning,
                        TYP_FOR_SNAV,
                        f"momentet {moment.rubrik!r} har även: "
                        f"{', '.join(utanfor)}",
                    )
                )

        if len(overlappande) > 1:
            rubriker = ", ".join(repr(m.rubrik) for m in overlappande)
            avvikelser.append(
                Avvikelse(
                    lag.forkortning,
                    avsnitt.beskrivning,
                    TYP_SPANNER_OVER_MOMENT,
                    f"berör momenten: {rubriker}",
                )
            )

        if len(overlappande) == 1:
            rubrik = overlappande[0].rubrik
            if rubrik.casefold() != avsnitt.beskrivning.casefold():
                avvikelser.append(
                    Avvikelse(
                        lag.forkortning,
                        avsnitt.beskrivning,
                        TYP_RUBRIKAVVIKELSE,
                        f"lagens rubrik lyder {rubrik!r}",
                    )
                )

    return tuple(avvikelser)


def kontrollera_alla() -> tuple[Avvikelse, ...]:
    """Kontrollera hela registret mot alla strukturfiler."""
    strukturer = ladda_lagstruktur()
    avvikelser: list[Avvikelse] = []
    for forkortning, lag in sorted(lagrum_register().items()):
        struktur = strukturer.get(forkortning)
        if struktur is None:
            continue
        avvikelser.extend(kontrollera_lag(lag, struktur))
    return tuple(avvikelser)
