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
- forvantan_for: promptblocket som talar om för tutorn hur hårt studentens
  eget svar ska bedömas på nivån. Utan det ändrar väljaren bara uppgiften,
  aldrig kraven, och en avancerad uppgift rättas som en grundläggande

Generatorn (utils.generator), genereringsprompten och tutorprompten
(utils.prompts) läser alla härifrån, så att svårighetssträngar aldrig
hårdkodas på flera ställen.
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
        "- Håll omständigheterna korta och entydiga (4 till 5 meningar).\n"
        "- Facit ska vila på 1 till 2 lagrum ur vitlistan.\n"
        "- Undvik komplikationer, undantag och konkurrerande normer."
    ),
    "medel": (
        "SVÅRIGHETSGRAD: MEDEL\n"
        "- Fallet ska ha en tydlig huvudfråga MEN med en komplikation eller en "
        "konkurrerande norm som studenten måste väga in.\n"
        "- Omständigheterna får vara något rikare (5 till 7 meningar).\n"
        "- Facit ska vila på 2 till 3 lagrum ur vitlistan."
    ),
    "avancerad": (
        "SVÅRIGHETSGRAD: AVANCERAD\n"
        "- Fallet ska ha FLERA sammanflätade rättsfrågor som hänger ihop.\n"
        "- Bygg in tvetydighet eller ett gränsfall som kräver avvägning.\n"
        "- Omständigheterna ska vara fylligare (6 till 8 meningar) med fler parter "
        "eller händelser.\n"
        "- Facit ska vila på 3 eller fler lagrum ur vitlistan."
    ),
}


# Vad studentens EGET svar måste hålla för att duga på nivån. Detta är
# generatorns spegelbild: instruktionsblocken ovan säger hur svårt fallet ska
# bli, blocken här säger hur hårt svaret ska bedömas.
#
# Skälet till att de behövs: en mätning visade att svårighetsgraden aldrig
# nådde bedömningen. Systemprompt och användarprompt var bytesidentiska för
# ett grundfall och ett avancerat fall av samma slag. Studenten som valde
# Avancerad fick alltså ett svårare fall och exakt samma krav på sitt svar,
# vilket gör väljaren till en kuliss.
_FORVANTAN: dict[str, str] = {
    "grund": (
        "BEDÖMNINGSNIVÅ: GRUND\n"
        "- Studenten ska identifiera rättsfrågan, ange rätt lagrum och dra en "
        "slutsats som följer av tillämpningen.\n"
        "- Kräv inte att gränsfall eller konkurrerande normer diskuteras: de "
        "finns inte i det här fallet.\n"
        "- Är alla fyra RNTS-stegen korrekta men kortfattade är svaret "
        "fullgott. Säg det."
    ),
    "medel": (
        "BEDÖMNINGSNIVÅ: MEDEL\n"
        "- Utöver grundkraven ska studenten ha uppmärksammat fallets "
        "komplikation eller den konkurrerande normen, och vägt in den.\n"
        "- Ett svar som bara löser huvudfrågan och går förbi komplikationen är "
        "ofullständigt även om varje angivet lagrum är rätt. Peka ut det.\n"
        "- Tillämpningssteget ska knyta omständigheterna till rekvisiten, inte "
        "bara namnge paragrafen."
    ),
    "avancerad": (
        "BEDÖMNINGSNIVÅ: AVANCERAD\n"
        "- Fallet innehåller flera sammanflätade rättsfrågor. Studenten ska ha "
        "behandlat dem alla. Saknas en, säg vilken.\n"
        "- Kräv att tvetydigheten eller gränsfallet uttryckligen diskuteras, "
        "med argument åt båda hållen, innan slutsatsen dras.\n"
        "- Kräv att förhållandet mellan de åberopade lagrummen framgår: vilket "
        "som är huvudregel, vilket som är undantag.\n"
        "- En obestämd slutsats som inte tar ställning duger inte på den här "
        "nivån."
    ),
}


# Hur många lagavsnitt genereringsprompten lägger fram att bygga fallet av.
# Skalar med nivån av samma skäl som lagrumskravet gör det: ett avancerat fall
# ska vila på flera normer, och kan inte göra det om bara ett tema ligger på
# bordet. Se utils.lagtext.lagtext_utbud för hur urvalet lottas.
_ANTAL_AVSNITT: dict[str, int] = {
    "grund": 1,
    "medel": 2,
    "avancerad": 3,
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
    """Genereringsblocket för en nivå. Okänt värde faller till STANDARDNIVA."""
    return _INSTRUKTION[normalisera(nyckel)]


def antal_avsnitt_for(nyckel: str | None) -> int:
    """Antal lagavsnitt att lägga fram för nivån. Okänt värde ger STANDARDNIVA."""
    return _ANTAL_AVSNITT[normalisera(nyckel)]


def forvantan_for(nyckel: str | None) -> str:
    """Bedömningsblocket för en nivå. Okänt värde faller till STANDARDNIVA.

    Används av utils.prompts.build_case_prompt så att tutorn håller studenten
    till den nivå fallet faktiskt ligger på.
    """
    return _FORVANTAN[normalisera(nyckel)]
