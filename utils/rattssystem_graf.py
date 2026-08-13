"""Taxonomin över svensk rätt som träd och som nod/kant-graf.

Bygger den fullständiga indelningen av svensk rätt ur data/rattssystem.json
och lagrumsregistret som ett rekursivt träd: rot -> toppgren -> ... -> lag.
Till skillnad från den personliga kunskapsgrafen (utils.graf), som växer med
studentens egna rättsfall, är den här grafen full redan på dag noll.

Två publika ingångar:

- ``taxonomi()``   : rättssystemets toppgrenar (rena dataklasser från
  utils.rattskarta, ingen rendering).
- ``bygg_taxonomigraf()`` : hela trädet som ``{"noder": [...], "kanter": [...]}``
  i exakt samma envelope som utils.graf, så att utils.graf_ui:s
  vis-network-mönster kan återanvändas rakt av.

Trädet följer rättens doktrinära systematik (offentlig rätt / civilrätt med
förmögenhetsrätt -> obligationsrätt/sakrätt). Färgen styrs av ``toppgren`` som
ärvs nedåt på varje nod. Juridisk metod visas inte i kartan (den nås via
sidopanelen). Ren Python utan Streamlit-beroende, så att allt kan enhetstestas.
"""

from __future__ import annotations

from typing import Iterator, TypedDict

from utils.lagrum import lagrum_register
from utils.rattskarta import Gren, ladda_rattssystem

# --- Nodgrupper (styr form och storlek i renderingen) -----------------------

GRUPP_ROT = "rot"
GRUPP_GREN = "gren"
GRUPP_LAG = "lag"
# Referenslag: klickbar kartnod för överblick, men utanför kursregistret. Egen
# grupp så att renderingen kan skilja den från kursens guldlagar.
GRUPP_REFERENS = "referenslag"

ROT_ID = "rot"
ROT_LABEL = "Svensk rätt"


def taxonomi() -> tuple[Gren, ...]:
    """Rättssystemets toppgrenar (offentlig rätt, civilrätt), i ordning."""
    return ladda_rattssystem()


def alla_lagar_i_registret() -> dict:
    """Genväg till lagrumsregistret (lat, för notbyggarna)."""
    return lagrum_register()


def alla_grenar() -> Iterator[Gren]:
    """Gå igenom trädet i förhandsordning och ge varje gren."""
    def _walk(grenar: tuple[Gren, ...]) -> Iterator[Gren]:
        for gren in grenar:
            yield gren
            yield from _walk(gren.grenar)

    yield from _walk(taxonomi())


# --- Grafen (samma envelope som utils.graf) ---------------------------------


class TaxNod(TypedDict, total=False):
    id: str
    label: str
    grupp: str
    niva: int
    # Förälderns nod-id, tom sträng för roten. Renderingen härleder både
    # förfäderskedja och ättlingar ur det här fältet i stället för att gå
    # igenom kantlistan; se utils/static/taxonomigraf_logik.js.
    foralder: str
    toppgren: str
    titel: str
    url: str
    # Endast lagnoder. Id:t är skopat efter gren och går inte att tolka som en
    # förkortning, så konsumenter läser den här i stället.
    forkortning: str


class TaxKant(TypedDict):
    fran: str
    till: str


class Taxonomigraf(TypedDict):
    noder: list[TaxNod]
    kanter: list[TaxKant]


def gren_id(gid: str) -> str:
    return f"gren::{gid}"


def lag_id(gren: str, forkortning: str) -> str:
    """Nod-id för en lag, skopat efter sin gren.

    Skopningen är nödvändig eftersom en lag kan höra till flera grenar. Utan
    förälder i id:t skulle två placeringar ge två noder med samma id, vilket
    får vis.DataSet att kasta och bryter trädinvarianten. Förkortningen läses
    därför aldrig ur id:t; lagnoder bär den i fältet ``forkortning``.
    """
    return f"lag::{gren}::{forkortning}"


def bygg_taxonomigraf() -> Taxonomigraf:
    """Bygg nod/kant-data för hela taxonomin.

    Ett strikt träd: varje nod utom roten har exakt en förälder, så antalet
    kanter är alltid antalet noder minus ett. ``toppgren`` ärvs nedåt på varje
    nod och driver färgsättningen; ``niva`` (djupet) driver nodstorleken;
    ``url`` sätts ENDAST på lagnoder och är det som gör dem klickbara.
    """
    register = lagrum_register()
    noder: list[TaxNod] = [
        {
            "id": ROT_ID,
            "label": ROT_LABEL,
            "grupp": GRUPP_ROT,
            "niva": 0,
            "foralder": "",
            "toppgren": "",
            "titel": "Svensk rätts doktrinära indelning.",
        }
    ]
    kanter: list[TaxKant] = []

    def _lagg_till(gren: Gren, foralder_id: str, niva: int) -> None:
        gid = gren_id(gren.id)
        titel = f"{gren.beskrivning}"
        if gren.nar:
            titel += f" När: {gren.nar}"
        noder.append(
            {
                "id": gid,
                "label": gren.namn,
                "grupp": GRUPP_GREN,
                "niva": niva,
                "foralder": foralder_id,
                "toppgren": gren.toppgren,
                "titel": titel,
            }
        )
        kanter.append({"fran": foralder_id, "till": gid})

        for barn in gren.grenar:
            _lagg_till(barn, gid, niva + 1)

        for lag in gren.lagar:
            lid = lag_id(gren.id, lag.forkortning)
            if lag.ar_referens:
                noder.append(
                    {
                        "id": lid,
                        "label": lag.forkortning,
                        "forkortning": lag.forkortning,
                        "grupp": GRUPP_REFERENS,
                        "niva": niva + 1,
                        "foralder": gid,
                        "toppgren": gren.toppgren,
                        "titel": (
                            f"{lag.namn} (SFS {lag.sfs}). {lag.beskrivning} "
                            "Överblick – utanför kursen."
                        ),
                        "url": f"https://lagen.nu/{lag.sfs}",
                    }
                )
                kanter.append({"fran": gid, "till": lid})
                continue
            info = register[lag.forkortning]
            noder.append(
                {
                    "id": lid,
                    "label": lag.forkortning,
                    "forkortning": lag.forkortning,
                    "grupp": GRUPP_LAG,
                    "niva": niva + 1,
                    "foralder": gid,
                    "toppgren": gren.toppgren,
                    "titel": (
                        f"{info.namn} (SFS {info.sfs}). "
                        f"{lag.beskrivning} När: {lag.nar}"
                    ),
                    "url": info.lagen_nu_bas_url,
                }
            )
            kanter.append({"fran": gid, "till": lid})

    for topp in taxonomi():
        _lagg_till(topp, ROT_ID, 1)

    return {"noder": noder, "kanter": kanter}
