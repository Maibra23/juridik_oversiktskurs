"""Appens CSS-mall, utbruten ur utils/ui.py för att hålla den filen under
radtaket i implementationsplanen (planens Global Constraints, 800 rader).

CSS_MALL är en formatbar sträng: `{BLACK}`-liknande platshållare fylls i av
inject_css() i utils/ui.py, som äger paletten och anropar `.format(...)` på
konstanten innan den injiceras med st.html. Denna modul har inget eget
Streamlit-beroende och innehåller ingen logik, bara mallen.
"""

from __future__ import annotations

CSS_MALL = """
        <style>
        :root {{
            --bl: {BLACK}; --perg: {PARCHMENT}; --panel: {PANEL};
            --ram: {BORDER}; --bla: {BLUE}; --guld: {GOLD};
            --gron: {GREEN}; --varn-fg: {WARN_FG}; --varn-bg: {WARN_BG};
            --varn-mork: {WARN_DARK}; --fel: {ERROR};

            /* Typskala (design_system.md 2.1). Sex steg, en roll var. */
            --t-hero: 28px;     /* sidrubrik, en per sida */
            --t-h2: 22px;       /* avsnittsrubrik */
            --t-h3: 18px;       /* kortrubrik */
            --t-brod: 17px;     /* brödtext, scenarier */
            --t-ui: 15px;       /* kontroller, kortmetadata */
            --t-etikett: 13px;  /* kapitäler, chips, metadata */

            /* Spacingskala, 4px-bas (design_system.md 2.2). Regeln: avstånd
               INOM en grupp är alltid mindre än avstånd MELLAN grupper. */
            --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px;
            --s5: 24px; --s6: 32px; --s7: 48px;
        }}
        .jok-hero {{
            max-width: 46rem; margin: 0 0 1.5rem 0;
        }}
        .jok-hero .eyebrow {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: var(--t-etikett);
            letter-spacing: .12em; color: var(--bla); text-transform: uppercase;
        }}
        .jok-hero h1 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif; color: var(--bl);
            font-size: var(--t-hero); line-height: 1.2; margin: .3rem 0 .6rem 0;
        }}
        .jok-hero p {{
            font-size: var(--t-brod); line-height: 1.65; color: var(--bl); margin: 0;
        }}
        .jok-section {{ margin: 1.8rem 0 .6rem 0; }}
        .jok-section .eyebrow {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: var(--t-etikett);
            letter-spacing: .12em; color: var(--bla); text-transform: uppercase;
        }}
        .jok-section h2 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif; color: var(--bl);
            font-size: var(--t-h2); margin: .2rem 0 0 0;
        }}
        .jok-summary {{
            max-width: 46rem; font-size: var(--t-brod); line-height: 1.65;
            color: var(--bl); margin: .5rem 0 1rem 0;
        }}
        .jok-kort {{
            background: var(--panel); border: 1px solid var(--ram);
            border-radius: 12px; padding: 1.1rem 1.3rem; margin: .6rem 0;
            box-shadow: 0 1px 3px rgba(26,35,50,.06);
        }}
        .jok-kort h3 {{
            font-family: Georgia, serif; color: var(--bl); font-size: var(--t-h3);
            margin: 0 0 .4rem 0;
        }}
        .jok-pipeline {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: .5rem 0; }}
        .jok-pipeline span {{
            background: var(--panel); border: 1px solid var(--ram);
            border-radius: 999px; padding: .35rem .9rem; font-size: var(--t-etikett);
        }}
        .jok-chip {{
            display: inline-flex; align-items: center; gap: .3rem;
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: var(--t-etikett);
            border: 1px solid var(--guld); border-radius: 999px;
            padding: .15rem .6rem; color: var(--bl); text-decoration: none;
            background: #FFFDF7;
        }}
        .jok-chip.ovarifierad {{
            border-color: var(--varn-mork); background: var(--varn-bg);
        }}
        .jok-varning, .jok-info {{
            border-radius: 10px; padding: .8rem 1rem; margin: .6rem 0;
            font-size: var(--t-ui); line-height: 1.55; max-width: 46rem;
        }}
        .jok-varning {{ background: var(--varn-bg); border: 1px solid var(--varn-mork); color: var(--bl); }}
        .jok-info {{ background: #EAF1F7; border: 1px solid var(--bla); }}
        .jok-tutortext {{
            background: var(--panel); border: 1px solid var(--ram);
            border-left: 3px solid var(--bla); border-radius: 10px;
            padding: .9rem 1.2rem; margin: .6rem 0; max-width: 46rem;
            font-size: var(--t-brod); line-height: 1.6; color: var(--bl);
        }}
        .jok-tutortext p {{ margin: 0 0 .6rem 0; }}
        .jok-tutortext p:last-child {{ margin-bottom: 0; }}
        .jok-tutortext .rnts-rubrik {{
            font-variant: small-caps; letter-spacing: .05em;
            color: var(--bla); font-weight: 700;
        }}
        .jok-varning ul {{ margin: .4rem 0 .2rem 1.1rem; padding: 0; }}
        .jok-case {{
            background: var(--panel); border: 1px solid var(--ram);
            border-top: 3px solid var(--guld); border-radius: 12px;
            padding: 1.1rem 1.3rem; margin: .6rem 0; max-width: 46rem;
            box-shadow: 0 1px 3px rgba(26,35,50,.06);
        }}
        .jok-case h3 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif; color: var(--bl);
            font-size: var(--t-h3); margin: 0 0 .2rem 0;
        }}
        .jok-case .meta {{ font-size: var(--t-etikett); color: #6B6459; margin-bottom: .5rem; }}
        .jok-case p {{ font-size: var(--t-brod); line-height: 1.65; color: var(--bl); margin: 0; }}
        .jok-rnts {{ margin: .4rem 0 .8rem 0; }}
        .jok-rnts .steg {{
            display: flex; align-items: center; gap: .55rem;
            font-size: var(--t-etikett); color: var(--bl); padding: .22rem 0;
        }}
        .jok-rnts .ikon {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 1.25rem; height: 1.25rem; border-radius: 999px;
            font-size: var(--t-etikett); line-height: 1; flex: 0 0 auto;
            border: 2px solid var(--ram); background: var(--panel); color: transparent;
        }}
        .jok-rnts .steg.pagar .ikon {{
            border-color: var(--bla); background: var(--bla);
        }}
        .jok-rnts .steg.godkand .ikon {{
            border-color: var(--gron); background: var(--gron);
        }}
        /* Bocken ritas som två kanter roterade 45 grader, inte som en teckenglyf (U+2713). */
        .jok-rnts .steg.godkand .ikon::after {{
            content: ""; display: block; width: .3rem; height: .55rem;
            margin: .12rem auto 0 auto; transform: rotate(45deg);
            border-right: 2px solid #fff; border-bottom: 2px solid #fff;
        }}
        .jok-rnts .steg.behover-mer .ikon {{
            border-color: var(--varn-mork); background: var(--varn-bg);
        }}
        /* Utropstecknet som stapel och punkt, av samma skäl som bocken. */
        .jok-rnts .steg.behover-mer .ikon::after {{
            content: ""; display: block; width: 2px; height: .45rem;
            margin: .2rem auto 0 auto; background: var(--varn-mork);
            box-shadow: 0 .18rem 0 0 var(--varn-mork);
        }}
        .jok-status {{ font-size: var(--t-etikett); line-height: 1.5; }}
        .jok-status .rad {{ display: flex; justify-content: space-between; }}
        .jok-status .prick {{ font-weight: 600; }}

        /* Navigeringshierarki i sidopanelen (design_system.md 4.1).
           Nivåerna skiljs åt med indrag, storlek och färgstyrka, inte med
           ikoner: huvudkategori (versaler, blå) > underkategori (bläck)
           > undergren (grå) > modul (st.page_link). */
        .jok-nav-kategori {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
            font-size: var(--t-etikett); letter-spacing: .1em; text-transform: uppercase;
            color: var(--bla); font-weight: 700;
            margin: 1.1rem 0 .2rem 0;
        }}
        .jok-nav-under {{
            font-size: var(--t-etikett); font-weight: 600; color: var(--bl);
            margin: .5rem 0 .15rem 0;
        }}
        .jok-nav-gren {{
            font-size: var(--t-etikett); font-weight: 600; color: #6B6459;
            letter-spacing: .02em; margin: .4rem 0 .15rem .6rem;
        }}
        .jok-nav-kommer {{
            font-size: var(--t-etikett); color: #9A9384; margin: .1rem 0 .1rem .6rem;
        }}
        /* Förfäderna till den öppna sidan får full bläckvikt, så att studenten
           hittar sin plats i ett fyra nivåer djupt träd. Ingen färg, ingen
           ikon: guld är reserverat för lagrum. */
        .jok-nav-under.aktiv, .jok-nav-gren.aktiv {{
            color: var(--bl); font-weight: 700;
        }}
        .jok-nav-kategori.aktiv {{ color: var(--bl); }}
        /* Färglegend för taxonomigrafen: riktiga färgrutor, inte prosa. */
        .jok-legend {{
            display: flex; flex-wrap: wrap; gap: .5rem 1.1rem;
            margin: .6rem 0 1rem 0; font-size: var(--t-etikett); color: var(--bl);
        }}
        .jok-legend-post {{ display: inline-flex; align-items: center; gap: .4rem; }}
        .jok-swatch {{
            display: inline-block; width: .85rem; height: .85rem;
            border-radius: 3px; border: 1px solid rgba(26,35,50,.25);
            flex: 0 0 auto;
        }}

        /* Lagkort i områdesträdet (flik Systemet). */
        .jok-lagkort {{
            background: var(--panel); border: 1px solid var(--ram);
            border-left: 3px solid var(--guld); border-radius: 10px;
            padding: .8rem 1rem; margin: .5rem 0; max-width: 46rem;
        }}
        .jok-lagkort h4 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
            font-size: var(--t-h3); color: var(--bl); margin: 0 0 .1rem 0;
        }}
        .jok-lagkort .sfs {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
            font-size: var(--t-etikett); color: #6B6459;
        }}
        .jok-lagkort p {{ font-size: var(--t-ui); line-height: 1.55; margin: .45rem 0 0 0; }}
        .jok-lagkort .nar {{ font-size: var(--t-etikett); color: #4A453D; margin-top: .4rem; }}
        .jok-lagkort .nar strong {{ color: var(--bla); }}
        .jok-lagkort .avsnitt {{
            margin-top: .7rem; padding-top: .6rem;
            border-top: 1px solid rgba(107, 100, 89, .18);
        }}
        .jok-lagkort .avsnittsrubrik {{
            font-size: var(--t-etikett); letter-spacing: .08em; text-transform: uppercase;
            color: #6B6459; display: flex; justify-content: space-between;
            gap: 1rem; margin-bottom: .35rem;
        }}
        .jok-lagkort .tackning {{ text-transform: none; letter-spacing: 0; }}
        .jok-lagkort .kapitelrad {{
            font-size: var(--t-etikett); font-weight: 600; color: var(--bla);
            margin: .45rem 0 .2rem 0;
        }}
        .jok-lagkort .avsnittsrad {{
            display: flex; gap: .6rem; font-size: var(--t-etikett); line-height: 1.5;
            padding: .1rem 0 .1rem .6rem;
        }}
        .jok-lagkort .avsnittsrad .spann {{
            flex: 0 0 6.5rem; color: var(--guld); font-variant-numeric: tabular-nums;
            text-decoration: none; font-weight: 600;
        }}
        .jok-lagkort .avsnittsrad .spann:hover {{ text-decoration: underline; }}
        .jok-lagkort .avsnittstext {{ color: #4A453D; }}
        .jok-lagkort .avsnittsnot {{
            font-size: var(--t-etikett); color: #6B6459; margin-top: .5rem; font-style: italic;
        }}

        /* Begreppskort (flik Nyckelbegrepp). */
        .jok-begrepp {{
            background: var(--panel); border: 1px solid var(--ram);
            border-radius: 12px; padding: 1rem 1.2rem; margin: .5rem 0 .2rem 0;
            max-width: 46rem; box-shadow: 0 1px 3px rgba(26,35,50,.06);
        }}
        .jok-begrepp h3 {{
            font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
            font-size: var(--t-h3); color: var(--bl); margin: 0 0 .1rem 0;
        }}
        .jok-begrepp .kapitel {{
            font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
            font-size: var(--t-etikett); letter-spacing: .08em; text-transform: uppercase;
            color: var(--bla);
        }}
        .jok-begrepp .falt {{ margin: .7rem 0 0 0; }}
        .jok-begrepp .falt .etikett {{
            font-variant: small-caps; letter-spacing: .05em; font-weight: 700;
            color: var(--bla); font-size: var(--t-etikett); display: block;
            margin-bottom: .15rem;
        }}
        .jok-begrepp .falt p {{
            font-size: var(--t-brod); line-height: 1.6; color: var(--bl); margin: 0;
        }}
        /* Skillnadsraden för kontrastpar: en enda framhävd rad. */
        .jok-begrepp .skillnad {{
            background: #F5F1EA; border-left: 3px solid var(--bla);
            border-radius: 0 6px 6px 0; padding: .5rem .8rem; margin: .7rem 0 0 0;
            font-size: var(--t-ui); line-height: 1.5;
        }}
        .jok-begrepp .igenkanning {{
            background: #FFFDF7; border: 1px dashed var(--guld);
            border-radius: 8px; padding: .6rem .8rem; margin-top: .7rem;
        }}

        .jok-footer {{
            margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--ram);
            font-size: var(--t-etikett); color: #6B6459; max-width: 46rem;
        }}
        </style>
        """
