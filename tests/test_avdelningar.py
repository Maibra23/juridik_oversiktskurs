"""Tester för avdelningsnivån som EN källa (AVD I-IV).

Bokens fyra avdelningar är kursdata, inte grafdata. De låg tidigare hårdkodade
i utils.rattssystem_graf, medan nyckeln ``avdelning`` per område lästes ur
data/rattssystem.json i en andra, separat JSON-läsning. Följden var att
Obsidian-exportens rättskarta inte hade någon avdelningsnivå alls: appen och
valvet visade olika kartor.

De här testerna låser att båda vyerna bygger på samma källa, så att de inte
kan glida isär igen.
"""

from __future__ import annotations

import pytest

from utils.rattskarta import (
    ladda_avdelningar,
    ladda_rattssystem,
    rattskarta_not,
)


@pytest.fixture(scope="module")
def avdelningar():
    return ladda_avdelningar()


def test_alla_fyra_avdelningarna_finns(avdelningar):
    assert len(avdelningar) == 4
    ider = [a.id for a in avdelningar]
    assert ider == [
        "avd1_introduktion",
        "avd2_offentlig_ratt",
        "avd3_civilratt",
        "avd4_straff_process",
    ], "avdelningarna ska komma i dispositionens ordning"


def test_varje_omrade_pekar_pa_en_giltig_avdelning(avdelningar):
    """Ett område utan giltig avdelning tappar en gren ur kartan."""
    giltiga = {a.id for a in avdelningar}
    for omrade in ladda_rattssystem():
        assert omrade.avdelning in giltiga, (
            f"{omrade.namn!r} pekar på okänd avdelning {omrade.avdelning!r}"
        )


def test_grafmodulen_haller_ingen_egen_kopia_av_avdelningarna():
    """Grafmodulen ska konsumera avdelningarna, inte äga dem.

    Varken en hårdkodad tuppel eller en modulkonstant som binds vid import:
    båda kan bli inaktuella mot datat och är precis vad som lät appen och
    Obsidian-exporten visa olika kartor.
    """
    from utils import rattssystem_graf

    assert not hasattr(rattssystem_graf, "AVDELNINGAR"), (
        "utils.rattssystem_graf ska anropa ladda_avdelningar() på "
        "användningsstället, inte hålla en egen modulkonstant"
    )


def test_grafens_avdelningar_ar_samma_som_kartans(avdelningar):
    """Trädet grafen bygger ska följa datats disposition, i samma ordning."""
    from utils.rattssystem_graf import taxonomi

    assert [a.id for a in taxonomi()] == [a.id for a in avdelningar]
    assert [a.label for a in taxonomi()] == [a.label for a in avdelningar]


# --- Exporten: samma avdelningar som appen ---------------------------------


def test_exportens_rattskarta_har_alla_avdelningar(avdelningar):
    """Valvet ska visa samma disposition som appen, inte en avkortad karta."""
    not_ = rattskarta_not()
    for a in avdelningar:
        assert a.label in not_, f"{a.label!r} saknas i Obsidian-exporten"


def test_exportens_omraden_ligger_under_ratt_avdelning(avdelningar):
    """Varje område ska stå efter sin egen avdelningsrubrik, inte någon annans."""
    not_ = rattskarta_not()
    etikett_for = {a.id: a.label for a in avdelningar}

    for omrade in ladda_rattssystem():
        rubrik = etikett_for[omrade.avdelning]
        pos_rubrik = not_.index(rubrik)
        pos_omrade = not_.index(f"[[{omrade.namn}]]")
        assert pos_rubrik < pos_omrade, (
            f"{omrade.namn!r} står före sin avdelningsrubrik {rubrik!r}"
        )

        # Ingen annan avdelningsrubrik får hamna emellan.
        mellan = not_[pos_rubrik:pos_omrade]
        for annan in avdelningar:
            if annan.id != omrade.avdelning:
                assert annan.label not in mellan, (
                    f"{omrade.namn!r} hamnade under {annan.label!r} i stället "
                    f"för under {rubrik!r}"
                )


def test_avd1_tas_med_i_exporten_trots_att_den_saknar_omraden(avdelningar):
    """AVD I är metodavdelningen och har inga rättsområden, men ska synas."""
    avd1 = next(a for a in avdelningar if a.id == "avd1_introduktion")
    not_ = rattskarta_not()
    assert avd1.label in not_
    assert avd1.beskrivning in not_


def test_exporten_ar_fortfarande_giltig_markdown():
    """Rubriknivåerna får inte kollidera med kartans callout-träd."""
    not_ = rattskarta_not()
    assert "# Rättskartan: det svenska rättssystemet" in not_
    # Avdelningarna ligger på H2, kartans egna rubriker likaså.
    assert "## Vilken lag gäller för mitt fall?" in not_
    # Callout-trädet ska inte ha fått en extra nivå av wrappning.
    assert "> > > [!" not in not_, (
        "avdelningarna ska vara rubriker, inte ytterligare en callout-nivå"
    )
