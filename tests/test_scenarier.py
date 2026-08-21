"""Tester för utils.scenarier.

Täcker inläsning av basscenarier, strukturvalidering, att varje lagrum i
Avtalsrätt-modulen verifieras mot data/lagrum.json och att varje
flervalsfråga har exakt ett rätt svar.
"""

from __future__ import annotations

import pytest

from utils.scenarier import (
    Modulscenarier,
    alla_lagrum,
    fragor_utan_exakt_ett_ratt,
    ladda_fil,
    ladda_modul,
    lista_moduler,
    ogiltiga_lagrum,
)


@pytest.fixture(scope="module")
def avtalsratt() -> Modulscenarier:
    return ladda_modul("avtalsratt")


# --- Inläsning och struktur -------------------------------------------------

def test_avtalsratt_laddas(avtalsratt):
    assert avtalsratt.modul == "Avtalsrätt"


def test_avtalsratt_har_forvantat_antal_ovningar(avtalsratt):
    assert len(avtalsratt.case) == 2
    assert len(avtalsratt.flervalsfragor) == 8
    assert len(avtalsratt.lagrumsjakt) == 4


def test_varje_case_har_rnts_facit(avtalsratt):
    for c in avtalsratt.case:
        assert c.facit.rattsfraga
        assert c.facit.lagrum
        assert c.facit.tillampningspunkter
        assert c.facit.slutsats


def test_lista_moduler_innehaller_avtalsratt():
    assert "avtalsratt" in lista_moduler()


# --- Hallucinationsskydd: lagrum måste verifieras ---------------------------

def test_alla_lagrum_i_avtalsratt_ar_verifierade(avtalsratt):
    # Kärnan i Dag 1: avtalsrättsdata inläst OCH validerad mot lagrum.json.
    problem = ogiltiga_lagrum(avtalsratt)
    assert problem == (), f"Overifierade lagrum: {problem}"


def test_alla_lagrum_tillhor_avtalslagen(avtalsratt):
    # Alla referenser i modulen ska peka på AvtL i denna modul.
    for ref in alla_lagrum(avtalsratt):
        assert ref.endswith("AvtL"), ref


# --- Quizintegritet ---------------------------------------------------------

def test_varje_flervalsfraga_har_exakt_ett_ratt(avtalsratt):
    assert fragor_utan_exakt_ett_ratt(avtalsratt) == ()


def test_varje_alternativ_har_forklaring(avtalsratt):
    for q in avtalsratt.flervalsfragor:
        for a in q.alternativ:
            assert a.forklaring, f"Alternativ utan förklaring i {q.id}"


# --- Ingress ------------------------------------------------------------------

def test_modul_utan_ingress_far_tom_strang():
    """Fältet är valfritt: befintliga scenariofiler ska läsas oförändrat."""
    from utils.scenarier import ladda_modul

    modul = ladda_modul("avtalsratt")
    assert isinstance(modul.ingress, str)


def test_ingress_lases_in_nar_den_finns(tmp_path, monkeypatch):
    import json

    from utils import scenarier

    data = {
        "modul": "Testmodul",
        "ingress": "En mening om just den här modulen.",
        "case": [],
        "flervalsfragor": [],
        "lagrumsjakt": [],
    }
    fil = tmp_path / "testmodul.json"
    fil.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(scenarier, "SCENARIER_DIR", tmp_path)
    assert scenarier.ladda_modul("testmodul").ingress == (
        "En mening om just den här modulen."
    )


# --- Deklarerad vitlista och rättsområde ------------------------------------
#
# Tillagt efter mätningen som visade att den härledda vitlistan gjorde
# rättsområdets täckning till en bieffekt av vilka fall någon råkat skriva.


def test_alla_moduler_deklarerar_lagar_och_omrade():
    """Varje modul ska säga vilka lagar den omfattar och vad området är."""
    for stem in lista_moduler():
        modul = ladda_modul(stem)
        assert modul.lagar, f"{stem} saknar deklarerad lagrumsvitlista"
        assert modul.omrade.strip(), f"{stem} saknar rättsområdesbeskrivning"


def test_deklarerade_lagar_finns_i_registret():
    from utils.lagrum import giltiga_forkortningar

    kanda = giltiga_forkortningar()
    for stem in lista_moduler():
        for fk in ladda_modul(stem).lagar:
            assert fk in kanda, f"{stem} deklarerar okänd förkortning {fk!r}"


def test_kuraterat_facit_ligger_i_modulens_deklarerade_vitlista():
    """Deklarationen får inte vara smalare än modulens egna rätta svar.

    Prövas mot rättsfallens facit och lagrumsjaktens facit, alltså det som
    modulen själv utpekar som RÄTT lagrum. Flervalsfrågornas alternativ är
    med flit undantagna: distraktorerna citerar avsiktligt lagrum från andra
    rättsområden (36 § AvtL som fel svar i en godtrosförvärvsfråga), och de
    ska inte kunna vidga vad sidan genererar.
    """
    for stem in lista_moduler():
        modul = ladda_modul(stem)
        facitlagrum = [ref for c in modul.case for ref in c.facit.lagrum]
        facitlagrum += [ref for lj in modul.lagrumsjakt for ref in lj.facit_lagrum]
        for ref in facitlagrum:
            fk = ref.split()[-1]
            assert fk in modul.lagar, (
                f"{stem}: kuraterat facitlagrum {ref!r} ligger utanför den "
                f"deklarerade vitlistan {modul.lagar}"
            )


def test_okand_forkortning_i_lagar_stoppar_inlasningen(tmp_path):
    """Ett stavfel ska fälla inläsningen, inte tyst krympa kursplanen."""
    import json

    fil = tmp_path / "trasig.json"
    fil.write_text(
        json.dumps({"modul": "Trasig", "lagar": ["AvtL", "AvtLL"], "case": []}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="AvtLL"):
        ladda_fil(fil)


def test_lagar_som_inte_ar_lista_stoppar_inlasningen(tmp_path):
    import json

    fil = tmp_path / "trasig.json"
    fil.write_text(
        json.dumps({"modul": "Trasig", "lagar": "AvtL", "case": []}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="lagar"):
        ladda_fil(fil)


def test_fil_utan_lagar_las_fortfarande():
    """Bakåtkompatibilitet: fältet är valfritt."""
    modul = Modulscenarier(modul="Tom", case=(), flervalsfragor=(), lagrumsjakt=())
    assert modul.lagar == ()
    assert modul.omrade == ""
