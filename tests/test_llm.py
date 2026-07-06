"""Tester för utils.llm.

Täcker tokenupplösning, modellnormalisering, <think>-strippning,
prompt-hashning, sessionstak (nya hashar debiteras, cacheträffar inte)
och felhierarkin LLMUnavailableError/LLMSessionCapError/LLMDailyCapError.
"""
