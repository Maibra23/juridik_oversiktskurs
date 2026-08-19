"""Modulsida: Straffrätt och processrätt.

Ansvarar för övningar om brottsbegreppet enligt brottsbalken (1962:700)
och rättegångens gång enligt rättegångsbalken (1942:740): rekvisit,
uppsåt/oaktsamhet, tvistemål och brottmål. Tutorförklaringar genereras
on demand med lagrumsverifiering.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida(
    "straff_och_processratt", "Straffrätt och processrätt", "STRAFFRÄTT"
)
