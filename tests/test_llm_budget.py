"""Tester för utils.llm_budget.

Täcker daglig räknare: nollställning vid nytt datum, korrupt fil ger
noll, fail open vid filsystemfel, LLM_DAILY_CAP-parsning och att
record_daily_call skriver atomiskt.
"""
