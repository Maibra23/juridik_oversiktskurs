"""Modulsida: Associationsrätt.

Ansvarar för övningar om bolagsformerna och deras ansvarsregler: handelsbolag
och enkla bolag (HBL), aktiebolagets frihet från personligt ägaransvar samt
bolagets organisation med stämma, styrelse och VD (ABL). Bygger scenarier
från data/scenarier/ och verifierar citerade lagrum (t.ex. "2 kap. 20 § HBL",
"1 kap. 3 § ABL") mot lagrumsregistret.

Själva vyn (tre flikar: Rättsfall, Quiz, Lagrumsjakt) delas med övriga
moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida("associationsratt", "Associationsrätt", "KAP. 12 · ASSOCIATIONSRÄTT")
