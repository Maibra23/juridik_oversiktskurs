"""On demand-tutorhjälpare.

Centraliserar mönstret som varje sida använder: tutorförklaringen körs
ENDAST när studenten trycker på knappen, aldrig vid rerun. Genererad
text cachas i st.session_state tillsammans med en hash av de
inputs/outputs som producerade den; vid oförändrad hash återges texten
gratis, vid ändrad hash markeras den som inaktuell och knappen byter
etikett till "Uppdatera förklaringen".

Skillnad mot ekonomistyrning: efter varje generering anropas
utils.lagrum.verify_lagrum i stället för verify_grounding, och en
varning visas om förklaringen citerar lagrum utanför registret.
Felhantering: LLMSessionCapError -> sessionstakskort,
LLMUnavailableError -> deterministisk fallbackmall.
"""
