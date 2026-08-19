"""Datalagret för Rättskartans kraftvy.

Kraftvyn visar samma taxonomi som den hierarkiska vyn i utils.taxonomi_ui, men
låter en fysiksimulering placera noderna fritt och ringar in varje toppgren med
ett hölje. Den här modulen räknar ut allt som inte är rendering:

- ``nodgrader()``    : hur många kanter varje nod har (driver nodstorleken),
- ``nodstorlek()``   : graden översatt till pixlar,
- ``hullgrupper()``  : vilka noder som ligger i vilket toppgrenshölje,
- ``grafstatistik()``: kartans nyckeltal för sidopanelen.

Modulen är fri från både Streamlit och färger. Paletten hör till
utils.taxonomi_ui, som äger designsystemets färgkontrakt, och plockas upp av
utils.kraftgraf_ui vid renderingen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from utils.rattssystem_graf import (
    GRUPP_GREN,
    GRUPP_LAG,
    GRUPP_REFERENS,
    ROT_ID,
    Taxonomigraf,
    taxonomi,
)

# --- Nodstorlekens skala ----------------------------------------------------
#
# I ett träd är graden = antal barn + en förälder, så skalan går från löven
# (grad 1) upp till de grenrikaste noderna. Ytterpunkterna ligger här som
# namngivna konstanter; ingen av dem upprepas i JavaScripten.

STORLEK_MIN = 12
STORLEK_MAX = 34

# --- Startpositionernas geometri --------------------------------------------
#
# Fysiken får en utgångspunkt i stället för att starta från en enda punkt: en
# sektor per toppgren, och ett steg utåt per nivå.

# Toppgrenarnas mittpunkter läggs på en cirkel runt roten. Varje gren växer
# sedan som en kompakt skiva kring sin egen mittpunkt i stället för som en kil
# ut från origo: en kil ger ett konvext hölje som skär tvärs över mitten och
# sväljer de mindre grenarna, medan skivor går att hålla isär.
GRUPP_AVSTAND = 1150
LOKAL_RADIE_PER_NIVA = 130
# Gyllene vinkeln (solrosmönstret). Den fyller en skiva jämnt utan att lägga
# noder i strålar, vilket ett jämnt vinkelsteg gör.
GYLLENE_VINKEL = 2.399963229728653


@dataclass(frozen=True)
class Hullgrupp:
    """En toppgren och de noder vars hölje ska ritas runt dem."""

    id: str
    etikett: str
    nod_id: tuple[str, ...]


@dataclass(frozen=True)
class Statistik:
    """Kartans nyckeltal, för sidopanelens översikt."""

    noder: int
    grenar: int
    registerlagar: int
    referenslagar: int
    djup: int


def nodgrader(graf: Taxonomigraf) -> dict[str, int]:
    """Antalet kanter per nod, oavsett riktning.

    Roten får graden lika med antalet toppgrenar, en gren får sina barn plus
    sin förälder, och ett löv får exakt en. Noder utan kanter förekommer inte i
    ett träd men initieras ändå till noll, så att uppslagningen aldrig kastar.
    """
    grader: dict[str, int] = {nod["id"]: 0 for nod in graf["noder"]}
    for kant in graf["kanter"]:
        for nid in (kant["fran"], kant["till"]):
            if nid in grader:
                grader[nid] += 1
    return grader


def nodstorlek(grad: int, maxgrad: int) -> int:
    """Översätt en nods grad till pixelstorlek, linjärt mellan skalans ändar.

    ``maxgrad`` är den högsta graden i grafen. Är den 1 (eller lägre) saknar
    skalan spännvidd och alla noder får minsta storleken i stället för en
    division med noll.
    """
    if maxgrad <= 1:
        return STORLEK_MIN
    andel = (min(grad, maxgrad) - 1) / (maxgrad - 1)
    return round(STORLEK_MIN + andel * (STORLEK_MAX - STORLEK_MIN))


def hullgrupper(graf: Taxonomigraf) -> tuple[Hullgrupp, ...]:
    """Noderna grupperade per toppgren, i samma ordning som datat.

    Roten hör inte till någon toppgren (dess ``toppgren`` är tom) och lämnas
    utanför alla höljen: den ligger i mitten och ska inte dra ut något hölje
    över hela kartan. Eftersom ``toppgren`` ärvs nedåt på varje nod blir
    grupperna disjunkta.
    """
    medlemmar: dict[str, list[str]] = {}
    for nod in graf["noder"]:
        gid = nod.get("toppgren", "")
        if not gid or nod["id"] == ROT_ID:
            continue
        medlemmar.setdefault(gid, []).append(nod["id"])

    etiketter = {gren.id: gren.namn for gren in taxonomi()}
    return tuple(
        Hullgrupp(
            id=gren.id, etikett=etiketter[gren.id], nod_id=tuple(medlemmar[gren.id])
        )
        for gren in taxonomi()
        if gren.id in medlemmar
    )


def startpositioner(graf: Taxonomigraf) -> dict[str, tuple[float, float]]:
    """Startkoordinater som ger varje toppgren en egen, kompakt skiva.

    Fysiken hittar själv en balans, men den bryr sig inte om vilken toppgren en
    nod tillhör: startar allt i samma punkt hamnar grenarna om vartannat och
    höljena växer in i varandra. Här får varje toppgren i stället en mittpunkt
    på en cirkel runt roten, och fylls inifrån och ut. Djupet styr avståndet
    till den egna mittpunkten, den gyllene vinkeln fördelar noderna jämnt runt
    den. Resultatet är skivor som går att ringa in var för sig.

    Roten ligger i origo. Allt är härlett ur datats ordning, så funktionen är
    deterministisk.
    """
    grupper = hullgrupper(graf)
    if not grupper:
        return {nod["id"]: (0.0, 0.0) for nod in graf["noder"]}

    steg = 2 * math.pi / len(grupper)
    nivaer = {nod["id"]: nod.get("niva", 0) for nod in graf["noder"]}
    positioner: dict[str, tuple[float, float]] = {ROT_ID: (0.0, 0.0)}

    for index, grupp in enumerate(grupper):
        mitt_x = GRUPP_AVSTAND * math.cos(index * steg)
        mitt_y = GRUPP_AVSTAND * math.sin(index * steg)
        for plats, nid in enumerate(grupp.nod_id):
            radie = max(nivaer.get(nid, 1) - 1, 0) * LOKAL_RADIE_PER_NIVA
            vinkel = plats * GYLLENE_VINKEL
            positioner[nid] = (
                round(mitt_x + radie * math.cos(vinkel), 2),
                round(mitt_y + radie * math.sin(vinkel), 2),
            )

    for nod in graf["noder"]:
        positioner.setdefault(nod["id"], (0.0, 0.0))
    return positioner


def grafstatistik(graf: Taxonomigraf) -> Statistik:
    """Kartans nyckeltal: hur många noder av varje slag och hur djupt trädet går."""
    grupper = [nod["grupp"] for nod in graf["noder"]]
    return Statistik(
        noder=len(graf["noder"]),
        grenar=sum(1 for grupp in grupper if grupp == GRUPP_GREN),
        registerlagar=sum(1 for grupp in grupper if grupp == GRUPP_LAG),
        referenslagar=sum(1 for grupp in grupper if grupp == GRUPP_REFERENS),
        djup=max((nod.get("niva", 0) for nod in graf["noder"]), default=0),
    )
