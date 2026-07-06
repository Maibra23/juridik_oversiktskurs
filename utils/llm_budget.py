"""Serverbaserad daglig LLM-anropsbudget.

Sessionstaket dör med sessionen, så på en publik deploy skulle någon
kunna tömma HF-tokenbudgeten genom att ladda om sidan. Denna modul
för en filbaserad daglig räknare (data/.llm_daily_usage.json) som delas
av alla sessioner på värden och inte kan nollställas från UI:t.

Räknaren är rådgivande, inte faktureringskritisk: vid filsystemfel
öppnar vi hellre (appen fortsätter fungera) och loggar problemet.
"""
