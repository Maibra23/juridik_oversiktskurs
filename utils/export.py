"""Export av studieframsteg till Markdown och Excel.

Ansvarar för att sammanställa studentens resultat till nedladdningsbara
rapporter (PRD 5: framsteg och export):
- bygg_markdown_rapport: läsbar Markdownrapport med quizresultat per modul
  och genomförda rättsfall
- bygg_excel_rapport: Excelarbetsbok (openpyxl) med samma innehåll i två blad
- registrera_case_genomford / genomforda_case: session-state-spårning av
  rättsfall där studenten fyllt i hela RNTS-analysen

Rapportbyggarna är rena funktioner utan Streamlit-beroende så att de kan
enhetstestas; endast session-state-hjälparna kräver en Streamlit-kontext.
"""

from __future__ import annotations

from datetime import date
from io import BytesIO
from typing import Mapping

RAPPORT_TITEL = "Studierapport: Juridikverkstan"
DISCLAIMER = (
    "Rapporten är ett studieunderlag från ett övningsverktyg och utgör inte "
    "juridisk rådgivning."
)


# --- Rena rapportbyggare ------------------------------------------------------

def _modulrader(
    quizresultat: Mapping[str, Mapping[str, bool]],
) -> tuple[tuple[str, int, int], ...]:
    """Sammanställ (modul, rätt, besvarade) sorterat på modulnamn."""
    return tuple(
        (modul, sum(1 for v in svar.values() if v), len(svar))
        for modul, svar in sorted(quizresultat.items())
    )


def bygg_markdown_rapport(
    quizresultat: Mapping[str, Mapping[str, bool]],
    case_genomforda: Mapping[str, tuple[str, ...]],
) -> str:
    """Bygg en Markdownrapport över quizresultat och genomförda rättsfall."""
    rader = [
        f"# {RAPPORT_TITEL}",
        "",
        f"Datum: {date.today().isoformat()}",
        "",
        "## Quizresultat per modul",
        "",
    ]

    modulrader = _modulrader(quizresultat)
    if modulrader:
        rader.append("| Modul | Rätt | Besvarade |")
        rader.append("| --- | ---: | ---: |")
        for modul, ratt, besvarade in modulrader:
            rader.append(f"| {modul} | {ratt}/{besvarade} | {besvarade} |")
    else:
        rader.append("Inga quizfrågor besvarade ännu.")

    rader += ["", "## Genomförda rättsfall", ""]
    if case_genomforda:
        for modul, case_ids in sorted(case_genomforda.items()):
            for case_id in case_ids:
                rader.append(f"- {modul}: `{case_id}`")
    else:
        rader.append("Inga rättsfall genomförda ännu.")

    rader += ["", "---", "", DISCLAIMER, ""]
    return "\n".join(rader)


def bygg_excel_rapport(
    quizresultat: Mapping[str, Mapping[str, bool]],
    case_genomforda: Mapping[str, tuple[str, ...]],
) -> bytes:
    """Bygg en Excelarbetsbok (två blad) och returnera den som bytes."""
    import openpyxl

    wb = openpyxl.Workbook()

    ws_quiz = wb.active
    ws_quiz.title = "Quizresultat"
    ws_quiz.append(("Modul", "Rätt", "Besvarade", "Andel"))
    for modul, ratt, besvarade in _modulrader(quizresultat):
        andel = round(ratt / besvarade, 2) if besvarade else 0.0
        ws_quiz.append((modul, ratt, besvarade, andel))

    ws_case = wb.create_sheet("Genomförda case")
    ws_case.append(("Modul", "Rättsfall"))
    for modul, case_ids in sorted(case_genomforda.items()):
        for case_id in case_ids:
            ws_case.append((modul, case_id))

    buffert = BytesIO()
    wb.save(buffert)
    return buffert.getvalue()


# --- Session-state-spårning av genomförda case --------------------------------

_CASE_NYCKEL = "case_genomforda"


def registrera_case_genomford(modul: str, case_id: str) -> None:
    """Markera ett rättsfall som genomfört (hela RNTS-analysen ifylld)."""
    import streamlit as st

    try:
        bok = st.session_state.setdefault(_CASE_NYCKEL, {})
    except Exception:
        return
    modulbok = bok.setdefault(modul, {})
    modulbok[case_id] = True


def genomforda_case() -> dict[str, tuple[str, ...]]:
    """Alla genomförda rättsfall per modul, som immutabla tupler."""
    import streamlit as st

    try:
        bok = st.session_state.get(_CASE_NYCKEL, {})
    except Exception:
        return {}
    return {modul: tuple(sorted(ids)) for modul, ids in bok.items()}
