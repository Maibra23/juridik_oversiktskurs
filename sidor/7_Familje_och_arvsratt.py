"""Modulsida: Familjerätt och arvsrätt.

Ansvarar för övningar om äktenskapsbalken, sambolagen (2003:376) och
ärvdabalken: bodelning, giftorättsgods, arvsordning och testamente.
Scenarier hämtas från data/scenarier/ och tutorns lagrumshänvisningar
verifieras mot lagrumsregistret.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida(
    "familje_och_arvsratt",
    "Familje- och successionsrätt",
    "KAP. 18–21 · FAMILJ OCH ARV",
)
