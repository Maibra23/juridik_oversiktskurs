"""Tester för utils.fallkontroll (granskning av genererade rättsfall).

Ren modul, inga LLM-anrop. Täcker de fyra felklasser mätningen över 72
genererade fall faktiskt hittade:
- lagrum utanför modulens vitlista (fältöverskridning)
- paragraf som finns men handlar om något annat än rättsfrågan, upptäckt
  genom att citatet inte går att hitta i lagtexten
- påhittade eller inlånade termer i löptexten
- lagrum skrivna baklänges i löptexten

Fixturernas citat är ordagranna ur data/lagtext. Det är avsiktligt: ett test
som citerade påhittad lagtext skulle testa attrappen, inte garden.
"""

from __future__ import annotations

import pytest

from utils.fallkontroll import (
    FORBJUDNA_ORD,
    MIN_CITATLANGD,
    granska_genererat_case,
)
from utils.lagtext import hamta_paragraftext
from utils.scenarier import Case, CaseFacit

STOLD = "8 kap. 1 § BrB"
NODVARN = "24 kap. 1 § BrB"
JAMKNING = "36 § AvtL"

CITAT_STOLD = "Den som olovligen tager vad annan tillhör"
CITAT_JAMKNING = "Avtalsvillkor får jämkas eller lämnas utan avseende"


def _case(
    lagrum: tuple[str, ...] = (STOLD,),
    rubrik: str = "Varan i fickan",
    scenariotext: str = "Kunden lämnade butiken utan att betala.",
    rattsfraga: str = "Har kunden gjort sig skyldig till stöld?",
    punkter: tuple[str, ...] = ("Tillgreppet innebar skada.",),
    slutsats: str = "Stöld föreligger.",
) -> Case:
    return Case(
        id="gen-test",
        rubrik=rubrik,
        svarighetsgrad="grund",
        uppskattad_tid_min=10,
        scenariotext=scenariotext,
        facit=CaseFacit(
            rattsfraga=rattsfraga,
            lagrum=lagrum,
            tillampningspunkter=punkter,
            slutsats=slutsats,
        ),
    )


def _stod(*par: tuple[str, str]) -> list[dict[str, str]]:
    return [{"lagrum": ref, "citat": citat} for ref, citat in par]


# --- Godkänt ----------------------------------------------------------------

def test_akta_citat_ur_ratt_paragraf_godkanns():
    granskning = granska_genererat_case(
        _case(), ["BrB"], _stod((STOLD, CITAT_STOLD))
    )
    assert granskning.godkand
    assert granskning.skal == ()


def test_citat_matchas_skiftlagesokansligt_och_utan_citattecken():
    granskning = granska_genererat_case(
        _case(), ["BrB"], _stod((STOLD, '"DEN SOM OLOVLIGEN TAGER VAD ANNAN TILLHÖR"'))
    )
    assert granskning.godkand


def test_stod_som_dict_accepteras():
    granskning = granska_genererat_case(_case(), ["BrB"], {STOLD: CITAT_STOLD})
    assert granskning.godkand


def test_tom_vitlista_hoppar_over_falkontrollen_men_inte_citatet():
    """Utan modulkontext prövas allt utom just vitlistetillhörigheten."""
    assert granska_genererat_case(_case(), (), _stod((STOLD, CITAT_STOLD))).godkand
    assert not granska_genererat_case(_case(), (), None).godkand


# --- Fältöverskridning ------------------------------------------------------

def test_lagrum_utanfor_modulens_vitlista_underkanns():
    granskning = granska_genererat_case(
        _case(lagrum=(JAMKNING,)), ["LAS"], _stod((JAMKNING, CITAT_JAMKNING))
    )
    assert not granskning.godkand
    assert "utanför modulens lagrumsvitlista" in granskning.aterkoppling


def test_lagrum_i_vitlistan_passerar_falkontrollen():
    granskning = granska_genererat_case(
        _case(lagrum=(JAMKNING,), rattsfraga="Är villkoret oskäligt?"),
        ["AvtL"],
        _stod((JAMKNING, CITAT_JAMKNING)),
    )
    assert granskning.godkand


# --- Roll: citatet avslöjar fel paragraf ------------------------------------

def test_paragraf_om_nagot_annat_underkanns_via_citatet():
    """Nödvärnsparagrafen i ett bedrägerifall: existerar, men bär inte frågan.

    Det här är den felklass som stod för 30 av 72 fall i mätningen. Modellen
    kan inte citera 24 kap. 1 § BrB om bedrägeri, eftersom paragrafen handlar
    om nödvärn.
    """
    granskning = granska_genererat_case(
        _case(lagrum=(NODVARN,), rattsfraga="Har Anna begått bedrägeri?"),
        ["BrB"],
        _stod((NODVARN, "Den som genom vilseledande förmår någon till handling")),
    )
    assert not granskning.godkand
    assert "står inte så i paragrafens lagtext" in granskning.aterkoppling


def test_saknat_citat_underkanns():
    granskning = granska_genererat_case(_case(), ["BrB"], None)
    assert not granskning.godkand
    assert "saknar citat" in granskning.aterkoppling


def test_citat_for_ett_av_tva_lagrum_racker_inte():
    granskning = granska_genererat_case(
        _case(lagrum=(STOLD, NODVARN)), ["BrB"], _stod((STOLD, CITAT_STOLD))
    )
    assert not granskning.godkand
    assert NODVARN in granskning.aterkoppling


def test_for_kort_citat_underkanns():
    kort = CITAT_STOLD[: MIN_CITATLANGD - 5]
    granskning = granska_genererat_case(_case(), ["BrB"], _stod((STOLD, kort)))
    assert not granskning.godkand
    assert "för kort" in granskning.aterkoppling


def test_citat_maste_vara_ordagrant_inte_bara_likt():
    granskning = granska_genererat_case(
        _case(), ["BrB"], _stod((STOLD, "Den som olovligen tar det som tillhör annan"))
    )
    assert not granskning.godkand


# --- Grundning --------------------------------------------------------------

def test_facit_utan_lagrum_underkanns():
    granskning = granska_genererat_case(_case(lagrum=()), ["BrB"], None)
    assert not granskning.godkand
    assert "saknar lagrum" in granskning.aterkoppling


def test_overifierat_lagrum_underkanns_utan_citatbesked():
    """Ett obefintligt lagrum ska ge ETT besked, inte två om samma sak."""
    granskning = granska_genererat_case(
        _case(lagrum=("99 § AvtL",)), ["AvtL"], _stod(("99 § AvtL", CITAT_JAMKNING))
    )
    assert not granskning.godkand
    assert "kunde inte verifieras" in granskning.aterkoppling
    assert "saknar citat" not in granskning.aterkoppling


# --- Språk och lagrumsform --------------------------------------------------

@pytest.mark.parametrize("ord_", FORBJUDNA_ORD)
def test_varje_forbjudet_ord_stoppas(ord_: str):
    granskning = granska_genererat_case(
        _case(scenariotext=f"Parterna tvistar om en {ord_} i avtalet."),
        ["BrB"],
        _stod((STOLD, CITAT_STOLD)),
    )
    assert not granskning.godkand
    assert ord_ in granskning.aterkoppling


def test_omvand_lagrumsordning_i_lloptext_underkanns():
    granskning = granska_genererat_case(
        _case(scenariotext="Enligt BrB 8 kap. 1 § är detta stöld."),
        ["BrB"],
        _stod((STOLD, CITAT_STOLD)),
    )
    assert not granskning.godkand
    assert "baklänges" in granskning.aterkoppling


def test_ratt_lagrumsordning_i_loptext_godkanns():
    granskning = granska_genererat_case(
        _case(scenariotext="Enligt 8 kap. 1 § BrB är detta stöld."),
        ["BrB"],
        _stod((STOLD, CITAT_STOLD)),
    )
    assert granskning.godkand


def test_omvand_ordning_upptacks_aven_i_slutsatsen():
    granskning = granska_genererat_case(
        _case(slutsats="Ansvar följer av BrB 8 kap. 1 §."),
        ["BrB"],
        _stod((STOLD, CITAT_STOLD)),
    )
    assert not granskning.godkand


# --- Återkoppling -----------------------------------------------------------

def test_flera_fel_samlas_i_en_aterkoppling():
    granskning = granska_genererat_case(
        _case(
            lagrum=(JAMKNING,),
            scenariotext="En penaltiklausul enligt AvtL 36 § är oskälig.",
        ),
        ["LAS"],
        None,
    )
    assert not granskning.godkand
    assert len(granskning.skal) >= 3
    assert granskning.aterkoppling.count(".") >= 3


def test_lagtexten_som_fixturerna_citerar_ar_akta():
    """Skydd mot att fixturerna tyst glider ifrån data/lagtext."""
    assert CITAT_STOLD in (hamta_paragraftext(STOLD) or "")
    assert CITAT_JAMKNING in (hamta_paragraftext(JAMKNING) or "")


# --- Tolerans mot korpusartefakter och moderniserade arkaismer --------------
#
# Exakt delsträngsmatchning underkände fall där modellen valt RÄTT paragraf.
# Trösklarna i utils.fallkontroll är kalibrerade mot de mätvärden som står
# dokumenterade där; testerna nedan håller kalibreringen på plats.


def test_citat_med_blankstegsartefakt_i_korpusen_godkanns():
    """13 kap. 3 § RB saknar ett blanksteg i vår egen korpus ("dockpå")."""
    ref = "13 kap. 3 § RB"
    granskning = granska_genererat_case(
        _case(lagrum=(ref,), rattsfraga="Får talan ändras?"),
        ["RB"],
        _stod(
            (
                ref,
                "Väckt talan får inte ändras. Käranden får dock på grund av "
                "omständighet, som inträffat under rättegången",
            )
        ),
    )
    assert granskning.godkand, granskning.aterkoppling


def test_citat_med_moderniserad_arkaism_godkanns():
    """Modellen skriver "ha" där 2 § AvtL har "hava". Paragrafen är rätt."""
    granskning = granska_genererat_case(
        _case(lagrum=("2 § AvtL",), rattsfraga="Kom svaret i tid?"),
        ["AvtL"],
        _stod(
            (
                "2 § AvtL",
                "Har anbudsgivaren bestämt viss tid för svar, skall han anses "
                "ha föreskrivit, att svaret skall inom den tid komma honom "
                "till handa.",
            )
        ),
    )
    assert granskning.godkand, granskning.aterkoppling


@pytest.mark.parametrize(
    ("ref", "pahitt"),
    [
        (NODVARN, "Den som genom vilseledande förmår någon till handling eller underlåtenhet"),
        (JAMKNING, "Ett avtal är bindande när anbud och accept överensstämmer med varandra"),
        ("5 § GFL", "Den som i god tro förvärvat lös egendom av omyndig person förvärvar äganderätt"),
    ],
)
def test_toleransen_slapper_inte_igenom_pahittade_citat(ref: str, pahitt: str):
    """Toleransen får inte öppna för juridiskt klingande påhitt."""
    granskning = granska_genererat_case(
        _case(lagrum=(ref,)), [ref.split()[-1]], _stod((ref, pahitt))
    )
    assert not granskning.godkand


def test_omskrivning_med_egna_ord_racker_inte():
    """Rätt paragraf men egna formuleringar: citatet ska vara avskrivet."""
    granskning = granska_genererat_case(
        _case(),
        ["BrB"],
        _stod(
            (
                STOLD,
                "Den som olovligen tar det som tillhör någon annan med avsikt "
                "att behålla det gör sig skyldig till stöld",
            )
        ),
    )
    assert not granskning.godkand


def test_spridda_funktionsord_ger_inte_tillrackligt_stod():
    """Täckning utan en lång sammanhängande passage ska inte räcka."""
    granskning = granska_genererat_case(
        _case(),
        ["BrB"],
        _stod((STOLD, "den som och att det annan med för till om av i en")),
    )
    assert not granskning.godkand


# --- Främmande bokstäver ----------------------------------------------------
#
# Blocklistan är efterklok och fångar bara ord någon redan sett. Den här
# kontrollen fångar en hel klass inlånade ord via tecknen i stället.


@pytest.mark.parametrize(
    ("text", "vantat"),
    [
        ("Arbetsgivaren åberopade en kündigungsperiod om tre månader.", "kündigungsperiod"),
        ("Parterna hänvisade till Straße 12 i avtalet.", "Straße"),
        ("Køberen ville häva köpet.", "Køberen"),
        ("Sælgeren bestred kravet.", "Sælgeren"),
    ],
)
def test_inlanade_ord_stoppas_pa_sina_bokstaver(text: str, vantat: str):
    granskning = granska_genererat_case(
        _case(scenariotext=text), ["BrB"], _stod((STOLD, CITAT_STOLD))
    )
    assert not granskning.godkand
    assert vantat in granskning.aterkoppling


def test_kyrillisk_homoglyf_stoppas():
    """Ett kyrilliskt a mitt i ett svenskt ord ser rätt ut men är det inte.

    Homoglyfen skrivs som escapesekvens, av samma skäl som i tests/test_sprak.py:
    annars flaggar repots egen språkvakt den här testfilen.
    """
    homoglyf = "Avtalet var ogiltigt enligt \u0430vtalslagen."
    granskning = granska_genererat_case(
        _case(scenariotext=homoglyf),
        ["BrB"],
        _stod((STOLD, CITAT_STOLD)),
    )
    assert not granskning.godkand
    assert "inte finns i svenskan" in granskning.aterkoppling


@pytest.mark.parametrize(
    "text",
    [
        "Anna ingick ett avtal om köp av en cykel för 5 000 kr.",
        "Han satt på ett kafé och fick en idé om ändrade förhållanden.",
        "Enligt 2 kap. 1 § SkL och 36 § AvtL gäller detta.",
        "Domstolen skrev ”sakliga skäl” i domen.",
        "Bolaget AB Nord & Co. betalade 12,5 % i ränta.",
    ],
)
def test_ren_svenska_slapps_igenom(text: str):
    granskning = granska_genererat_case(
        _case(scenariotext=text), ["BrB"], _stod((STOLD, CITAT_STOLD))
    )
    assert granskning.godkand, granskning.aterkoppling


def test_kuraterat_innehall_skulle_inte_fallas():
    """Guarden får inte vara hårdare än appens eget granskade innehåll."""
    from utils.fallkontroll import _frammande_bokstaver
    from utils.scenarier import ladda_modul, lista_moduler

    for stem in lista_moduler():
        modul = ladda_modul(stem)
        for case in modul.case:
            text = " ".join(
                [case.rubrik, case.scenariotext, case.facit.rattsfraga,
                 case.facit.slutsats, *case.facit.tillampningspunkter]
            )
            assert _frammande_bokstaver(text) == [], f"{stem}/{case.id}"


def test_lagtextkorpusen_skulle_inte_fallas():
    """Samma krav på de 21 författningarnas egen ordalydelse."""
    from utils.fallkontroll import _frammande_bokstaver
    from utils.lagtext import ladda_lagtext

    for forkortning, lagtext in ladda_lagtext().items():
        for nyckel, text in lagtext.paragrafer.items():
            assert _frammande_bokstaver(text) == [], f"{forkortning} {nyckel}"
