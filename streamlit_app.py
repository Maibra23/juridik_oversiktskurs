"""Startsida för Juridisk översiktskurs.

Ingångspunkt för Streamlit-multipage-appen. Ansvarar för:
- st.set_page_config (måste köras först av alla Streamlit-anrop)
- Hjärtat på landningssidan: hero-block, modulkarta och arbetsgång
- Navigering till modulsidorna i pages/ via st.page_link
- Injektion av gemensam CSS och rendering av sidopanelen via utils.ui

Ingen affärslogik här: all LLM-, lagrums- och scenariologik ligger i utils/.
"""
