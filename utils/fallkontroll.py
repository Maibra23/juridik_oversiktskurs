"""Granska ett GENERERAT rättsfall innan studenten får se det.

Tre garder finns i appen, och de svarar på olika frågor:

- ``utils.lagrum.validera_lagrum``  Finns paragrafen?
- ``utils.granskning``              Används paragrafen i rätt ROLL i ett
                                    tutorsvar?
- den här modulen                   Bär ett genererat fall den juridik det
                                    utger sig för att bära?

DEN AVGÖRANDE MÄTNINGEN
=======================

En mätning över 72 genererade fall (12 moduler, tre svårighetsgrader, två
körningar) visade att existenskontrollen inte räcker. Alla 72 fall passerade
den. Ändå byggde 30 av dem sitt facit på minst en paragraf som handlar om
något annat än den fråga fallet ställer:

    "Har Anna begått bedrägeri?"  ->  24 kap. 1 § BrB

24 kap. 1 § BrB finns, ligger i vitlistan och verifieras utan anmärkning.
Den handlar om nödvärn. Fyra av sex straffrättsfall byggde på den.
Motsvarande mönster fanns i sex moduler till: 11 § LAS (uppsägningstidens
längd) som formkrav, 6 kap. 1 § JB (pantbrev) i en hyrestvist, 2 kap. 2 §
SkL (ren förmögenhetsskada genom brott) vid personskada.

Ett sådant fall är värre än inget fall. Det ser korrekt ut, citerar en äkta
paragraf, passerar varje kontroll appen hade, och lär studenten fel.

HUR ROLLEN KONTROLLERAS UTAN ETT ANDRA LLM-ANROP
================================================

Modellen ombeds citera ordagrant ur varje paragraf den åberopar
(``facit.lagrumsstod`` i genereringsprompten). Citatet jämförs sedan mot
appens egen författningstext i data/lagtext. Kontrollen är deterministisk:
citatet mäts tecken för tecken mot den verkliga lagtexten, med en kalibrerad
tolerans för blankstegsartefakter i korpusen och moderniserade arkaismer (se
MIN_TACKNING nedan). Ingen andra LLM behövs.

Det är inte ett fullt rollprov, och utger sig inte för att vara det: en modell
kan citera rätt mening och ändå dra fel slutsats. Poängen är att den inte kan
citera nödvärnsparagrafen bredvid ett bedrägerifall utan att det syns. Att
tvinga fram ordalydelsen är också det som får modellen att faktiskt läsa den.

KONSERVATIV ÅT ANDRA HÅLLET ÄN utils.granskning
===============================================

utils.granskning släpper igenom vid tvekan: ett stoppat tutorsvar kostar
undervisning. Här gäller motsatsen. Ett underkänt fall kostar ingenting alls,
eftersom generatorn gör om försöket och i sista hand visar ett kuraterat fall
som redan är granskat av en människa. Vid tvekan underkänner vi därför.

Ren modul: inga LLM-anrop, ingen Streamlit, allt testbart.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from difflib import SequenceMatcher

from utils.lagrum import (
    STATUS_VERIFIERAD,
    Lagrumsref,
    _som_ref,
    giltiga_forkortningar,
    validera_lagrum,
)
from utils.scenarier import Case

# Minsta längd på ett citat som ska räknas som stöd. Kortare än så bevisar
# ingenting: "att" och "eller" finns i varje författning.
MIN_CITATLANGD = 30

# Hur nära källan ett citat måste ligga. Exakt delsträngsmatchning visade sig
# vara för hårt: den föll på artefakter i vår egen korpus (13 kap. 3 § RB
# saknar ett blanksteg i "dockpå") och på att modellen moderniserar enstaka
# arkaiska ord ("hava" -> "ha"). I båda fallen hade modellen valt RÄTT
# paragraf, vilket är det garden finns till för att pröva.
#
# Trösklarna är kalibrerade mot mätta värden, inte gissade:
#
#   äkta citat, blankstegsartefakt      täckning 0.97   längsta 96
#   äkta citat, "hava" -> "ha"          täckning 1.00   längsta 68
#   äkta citat, ordagrant               täckning 1.00   längsta 73
#   påhitt, nödvärn som bedrägeri       täckning 0.45   längsta  8
#   påhitt, rimlig men fel paragraf     täckning 0.66   längsta  6
#   påhitt, juridiskt klingande nonsens täckning 0.62   längsta 11
#   omskrivning med egna ord            täckning 0.62   längsta 20
#
# Båda villkoren måste hållas. Täckningen ensam går att nå med spridda
# funktionsord ("och", "eller", "som"); kravet på en lång SAMMANHÄNGANDE
# passage är det som gör att bara den som faktiskt skrivit av kommer igenom.
MIN_TACKNING = 0.85
MIN_SAMMANHANGANDE = 25

# Ord som modellen har hittat på eller lånat in i mätningen, plus de som
# genereringsprompten uttryckligen förbjuder. Listan är MÄTT, inte gissad:
# varje post har förekommit i ett genererat fall som visades som svensk
# juridisk text. 21 av 72 fall innehöll minst en av dem.
FORBJUDNA_ORD: tuple[str, ...] = (
    "penaltiklausul",
    "vicesklausul",
    "embezzling",
    "kündigung",
    "terminationsfrihet",
    "leasemål",
    "leasemåt",
    "skuldsaning",
    "ongiltig",
    "anlade ett avtal",
    "proxim",
    "negligens",
)

# Bokstäver svenskan inte har. Blocklistan ovan är per definition efterklok:
# den fångar bara ord någon redan sett. Den här kontrollen fångar i stället en
# HEL KLASS av inlånade ord, oavsett vilket ordet råkar vara, genom att titta
# på tecknen. "kündigungsperiod" faller på ü, danska ord på ø och æ, tyska på
# ß, och kyrilliska homoglyfer på att de inte är latinska alls.
#
# Medvetet begränsad: é och è förekommer i svenska lånord (idé, kafé) och är
# tillåtna. Fel som "Firmaen" och "Omstalskada" består bara av svenska
# bokstäver och går inte att fånga så här. Att stava-kontrollera fri svensk
# text kräver en ordlista, och en ordlista fäller sammansättningar
# ("godtrosförvärvssituation") som är fullt korrekta. Den avvägningen är
# medveten: hellre en kontroll som aldrig har fel än en som ropar varg.
_SVENSKA_TECKEN = re.compile(r"[a-zåäöéèA-ZÅÄÖÉÈ]")
_ICKE_SVENSK_BOKSTAV = re.compile(r"[^\W\d_]", re.UNICODE)

# Lagrum skrivet baklänges: "BrB 24 kap. 1 §" i stället för "24 kap. 1 § BrB".
# Genereringsprompten kallar formen FEL, och 23 av 72 fall använde den ändå i
# löptexten. Facitlistan normaliseras av lagrumsparsern, men scenariotexten
# är det studenten läser, och där lärs vanan ut.
_OMVAND_ORDNING = re.compile(
    r"\b(?P<fk>{fk})\s+\d+\s*(kap\.|§)".format(
        fk="|".join(re.escape(f) for f in sorted(giltiga_forkortningar(), key=len, reverse=True))
    )
)


@dataclass(frozen=True)
class Fallgranskning:
    """Utfallet av en granskning av ett genererat fall.

    ``aterkoppling`` skrivs för modellen, inte för studenten: den går rakt in
    i nästa försöks prompt. Den ska därför vara konkret nog att gå att rätta.
    """

    godkand: bool
    skal: tuple[str, ...] = ()

    @property
    def aterkoppling(self) -> str:
        """Skälen som en mening, redo att injiceras i omförsöket."""
        return " ".join(self.skal)


def _normalisera_text(text: str) -> str:
    """Jämförbar form för delsträngsjämförelse mot lagtext.

    Slår ihop blanksteg, tar bort skiljetecken som ofta skiljer ett citat från
    källan, och gör jämförelsen skiftlägesokänslig. Unicode-normaliseras så
    att ett dekomponerat "å" matchar ett komponerat.
    """
    t = unicodedata.normalize("NFC", text or "").casefold()
    # \s täcker även U+00A0 för str-mönster. Skriv aldrig ut det tecknet
    # bokstavligen här: det är osynligt i en diff och är precis den sorts
    # tecken tests/test_sprak.py finns till för att stoppa på andra håll.
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"[\"'«»„“”‚‘’]", "", t)
    return t.strip()


def _citatgrad(normaliserat_citat: str, lagtext: str) -> tuple[float, int]:
    """Hur väl ett citat täcks av lagtexten: (andel, längsta sammanhängande).

    ``andel`` är hur stor del av citatets tecken som återfinns i lagtexten,
    luckor tillåtna. ``längsta sammanhängande`` är den längsta obrutna
    passagen. Se trösklarna ovan för varför båda behövs.

    ``autojunk=False`` är inte valfritt: difflibs heuristik stämplar tecken
    som förekommer i mer än 1 % av en sekvens längre än 200 tecken som skräp,
    och i svensk lagtext betyder det vanliga bokstäver. Med den påslagen blir
    mätningen obrukbar för just de långa paragrafer den ska skydda.
    """
    normaliserad_lagtext = _normalisera_text(lagtext)
    if not normaliserat_citat or not normaliserad_lagtext:
        return 0.0, 0
    matchare = SequenceMatcher(
        None, normaliserat_citat, normaliserad_lagtext, autojunk=False
    )
    block = matchare.get_matching_blocks()
    traffade = sum(b.size for b in block)
    langsta = max((b.size for b in block), default=0)
    return traffade / len(normaliserat_citat), langsta


def _lagtext_for(ref: str) -> str:
    """Ordagrann lagtext för en paragraf, eller tom sträng om den saknas."""
    from utils.lagtext import hamta_paragraftext

    return hamta_paragraftext(ref) or ""


def _stodkarta(ra: object) -> dict[str, str]:
    """Plocka ut {lagrum: citat} ur facit.lagrumsstod i det råa JSON-svaret.

    Formen är modellens, inte vår, så vi är toleranta mot hur den kom ut:
    en lista av objekt är det begärda, men en dict {lagrum: citat} accepteras
    också. Allt annat ger en tom karta, och kontrollen underkänner.
    """
    if isinstance(ra, dict):
        return {str(k): str(v) for k, v in ra.items() if k and v}
    if not isinstance(ra, list):
        return {}
    karta: dict[str, str] = {}
    for post in ra:
        if not isinstance(post, dict):
            continue
        lagrum = str(post.get("lagrum", "")).strip()
        citat = str(post.get("citat", "")).strip()
        if lagrum and citat:
            karta[lagrum] = citat
    return karta


def _kanonisk(ref: Lagrumsref) -> str:
    """Jämförbar nyckel oavsett hur referensen skrevs."""
    kapitel = f"{ref.kapitel}:" if ref.kapitel else ""
    return f"{ref.forkortning.lower()}|{kapitel}{ref.paragraf}"


def _nyckel(ref: str) -> str | None:
    parsad = _som_ref(ref)
    return _kanonisk(parsad) if parsad is not None else None


def _forkortning(ref: str) -> str:
    delar = (ref or "").split()
    return delar[-1] if delar else ""


def _prosa(case: Case) -> str:
    """All text studenten faktiskt läser, som ett block."""
    return "\n".join(
        (
            case.rubrik,
            case.scenariotext,
            case.facit.rattsfraga,
            *case.facit.tillampningspunkter,
            case.facit.slutsats,
        )
    )


# --- Delkontroller ----------------------------------------------------------

def _kontrollera_vitlista(case: Case, tillatna: Iterable[str]) -> list[str]:
    """Varje lagrum i facit måste ligga i modulens egen vitlista.

    Existenskontrollen prövar mot HELA registret, inte mot modulens lagar. Ett
    arbetsrättsfall som citerar 36 § AvtL skulle alltså passera den. Här
    stängs det.
    """
    tillatna_set = {t for t in tillatna}
    if not tillatna_set:
        return []
    fel = [
        ref for ref in case.facit.lagrum if _forkortning(ref) not in tillatna_set
    ]
    if not fel:
        return []
    return [
        f"{', '.join(fel)} ligger utanför modulens lagrumsvitlista "
        f"({', '.join(sorted(tillatna_set))}). Fallet måste kunna lösas med "
        "modulens egna lagar."
    ]


def _kontrollera_grundning(case: Case) -> list[str]:
    """Alla lagrum måste verifieras mot registret, och minst ett måste finnas."""
    if not case.facit.lagrum:
        return ["Facit saknar lagrum. Ett fall utan norm går inte att lösa."]
    fel = [ref for ref in case.facit.lagrum if validera_lagrum(ref) != STATUS_VERIFIERAD]
    if fel:
        return [
            f"{', '.join(fel)} kunde inte verifieras mot lagrumsregistret. "
            "Paragrafen finns inte, eller ligger utanför lagens angivna avsnitt."
        ]
    return []


def _kontrollera_lagrumsstod(case: Case, stod: dict[str, str]) -> list[str]:
    """Varje åberopad paragraf måste stödjas av ett äkta citat ur lagtexten."""
    skal: list[str] = []
    per_nyckel = {
        n: citat for ref, citat in stod.items() if (n := _nyckel(ref)) is not None
    }

    for ref in case.facit.lagrum:
        lagtext = _lagtext_for(ref)
        if not lagtext:
            skal.append(
                f"{ref} saknar ordagrann lagtext i appens underlag och kan "
                "därför inte kontrolleras. Välj en annan paragraf."
            )
            continue

        nyckel = _nyckel(ref)
        citat = per_nyckel.get(nyckel) if nyckel else None
        if not citat:
            skal.append(
                f"{ref} saknar citat i facit.lagrumsstod. Varje åberopad "
                "paragraf måste stödjas av ett ordagrant citat ur dess lagtext."
            )
            continue

        normaliserat = _normalisera_text(citat)
        if len(normaliserat) < MIN_CITATLANGD:
            skal.append(
                f"Citatet för {ref} är för kort för att bevisa något "
                f"(minst {MIN_CITATLANGD} tecken krävs)."
            )
            continue

        tackning, sammanhangande = _citatgrad(normaliserat, lagtext)
        if tackning < MIN_TACKNING or sammanhangande < MIN_SAMMANHANGANDE:
            skal.append(
                f"Citatet för {ref} står inte så i paragrafens lagtext. "
                f"Antingen handlar {ref} om något annat än den rättsfråga du "
                "ställer, eller så har du formulerat om i stället för att "
                "skriva av. Välj den paragraf vars ordalydelse faktiskt avgör "
                "frågan och citera den ordagrant."
            )

    return skal


def _kontrollera_sprak(case: Case) -> list[str]:
    """Löptexten får inte innehålla påhittade termer eller omvända lagrum."""
    skal: list[str] = []
    prosa = _prosa(case)
    lag = prosa.casefold()

    traffar = sorted({ord_ for ord_ in FORBJUDNA_ORD if ord_.casefold() in lag})
    if traffar:
        skal.append(
            f"Texten innehåller ord som inte är svenska juridiska termer: "
            f"{', '.join(traffar)}. Skriv på vedertagen svensk facksvenska."
        )

    frammande = _frammande_bokstaver(prosa)
    if frammande:
        skal.append(
            f"Texten innehåller bokstäver som inte finns i svenskan: "
            f"{', '.join(frammande)}. Ordet är inlånat från ett annat språk. "
            "Använd den vedertagna svenska termen."
        )

    omvanda = sorted({m.group(0).strip() for m in _OMVAND_ORDNING.finditer(prosa)})
    if omvanda:
        skal.append(
            f"Lagrum skrivna baklänges i löptexten: {', '.join(omvanda)}. "
            "Paragrafnumret ska stå först, förkortningen sist."
        )

    return skal


def _frammande_bokstaver(text: str) -> list[str]:
    """De ord i texten som bär en bokstav svenskan inte har.

    Returnerar orden, inte tecknen: modellen kan rätta "kündigungsperiod",
    men har ingen nytta av beskedet "ü".
    """
    traffade: list[str] = []
    for ord_ in re.findall(r"\S+", text):
        bokstaver = _ICKE_SVENSK_BOKSTAV.findall(ord_)
        if any(not _SVENSKA_TECKEN.fullmatch(b) for b in bokstaver):
            rensat = ord_.strip(".,;:!?()\"'")
            if rensat and rensat not in traffade:
                traffade.append(rensat)
    return sorted(traffade)


# --- Publikt API ------------------------------------------------------------

def granska_genererat_case(
    case: Case,
    tillatna_forkortningar: Iterable[str] = (),
    lagrumsstod: object = None,
) -> Fallgranskning:
    """Avgör om ett genererat fall kan visas för studenten.

    ``tillatna_forkortningar`` är modulens vitlista. Tom vitlista hoppar över
    just den kontrollen (men inte de övriga), så att en anropare utan
    modulkontext fortfarande kan använda funktionen.

    ``lagrumsstod`` är råvärdet av ``facit.lagrumsstod`` ur modellens JSON.
    Det ligger utanför Case-dataklassen med flit: fältet är ett kvitto som
    kontrollen förbrukar, inte innehåll som ska sparas, exporteras eller
    visas. Curerade fall har inget lagrumsstöd och ska inte behöva ha det.
    """
    skal: list[str] = []
    skal += _kontrollera_grundning(case)
    skal += _kontrollera_vitlista(case, tillatna_forkortningar)
    # Citatkontrollen förutsätter att paragrafen finns. Hoppa över den om
    # grundningen redan fallit, annars staplas två besked om samma fel.
    if not skal:
        skal += _kontrollera_lagrumsstod(case, _stodkarta(lagrumsstod))
    skal += _kontrollera_sprak(case)

    return Fallgranskning(godkand=not skal, skal=tuple(dict.fromkeys(skal)))
