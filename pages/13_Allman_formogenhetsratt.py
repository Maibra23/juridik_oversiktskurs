"""Modulsida: Allmän förmögenhetsrätt (kap 6).

Ansvarar för övningar om äganderättens övergång till lös egendom: godtrosförvärv
enligt lagen (1986:796) om godtrosförvärv av lösöre, undantaget för olovligen
tagen egendom, lösningsrätt och hävd.

Modulen är grunden för köprätten: den besvarar frågan vem som äger saken, innan
köprätten prövar fel och påföljder i förhållandet mellan säljare och köpare.

Själva vyn (tre flikar: Rättsfall, Quiz, Lagrumsjakt) delas med övriga
moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida(
    "allman_formogenhetsratt",
    "Allmän förmögenhetsrätt",
    "KAP. 6 · ALLMÄN FÖRMÖGENHETSRÄTT",
)
