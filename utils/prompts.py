"""Promptbibliotek för juridiktutorn.

Alla prompts som används i appen ligger här. Varje byggarfunktion
returnerar en tupel (system_prompt, user_prompt). Ren Python: ingen
Streamlit, ingen LLM-klient. Ansvarar för:
- SYSTEM_PROMPT_BASE: roll, register, struktur (Omständigheter,
  Rättsregel, Tillämpning, Slutsats) och absoluta regler
- Juridisk ORDLISTA: kanoniska svenska termer med vanliga felvarianter
- Regeln att tutorn ENDAST får citera lagrum som anges i promptens
  LAGRUMSBLOCK (motsvarigheten till "hitta inte på tal")
- Byggare per modul: förklaring, steg-för-steg-guide, quizgenerering,
  scenariogenerering samt deterministiska fallbackmallar för offlineläge
"""
