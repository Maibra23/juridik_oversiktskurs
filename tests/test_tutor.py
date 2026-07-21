"""Tester för utils.tutor och utils.ui.render_tutortext.

Täcker on demand-mönstrets rena delar: hashning av inputs, upptäckt av
inaktuell cache samt att tutortext-renderingen byter ut verifierade
lagrum mot chips och flaggar overifierade referenser i en varningsruta.
Streamlit-beroende delar (knappen) testas inte här utan i röktestet.
"""

from __future__ import annotations

from utils.tutor import Tutorsvar, _hash_inputs
from utils.ui import _tutortext_html


def test_hash_inputs_stabil_och_kansliga_for_andring():
    a = _hash_inputs("system", "fråga 1")
    b = _hash_inputs("system", "fråga 1")
    c = _hash_inputs("system", "fråga 2")
    assert a == b
    assert a != c


def test_tutorsvar_ar_immutabelt():
    svar = Tutorsvar(text="hej", input_hash="abc")
    try:
        svar.text = "ändrat"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Tutorsvar borde vara frozen")


def test_render_verifierat_lagrum_blir_chip():
    text = "Enligt 36 § AvtL kan villkoret jämkas."
    html_ut, ovarifierade = _tutortext_html(text)
    assert "jok-chip" in html_ut
    assert "lagen.nu" in html_ut
    assert "36 § AvtL" in html_ut
    assert ovarifierade == ()


def test_render_kapitelindelat_lagrum_blir_chip():
    text = "Culpabedömningen görs enligt 2 kap. 1 § SkL."
    html_ut, ovarifierade = _tutortext_html(text)
    assert "jok-chip" in html_ut
    assert "2 kap. 1 § SkL" in html_ut
    assert ovarifierade == ()


def test_render_okand_paragraf_hamnar_i_ovarifierade():
    # 999 § AvtL finns inte i något kursavsnitt.
    text = "Se 999 § AvtL för detta."
    html_ut, ovarifierade = _tutortext_html(text)
    assert len(ovarifierade) == 1
    assert ovarifierade[0].ra == "999 § AvtL"
    # Ett overifierat lagrum ska inte bli en klickbar chip.
    assert "jok-chip" not in html_ut


def test_render_pahittad_lag_hamnar_i_ovarifierade():
    text = "Detta regleras i 5 § Phony."
    _, ovarifierade = _tutortext_html(text)
    assert any(t.ra == "5 § Phony" for t in ovarifierade)


def test_render_rattsfall_flaggas():
    text = "Jämför NJA 2015 s. 1040 i denna fråga."
    _, ovarifierade = _tutortext_html(text)
    assert any("NJA" in t.ra for t in ovarifierade)


def test_render_tom_text():
    html_ut, ovarifierade = _tutortext_html("")
    assert ovarifierade == ()
    assert "jok-tutortext" in html_ut


# --- Vad "verifierad" faktiskt betyder --------------------------------------


def test_verifieringsnot_visas_nar_svaret_har_verifierade_lagrum():
    """Ett grönt chip betyder att lagrummet finns, inte att det är rätt.

    Verifieringen slår upp paragrafen i kursens lagrumslista. Den säger
    ingenting om huruvida paragrafen är den tillämpliga för studentens fall.
    Observerat i skarpt läge: tutorn hänvisade en korrekt löst uppgift vidare
    till 36 § AvtL med påståendet att den "reglerar avtalens bildande", vilket
    är fel. Chipet var ändå grönt och klickbart. Noten sätter den gränsen i
    ord för studenten.
    """
    from utils.ui import _har_verifierade_lagrum, _tutortext_html

    html_ut, _ = _tutortext_html("Rätt norm är 36 § AvtL i det här fallet.")
    assert _har_verifierade_lagrum(html_ut) is True


def test_verifieringsnot_uteblir_utan_lagrum():
    """Ingen not när svaret inte hänvisar till något lagrum alls."""
    from utils.ui import _har_verifierade_lagrum, _tutortext_html

    html_ut, _ = _tutortext_html("Din struktur är tydlig, men utveckla slutsatsen.")
    assert _har_verifierade_lagrum(html_ut) is False


def test_verifieringsnot_uteblir_nar_alla_lagrum_ar_ovarifierade():
    """Overifierade lagrum har redan sin egen, starkare varningsruta."""
    from utils.ui import _har_verifierade_lagrum, _tutortext_html

    html_ut, ovarifierade = _tutortext_html("Se 87 § AvtL om acceptfrist.")
    assert ovarifierade, "87 § AvtL ska vara overifierad"
    assert _har_verifierade_lagrum(html_ut) is False


def test_verifieringsnoten_lovar_inte_att_lagrummet_ar_ratt():
    """Noten måste säga att den bara intygar existens, inte relevans."""
    from utils.ui import VERIFIERINGSNOT

    assert "finns" in VERIFIERINGSNOT.lower()
    assert "inte" in VERIFIERINGSNOT.lower()
    # Får aldrig formuleras som ett kvalitetsintyg.
    for forbjudet in ("korrekt lagrum", "rätt lagrum", "garanterar"):
        assert forbjudet not in VERIFIERINGSNOT.lower()
