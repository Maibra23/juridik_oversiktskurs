"""Delade UI-komponenter och tema.

Ansvarar för allt visuellt som delas mellan sidorna:
- inject_css: appens gemensamma stilar (inklusive varningsbadge för
  ohallucinerade/ogrundade lagrumshänvisningar och offlinebadge)
- render_sidebar: navigering, modellväljare och räknare för återstående
  LLM-anrop (session + dagsbudget)
- hero, section_heading, summary_box, module_map, pipeline_steps,
  footer_note: HTML-byggstenar för landnings- och modulsidor
- render_session_cap_card och render_daily_cap_card: vänliga svenska
  informationskort när anropsbudgeten är slut
- render_lagrum_card: enhetlig visning av verifierade lagrum med länk
"""
