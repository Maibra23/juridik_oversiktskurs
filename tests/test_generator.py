"""Tester för utils.generator (LLM-genererade rättsfall).

Använder en injicerad fejkklient – inga live-LLM-anrop. Täcker:
- giltig JSON med grundade lagrum -> genererat case
- kod-fence runt JSON strippas
- ogrundat lagrum -> omförsök, sedan grundat -> genererat
- ogrundat i båda försöken -> fallback till kuraterat case
- trasig JSON -> fallback
- LLM ej tillgänglig -> fallback utan krasch
- slumpmodulval ger en giltig modul
"""

from __future__ import annotations

import json
import random

from utils.generator import GenereratResultat, generera_case, valj_slumpmodul
from utils.lagrum import STATUS_VERIFIERAD, validera_lagrum
from utils.llm import LLMUnavailableError
from utils.scenarier import ladda_modul, lista_moduler

MODUL = "avtalsratt"


def _case_json(lagrum: list[str]) -> str:
    return json.dumps(
        {
            "id": "gen-anbud",
            "rubrik": "Det brådskande anbudet",
            "svarighetsgrad": "medel",
            "uppskattad_tid_min": 12,
            "scenariotext": "Anna skickar ett skriftligt anbud till Bertil.",
            "facit": {
                "rattsfraga": "Är ett bindande avtal slutet?",
                "lagrum": lagrum,
                "tillampningspunkter": ["Anbud och accept", "Oskälighet"],
                "slutsats": "Ett bindande avtal har slutits.",
            },
        }
    )


GILTIGT = _case_json(["1 § AvtL", "36 § AvtL"])
OGRUNDAT = _case_json(["99 § AvtL"])  # AvtL finns men 99 § är utanför kursen
TRASIGT = "Det här är inte JSON alls {kaputt"


class FejkKlient:
    """Returnerar förutbestämda svar i tur och ordning."""

    def __init__(self, *svar: str) -> None:
        self._svar = list(svar)
        self.anrop = 0

    def chat(self, system_prompt: str, user_prompt: str, **kwargs: object) -> str:
        i = min(self.anrop, len(self._svar) - 1)
        self.anrop += 1
        return self._svar[i]


class TrasigKlient:
    def chat(self, *a: object, **k: object) -> str:
        raise LLMUnavailableError("LLM nere")


def test_giltig_json_ger_genererat_case():
    res = generera_case(MODUL, klient=FejkKlient(GILTIGT))
    assert isinstance(res, GenereratResultat)
    assert res.kalla == "genererad"
    assert res.case.rubrik == "Det brådskande anbudet"
    for ref in res.case.facit.lagrum:
        assert validera_lagrum(ref) == STATUS_VERIFIERAD


def test_kod_fence_strippas():
    inbaddat = f"```json\n{GILTIGT}\n```"
    res = generera_case(MODUL, klient=FejkKlient(inbaddat))
    assert res.kalla == "genererad"


def test_ogrundat_lagrum_utloser_omforsok_sedan_grundat():
    klient = FejkKlient(OGRUNDAT, GILTIGT)
    res = generera_case(MODUL, klient=klient)
    assert res.kalla == "genererad"
    assert klient.anrop == 2  # ett omförsök gjordes


def test_ogrundat_i_bada_forsoken_ger_fallback():
    res = generera_case(MODUL, klient=FejkKlient(OGRUNDAT, OGRUNDAT))
    assert res.kalla == "fallback"
    kanda_rubriker = {c.rubrik for c in ladda_modul(MODUL).case}
    assert res.case.rubrik in kanda_rubriker


def test_trasig_json_ger_fallback():
    res = generera_case(MODUL, klient=FejkKlient(TRASIGT, TRASIGT))
    assert res.kalla == "fallback"


def test_llm_ej_tillganglig_ger_fallback_utan_krasch():
    res = generera_case(MODUL, klient=TrasigKlient())
    assert res.kalla == "fallback"
    assert res.notis  # en svensk notis ska finnas


def test_fallback_case_ar_alltid_grundat():
    res = generera_case(MODUL, klient=TrasigKlient())
    for ref in res.case.facit.lagrum:
        assert validera_lagrum(ref) == STATUS_VERIFIERAD


def test_valj_slumpmodul_ger_giltig_modul():
    modul = valj_slumpmodul(rng=random.Random(0))
    assert modul in lista_moduler()


# --- Budgetdisciplin --------------------------------------------------------

def test_standardklienten_gar_genom_cached_chat(monkeypatch):
    """Generatorn får aldrig tala med LLMClient direkt.

    cached_chat äger cachen, sessionsräknaren och dagsbudgeten (PRD 5.5).
    En klient som går förbi den förbrukar HF-token utan att debiteras och
    utan att stoppas när taken är slut. Regression: generatorn byggde
    tidigare en rå LLMClient, så varje genererat rättsfall var gratis.
    """
    from utils import generator as gen

    anrop: list[tuple[str, str]] = []

    def fejkad_cached_chat(system_prompt: str, user_prompt: str, *a, **kw) -> str:
        anrop.append((system_prompt, user_prompt))
        return "{}"

    import utils.llm as llm_modul

    monkeypatch.setattr(llm_modul, "cached_chat", fejkad_cached_chat)
    monkeypatch.setattr(llm_modul, "is_llm_available", lambda: True)

    klient = gen._standardklient()
    assert klient is not None
    klient.chat("sp", "up")
    assert anrop == [("sp", "up")], "Anropet gick inte genom cached_chat."


def test_standardklienten_ar_none_utan_token(monkeypatch):
    """Utan token ska generatorn falla tillbaka i stället för att krascha."""
    from utils import generator as gen
    import utils.llm as llm_modul

    monkeypatch.setattr(llm_modul, "is_llm_available", lambda: False)
    assert gen._standardklient() is None


# --- Unika fall och korrekta budgetbesked -----------------------------------

def test_varje_generering_ger_unik_prompt():
    """Två genereringar av samma modul får inte skicka identisk prompt.

    Regression: generatorn går genom utils.llm.cached_chat, som cachar på
    promptinnehåll. Utan variationsfrö blev prompten identisk för en given
    modul, cachen svarade med samma rättsfall vid varje knapptryck och
    studenten fick aldrig något nytt fall.
    """
    from utils.generator import generera_case

    prompts: list[str] = []

    class Spion:
        def chat(self, system_prompt: str, user_prompt: str) -> str:
            prompts.append(user_prompt)
            return "inte json"

    generera_case("avtalsratt", klient=Spion())
    generera_case("avtalsratt", klient=Spion())
    assert len(set(prompts)) == len(prompts), (
        "Samma prompt skickades flera gånger; cachen ger då samma rättsfall."
    )


def test_sessionstak_ger_budgetbesked_inte_otillganglig():
    """Ett fullt budgettak är inte samma sak som att LLM:en saknas.

    Regression: LLMSessionCapError ärver LLMUnavailableError, så taket
    fångades av det generella grenen och studenten fick beskedet
    "LLM är inte tillgänglig just nu" utan att förstå att det var budgeten.
    """
    from utils.generator import generera_case, LLM_EJ_TILLGANGLIG_NOTIS
    from utils.llm import SESSION_CAP_MESSAGE, LLMSessionCapError

    class TaketSlut:
        def chat(self, system_prompt: str, user_prompt: str) -> str:
            raise LLMSessionCapError(SESSION_CAP_MESSAGE)

    resultat = generera_case("avtalsratt", klient=TaketSlut())
    assert resultat.kalla == "fallback"
    assert resultat.notis == SESSION_CAP_MESSAGE
    assert resultat.notis != LLM_EJ_TILLGANGLIG_NOTIS


def test_dagsbudget_ger_budgetbesked():
    from utils.generator import generera_case
    from utils.llm import LLMDailyCapError
    from utils.llm_budget import DAILY_CAP_MESSAGE

    class DagenSlut:
        def chat(self, system_prompt: str, user_prompt: str) -> str:
            raise LLMDailyCapError(DAILY_CAP_MESSAGE)

    resultat = generera_case("avtalsratt", klient=DagenSlut())
    assert resultat.notis == DAILY_CAP_MESSAGE
