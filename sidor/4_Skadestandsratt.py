"""Modulsida: Skadeståndsrätt.

Ansvarar för övningar om utomobligatoriskt skadestånd enligt
skadeståndslagen (1972:207): culparegeln, person- och sakskada, ren
förmögenhetsskada samt principalansvar. Tutorförklaringar genereras on
demand och citerade lagrum verifieras mot registret.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida("skadestandsratt", "Skadeståndsrätt", "KAP. 10 · SKADESTÅNDSRÄTT")
