"""Kanoniskt svårighetsbegrepp för genererade rättsfall.

Enda ägaren av de tre svårighetsnivåerna (grund, medel, avancerad). Ren
Python: ingen Streamlit, ingen LLM. Ansvarar för:
- SVARIGHETSNIVAER: nyckel -> visningsetikett, i stigande svårighetsordning
- normalisera: mappa godtyckliga eller äldre värden (t.ex. det felstavade
  kuraterade "svar", eller "svår") till en kanonisk nyckel, med grund som
  fallback så att inget oväntat värde kan smita förbi
- etikett_for: visningsetikett för sidopanelens väljare
- instruktion_for: det svenska promptblock som talar om för modellen hur svårt
  fallet ska vara (antal fakta, sammanflätade frågor och lagrum)

Både generatorn (utils.generator) och prompten (utils.prompts) läser härifrån,
så att svårighetssträngar aldrig hårdkodas på flera ställen.
"""

from __future__ import annotations

# Nyckel -> visningsetikett, i stigande svårighetsordning. Ordningen styr både
# väljaren i UI och listningen i tester.
SVARIGHETSNIVAER: tuple[tuple[str, str], ...] = (
    ("grund", "Grund"),
    ("medel", "Medel"),
    ("avancerad", "Avancerad"),
)

STANDARDNIVA = "grund"

NYCKLAR: tuple[str, ...] = tuple(nyckel for nyckel, _ in SVARIGHETSNIVAER)

_ETIKETT: dict[str, str] = dict(SVARIGHETSNIVAER)

# Äldre eller felstavade värden som förekommer i kuraterad data eller kan komma
# från en LLM. Mappas till en kanonisk nyckel i normalisera().
_ALIAS: dict[str, str] = {
    "svar": "avancerad",   # felstavning/trunkering av "svår" i kuraterad data
    "svår": "avancerad",
    "svaar": "avancerad",
    "latt": "grund",
    "lätt": "grund",
}

# Instruktionsblocken som injiceras i genereringsprompten. Var och en beskriver
# hur svårt fallet ska vara i termer modellen kan kalibrera mot: antal fakta,
# antal sammanflätade rättsfrågor och antal lagrum.
_INSTRUKTION: dict[str, str] = {
    "grund": (
        "SVÅRIGHETSGRAD: GRUND\n"
        "- Fallet ska ha EN tydlig rättsfråga.\n"
        "- Håll omständigheterna korta och entydiga (4–5 meningar).\n"
        "- Facit ska vila på 1–2 lagrum ur vitlistan.\n"
        "- Undvik komplikationer, undantag och konkurrerande normer."
    ),
    "medel": (
        "SVÅRIGHETSGRAD: MEDEL\n"
        "- Fallet ska ha en tydlig huvudfråga MEN med en komplikation eller en "
        "konkurrerande norm som studenten måste väga in.\n"
        "- Omständigheterna får vara något rikare (5–7 meningar).\n"
        "- Facit ska vila på 2–3 lagrum ur vitlistan."
    ),
    "avancerad": (
        "SVÅRIGHETSGRAD: AVANCERAD\n"
        "- Fallet ska ha FLERA sammanflätade rättsfrågor som hänger ihop.\n"
        "- Bygg in tvetydighet eller ett gränsfall som kräver avvägning.\n"
        "- Omständigheterna ska vara fylligare (6–8 meningar) med fler parter "
        "eller händelser.\n"
        "- Facit ska vila på 3 eller fler lagrum ur vitlistan."
    ),
}


def normalisera(varde: str | None) -> str:
    """Mappa ett godtyckligt värde till en kanonisk svårighetsnyckel.

    Skiftlägesokänsligt och trimmande. Äldre stavningar (``svar``/``svår``)
    mappas via aliaslistan. Okänt, tomt eller ``None`` blir STANDARDNIVA, så
    att inget oväntat värde kan nå generatorn eller prompten.
    """
    if not varde:
        return STANDARDNIVA
    nyckel = varde.strip().lower()
    if nyckel in _ETIKETT:
        return nyckel
    if nyckel in _ALIAS:
        return _ALIAS[nyckel]
    return STANDARDNIVA


def etikett_for(nyckel: str | None) -> str:
    """Visningsetikett för en nivå. Okänt värde faller till STANDARDNIVA."""
    return _ETIKETT[normalisera(nyckel)]


def instruktion_for(nyckel: str | None) -> str:
    """Promptblocket för en nivå. Okänt värde faller till STANDARDNIVA."""
    return _INSTRUKTION[normalisera(nyckel)]
