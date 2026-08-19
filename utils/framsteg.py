"""Studentens framsteg, sammanställt ur sessionens två böcker.

Ansvarar för en enda fråga: vilka övningsmoduler har studenten börjat på? Svaret
driver startsidans "nästa steg" (utils.navigation.nasta_ovningsmodul).

Den rena funktionen ``pabborjade_ur_bocker`` tar böckerna som argument och kan
därför enhetstestas utan Streamlit. ``pabborjade_moduler`` är det tunna skalet
som hämtar dem ur session_state.

Framstegen är sessionsbundna: stänger studenten fliken är de borta. Det sägs
rent ut i UI:t (sidor/0_Hem.py) i stället för att antydas i en rubrik.
"""

from __future__ import annotations


def pabborjade_ur_bocker(
    quizresultat: dict[str, tuple[int, int]],
    case_bok: dict[str, tuple[str, ...]],
) -> frozenset[str]:
    """Modulnamnen studenten har registrerat något arbete på.

    ``quizresultat`` är utils.quiz.alla_resultat(): modulnamn -> (rätt, besvarade).
    ``case_bok`` är utils.export.genomforda_case(): modulnamn -> case-id.
    Båda är nycklade på modulens visningsnamn, identiskt med
    utils.navigation.byggda_namn().

    En post med noll besvarade frågor eller noll genomförda fall räknas inte:
    böckerna kan innehålla tomma poster efter en avbruten interaktion, och de
    ska inte få startsidan att hoppa över en modul studenten inte gjort.
    """
    paborjade = {modul for modul, (_ratt, besvarade) in quizresultat.items() if besvarade}
    paborjade |= {modul for modul, ids in case_bok.items() if ids}
    return frozenset(paborjade)


def pabborjade_moduler() -> frozenset[str]:
    """Påbörjade moduler i den här sessionen. Tom mängd om något går fel."""
    from utils.export import genomforda_case
    from utils.quiz import alla_resultat

    try:
        return pabborjade_ur_bocker(alla_resultat(), genomforda_case())
    except Exception:  # noqa: BLE001 (startsidan ska aldrig krascha på framsteg)
        return frozenset()
