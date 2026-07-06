"""Tester för utils.tutor.

Täcker on demand-mönstret: inget LLM-anrop utan knapptryck, cachad text
återges vid oförändrad hash, inaktuell markering vid ändrad hash samt
att lagrumsverifieringens varning lagras tillsammans med texten.
"""
