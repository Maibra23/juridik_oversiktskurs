"""Tester för försoningen mellan lagavsnitt och lagens struktur.

Bakgrund: data/lagrum.json bär 105 lagavsnitt, varav 78 flaggade med
"verifiera": true, osäkra paragrafgränser som skulle kontrolleras mot
lagen.nu. Så länge avsnitten bara matade validering och prompter var en
oskarp gräns billig. När de visas i lagkortet blir den ett påstående
studenten läser som sant.

Korpusen i data/lagtext/ kan inte användas som facit: den härleddes ur
lagavsnitten (scripts/hamta_lagtext.py sparar bara paragrafer inom dem),
så den fångar bara för vida gränser, aldrig för snäva. Lagens egen struktur
fångar båda.
"""

from __future__ import annotations

import pytest

from utils.lagavsnitt_kontroll import (
    TYP_FOR_SNAV,
    TYP_OVERSKJUTANDE,
    Avvikelse,
    avsnittsnycklar,
    kontrollera_alla,
    kontrollera_lag,
)
from utils.lagrum import Lag, Lagavsnitt
from utils.lagstruktur import Kapitel, Lagstruktur, Moment


def _lag(kapitelindelad: bool, avsnitt: tuple[Lagavsnitt, ...]) -> Lag:
    return Lag(
        forkortning="TestL",
        namn="Testlagen",
        sfs="2026:1",
        kapitelindelad=kapitelindelad,
        lagen_nu_bas_url="https://lagen.nu/2026:1",
        lagavsnitt=avsnitt,
    )


def _avsnitt(beskrivning, kapitel, fran, till, verifiera=True) -> Lagavsnitt:
    return Lagavsnitt(
        beskrivning=beskrivning,
        kapitel=kapitel,
        paragraf_fran=fran,
        paragraf_till=till,
        lagen_nu_url="https://lagen.nu/2026:1",
        verifiera=verifiera,
    )


def _struktur(kapitel=(), moment=()) -> Lagstruktur:
    return Lagstruktur(
        forkortning="TestL",
        namn="Testlagen",
        sfs="2026:1",
        kalla="",
        kallnamn="",
        hamtad="",
        licens="",
        kapitel=kapitel,
        moment=moment,
    )


def test_avsnittsnycklar_expanderar_kapitelindelat_intervall():
    lag = _lag(True, ())
    assert avsnittsnycklar(lag, _avsnitt("x", "3", 1, 3)) == ("3:1", "3:2", "3:3")


def test_avsnittsnycklar_expanderar_platt_intervall():
    lag = _lag(False, ())
    assert avsnittsnycklar(lag, _avsnitt("x", None, 10, 12)) == ("10", "11", "12")


def test_avsnittsnycklar_ignorerar_kapitel_for_kapitellos_lag():
    """AvtL bär kapitel i strukturen men refererar platt i registret."""
    lag = _lag(False, ())
    assert avsnittsnycklar(lag, _avsnitt("x", "2", 10, 11)) == ("10", "11")


def test_overskjutande_grans_upptacks():
    """Avsnittet påstår paragrafer som inte finns i lagen."""
    lag = _lag(True, (_avsnitt("Talan", "13", 1, 9),))
    struktur = _struktur(
        kapitel=(Kapitel("13", "Om talan", ("13:1", "13:2", "13:3")),)
    )
    avvikelser = kontrollera_lag(lag, struktur)
    overskjutande = [a for a in avvikelser if a.typ == TYP_OVERSKJUTANDE]
    assert len(overskjutande) == 1
    assert "13:4" in overskjutande[0].detalj


def test_ingen_avvikelse_nar_gransen_stammer():
    lag = _lag(True, (_avsnitt("Om talan", "13", 1, 3),))
    struktur = _struktur(
        kapitel=(Kapitel("13", "Om talan", ("13:1", "13:2", "13:3")),)
    )
    kvar = [a for a in kontrollera_lag(lag, struktur) if a.typ == TYP_OVERSKJUTANDE]
    assert kvar == []


def test_for_snav_grans_upptacks():
    """Momentet sträcker sig utanför avsnittet, korpusen kunde aldrig se detta."""
    lag = _lag(True, (_avsnitt("Påföljder", "5", 1, 2),))
    struktur = _struktur(
        kapitel=(Kapitel("5", "Påföljder", ("5:1", "5:2", "5:3")),),
        moment=(Moment("Påföljder vid fel", "5", ("5:1", "5:2", "5:3")),),
    )
    avvikelser = [a for a in kontrollera_lag(lag, struktur) if a.typ == TYP_FOR_SNAV]
    assert len(avvikelser) == 1
    assert "5:3" in avvikelser[0].detalj


def test_avvikelser_ar_immutabla():
    a = Avvikelse("TestL", "Talan", TYP_OVERSKJUTANDE, "13:4")
    with pytest.raises(Exception):
        a.typ = TYP_FOR_SNAV


def test_kontrollera_alla_tacker_hela_registret():
    """Kontrollen ska köras mot alla lagar, inte bara dem som råkar avvika."""
    avvikelser = kontrollera_alla()
    assert isinstance(avvikelser, tuple)
    assert all(isinstance(a, Avvikelse) for a in avvikelser)


def test_varje_lagavsnitt_pekar_pa_ett_kapitel_som_finns():
    """En kapitelindelad lags avsnitt måste peka på ett verkligt kapitel.

    Överskjutandetestet fångar paragrafer utanför lagen, men inte ett avsnitt
    som pekar på ett kapitel som inte existerar alls, då blir hela
    anspråket okänt och avsnittet skulle visas utan ryggrad i lagkortet.
    """
    from utils.lagrum import lagrum_register
    from utils.lagstruktur import ladda_lagstruktur

    strukturer = ladda_lagstruktur()
    fel = []
    for forkortning, lag in sorted(lagrum_register().items()):
        if not lag.kapitelindelad:
            continue
        nummer = {k.nummer for k in strukturer[forkortning].kapitel}
        for avsnitt in lag.lagavsnitt:
            if avsnitt.kapitel is not None and avsnitt.kapitel not in nummer:
                fel.append(
                    f"{forkortning}: {avsnitt.beskrivning!r} pekar på "
                    f"{avsnitt.kapitel} kap., som inte finns i lagen"
                )
    assert fel == [], "\n".join(fel)


def test_inga_lagavsnitt_pekar_utanfor_lagen():
    """Bärande invariant: inget lagavsnitt får påstå paragrafer som inte finns.

    RÖD tills de flaggade avsnitten gåtts igenom. Därefter en permanent
    spärr mot att nästa lagändring smyger in samma fel.
    """
    fel = [a for a in kontrollera_alla() if a.typ == TYP_OVERSKJUTANDE]
    assert fel == [], "\n".join(
        f"{a.forkortning}: {a.avsnitt} -- {a.detalj}" for a in fel
    )
