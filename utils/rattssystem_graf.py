"""Taxonomin över svensk rätt som träd och som nod/kant-graf.

Bygger den fullständiga indelningen av svensk rätt ur data/rattssystem.json
och lagrumsregistret: rot -> avdelning -> rättsområde -> delområde -> lag.
Till skillnad från den personliga kunskapsgrafen (utils.graf), som växer med
studentens egna rättsfall, är den här grafen full redan på dag noll.

Två publika ingångar:

- ``taxonomi()``   : det ordnade trädet (rena dataklasser, ingen rendering).
- ``bygg_taxonomigraf()`` : samma träd som ``{"noder": [...], "kanter": [...]}``
  i exakt samma envelope som utils.graf, så att utils.graf_ui:s
  vis-network-mönster kan återanvändas rakt av.

Avdelningsnivån (AVD I Introduktion, AVD II Offentlig rätt, AVD III Civilrätt,
AVD IV Straff- och processrätt) ägs av utils.rattskarta och läses ur
data/rattssystem.json, där varje område pekar på sin avdelning via nyckeln
``avdelning``. Modulen deklarerar alltså inte avdelningarna själv: samma lista
driver Obsidian-exportens rättskarta, och en hårdkodad kopia här skulle låta de
två vyerna glida isär. AVD I har inga rättsområden i datat och representeras av
en enda nod som pekar på modulen Juridisk metod.

Grundningsprincipen från utils.rattskarta gäller även här: lagnoder hämtar
namn, SFS och lagen.nu-URL ur lagrumsregistret och konstruerar dem aldrig
själva. Ren Python utan Streamlit-beroende, så att allt kan enhetstestas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, TypedDict

from utils.lagrum import lagrum_register
from utils.rattskarta import ladda_avdelningar, ladda_rattssystem

# --- Nodgrupper (styr form och storlek i renderingen) -----------------------

GRUPP_ROT = "rot"
GRUPP_AVDELNING = "avdelning"
GRUPP_OMRADE = "omrade"
GRUPP_UNDEROMRADE = "underomrade"
GRUPP_LAG = "lag"

ROT_ID = "rot"
ROT_LABEL = "Svensk rätt"


# Bokens avdelningar ägs av utils.rattskarta och läses ur data/rattssystem.json.
# Modulen håller medvetet ingen egen kopia, inte ens en modulkonstant: en
# konstant hade bundits vid import och blivit inaktuell om datat läses om.
# Anropa ladda_avdelningar() på användningsstället i stället.


# --- Trädet (delad källa för graf och framtida markdownbyggare) -------------


@dataclass(frozen=True)
class TaxLag:
    """Ett löv: en lag med kartans texter och registrets identitet."""

    forkortning: str
    namn: str
    sfs: str
    url: str
    beskrivning: str
    nar: str


@dataclass(frozen=True)
class TaxUnderomrade:
    id: str
    namn: str
    beskrivning: str
    nar: str
    lagar: tuple[TaxLag, ...]


@dataclass(frozen=True)
class TaxOmrade:
    id: str
    namn: str
    beskrivning: str
    nar: str
    farg: str
    underomraden: tuple[TaxUnderomrade, ...]


@dataclass(frozen=True)
class TaxAvdelning:
    id: str
    label: str
    beskrivning: str
    sida: str | None
    omraden: tuple[TaxOmrade, ...]


def taxonomi() -> tuple[TaxAvdelning, ...]:
    """Bygg hela taxonomin som ett ordnat, immutabelt träd.

    Avdelningarna kommer i dispositionens ordning och tas med även när de
    saknar rättsområden i datat (AVD I), så att bokens struktur syns i sin
    helhet. Lagarnas namn, SFS och lagen.nu-URL hämtas ur lagrumsregistret.
    """
    register = lagrum_register()
    avdelningar = ladda_avdelningar()
    per_avdelning: dict[str, list[TaxOmrade]] = {a.id: [] for a in avdelningar}

    for omrade in ladda_rattssystem():
        underomraden = tuple(
            TaxUnderomrade(
                id=under.id,
                namn=under.namn,
                beskrivning=under.beskrivning,
                nar=under.nar,
                lagar=tuple(
                    TaxLag(
                        forkortning=lag.forkortning,
                        namn=register[lag.forkortning].namn,
                        sfs=register[lag.forkortning].sfs,
                        url=register[lag.forkortning].lagen_nu_bas_url,
                        beskrivning=lag.beskrivning,
                        nar=lag.nar,
                    )
                    for lag in under.lagar
                ),
            )
            for under in omrade.underomraden
        )
        per_avdelning[omrade.avdelning].append(
            TaxOmrade(
                id=omrade.id,
                namn=omrade.namn,
                beskrivning=omrade.beskrivning,
                nar=omrade.nar,
                farg=omrade.farg,
                underomraden=underomraden,
            )
        )

    return tuple(
        TaxAvdelning(
            id=a.id,
            label=a.label,
            beskrivning=a.beskrivning,
            sida=a.sida,
            omraden=tuple(per_avdelning[a.id]),
        )
        for a in avdelningar
    )


def alla_lagar() -> Iterator[TaxLag]:
    """Gå igenom trädet och ge varje lag, i trädets ordning."""
    for avdelning in taxonomi():
        for omrade in avdelning.omraden:
            for under in omrade.underomraden:
                yield from under.lagar


# --- Grafen (samma envelope som utils.graf) ---------------------------------


class TaxNod(TypedDict, total=False):
    id: str
    label: str
    grupp: str
    niva: int
    avdelning: str
    titel: str
    url: str
    # Endast lagnoder. Id:t är skopat efter delområde och går inte att tolka
    # som en förkortning, så konsumenter läser den här i stället.
    forkortning: str


class TaxKant(TypedDict):
    fran: str
    till: str


class Taxonomigraf(TypedDict):
    noder: list[TaxNod]
    kanter: list[TaxKant]


def avdelning_id(avd: str) -> str:
    return f"avd::{avd}"


def omrade_id(oid: str) -> str:
    return f"omrade::{oid}"


def underomrade_id(uid: str) -> str:
    return f"under::{uid}"


def lag_id(under_id: str, forkortning: str) -> str:
    """Nod-id för en lag, skopat efter sitt delområde.

    Skopningen är nödvändig eftersom en lag kan höra till flera delområden:
    AvtL bär både avtalsrätten och den allmänna förmögenhetsrätten. Utan
    förälder i id:t skulle två sådana placeringar ge två noder med samma id,
    vilket får vis.DataSet att kasta och bryter trädinvarianten. Lagen får i
    stället en nod per placering, vilket också är sanningen kartan ska visa.

    Förkortningen läses därför aldrig ur id:t. Lagnoder bär den i fältet
    ``forkortning``.
    """
    return f"lag::{under_id}::{forkortning}"


def bygg_taxonomigraf() -> Taxonomigraf:
    """Bygg nod/kant-data för hela taxonomin.

    Ett strikt träd: varje nod utom roten har exakt en förälder, så antalet
    kanter är alltid antalet noder minus ett. ``avdelning`` ärvs nedåt på
    varje nod och driver färgsättningen; ``niva`` driver nodstorleken;
    ``url`` sätts ENDAST på lagnoder och är det som gör dem klickbara.
    """
    noder: list[TaxNod] = [
        {
            "id": ROT_ID,
            "label": ROT_LABEL,
            "grupp": GRUPP_ROT,
            "niva": 0,
            "avdelning": "",
            "titel": "Svensk rätts indelning enligt kursens disposition.",
        }
    ]
    kanter: list[TaxKant] = []

    for avdelning in taxonomi():
        aid = avdelning_id(avdelning.id)
        noder.append(
            {
                "id": aid,
                "label": avdelning.label,
                "grupp": GRUPP_AVDELNING,
                "niva": 1,
                "avdelning": avdelning.id,
                "titel": avdelning.beskrivning,
            }
        )
        kanter.append({"fran": ROT_ID, "till": aid})

        for omrade in avdelning.omraden:
            oid = omrade_id(omrade.id)
            noder.append(
                {
                    "id": oid,
                    "label": omrade.namn,
                    "grupp": GRUPP_OMRADE,
                    "niva": 2,
                    "avdelning": avdelning.id,
                    "titel": f"{omrade.beskrivning} När: {omrade.nar}",
                }
            )
            kanter.append({"fran": aid, "till": oid})

            for under in omrade.underomraden:
                uid = underomrade_id(under.id)
                noder.append(
                    {
                        "id": uid,
                        "label": under.namn,
                        "grupp": GRUPP_UNDEROMRADE,
                        "niva": 3,
                        "avdelning": avdelning.id,
                        "titel": f"{under.beskrivning} När: {under.nar}",
                    }
                )
                kanter.append({"fran": oid, "till": uid})

                for lag in under.lagar:
                    lid = lag_id(under.id, lag.forkortning)
                    noder.append(
                        {
                            "id": lid,
                            "label": lag.forkortning,
                            "forkortning": lag.forkortning,
                            "grupp": GRUPP_LAG,
                            "niva": 4,
                            "avdelning": avdelning.id,
                            "titel": (
                                f"{lag.namn} (SFS {lag.sfs}). "
                                f"{lag.beskrivning} När: {lag.nar}"
                            ),
                            "url": lag.url,
                        }
                    )
                    kanter.append({"fran": uid, "till": lid})

    return {"noder": noder, "kanter": kanter}
