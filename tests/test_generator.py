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
