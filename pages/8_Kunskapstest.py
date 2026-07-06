"""Modulsida: Kunskapstest.

Ansvarar för quizflödet över samtliga juridikmoduler. Frågor genereras
av LLM (eller hämtas från deterministisk fallback i data/) och varje
fråga kvalitetskontrolleras: citerade lagrum måste finnas i
lagrumsregistret innan frågan visas för studenten. Sparar progress i
session state.
"""
