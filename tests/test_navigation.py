"""Tester för navigeringsträdet i sidopanelen.

Vaktar den enda invariant som gör trädet trovärdigt: varje modul i trädet
pekar antingen på en sida som faktiskt finns i sidor/, eller saknar sida
och visas som "(kommer)". Ett stavfel i en sökväg ska fångas här och inte
som en trasig länk i UI:t.

Kontrollerar dessutom att trädet och st.Page-registret i streamlit_app.py
hålls i synk, eftersom sidopanelen känner igen den öppna sidan på titeln.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from utils.navigation import (
    FALLBACK_CTA_SIDA,
    FALLBACK_CTA_TITEL,
    NAV_TRAD,
    Grupp,
    Modul,
    alla_moduler,
    byggda_namn,
    byggda_sidor,
    cta_mal,
    nasta_ovningsmodul,
    registrera_besok,
    rubrikkedja,
    sida_finns,
    sida_for_namn,
    övningsmoduler,
)

ROT = Path(__file__).resolve().parent.parent
MODULER = tuple(alla_moduler())


def test_tradet_har_moduler():
    assert len(MODULER) >= 10, "Navigeringsträdet ser oväntat tomt ut."


@pytest.mark.parametrize("modul", MODULER, ids=lambda m: m.namn)
def test_modul_pekar_pa_befintlig_sida_eller_ar_planerad(modul: Modul):
    """Varje modul pekar på en fil som finns, eller är märkt som planerad."""
    if modul.planerad:
        assert modul.sida is None
        return
    assert modul.sida is not None
    assert sida_finns(modul.sida), (
        f"{modul.namn!r} pekar på {modul.sida!r} som inte finns i projektet."
    )


def test_planerade_moduler_har_ingen_sida():
    """Planerad och byggd är varandras motsatser, aldrig något mittemellan."""
    for modul in MODULER:
        assert modul.planerad == (modul.sida is None), (
            f"{modul.namn!r} är inkonsekvent märkt."
        )


def test_inga_dubbletter_av_sidor():
    sidor = byggda_sidor()
    assert len(sidor) == len(set(sidor)), "Samma sida förekommer flera gånger."


def test_inga_dubbletter_av_modulnamn():
    namn = [m.namn for m in MODULER]
    assert len(namn) == len(set(namn)), f"Dubblerade modulnamn: {namn}"


def test_alla_grupper_har_barn():
    """En tom rubriknivå ska aldrig ritas ut i panelen."""

    def granska(noder):
        for nod in noder:
            if isinstance(nod, Grupp):
                assert nod.barn, f"Gruppen {nod.namn!r} saknar barn."
                granska(nod.barn)

    granska(NAV_TRAD)


def test_alla_modulsidor_finns_med_i_tradet():
    """Ingen sida i sidor/ får sakna plats i navigeringen.

    Utan den här kontrollen kan en ny modulsida bli oåtkomlig, eftersom
    Streamlits egen sidlista är avstängd (position="hidden").
    """
    pa_disk = {
        f"sidor/{p.name}" for p in (ROT / "sidor").glob("*.py") if p.name != "__init__.py"
    }
    i_tradet = set(byggda_sidor())
    assert pa_disk == i_tradet, (
        f"Sidor utanför trädet: {sorted(pa_disk - i_tradet)}. "
        f"Träd utan fil: {sorted(i_tradet - pa_disk)}."
    )


def test_tradets_namn_matchar_sidregistret():
    """Modulnamnen i trädet ska vara identiska med titlarna i st.Page.

    Sidopanelen fäller ut rätt sektion genom att jämföra den öppna sidans
    titel med modulnamnet, så de två listorna måste hållas i synk.
    """
    kalla = (ROT / "streamlit_app.py").read_text(encoding="utf-8")
    titlar = set(re.findall(r'st\.Page\("[^"]+",\s*title="([^"]+)"', kalla))
    assert set(byggda_namn()) == titlar, (
        f"Bara i trädet: {sorted(set(byggda_namn()) - titlar)}. "
        f"Bara i registret: {sorted(titlar - set(byggda_namn()))}."
    )


# --- sida_for_namn -----------------------------------------------------------

def test_sida_for_namn_kand_modul():
    assert sida_for_namn("Avtalsrätt") == "sidor/2_Avtalsratt.py"


def test_sida_for_namn_okant_namn_ger_none():
    assert sida_for_namn("Påhittad modul") is None


def test_sida_for_namn_planerad_modul_ger_none():
    """Statsrätt saknar sida i trädet och kan därför aldrig slås upp."""
    assert sida_for_namn("Statsrätt") is None


# --- registrera_besok ---------------------------------------------------------

def test_registrera_besok_sparar_titel():
    session_state: dict = {}
    registrera_besok(session_state, "Avtalsrätt")
    assert session_state["_jok_senast_besokt"] == "Avtalsrätt"


def test_registrera_besok_ignorerar_hem():
    session_state: dict = {}
    registrera_besok(session_state, "Hem")
    assert "_jok_senast_besokt" not in session_state


def test_registrera_besok_hem_skriver_inte_over_tidigare_besok():
    session_state = {"_jok_senast_besokt": "Avtalsrätt"}
    registrera_besok(session_state, "Hem")
    assert session_state["_jok_senast_besokt"] == "Avtalsrätt"


# --- övningsmoduler / nasta_ovningsmodul --------------------------------------------

def test_övningsmoduler_foljer_tradets_ordning():
    namn = [m.namn for m in övningsmoduler()]
    assert namn[0] == "Juridisk metod"
    assert namn.index("Personrätt") < namn.index("Avtalsrätt")
    assert namn.index("Avtalsrätt") < namn.index("Skadeståndsrätt")


def test_övningsmoduler_utesluter_verktygssidor():
    namn = {m.namn for m in övningsmoduler()}
    for verktyg in ("Hem", "Rättskartan", "Kunskapstest", "Kunskapskarta",
                    "Kunskapsutmaning"):
        assert verktyg not in namn


def test_övningsmoduler_matchar_scenariodatan():
    """Vakt mot drift: varje ovningsmodul måste ha övningsinnehåll, och omvänt."""
    from utils.scenarier import ladda_modul, lista_moduler

    ur_data = {ladda_modul(stem).modul for stem in lista_moduler()}
    ur_tradet = {m.namn for m in övningsmoduler()}
    assert ur_tradet == ur_data


def test_nasta_ovningsmodul_utan_framsteg_ger_forsta():
    assert nasta_ovningsmodul(frozenset()).namn == "Juridisk metod"


def test_nasta_ovningsmodul_hoppar_over_paborjade():
    nasta = nasta_ovningsmodul(frozenset({"Juridisk metod", "Personrätt"}))
    assert nasta.namn == "Allmän förmögenhetsrätt"


def test_nasta_ovningsmodul_alla_paborjade_ger_none():
    alla = frozenset(m.namn for m in övningsmoduler())
    assert nasta_ovningsmodul(alla) is None


# --- cta_mal -------------------------------------------------------------------

def test_cta_mal_ny_session_ger_appens_forsta_modul():
    mal = cta_mal(None)
    assert mal.titel == "Juridisk metod"
    assert mal.sida == "sidor/1_Juridisk_metod.py"
    assert mal.ateruppta is False
    assert mal.skal


def test_cta_mal_foredrar_nasta_i_kursordning_framfor_senast_besokt():
    """Kärnan i ändringen: senast besökta modul får inte låsa studenten."""
    mal = cta_mal("Associationsrätt", pabborjade=frozenset({"Juridisk metod"}))
    assert mal.titel == "Personrätt"
    assert mal.ateruppta is False


def test_cta_mal_alla_övningsmoduler_paborjade_ger_ateruppta():
    from utils.navigation import övningsmoduler

    alla = frozenset(m.namn for m in övningsmoduler())
    mal = cta_mal("Avtalsrätt", pabborjade=alla)
    assert mal.titel == "Avtalsrätt"
    assert mal.ateruppta is True


def test_cta_mal_okand_senast_besokt_faller_tillbaka_pa_kursordning():
    alla = frozenset(m.namn for m in övningsmoduler())
    mal = cta_mal("Modul som inte längre finns", pabborjade=alla)
    assert mal.titel == FALLBACK_CTA_TITEL
    assert mal.sida == FALLBACK_CTA_SIDA
    assert mal.ateruppta is False


# --- rubrikkedja -----------------------------------------------------------

def test_rubrikkedja_for_djupt_nastlad_modul():
    assert rubrikkedja("Avtalsrätt") == (
        "CIVILRÄTT", "Förmögenhetsrätt", "Kontraktsrätt",
    )


def test_rubrikkedja_for_modul_direkt_under_kategori():
    assert rubrikkedja("Juridisk metod") == ("START OCH METOD",)


def test_rubrikkedja_for_okand_modul_ar_tom():
    assert rubrikkedja("Modul som inte finns") == ()
