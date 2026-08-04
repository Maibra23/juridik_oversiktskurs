"""Tester för granskningen av tutorsvar (utils.granskning).

Garden släpper igenom eller stoppar ett svar INNAN studenten ser det. Den
bygger på en insikt ur sessionens mätningar som är lätt att missa:

**Det bästa svaret innehöll ett påhittat lagrum.**

När en student citerade det obefintliga "87 § AvtL" var det korrekta
tutorsvaret att nämna paragrafen och avvisa den: "87 § AvtL finns inte i
lagrumslistan. Detta är ett allvarligt fel." En gard som bara letar efter
overifierade lagrum hade blockerat just det svaret och släppt igenom det
sämre.

Avgörande är därför inte OM ett lagrum nämns, utan i vilken roll. Ett lagrum
utanför underlaget måste avvisas i texten. Går det inte att avgöra godkänns
svaret och varnas som förut: hellre släppa igenom ett tveksamt svar än
censurera korrekt undervisning.
"""

from __future__ import annotations

from utils.granskning import granska_tutorsvar

UNDERLAG = ("1 § AvtL", "4 § AvtL")


# --- Godkända svar ----------------------------------------------------------


def test_svar_med_enbart_underlagets_lagrum_godkanns():
    text = (
        "**Norm** Studenten nämner korrekt 1 § AvtL och 4 § AvtL. "
        "En för sen accept utgör ett nytt anbud."
    )
    g = granska_tutorsvar(text, UNDERLAG)
    assert g.godkand
    assert not g.ovarifierade
    assert not g.utanfor_underlag


def test_svar_utan_lagrum_godkanns():
    """Ett svar om struktur och metod behöver inte citera något alls."""
    g = granska_tutorsvar("Din slutsats saknar motivering. Utveckla den.", UNDERLAG)
    assert g.godkand


def test_pahittat_lagrum_som_avvisas_godkanns():
    """Det verkliga bästa svaret ur sessionens fälla.

    Utan den här regeln blockerar garden exakt den undervisning den finns
    till för att möjliggöra.
    """
    text = (
        "**Norm** Studenten nämner 87 § AvtL och 12 kap. 4 § AvtL, men dessa "
        "lagrum finns inte i lagrumslistan. Detta är ett allvarligt fel. "
        "Rätt tillämpliga lagrum är 1 § AvtL och 4 § AvtL."
    )
    g = granska_tutorsvar(text, UNDERLAG)
    assert g.godkand, g.skal
    # De ska ändå rapporteras, så att UI:t kan visa varningsrutan.
    assert "87 § AvtL" in g.ovarifierade


def test_lagrum_utanfor_underlaget_som_avvisas_godkanns():
    text = (
        "Studenten hänvisar till 36 § AvtL, vilket inte är tillämpligt här. "
        "36 § reglerar jämkning av oskäliga avtalsvillkor. Rätt lagrum är "
        "1 § AvtL och 4 § AvtL."
    )
    g = granska_tutorsvar(text, UNDERLAG)
    assert g.godkand, g.skal


# --- Underkända svar --------------------------------------------------------


def test_pahittat_lagrum_som_framhalls_underkanns():
    """Det verkliga sämsta svaret: tutorn intygade ett påhitt som rätt norm."""
    text = (
        "**Norm** Rätt norm är 87 § AvtL, som reglerar acceptans och bindande "
        "avtal. Enligt 87 § AvtL har acceptanten 14 dagars respitfrist."
    )
    g = granska_tutorsvar(text, UNDERLAG)
    assert not g.godkand
    assert "87 § AvtL" in g.ovarifierade


def test_lagrum_utanfor_underlaget_som_framhalls_underkanns():
    """Det verkliga felet: en korrekt löst uppgift pekades mot 36 § AvtL."""
    text = (
        "Studenten saknar viktigt lagrum, 36 § AvtL, som reglerar avtalens "
        "bildande. Lägg till 36 § AvtL i Norm."
    )
    g = granska_tutorsvar(text, UNDERLAG)
    assert not g.godkand
    assert "36 § AvtL" in g.utanfor_underlag


def test_skalet_beskriver_varfor_svaret_stoppades():
    """Skälet loggas och ska gå att förstå utan att läsa koden."""
    text = "Rätt norm är 87 § AvtL."
    g = granska_tutorsvar(text, UNDERLAG)
    assert not g.godkand
    assert g.skal
    assert "87 § AvtL" in g.skal


# --- Konservativ vid tveksamhet ---------------------------------------------


def test_tomt_underlag_stanger_inte_av_allt():
    """Utan underlag finns inget att jämföra mot: bara påhitt ska stoppas."""
    god = granska_tutorsvar("Se 4 § AvtL för sen accept.", ())
    assert god.godkand

    ond = granska_tutorsvar("Se 87 § AvtL för respitfrist.", ())
    assert not ond.godkand


def test_tomt_svar_godkanns_inte_men_kraschar_inte():
    for tomt in ("", "   ", None):
        g = granska_tutorsvar(tomt, UNDERLAG)  # type: ignore[arg-type]
        assert not g.godkand


def test_underlaget_matchas_oberoende_av_ordning_och_skiftlage():
    """"AvtL 4 §" är samma lagrum som "4 § AvtL" och ska räknas som underlag."""
    g = granska_tutorsvar("Studenten hänvisar rätt till AvtL 4 §.", UNDERLAG)
    assert g.godkand, g.skal
