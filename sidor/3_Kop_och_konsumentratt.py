"""Modulsida: Köprätt och konsumenträtt.

Ansvarar för övningar om köplagen (1990:931), konsumentköplagen
(2022:260) och distansavtalslagen. Sidan låter studenten analysera
felansvar, reklamation och påföljder i genererade scenarier, med
lagrumsverifierade tutorförklaringar.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida(
    "kop_och_konsumentratt", "Köp- och konsumenträtt", "KAP. 8 · KÖPRÄTT"
)
