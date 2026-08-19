"""Modulsida: Juridisk metod och rättskällor.

Ansvarar för den interaktiva övningen i rättskälleläran: författningar,
förarbeten, praxis och doktrin samt lagtolkningsmetoder. Sidan samlar
studentens input, anropar tutorn on demand via utils.tutor och verifierar
att förklaringens lagrumshänvisningar finns i utils.lagrum-registret.

Vyn (tre flikar) delas med övriga moduler via utils.modulvy.
"""

from __future__ import annotations

from utils.modulvy import rendera_modulsida

rendera_modulsida("juridisk_metod", "Juridisk metod", "JURIDISK METOD")
