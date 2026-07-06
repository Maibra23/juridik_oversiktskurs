"""Delade pytest-fixturer.

Ansvarar för testmiljön: blockerar riktiga LLM-anrop, tillhandahåller
fejkade Streamlit-secrets/session_state, temporär budgetfil via
LLM_BUDGET_FILE samt fixturer med ett minimalt lagrumsregister och
exempelscenarier.
"""
