"""Lagrumsregister och verifiering av lagrumshänvisningar.

Juridikappens motsvarighet till ekonomistyrnings verify_grounding, men
för lagrum i stället för siffror. Ansvarar för:
- Inläsning och validering av data/lagrum.json (SFS-nummer, lagnamn,
  vedertagen förkortning, paragrafer och kort beskrivning per lagrum)
- extract_lagrum(text): parsa hänvisningar ur LLM-text, t.ex.
  "36 § avtalslagen", "36 § AvtL", "3 kap. 1 § skadeståndslagen"
  och normalisera till kanonisk form
- verify_lagrum(text, expected): jämför citerade lagrum mot de
  förväntade/tillåtna för scenariot och returnera
  {"matched": [...], "missing": [...], "hallucinated": [...]}
- Uppslag för UI:t: visa fulltextetikett och länk till lagen.nu/riksdagen
  för varje verifierat lagrum
"""
