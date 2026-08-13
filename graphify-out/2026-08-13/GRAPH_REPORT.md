# Graph Report - juridik_oversiktskurs  (2026-08-13)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1995 nodes · 3663 edges · 114 communities (109 shown, 5 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 58 edges (avg confidence: 0.5)
- Token cost: 15,231 input · 5,580 output

## Graph Freshness
- Built from commit: `3a44034e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Graph Structure Tests
- Taxonomy Rendering
- Navigation Tree Tests
- Homepage Components
- Scenario Validation
- LLM Budget Testing
- Legal System Graph
- Key Concepts Testing
- LLM Function Tests
- Concept Section Validation
- Legal System Loading
- Course Section Check
- Case Generation
- Register Section Grouping
- Legal Section Extraction
- Scenario Generation
- Concept Prompt Building
- Module Prompt Testing
- modulvy.py
- Legal Structure Parsing
- Quiz Question Validation
- Tutor Helper
- Development Tasks
- Module Pages
- Tutor Text Rendering
- Prompt Generation
- Reference Validation
- Structure Parsing
- Legal Tree Structure
- Section Validation
- UI Component Testing
- Legal Text Fetching
- Legal Map Page Rendering
- Tutor Response Grading
- Section Key Expansion
- Data Flow Design
- Legal Map Interaction
- Special Legal Areas
- Product Requirements
- Legal Text Corpus
- UX Legal Redesign
- Legal System Restructuring
- Methodology
- Legal Case Example
- Homepage Testing
- Legal Text Corpus
- Quiz Grading
- Section Block Rendering
- Design System
- Knowledge Challenges
- RNTS Steps Testing
- Sidebar Rendering
- Legal Reference Check
- Difficulty Level Generation
- Structure Parsing
- Structure and Sections
- Alias Mapping
- LLM Client Errors
- Difficulty Levels
- Module Loading
- Knowledge Challenges
- Legal Map Interaction
- Alias Matching
- Reference Verification
- Language QA
- Alias Matching
- Obsidian Export
- Alias Validation
- Module View Testing
- Fake Client Testing
- Sidebar Rendering
- APPGUIDE
- Wireframes
- Legal Structure Fetching
- Cached Chat
- Quiz Prompts
- App Sections
- Module Pages
- Section Grading
- UX Redesign
- README
- Reference Chips
- Structure Validation
- System Components
- Components and Tutors
- Visual Design
- Whitelist
- CSS
- Measurement Results
- Legal Types
- Validation
- Taxonomy Graph Logic
- Visualization
- Legal Map Page
- Summary
- Prioritized Plan
- Taxonomy Graph
- Ordlista
- Homepage
- Knowledge Map
- 8. `11_Kunskapsutmaning` — genererat rättsfall
- 12. Ändringar i `design_system.md`
- 2. Informationsarkitektur
- 3. Startsidan
- _rendera_begrepp
- conftest.py
- taxonomigraf_logik.test.mjs
- 14. Styrkor och svagheter
- 4. Sidopanelen
- CLAUDE.md
- tests/__init__.py
- test_register_laddas_med_21_lagar
- test_inget_kursavsnitt_ar_overifierat
- utils/__init__.py

## God Nodes (most connected - your core abstractions)
1. `lagrum_register()` - 58 edges
2. `validera_lagrum()` - 50 edges
3. `extrahera_lagrum()` - 46 edges
4. `ladda_modul()` - 33 edges
5. `generera_case()` - 29 edges
6. `Lagrumsref` - 28 edges
7. `Modulscenarier` - 25 edges
8. `Lag` - 25 edges
9. `ladda_rattssystem()` - 25 edges
10. `build_begrepp_prompt()` - 24 edges

## Surprising Connections (you probably didn't know these)
- `FangaPromptKlient` --uses--> `LLMUnavailableError`  [INFERRED]
  tests/test_generator.py → utils/llm.py
- `FejkKlient` --uses--> `LLMUnavailableError`  [INFERRED]
  tests/test_generator.py → utils/llm.py
- `TrasigKlient` --uses--> `LLMUnavailableError`  [INFERRED]
  tests/test_generator.py → utils/llm.py
- `test_tutorsvar_ar_immutabelt()` --calls--> `Tutorsvar`  [EXTRACTED]
  tests/test_tutor.py → utils/tutor.py
- `test_valv_innehaller_rattskartan_aven_utan_analyser()` --calls--> `bygg_valv()`  [EXTRACTED]
  tests/test_rattskarta.py → utils/obsidian.py

## Import Cycles
- None detected.

## Communities (114 total, 5 thin omitted)

### Community 0 - "Graph Structure Tests"
Cohesion: 0.05
Nodes (76): _case(), _nod(), Tester för kunskapsgrafen: nod/kant-data och HTML-serialisering. Testar de rena…, _svar(), test_delat_lagrum_blir_en_nod_med_kant_fran_bada_fallen(), test_graf_har_modul_rattsfall_och_lagrumnoder(), test_grafens_lagrum_matchar_obsidianexporten(), test_html_bar_med_noder_och_cdn() (+68 more)

### Community 1 - "Taxonomy Rendering"
Cohesion: 0.04
Nodes (65): graf(), html(), fixture, Tester för renderingen av taxonomigrafen (utils.taxonomi_ui). Vaktar det som…, Strukturnoder ska färgas efter sin toppgren, inte efter djup., JSON-blocket ska gå att parsa, annars ritas inget alls., Utan CDN ska komponenten säga till och peka på områdesträdet., En etikett med </script> får aldrig kunna stänga script-taggen. (+57 more)

### Community 2 - "Navigation Tree Tests"
Cohesion: 0.05
Nodes (66): parametrize, Tester för navigeringsträdet i sidopanelen. Vaktar den enda invariant som gör…, Modulnamnen i trädet ska vara identiska med titlarna i st.Page. Sidopanelen…, Statsrätt saknar sida i trädet och kan därför aldrig slås upp., Vakt mot drift: varje kursmodul måste ha övningsinnehåll, och omvänt., Kärnan i ändringen: senast besökta modul får inte låsa studenten., Varje modul pekar på en fil som finns, eller är märkt som planerad., Planerad och byggd är varandras motsatser, aldrig något mittemellan. (+58 more)

### Community 3 - "Homepage Components"
Cohesion: 0.05
Nodes (61): Startsida: hero-block, en enda call-to-action och framsteg. Registreras som…, Exportknapparna: valvet primärt, rapporterna sekundära. Obsidianvalvet ligger…, Hämta rå quizresultatbok ur session_state för rapportbyggarna., Rendera hela landningssidan., Startsidans enda call-to-action: ett kort som svarar på vad och varför.…, Framstegssektion: tre tal, en ärlig rad om sessionen, och exporten. Tomt…, _render_cta(), _render_export() (+53 more)

### Community 4 - "Scenario Validation"
Cohesion: 0.06
Nodes (45): avtalsratt(), fixture, Tester för utils.scenarier. Täcker inläsning av basscenarier,…, Fältet är valfritt: befintliga scenariofiler ska läsas oförändrat., test_alla_lagrum_i_avtalsratt_ar_verifierade(), test_alla_lagrum_tillhor_avtalslagen(), test_ingress_lases_in_nar_den_finns(), test_modul_utan_ingress_far_tom_strang() (+37 more)

### Community 5 - "LLM Budget Testing"
Cohesion: 0.06
Nodes (46): Ingångspunkt och router för Juridisk översiktskurs. Ansvarar för: -…, budget_file(), fixture, Tester för utils.llm_budget. Täcker daglig räknare: nollställning vid nytt…, test_cap_override_via_env(), test_corrupt_file_treated_as_fresh(), test_default_cap_is_300(), test_default_cap_is_positive() (+38 more)

### Community 6 - "Legal System Graph"
Cohesion: 0.05
Nodes (38): parametrize, Tester för taxonomigrafen över svensk rätt (utils.rattssystem_graf). Vaktar att…, Bara lagnoder är klickbara — kurslagar och referenslagar, inte struktur., lag_id skopas efter gren så samma lag kan förekomma flera gånger., Fail fast: en tvetydig gren eller okänd färg får inte laddas tyst., De tre toppområdena ska vara grennoderna på nivå 1., foralder ska vara härledd ur samma träd som kanterna, inte gissad., Ett strikt träd har exakt en nod utan förälder. (+30 more)

### Community 7 - "Key Concepts Testing"
Cohesion: 0.08
Nodes (35): Global sida: Rättskartan. Kursens orienteringssida. Till skillnad från…, begrepp(), fixture, Tester för begreppsbanken (data/nyckelbegrepp.json, utils.nyckelbegrepp).…, Varje delområde med egna KURSlagar ska ha minst tre begrepp. Undantag:…, Definition, förklaring, exempel och igenkänning måste alla vara ifyllda., Fälten ska vara skrivna, inte platshållare på ett par ord., Fail fast: ett begrepp utan alla fyra fält får aldrig läsas in. (+27 more)

### Community 8 - "LLM Function Tests"
Cohesion: 0.09
Nodes (33): Tester för utils.llm. Täcker tokenupplösning, modellnormalisering,…, test_active_model_uses_alternative_when_configured(), test_get_hf_token_from_env(), test_get_hf_token_missing(), test_get_llm_config_defaults(), test_get_llm_config_from_env(), test_is_llm_available_false_when_missing(), test_is_llm_available_true_with_token() (+25 more)

### Community 9 - "Concept Section Validation"
Cohesion: 0.08
Nodes (37): test_alla_begreppsdelomraden_finns_kvar(), test_varje_begrepp_hor_till_ett_verkligt_delomrade(), _kontrollera_beskrivning(), Tester för utils/rattskarta.py: Obsidiankarta över det svenska rättssystemet.…, Snabbguiden fall -> lag hjälper studenten hitta rätt lag direkt., De två toppgrenarna ska få var sin callouttyp (färg)., Lagnoten pekar tillbaka in i toppgrenens note via en rubrik., Kurslagar (ej referenslagar) måste finnas i registret — grundningen.… (+29 more)

### Community 10 - "Legal System Loading"
Cohesion: 0.08
Nodes (36): test_toppgrenarna_bar_ratt_farg(), test_omradesnot_renderar_subtrad_med_rubriker(), test_rattssystemet_laddar_med_toppgrenar(), _alla_grenar(), _bygg_gren(), _bygg_referenslag(), delomraden_med_vag(), _frontmatter() (+28 more)

### Community 11 - "Course Section Check"
Cohesion: 0.11
Nodes (31): main(), Tester för försoningen mellan kursavsnitt och lagens struktur. Bakgrund:…, Kontrollen ska köras mot alla lagar, inte bara dem som råkar avvika., En kapitelindelad lags avsnitt måste peka på ett verkligt kapitel.…, Bärande invariant: inget kursavsnitt får påstå paragrafer som inte finns. RÖD…, test_avvikelser_ar_immutabla(), test_inga_kursavsnitt_pekar_utanfor_lagen(), test_kontrollera_alla_tacker_hela_registret() (+23 more)

### Community 12 - "Case Generation"
Cohesion: 0.12
Nodes (29): FangaPromptKlient, FejkKlient, Tester för utils.generator (LLM-genererade rättsfall). Använder en injicerad…, Två genereringar av samma modul får inte skicka identisk prompt. Regression:…, Ett fullt budgettak är inte samma sak som att LLM:en saknas. Regression:…, Fångar den user-prompt generatorn skickar, returnerar ett giltigt case., Returnerar förutbestämda svar i tur och ordning., test_dagsbudget_ger_budgetbesked() (+21 more)

### Community 13 - "Register Section Grouping"
Cohesion: 0.11
Nodes (32): Tester för grupperingen av kursavsnitt inför lagkortet. Registret bär avsnitten…, KKöpL har nio kapitel; kursen berör sex av dem., Utan kapitel finns inget att räkna, och raden ska då utebli helt., Regression: ingen lag får krascha grupperingen., 36 §, aldrig 36 §§. Pluralfel i lagrum läser studenten som slarv., Registret är redaktionellt sorterat och kan lägga 6 kap. före 3 kap. I ett…, test_alla_lagar_i_registret_kan_grupperas(), test_avsnitten_gar_inte_forlorade_vid_sortering() (+24 more)

### Community 14 - "Legal Section Extraction"
Cohesion: 0.11
Nodes (31): Tester för utils.lagrum. Täcker registerinläsning/-validering av…, skuldebrevslagen 3 paragrafen' ska tolkas som 3 § SkbrL., 3 paragrafen SkbrL' (paragrafordet före förkortningen) ska också gå., 3 kapitlet 1 paragrafen skadeståndslagen' ska ge SkL 3 kap. 1 §., Den säkra förkortningen 'par.' (med punkt) ska accepteras., Markörordet ska tolkas oavsett skiftläge, precis som lagnamnet., Bart 'p' är för lätt att förväxla med vanlig text och accepteras inte., test_extrahera_avvisar_bart_p_som_paragrafmarkor() (+23 more)

### Community 15 - "Scenario Generation"
Cohesion: 0.10
Nodes (29): Protocol, Random, Generatorn får aldrig tala med LLMClient direkt. cached_chat äger cachen,…, Utan token ska generatorn falla tillbaka i stället för att krascha., test_standardklienten_ar_none_utan_token(), test_standardklienten_gar_genom_cached_chat(), _BudgeteradKlient, _case_ar_grundat() (+21 more)

### Community 16 - "Concept Prompt Building"
Cohesion: 0.09
Nodes (30): begrepp(), fixture, Tester för build_begrepp_prompt (utils.prompts). Vaktar att…, Prompten ska nämna vitlistan, förbudet mot påhitt och formatkravet., Fokuserad vitlista: AvtL ska med, orelaterade lagar inte., Byggaren ska klara både dataklass och dict, som övriga byggare., Utan egna lagrum faller vi tillbaka på registret, aldrig på en tom lista., Begreppsfördjupningen har en egen systemprompt, inte fallgranskningens.… (+22 more)

### Community 17 - "Module Prompt Testing"
Cohesion: 0.11
Nodes (24): Tester för utils.prompts. Täcker att varje promptbyggare returnerar (system,…, Lagrum, tillämpningspunkter och slutsats ska alla med, inte bara frågan., Studenten ska aldrig få veta att en lösningsnyckel finns. Observerat i skarpt…, Svaret ska alltid vara på svenska, oavsett vad studenten skriver., Kärnan i förbättringen: säg till när studentens lagrum inte är facits., Facit får vägleda granskningen, inte serveras som lösning., Tutorn ska kunna säga VARFÖR studentens paragraf inte passar. Utan textens…, Saknad lagtext ska ge en prompt utan lagtextblock, inte ett fel. (+16 more)

### Community 18 - "modulvy.py"
Cohesion: 0.13
Nodes (22): Markera ett rättsfall som genomfört (hela RNTS-analysen ifylld)., registrera_case_genomford(), _jakt_ratta_nyckel(), _lagrum_chip_rad(), _norm_feedback(), Delad modulsidevy: Rättsfall, Quiz och Lagrumsjakt. Varje modulsida i sidor/ är…, Rendera ett rättsfall som RNTS-övning: kort, formulär, tutor och facit. Delas…, Rita RNTS-fälten och returnera studentens svar som en dict. (+14 more)

### Community 19 - "Legal Structure Parsing"
Cohesion: 0.09
Nodes (24): fixture, Tester för läsningen av lagstrukturen (utils.lagstruktur). Strukturen är appens…, Hela lagen, inte kursens del: KKöpL har nio kapitel., Fail fast: hellre ett fel vid uppstart än ett halvt kapitel i vyn., AvtL och SkbrL har kapitelrubriker men löpande numrering. Nyckelns form följer…, strukturer(), test_alla_lagar_i_registret_har_en_strukturfil(), test_antal_kapitel_ar_noll_for_kapitellos_lag() (+16 more)

### Community 20 - "Quiz Question Validation"
Cohesion: 0.11
Nodes (28): _fraga(), test_avtalsratt_alla_mc_har_exakt_ett_ratt(), test_fel_svar_ger_ratt_index_och_forklaring(), test_fraga_utan_exakt_ett_ratt_kastar(), test_ratt_svar_ger_korrekt(), test_valt_index_utanfor_intervall_kastar(), _rendera_quizfraga(), LagrumsjaktResultat (+20 more)

### Community 21 - "Tutor Helper"
Cohesion: 0.11
Nodes (29): ar_inaktuell(), _cache(), generera_tutorsvar(), hamta_cachat(), _hash_inputs(), On demand-tutorhjälpare. Centraliserar mönstret som varje sida använder:…, Rita tutorknappen, hantera generering, granskning, cache och rendering.…, Ett cachat tutorsvar med hashen av de inputs som skapade det. ``godkand=False``… (+21 more)

### Community 22 - "Development Tasks"
Cohesion: 0.07
Nodes (28): 1.1 (DEV) Analysera referensrepot, 1.2 (DEV) Skapa projektstruktur, 1.3 (INN) Bygg lagrumsdatabasen (kärnan i hallucinationsskyddet), 1.4 (DEV) LLM wrapper och budgetskydd, 1.5 (DEV) Lagrumsvalidering, 1.6 (DEV) Streamlit skelett och startsida, 1.7 (INN + PE) Första modulens innehåll: Avtalsrätt, 2.1 (PE) Systemprompt för tutorn (+20 more)

### Community 23 - "Module Pages"
Cohesion: 0.06
Nodes (24): Modulsida: Personrätt (kap 5). Ansvarar för övningar om rättskapacitet och…, Modulsida: Allmän förmögenhetsrätt (kap 6). Ansvarar för övningar om…, Modulsida: Fastighetsrätt (kap 9). Ansvarar för övningar om fast egendom:…, Modulsida: Fordringsrätt (kap 15 till 17). Ansvarar för övningar om fordringar…, Modulsida: Juridisk metod och rättskällor. Ansvarar för den interaktiva…, Modulsida: Avtalsrätt. Ansvarar för övningar om avtals ingående, fullmakt och…, Modulsida: Köprätt och konsumenträtt. Ansvarar för övningar om köplagen…, Modulsida: Skadeståndsrätt. Ansvarar för övningar om utomobligatoriskt… (+16 more)

### Community 24 - "Tutor Text Rendering"
Cohesion: 0.10
Nodes (27): Tester för utils.tutor och utils.ui.render_tutortext. Täcker on demand-…, Overifierade lagrum har redan sin egen, starkare varningsruta., Noten måste säga att den bara intygar existens, inte relevans., Ett grönt chip betyder att lagrummet finns, inte att det är rätt. Verifieringen…, Ingen not när svaret inte hänvisar till något lagrum alls., test_hash_inputs_stabil_och_kansliga_for_andring(), test_render_kapitelindelat_lagrum_blir_chip(), test_render_okand_paragraf_hamnar_i_ovarifierade() (+19 more)

### Community 25 - "Prompt Generation"
Cohesion: 0.10
Nodes (25): Prompten ska innehålla exakt det block som hör till vald nivå., JSON-schemat ska tvinga svarighetsgrad till den valda nivån., Genereringen ska uttryckligen be om korrekt, idiomatisk svenska. Scenariotexten…, test_generate_prompt_default_ar_grund(), test_generate_prompt_injicerar_vald_svarighetsinstruktion(), test_generate_prompt_kraver_korrekt_svensk_sprakkvalitet(), test_generate_prompt_ogiltig_niva_normaliseras_till_grund(), test_generate_prompt_olika_nivaer_ger_olika_instruktion() (+17 more)

### Community 26 - "Reference Validation"
Cohesion: 0.10
Nodes (25): test_register_innehaller_forvantade_forkortningar(), graf(), fixture, Tester för referenslag: kartnoder som ger överblick men står utanför kursen. En…, EU-rätt och internationell privaträtt ska bära klickbara referenser., RF finns inte i kursregistret men ska ändå gå att bygga som referens., EU-rätt finns inte på lagen.nu; en explicit url ska räcka., Utan namn, och utan antingen SFS eller url, går ingen länk att bygga. (+17 more)

### Community 27 - "Structure Parsing"
Cohesion: 0.09
Nodes (17): Tester för strukturparsern (utils.lagstruktur_extrahering). Fixturerna är…, AvtL har kapitelrubriker men löpande numrering: "10", inte "2:10"., Platta nycklar får inte kosta kapitelindelningen i kartan., h3-bruset "Innehåll:" och "Övergångsbestämmelser" ska filtreras bort., En rubrik som inte äger någon paragraf är en mellanrubrik, inte ett moment., Kursavsnitten refererar bara hela paragrafnummer, aldrig "1 a §"., Källan märker AvtL:s paragrafer K2P10 fast numreringen löper 1-41. Registret…, test_avtl_grupperar_fortfarande_under_sina_kapitel() (+9 more)

### Community 28 - "Legal Tree Structure"
Cohesion: 0.11
Nodes (23): _kontrollera_form(), _kontrollera_toppgren(), Tester för rättssystemets doktrinära trädstruktur. Ersätter de gamla…, Axis 2 som kompakt hint: kartan nudgar användaren att fråga vilka parterna är,…, Tre toppområden: de två klassiska plus internationell rätt/EU-rätt.…, Axis 1: speciell avtalsrätt grupperas efter vad avtalet gör med saken.…, test_avtalstyper_ligger_i_ratt_transaktionsfamilj(), test_juridisk_metod_finns_inte_i_tradet() (+15 more)

### Community 29 - "Section Validation"
Cohesion: 0.09
Nodes (23): Hela vägen: en utskriven referens ska bli VERIFIERAD som en §-referens., En påhittad lag med utskrivet paragraford ska flaggas, inte verifieras., Regressionsvakt: skärpningen får inte träffa kapitelindelade lagar., test_utskrivet_paragraford_bevarar_hallucinationsspärren(), test_utskrivet_paragraford_verifieras_mot_registret(), test_validera_accepterar_lagrumsref_objekt(), test_validera_gement_okant_ord_ar_ej_validerbart(), test_validera_kapitellag_utan_kapitel_ger_okand_paragraf() (+15 more)

### Community 30 - "UI Component Testing"
Cohesion: 0.13
Nodes (21): Tester för designsystemets rena HTML-komponenter i utils/ui.py. Testar de…, test_render_case_escapar_html(), test_render_case_innehaller_rubrik_meta_och_text(), test_render_lagrum_chip_ovarifierad(), test_render_lagrum_chip_verifierad_med_url(), test_rnts_steg_escapar_html(), test_rnts_steg_innehaller_alla_etiketter(), test_rnts_steg_okand_status_ger_fel() (+13 more)

### Community 31 - "Legal Text Fetching"
Cohesion: 0.16
Nodes (21): bygg_lagfil(), extrahera_paragrafer(), extrahera_paragrafer_riksdagen(), filnamn_for(), hamta_lag(), hamta_riksdagen_html(), hamta_sida(), kursens_nycklar() (+13 more)

### Community 32 - "Legal Map Page Rendering"
Cohesion: 0.09
Nodes (20): fixture, Renderingstester för sidan Rättskartan (sidor/16_Rattskartan.py). Sidans hela…, Utan den läser studenten avsnittslistan som om lagen tog slut där., Kartans vy återställs i iframen; sidknappen rörde bara filtren., Kör Rättskartan med tom session_state, utan token och utan LLM., Grundlöftet: inget krav på tidigare arbete, inget krav på token., Spionen i fixturen failar om modellen anropas. Detta befäster det., Systemet, Falltypsguide och Nyckelbegrepp ska alla vara fulla. (+12 more)

### Community 33 - "Tutor Response Grading"
Cohesion: 0.14
Nodes (20): Tester för granskningen av tutorsvar (utils.granskning). Garden släpper igenom…, Skälet loggas och ska gå att förstå utan att läsa koden., Utan underlag finns inget att jämföra mot: bara påhitt ska stoppas., AvtL 4 §" är samma lagrum som "4 § AvtL" och ska räknas som underlag., Ett svar om struktur och metod behöver inte citera något alls., Det verkliga bästa svaret ur sessionens fälla. Utan den här regeln blockerar…, Det verkliga sämsta svaret: tutorn intygade ett påhitt som rätt norm., Det verkliga felet: en korrekt löst uppgift pekades mot 36 § AvtL. (+12 more)

### Community 34 - "Section Key Expansion"
Cohesion: 0.17
Nodes (20): _avsnitt(), _lag(), AvtL bär kapitel i strukturen men refererar platt i registret., test_avsnittsnycklar_expanderar_kapitelindelat_intervall(), test_avsnittsnycklar_expanderar_platt_intervall(), test_avsnittsnycklar_ignorerar_kapitel_for_kapitellos_lag(), avsnittsnycklar(), Paragrafnycklarna ett kursavsnitt gör anspråk på. Samma expansion som… (+12 more)

### Community 35 - "Data Flow Design"
Cohesion: 0.11
Nodes (17): Dataflöde, Datamodell: `data/lagstruktur/<sfs>.json`, Faser och överlämning, Felhantering, Komponenter, Källans tre former, Lagstruktur och kursavsnitt i lagkortet (projekt D), Mål (+9 more)

### Community 36 - "Legal Map Interaction"
Cohesion: 0.11
Nodes (17): De tre skikten, Felhantering, Filtrens återställningsknappar, Kartans återställningsknapp, Komponenter, Känd risk att undersöka — avskriven 2026-08-05, Mål, Problem (+9 more)

### Community 37 - "Special Legal Areas"
Cohesion: 0.11
Nodes (17): Avtalsrätten i Rättskartan: särskild avtalsrätt bryts ned i sina avtalstyper, Dokumentation, `fastighetsratt` (ändrad, kvar som toppgren under Civilrätt), `hyra_av_fast_egendom` (ny, under `speciell_avtalsratt`), `kop_av_fast_egendom` (ny, under `speciell_avtalsratt`), `kop_och_konsumentratt` och `arbetsratt`, Källor (lagnamn/SFS-nummer, verifierade 2026-08-06), `leasing` (ny, under `speciell_avtalsratt`, lagfri) (+9 more)

### Community 38 - "Product Requirements"
Cohesion: 0.11
Nodes (17): 1. Problem och syfte, 2. Målgrupp, 3. Mål, 4. Icke mål (avgränsningar), 5.1 Moduler (Paretourvalet, P0), 5.2 Scenariotyper (P0), 5.3 LLM tutor (P0), 5.4 Hallucinationsskydd (P0) (+9 more)

### Community 39 - "Legal Text Corpus"
Cohesion: 0.15
Nodes (15): Tester för lagtextkorpusen (utils.lagtext). Korpusen är appens svar på den…, Ett påhittat lagrum ska inte ge en tom eller påhittad rad., Inget block alls hellre än en rubrik utan innehåll., Prompten måste veta att detta är källtext, inte en parafras., Varje lag i registret ska ha en fil i korpusen., Spårbarhet: en läsare ska kunna se var texten kommer ifrån och när., test_korpusen_anger_kalla_och_hamtningsdatum(), test_korpusen_innehaller_kursens_lagar() (+7 more)

### Community 40 - "UX Legal Redesign"
Cohesion: 0.12
Nodes (15): Filstruktur, Global Constraints, Kvarstår till senare etapper, Slutkontroll, Task 10: Död kod och modulingressen, Task 1: Kursordning och ett sant nästa steg, Task 2: Facitexpandern i lagrumsjakten försvinner (verklig bugg), Task 3: Facit bakom ett försök (+7 more)

### Community 41 - "Legal System Restructuring"
Cohesion: 0.12
Nodes (15): Datamodell (`data/rattssystem.json`), Hård begränsning: bevara delområdes-id:na, Kodändringar, Kärnbeslut: rekursivt träd, Mål, Nytt träd (grenar med bevarade löv-id inom parentes), Problem, Rättskartan: doktrinär ombyggnad (projekt B+C) (+7 more)

### Community 42 - "Methodology"
Cohesion: 0.12
Nodes (15): 1.1 Paretoprincipen 80/20, 1.2 Fallbaserad inlärning, 1.3 Stegvisa förklaringar och produktiv kamp, 1.4 Mätning, 1. Pedagogisk metod, 2.1 RNTS strukturen, 2.2 Rättskälleläran, 2.3 Lagtolkning och systematik (+7 more)

### Community 43 - "Legal Case Example"
Cohesion: 0.12
Nodes (16): Det påhittade lagrummet ur sessionens fälla., 4 § AvtL är kursens skolexempel på sen accept., 2 kap. 1 § SkL är culparegeln., Uppslagningen får inte glida en paragraf fel., Regressionsvakt mot det verkliga felet tutorn gjorde. Modellen påstod att 36 §…, En paragraf utanför kursavsnitten finns inte i korpusen., test_36_paragrafen_ar_jamkning_inte_avtals_ingaende(), test_hamtar_text_for_kapitelindelad_lag() (+8 more)

### Community 44 - "Homepage Testing"
Cohesion: 0.16
Nodes (14): AppTest, fixture, MonkeyPatch, Tester för startsidans tomma tillstånd (sidor/0_Hem.py, Task 8). Löftet är att…, Kör appen med helt tom session_state (en förstagångsbesökare)., CTA:n är den enda handlingen en förstagångsbesökare ska mötas av., Inga nedladdningsknappar för en rapport eller ett valv som är tomt., `_render_export` (och därmed `bygg_valv`) får inte köras i tomt läge. Poängen… (+6 more)

### Community 45 - "Legal Text Corpus"
Cohesion: 0.14
Nodes (14): korpus(), fixture, test_har_lagtext_speglar_hamtningen(), har_lagtext(), _kanonisk_etikett(), ladda_lagtext(), Lagtext, _nyckel_for() (+6 more)

### Community 46 - "Quiz Grading"
Cohesion: 0.31
Nodes (14): Tester för utils.quiz rättningslogik. Täcker deterministisk rättning av…, test_lagrumsjakt_accepterar_alternativ_forkortning(), test_lagrumsjakt_accepterar_fullt_lagnamn_mot_forkortningsfacit(), test_lagrumsjakt_accepterar_gemener_forkortning(), test_lagrumsjakt_accepterar_versal_forkortning(), test_lagrumsjakt_exakt_traff(), test_lagrumsjakt_fel_paragraf(), test_lagrumsjakt_flera_facit_delvis() (+6 more)

### Community 47 - "Section Block Rendering"
Cohesion: 0.19
Nodes (15): _grupp(), Utan noten läses listan som om lagen tog slut där., BrB 3 kap. heter "Om brott mot liv och hälsa" och avsnittet likaså. Att skriva…, test_avsnittsrubrik_som_skiljer_sig_star_kvar(), test_avsnittsrubrik_som_upprepar_kapitelrubriken_utelamnas(), test_avsnittsspannet_lankar_till_lagen_nu(), test_kapitellos_grupp_renderar_ingen_kapitelrubrik(), test_lagkortet_escapar_avsnittsrubriker() (+7 more)

### Community 48 - "Design System"
Cohesion: 0.14
Nodes (13): 1. Färgpalett, 2.1 Typskala, 2.2 Spacingskala, 2. Typografi, 3. Komponentbibliotek (utils/ui.py), 4.1 Navigeringshierarki, 4.2 Rättskartan: appens orienteringssida, 4.3 Sidhjälp (+5 more)

### Community 49 - "Knowledge Challenges"
Cohesion: 0.14
Nodes (13): 1. Expertpersona i systemprompten, 2. Robust lagrumsparser (löser formatglappet), 2a. Parser fångar omvänd ordning, 2b. Skärpt prompt, 3. Publik case-byggare, 4. Kunskapsutmaning (LLM-genererade rättsfall), Arkitektur (återbruk framför nybygge), Dataflöde med grundning (+5 more)

### Community 50 - "RNTS Steps Testing"
Cohesion: 0.18
Nodes (8): Test för utils.rnts: RNTS-stegen och vilken aktivitet som tränar vilket steg.…, Vakt mot stavfel: ett okänt stegnamn ska inte kunna smyga in., test_alla_angivna_steg_finns_i_rnts_steg(), test_tranar_etikett_ar_versal_och_kommaseparerad(), test_tranar_etikett_okand_aktivitet_ger_valueerror(), RNTS-stegen och vilken aktivitet som tränar vilket steg. RNTS är appens…, Kapitälsetiketten för en aktivitet, t.ex. "TRÄNAR: NORM". ValueError vid okänd…, tranar_etikett()

### Community 51 - "Sidebar Rendering"
Cohesion: 0.18
Nodes (14): _har_rubrik(), Kör render_sidopanel och samla både HTML-raderna och modullänkarnas namn.…, Sant om ``namn`` ritats som en egen grupprubrik., Gruppen "Personrätt" omsluter en modul med exakt samma namn. Panelen skrev…, Enbarnsgrupper med ett EGET namn måste behålla sin rubrik. Modullänkar ritas av…, Vakt mot att fälla allt: grupper med flera barn bär fortfarande struktur., Statsrätt och förvaltningsrätt delar en enda dämpad rad. Kursens omfattning ska…, Sammanlagt: panelen ritar färre rader än trädet har noder. Jämförelsetalet… (+6 more)

### Community 52 - "Legal Reference Check"
Cohesion: 0.21
Nodes (13): _avvisas(), Granskning, _kanonisk(), _meningar(), Granska ett tutorsvar innan studenten ser det. Garden i utils.lagrum svarar på…, Sant om lagrummet nämns i en avvisande mening. Tittar bara i de meningar där…, Utfallet av en granskning., Jämförbar form oavsett hur referensen skrevs i texten. (+5 more)

### Community 53 - "Difficulty Level Generation"
Cohesion: 0.15
Nodes (12): 1. Ny modul `utils/svarighetsgrad.py`, 2. `utils/prompts.py` — `build_generate_prompt` får parameter `svarighetsgrad`, 3. `utils/generator.py` — `generera_case` får parameter `svarighetsgrad`, 4. UI — väljare före "Generera nytt rättsfall", 5. Datafix, Felhantering, Komponenter, Nivåer (+4 more)

### Community 54 - "Structure Parsing"
Cohesion: 0.23
Nodes (12): avtl(), kkopl(), _las(), preskl(), fixture, test_rensa_html_tar_bort_taggar_och_normaliserar(), extrahera_struktur(), _ny_post() (+4 more)

### Community 55 - "Structure and Sections"
Cohesion: 0.17
Nodes (11): Filstruktur, Global Constraints, Lagstruktur och kursavsnitt i lagkortet — implementationsplan, Självgranskning, Task 1: Strukturparser med fixturer, Task 2: Hämtare som skriver data/lagstruktur/, Task 3: Läsande lager utils/lagstruktur.py, Task 4: Kontrollager och överskjutandetestet (+3 more)

### Community 56 - "Alias Mapping"
Cohesion: 0.17
Nodes (12): Match, test_bygg_alias_karta_kastar_vid_kolliderande_alias(), test_bygg_alias_karta_loser_alias_till_forkortning(), test_riktiga_registret_har_kollisionsfria_alias(), _bygg_alias_karta(), _forkortning_gemener_karta(), _normalisera_forkortning(), Bygg en gemena-till-kanonisk-karta ur ett register. Nyckel är förkortningen… (+4 more)

### Community 57 - "LLM Client Errors"
Cohesion: 0.20
Nodes (8): RuntimeError, test_llm_unavailable_error_is_exception(), LLMClient, LLMUnavailableError, Tunt lager runt huggingface_hub.InferenceClient. Alla undantag fångas och…, Enkelt chat-anrop. Returnerar textinnehållet., Strömmande chat-anrop. Yieldar textbitar. Buffrar bort eventuella…, Kastas när LLM:en inte kan betjäna en förfrågan. Orsaker: saknad token,…

### Community 58 - "Difficulty Levels"
Cohesion: 0.20
Nodes (9): parametrize, Tester för utils.svarighetsgrad (kanoniskt svårighetsbegrepp). Ren logik, ingen…, test_etikett_for_kanda_nycklar(), test_etikett_for_okand_faller_till_standard(), test_instruktion_ar_distinkt_och_icke_tom_per_niva(), test_instruktion_for_okand_niva_normaliseras(), test_normalisera(), etikett_for() (+1 more)

### Community 59 - "Module Loading"
Cohesion: 0.17
Nodes (12): _brusten_ladda_modul(), _modulsida_html_vid_lasfel(), MonkeyPatch, Kör _rendera_rattsfall utanför AppTest och samla den ritade HTML:en. Samma skäl…, Tom case-tupel: ingen TRÄNAR-rad, trots innehåll i de andra två flikarna., Motsatsen till testet ovan: med ett rättsfall ska raden faktiskt ritas. Utan…, Kör rendera_modulsida med en ladda_modul som kastar och samla HTML:en. Samma…, Felvägen vid trasig scenariofil ska ändå rita hero, inte bara varningen. Hero… (+4 more)

### Community 60 - "Knowledge Challenges"
Cohesion: 0.24
Nodes (10): cache_data, Global sida: Kunskapsutmaning. Studenten testar sin förmåga på ett färskt,…, Karta från filnamn (stem) till modulens visningsnamn., _visningsnamn(), test_valj_slumpmodul_ger_giltig_modul(), test_lista_moduler_innehaller_avtalsratt(), Välj en slumpmässig modul för 'Överraska mig'., valj_slumpmodul() (+2 more)

### Community 61 - "Legal Map Interaction"
Cohesion: 0.18
Nodes (10): Global Constraints, Rättskartans grafinteraktion — implementationsplan, Task 1: Varje nod bär sin förälder, Task 2: Konfigurationsblock och foralder ut i renderingen, Task 3: Flytta ut JavaScripten ur f-strängen, Task 4: Skiktlogiken som testbar JavaScript, Task 5: Fokusera grenen vid klick, Task 6: Zoomgolv, återställningsknapp och Escape (+2 more)

### Community 62 - "Alias Matching"
Cohesion: 0.18
Nodes (10): 1. Datamodell: `aliaser` per lag i `data/lagrum.json`, 2. Matchning: `utils/lagrum.py`, 3. UI och rapportering, Bakgrund, Design, Designspec: Alternativa sätt att ange lagrum i lagrumsjakten, Icke-mål, Mål (+2 more)

### Community 63 - "Reference Verification"
Cohesion: 0.18
Nodes (11): test_verify_lagrum_blandad_text(), test_verify_lagrum_fangar_omvand_ordning(), test_verify_lagrum_markerar_nja_som_ej_validerbar(), test_verify_lagrum_markerar_pahittad_lag(), test_verify_lagrum_verifierad_traff_har_url_och_beskrivning(), Lagrumstraff, _matchande_avsnitt(), Hitta det kursavsnitt som täcker referensens paragraf (och kapitel). (+3 more)

### Community 64 - "Language QA"
Cohesion: 0.31
Nodes (10): _glyfundantagen(), _granskade_filer(), parametrize, Path, Språk-QA: automatiska kontroller av svenskan innan den når UI:t. Fångar den…, Sant om filen är undantagen från glyfvakten., Ingen emoji eller dekorativ glyf i kod, data eller dokumentation. Hierarki och…, test_inga_ikoner_eller_emoji() (+2 more)

### Community 65 - "Alias Matching"
Cohesion: 0.20
Nodes (9): File Structure, Final Verification, Global Constraints, Lagrumsjakt: Alternativa sätt att ange lagrum — Implementation Plan, Task 1: `Lag.aliaser` field and parsing, Task 2: Alias-aware lookup map with collision detection, Task 3: Add the alias table to `data/lagrum.json`, Task 4: End-to-end extraction/validation tests (+1 more)

### Community 66 - "Obsidian Export"
Cohesion: 0.20
Nodes (9): Arkitektur, Avgränsningar (YAGNI), Design: Obsidianexport (tasks.md 3.7), Designbeslut, Funktioner i `utils/obsidian.py`, Fångad data, Syfte, Testning (+1 more)

### Community 67 - "Alias Validation"
Cohesion: 0.20
Nodes (10): En sträng itereras tecken för tecken och skulle tyst släppa igenom skräp som…, Regexerna fångar aldrig mer än ett ord som förkortning, så en flerordsfras i…, test_validera_ra_lag_alias_falt_default_tomt(), test_validera_ra_lag_aliaser_med_flerordsfras_kastar(), test_validera_ra_lag_aliaser_med_icke_strang_element_kastar(), test_validera_ra_lag_aliaser_som_strang_kastar(), test_validera_ra_lag_giltiga_aliaser_ok(), test_validera_ra_lag_las_alias_falt() (+2 more)

### Community 68 - "Module View Testing"
Cohesion: 0.27
Nodes (9): Test för modulsidans grindar: facit ska överleva en rerun och kosta ett försök.…, Att låsa upp ett facit får inte låsa upp alla andra., Facitgrinden får inte renderas inuti `if st.button("Rätta")`. Ligger den där…, test_facit_ar_last_fran_borjan(), test_facit_las_ar_per_uppgift(), test_facit_oppnas_av_uttryckligt_val(), test_jaktfacitgrinden_ligger_inte_i_knappblocket(), facit_upplast() (+1 more)

### Community 69 - "Fake Client Testing"
Cohesion: 0.20
Nodes (10): _fejkklient(), Bygg en cached_chat-ersättare som returnerar givna svar i tur och ordning., Ett rent svar ska kosta exakt ett LLM-anrop., Första svaret framhåller ett påhitt, det andra är rent., Hellre inget svar än felaktig juridik: studenten kan inte skilja dem åt., Saknas facit finns inget att jämföra mot, men påhitt stoppas ändå., test_godkant_svar_slipper_omforsok(), test_tva_underkanda_svar_ger_inget_svar_alls() (+2 more)

### Community 70 - "Sidebar Rendering"
Cohesion: 0.22
Nodes (10): _klass_for(), Kör render_sidopanel utanför AppTest och samla den ritade HTML:en. AppTest kan…, Klassattributet för den rad vars textinnehåll är exakt ``namn``., Avtalsrätt öppen: dess tre förfäder (i var sitt <div>) ska bära aktiv., Grupper som inte omsluter den öppna sidan ska aldrig bära aktiv. Utan den här…, Tom session_state (ny session, eller en sida utanför trädet): inget aktiv alls., _sidopanel_html(), test_render_sidopanel_grupp_utanfor_kedjan_ar_inte_aktiv() (+2 more)

### Community 71 - "APPGUIDE"
Cohesion: 0.22
Nodes (8): 15. Optimeringsmöjligheter, prioriterade, 16. Vad dokumentet inte täcker, 1. Snabbstart, 3. Arkitektur i korthet, 6. `9_Kunskapstest` — resultatöversikt, APPGUIDE.md: vad varje sida gör, hur den fungerar och var den brister, Begränsningar, Vad du ser

### Community 72 - "Wireframes"
Cohesion: 0.22
Nodes (9): 10.1 Startsidan — alternativ A (rekommenderat): en spalt, avtagande vikt, 10.2 Startsidan — alternativ B: metoden först, 10.3 Sidopanelen — alternativ A (rekommenderat): tre plan, allt öppet, 10.4 Sidopanelen — alternativ B: plan öppna, doktrinära grenar hopfällda, 10.5 Modulsidan — alternativ A (rekommenderat): ramp, ett fokus, 10.6 Modulsidan — alternativ B: ett RNTS-steg per skärm, 10.7 Framsteg och samband, 10.8 Rättskartan (+1 more)

### Community 73 - "Legal Structure Fetching"
Cohesion: 0.36
Nodes (8): bygg_strukturfil(), filnamn_for(), _form(), hamta_lag(), main(), Path, Hämta och spara en lags struktur. Returnerar (antal kapitel, antal moment)., Vilken av källans tre former lagen visade sig ha. Specen klassificerade sju…

### Community 74 - "Cached Chat"
Cohesion: 0.22
Nodes (8): test_cached_chat_raises_daily_cap_when_exhausted(), test_cached_chat_raises_session_cap_when_used_up(), cached_chat(), _hash_prompt(), increment_session_calls(), Stabil hash av prompt + relevanta kwargs, för cachning., Cachat enkelt chat-anrop. Används inifrån Streamlit-sidor. Cachen nyckas på…, Registrera ett LLM-anrop för denna session. Returnerar antal kvar.

### Community 75 - "Quiz Prompts"
Cohesion: 0.22
Nodes (9): test_build_quiz_prompt_markerar_valt_alternativ(), build_quiz_prompt(), _forkortningar_ur(), _hamta(), _lagtext_for(), Plocka ut lagförkortningen ur en samling lagrumsträngar. "2 kap. 1 § SkL" ->…, Bygg (system, user) för förklaring av ett quizsvar. ``fraga`` är en…, Bygg lagtextblocket för flera grupper av lagrum, med avslutande radbryt.… (+1 more)

### Community 76 - "App Sections"
Cohesion: 0.25
Nodes (8): 1. Hem — orientering och nästa steg, 2. Din första session — vad du möter, i tur och ordning, 2. Rättskartan — dit man bör gå härnäst, 3. En modulsida — själva arbetet, 4. Vad som räknas som framsteg, 5. Kunskapskartan växer fram, 6. Innan du stänger fliken, Sidopanelen ligger fast

### Community 77 - "Module Pages"
Cohesion: 0.25
Nodes (8): 4. Modulsidorna (11 av 17), Begränsningar, Flik 1 — Rättsfall, steg för steg, Flik 2 — Quiz, Flik 3 — Lagrumsjakt, Styrkor, Under huven, Vad du ser

### Community 78 - "Section Grading"
Cohesion: 0.25
Nodes (7): Efterkontroll: de 14 "saknade" paragraferna var upphävda, Grupp A — gränsjustering (12 avsnitt), Grupp B — pekar på fel kapitel (3 avsnitt), KKöpL — tre avsnitt är felmappade, Rättningsförslag för de 15 överskjutande kursavsnitten, Vad som inte ingick i det här förslaget, ÄktB — två avsnitt spänner över fel eller flera kapitel

### Community 79 - "UX Redesign"
Cohesion: 0.25
Nodes (7): 11. Invändningar mot granskningens egna förslag, 13. Vad som inte granskats, 7. Lärandeupplevelsen, 8. Nybörjarens första fem minuter, Hur gränssnittet ska bära dem i stället, Om dokumentet, UX-granskning och omdesign av Juridisk översiktskurs

### Community 80 - "README"
Cohesion: 0.25
Nodes (7): Arkitektur, Funktioner, Hugging Face-token (aktiverar tutorn), Installation, Juridisk översiktskurs – fallbaserad övningsapp, Skärmbilder, Utveckling

### Community 81 - "Reference Chips"
Cohesion: 0.25
Nodes (8): _lagrum_chips(), Bygg chipsrad för ett begrepps lagrum (guld = lagrum, alltid klickbar)., test_lagen_nu_url_kapitellag(), test_lagen_nu_url_med_fullt_lagnamn_ar_samma_som_forkortning(), test_lagen_nu_url_okand_lag_ar_none(), test_lagen_nu_url_paragraflag(), lagen_nu_url(), Bygg en djuplänk till lagen.nu, eller None om lagen är okänd.

### Community 82 - "Structure Validation"
Cohesion: 0.32
Nodes (8): Momentet sträcker sig utanför avsnittet -- korpusen kunde aldrig se detta., Avsnittet påstår paragrafer som inte finns i lagen., _struktur(), test_for_snav_grans_upptacks(), test_ingen_avvikelse_nar_gransen_stammer(), test_overskjutande_grans_upptacks(), Kapitel, Ett kapitel i lagen med sin egen rubrik och sina paragrafer.

### Community 83 - "System Components"
Cohesion: 0.29
Nodes (7): 11. Tvärgående system, Export, Granskningen — sista ledet före studenten, Lagrumsgarden — vad den faktiskt intygar, Lagtextkorpusen — vad modellen läser i stället för att minnas, Persistens — den viktigaste begränsningen, Tutorn

### Community 84 - "Components and Tutors"
Cohesion: 0.29
Nodes (7): 5. Komponenter, Aviseringar och tutor, Kort och behållare, Navigering och ram, Quiz och lagrumsjakt, RNTS-formuläret — appens viktigaste yta, Övrigt

### Community 85 - "Visual Design"
Cohesion: 0.29
Nodes (7): 6. Visuell design, Färg, Ikoner, Kort, radier och skuggor, Mikrointeraktioner och animationer, Spacing, Typografi

### Community 86 - "Whitelist"
Cohesion: 0.29
Nodes (7): test_vitlista_fokuserad_utesluter_orelevanta_lagar(), test_vitlista_hel_innehaller_kanda_lagar(), test_vitlista_okand_forkortning_faller_tillbaka_pa_hela(), _lag_vitlisterad(), Formatera en lag till en rad i LAGRUMSVITLISTAN., Bygg LAGRUMSVITLISTAN ur registret. Om ``forkortningar`` anges tas endast dessa…, vitlista_block()

### Community 87 - "CSS"
Cohesion: 0.29
Nodes (7): _css(), Plocka ut CSS-mallen ur utils.css utan att köra Streamlit. CSS_MALL flyttades…, font-size ska referera en token, aldrig ett px-tal. Tokendeklarationerna i…, Appen kör layout="wide" och behållaren ska INTE begränsas i CSS. En centrerad,…, test_alla_tokens_ar_deklarerade(), test_inga_hardkodade_typstorlekar(), test_ingen_global_breddgrans_pa_huvudkolumnen()

### Community 88 - "Measurement Results"
Cohesion: 0.33
Nodes (6): 12. Mätresultat, 2026-07-21, Begreppsfördjupningen, Fallgranskningen, före och efter facitinjektion, Granskningen, skarp körning, Qwen3-8B mot Qwen3-14B, Rendering

### Community 89 - "Legal Types"
Cohesion: 0.33
Nodes (5): Avtalsrätt: sju avtalstyper i Rättskartan Implementation Plan, Global Constraints, Task 1: Fastighetsköp och -hyra kopplas till avtalsrätten (JB delas i tre noder), Task 2: Transportavtal, leasing och licensavtal som lagfria kartnoder, Task 3: Dokumentation och full verifiering

### Community 90 - "Validation"
Cohesion: 0.33
Nodes (6): parametrize, En lag utan kapitelindelning får aldrig verifieras med ett kapitel.…, test_extrahera_alias_skiftlagesokansligt(), test_extrahera_kant_alias_normaliseras_till_forkortning(), test_validera_avvisar_kapitel_pa_lag_utan_kapitel(), test_validera_verifierad_oavsett_skiftlage()

### Community 91 - "Taxonomy Graph Logic"
Cohesion: 0.60
Nodes (5): attlingar(), beraknaSkikt(), byggBarnkarta(), byggForalderkarta(), forfader()

### Community 92 - "Visualization"
Cohesion: 0.40
Nodes (5): 10. Visualiseringar — vad som ritas, och varför, Färgspråket bär betydelse, Interaktiva grafer (vis-network), Statusindikatorer och kort, Vad som inte finns

### Community 93 - "Legal Map Page"
Cohesion: 0.40
Nodes (5): 9. `16_Rattskartan` — kursens orienteringssida, Begränsningar, Flik 1 — Systemet, Flik 2 — Falltypsguide, Flik 3 — Nyckelbegrepp

### Community 94 - "Summary"
Cohesion: 0.40
Nodes (5): 1. Sammanfattning, Främsta styrkor, Främsta svagheter, Helhetsbedömning, Största möjligheterna

### Community 95 - "Prioritized Plan"
Cohesion: 0.40
Nodes (5): 9. Prioriterad plan, Framtida idéer, Hög effekt / låg insats, Hög effekt / medelinsats, Hög effekt / stor insats

### Community 96 - "Taxonomy Graph"
Cohesion: 0.80
Nodes (4): aterstall(), fokusera(), markeraKedjan(), satOpacitet()

### Community 97 - "Ordlista"
Cohesion: 0.50
Nodes (4): 13. Ordlista — termer i appen och i koden, Juridiska termer studenten möter, Pedagogiska begrepp, Termer i koden

### Community 98 - "Homepage"
Cohesion: 0.50
Nodes (4): 5. `0_Hem` — landningssidan, Begränsningar, Framstegssektionen, Vad du ser

### Community 99 - "Knowledge Map"
Cohesion: 0.50
Nodes (4): 7. `10_Kunskapskarta` — din egen graf, Begränsningar, Under huven, Vad du ser

### Community 100 - "8. `11_Kunskapsutmaning` — genererat rättsfall"
Cohesion: 0.50
Nodes (4): 8. `11_Kunskapsutmaning` — genererat rättsfall, Begränsningar, Steg för steg, Under huven

### Community 101 - "12. Ändringar i `design_system.md`"
Cohesion: 0.50
Nodes (4): 12. Ändringar i `design_system.md`, Avvisat ur uppdragsbeskrivningen, med skäl, Behålls oförändrat, Ändras

### Community 102 - "2. Informationsarkitektur"
Cohesion: 0.50
Nodes (4): 2. Informationsarkitektur, Nuvarande arkitektur, Problem, Rekommenderad arkitektur

### Community 103 - "3. Startsidan"
Cohesion: 0.50
Nodes (4): 3. Startsidan, Ny startsida, uppifrån och ner, Vad som är fel i dag, Vad studenten kan besvara på tio sekunder

### Community 104 - "_rendera_begrepp"
Cohesion: 0.50
Nodes (4): Rendera ett begreppskort med korslänkar och valfri LLM-fördjupning. LLM-lagret…, _rendera_begrepp(), Begreppskort med de fyra fasta fälten. Igenkänningsfältet får guldstreckad ram…, render_begreppskort()

### Community 105 - "conftest.py"
Cohesion: 0.50
Nodes (3): _isolera_streamlit_secrets(), fixture, Delade pytest-fixturer. Streamlit läser .streamlit/secrets.toml första gången…

### Community 106 - "taxonomigraf_logik.test.mjs"
Cohesion: 0.50
Nodes (3): { beraknaSkikt }, kod, NODER

### Community 107 - "14. Styrkor och svagheter"
Cohesion: 0.67
Nodes (3): 14. Styrkor och svagheter, Styrkor, Svagheter

### Community 108 - "4. Sidopanelen"
Cohesion: 0.67
Nodes (3): 4. Sidopanelen, Bedömning av det som finns, Ny sidopanel

## Knowledge Gaps
- **308 isolated node(s):** `Begränsningar`, `Steg för steg`, `Under huven`, `Avvisat ur uppdragsbeskrivningen, med skäl`, `Behålls oförändrat` (+303 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `lagrum_register()` connect `Register Section Grouping` to `Graph Structure Tests`, `Taxonomy Rendering`, `Legal System Graph`, `Key Concepts Testing`, `Concept Section Validation`, `Legal System Loading`, `Course Section Check`, `Legal Section Extraction`, `Legal Structure Parsing`, `Prompt Generation`, `Reference Validation`, `Section Validation`, `Section Key Expansion`, `Legal Text Corpus`, `Legal Case Example`, `Legal Text Corpus`, `Alias Mapping`, `Reference Verification`, `Alias Validation`, `Reference Chips`, `Whitelist`, `test_register_laddas_med_21_lagar`, `test_inget_kursavsnitt_ar_overifierat`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `validera_lagrum()` connect `Section Validation` to `Graph Structure Tests`, `Reference Validation`, `Scenario Validation`, `Key Concepts Testing`, `Case Generation`, `Register Section Grouping`, `Legal Section Extraction`, `Scenario Generation`, `Quiz Grading`, `Reference Chips`, `modulvy.py`, `Legal Reference Check`, `Quiz Question Validation`, `Validation`, `Reference Verification`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `ladda_begrepp()` connect `Key Concepts Testing` to `Legal Map Page Rendering`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **What connects `Begränsningar`, `Steg för steg`, `Under huven` to the rest of the system?**
  _308 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Graph Structure Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.05339506172839506 - nodes in this community are weakly interconnected._
- **Should `Taxonomy Rendering` be split into smaller, more focused modules?**
  _Cohesion score 0.04072565716401333 - nodes in this community are weakly interconnected._
- **Should `Navigation Tree Tests` be split into smaller, more focused modules?**
  _Cohesion score 0.051106639839034206 - nodes in this community are weakly interconnected._