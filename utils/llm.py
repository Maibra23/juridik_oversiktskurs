"""LLM-klient för Hugging Face Inference Providers.

Centraliserar all LLM-åtkomst för appen. Ansvarar för:
- Läsning av HF_TOKEN och modellval från st.secrets eller miljövariabler
- LLMClient: tunt lager runt InferenceClient med chat och stream_chat,
  inklusive strippning av Qwen3:s <think>-block
- cached_chat: st.cache_data-cachad chatt, nyckelad på hash av
  systemprompt + användarprompt + parametrar + modell
- Sessionstak (t.ex. 50 anrop) räknat i st.session_state; endast nya
  prompt-hashar debiteras, cacheträffar är gratis
- Enhetlig felhierarki: LLMUnavailableError, LLMSessionCapError,
  LLMDailyCapError så att alla sidor kan falla tillbaka deterministiskt

Ersätter ekonomistyrnings sifferextraktion: lagrumsverifieringen ligger
i utils.lagrum, inte här.
"""
