"""Modulsida: Avtalsrätt.

Ansvarar för övningar om avtals ingående, fullmakt och ogiltighetsgrunder
enligt avtalslagen (1915:218). Bygger scenarier från data/scenarier/,
genererar tutorförklaringar on demand och verifierar citerade lagrum
(t.ex. "1 § AvtL", "36 § AvtL") mot lagrumsregistret.

Själva vyn (tre flikar: Rättsfall, Quiz, Lagrumsjakt) delas med övriga
moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida("avtalsratt", "Avtalsrätt", "AVTALSRÄTT")
