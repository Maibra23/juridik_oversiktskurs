"""Scenariogenerering och scenariohantering.

Ansvarar för de fiktiva rättsfallsscenarier som modulsidorna övar på:
- Inläsning av deterministiska basscenarier från data/scenarier/*.json
- LLM-generering av varierade scenarier (namn, belopp, omständigheter)
  med strikt JSON-schema och robust JSON-extraktion ur LLM-svar
- Validering: ett genererat scenario måste ange vilka lagrum som är
  relevanta och samtliga måste finnas i utils.lagrum-registret, annars
  förkastas det och fallbackscenariot används
- Aktuellt scenario lagras i st.session_state så att det överlever
  reruns och delas mellan förklaring, guide och quiz
"""
