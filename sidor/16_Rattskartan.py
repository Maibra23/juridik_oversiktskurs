"""Global sida: Rättskartan.

Kursens orienteringssida. Till skillnad från Kunskapskartan, som växer med
studentens egna rättsfall, är den här sidan full redan på dag noll och
fungerar helt utan LLM och utan genomförda övningar.

Tre flikar:

1. **Systemet**: hela taxonomin över svensk rätt som interaktiv graf
   (utils.rattssystem_graf + utils.taxonomi_ui), följd av områdesträdet som
   hopfällbara expanders med ett kort per lag.
2. **Falltypsguide**: sökbar tabell över vilken lag som gäller för vilken
   typ av fall.
3. **Nyckelbegrepp**: kursens begreppsbank (data/nyckelbegrepp.json) med
   fyra fasta fält per begrepp, plus en valfri LLM-fördjupning.

Grunddatan i alla tre flikarna är deterministisk och verifierad mot
lagrumsregistret. LLM används endast bakom knappen "Förklara djupare".
"""

from __future__ import annotations

import streamlit as st

from utils.kraftgraf_ui import render_kraftgraf
from utils.lagkort_avsnitt import gruppera_kursavsnitt, tackningstext
from utils.lagrum import (
    STATUS_VERIFIERAD,
    lagen_nu_url,
    lagrum_register,
    validera_lagrum,
)
from utils.nyckelbegrepp import begrepp_per_omrade, ladda_begrepp, sok_begrepp
from utils.prompts import LAS_FORDJUPNING, LAS_OVNING, build_begrepp_prompt
from utils.rattskarta import delomraden, delomraden_med_vag, falltypsguide
from utils.rattssystem_graf import bygg_taxonomigraf, gren_id
from utils.taxonomi_ui import render_farglegend, render_taxonomigraf
from utils.tutor import tutorknapp
from utils.ui import (
    footer_note,
    hero,
    render_begreppskort,
    render_info,
    render_lagkort,
    render_lagrum_chip,
    render_sidhjalp,
    section_heading,
)

# Kartans två vyer. Kraftvyn är standard: den visar hela systemet på en gång
# och bär sökruta, grenfilter och infopanel. Trädvyn finns kvar för den som
# vill läsa systematiken strikt ovanifrån, med kedjan upp mot roten.
VY_KRAFT = "Kraftvy"
VY_TRAD = "Trädvy"

st.html(
    hero(
        eyebrow="RÄTTSKARTAN",
        title="Så är svensk rätt uppdelad",
        lead=(
            "En karta över rättssystemet: vilka områden som finns, vilka lagar "
            "som bär varje område, när de ska övervägas och vilka begrepp du "
            "måste kunna. Kartan är fullständig från början och kräver varken "
            "tutor eller genomförda övningar."
        ),
    )
)

render_sidhjalp(
    (
        "**Systemet** visar hela indelningen som en graf, i två vyer. I "
        "**kraftvyn** ringas varje toppgren in: klicka på en nod för att se "
        "vad den är och vad den hänger samman med, och dubbelklicka på en "
        "guldfärgad lagnod för att öppna lagen på lagen.nu. I **trädvyn** "
        "räcker ett klick på lagnoden för att öppna lagen.",
        "Under grafen kan du fälla ut varje rättsområde och läsa vad varje "
        "lag täcker och när den blir aktuell.",
        "**Falltypsguide** svarar på frågan \"vilken lag gäller för mitt "
        "fall?\". Sök på situationen du har framför dig.",
        "**Nyckelbegrepp** samlar de begrepp du måste kunna, med definition, "
        "exempel och de signalord som avslöjar begreppet i ett scenario.",
        "Allt på sidan är verifierat mot kursens lagrumslista. Endast "
        "knappen \"Förklara djupare\" använder tutorn.",
    )
)

# Ingen sidövergripande återställning här: den knappen låg ovanför flikraden
# och tömde sökrutor som hör hemma i två andra flikar, så på fliken Systemet
# såg den ut att inte göra någonting. Varje flik rensar nu sina egna filter,
# och kartans vy återställs i grafen med knappen i dess övre högra hörn.
flik_system, flik_falltyp, flik_begrepp = st.tabs(
    ["Systemet", "Falltypsguide", "Nyckelbegrepp"]
)


# --- Flik 1: Systemet -------------------------------------------------------

with flik_system:
    st.html(section_heading("ÖVERSIKT", "Rättssystemets indelning"))
    st.markdown(
        "Svensk rätt delas i **offentlig rätt** (mellan enskild och det "
        "allmänna, däribland straffrätten och processrätten) och **civilrätt** "
        "(mellan enskilda). Civilrätten delas i sin tur i förmögenhetsrätt "
        "(obligationsrätt och sakrätt), familjerätt, associationsrätt och "
        "fastighetsrätt. Grafen följer den doktrinära systematiken."
    )

    visa_referens = st.checkbox(
        "Visa även referenslagar (hela svensk rätt i överblick)",
        value=True,
        help=(
            "Referenslagar är klickbara översiktsnoder utanför kursen — t.ex. "
            "grundlagarna, förvaltnings- och skatterätten samt EU-rätten. "
            "Avmarkera för en ren kurskarta med bara de lagar kursen rättar mot."
        ),
    )

    vy = st.radio(
        "Kartans vy",
        options=(VY_KRAFT, VY_TRAD),
        horizontal=True,
        help=(
            f"**{VY_KRAFT}** låter en fysiksimulering placera noderna och "
            "ringar in varje toppgren, med sökruta, grenfilter och infopanel "
            f"vid sidan. **{VY_TRAD}** visar samma karta som ett strikt träd "
            "ovanifrån, där en klickad gren tänder kedjan upp mot roten."
        ),
    )

    kurs_graf = bygg_taxonomigraf(inkludera_referens=visa_referens)
    if vy == VY_KRAFT:
        render_kraftgraf(kurs_graf)
    else:
        render_taxonomigraf(kurs_graf)
    render_farglegend()

    st.html(section_heading("OMRÅDEN", "Rättsområden och deras lagar"))
    st.caption(
        "Fäll ut ett delområde för att se var i systematiken det hör hemma, "
        "vilka lagar som bär det och när de ska övervägas."
    )

    # Listan speglar grafen exakt: i ren kursvy visas bara de delområden som
    # överlever grafens städning (grenar med kurslag i underträdet).
    synliga_grenar = {n["id"] for n in kurs_graf["noder"]}

    register = lagrum_register()
    for vag, lov in delomraden_med_vag():
        if gren_id(lov.id) not in synliga_grenar:
            continue
        lagar = lov.lagar
        if not visa_referens:
            lagar = tuple(lag for lag in lagar if not lag.ar_referens)
        etikett = " · ".join((*vag, lov.namn))
        with st.expander(etikett, expanded=False):
            st.markdown(lov.beskrivning)
            if lov.nar:
                st.markdown(f"**När hamnar ett fall här?** {lov.nar}")

            if not lagar:
                st.caption(
                    "Inga lagar ur kursens lagrumslista i detta delområde."
                )
            for lag in lagar:
                if lag.ar_referens:
                    st.html(
                        render_lagkort(
                            forkortning=lag.forkortning,
                            namn=lag.namn,
                            sfs=lag.sfs or "",
                            beskrivning=lag.beskrivning,
                            nar=lag.nar,
                            url=lag.url,
                            tackning="Referenslag för överblick – utanför kursens lagrumslista.",
                        )
                    )
                    continue
                info = register[lag.forkortning]
                st.html(
                    render_lagkort(
                        forkortning=lag.forkortning,
                        namn=info.namn,
                        sfs=info.sfs,
                        beskrivning=lag.beskrivning,
                        nar=lag.nar,
                        url=info.lagen_nu_bas_url,
                        kursavsnitt=gruppera_kursavsnitt(info),
                        tackning=tackningstext(info),
                    )
                )


# --- Flik 2: Falltypsguide --------------------------------------------------

with flik_falltyp:
    st.html(section_heading("FALLTYPSGUIDE", "Vilken lag gäller för mitt fall?"))
    st.caption(
        "Sök på situationen du har framför dig, till exempel \"uppsagd\", "
        "\"fel\" eller \"arv\". Fler än en lag kan vara tillämplig samtidigt."
    )

    fras = st.text_input(
        "Sök situation eller lag",
        key="falltyp_sok",
        placeholder="T.ex. uppsagd, fastighet, konkurs, testamente",
        help="Filtrerar tabellen på både situationsbeskrivningen och lagens "
        "förkortning.",
    )

    # Rensar bara den här flikens sökruta. Kartans vy återställs i grafen,
    # med knappen i dess övre högra hörn.
    if st.button("Rensa sökningen", help="Töm sökrutan ovan."):
        st.session_state.pop("falltyp_sok", None)
        st.rerun()

    guide = falltypsguide()
    q = (fras or "").strip().lower()
    rader = [
        {"Situationen": situation, "Börja här": lag}
        for situation, lag, sokord in guide
        if not q
        or q in situation.lower()
        or q in lag.lower()
        or q in sokord
    ]

    if rader:
        st.dataframe(
            rader,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Situationen": st.column_config.TextColumn(width="large"),
                "Börja här": st.column_config.TextColumn(width="small"),
            },
        )
        st.caption(f"{len(rader)} av {len(guide)} falltyper visas.")
    else:
        render_info(
            "Ingen falltyp matchade din sökning. Prova ett bredare ord, eller "
            "töm sökrutan för att se hela guiden."
        )

    render_info(
        "Ett avskedande kan väcka både LAS-frågor och skadeståndsfrågor "
        "enligt SkL. Fastna inte vid en enda lag: kontrollera alltid om "
        "flera regelverk är tillämpliga samtidigt."
    )


# --- Flik 3: Nyckelbegrepp --------------------------------------------------


def _lagrum_chips(refs: tuple[str, ...]) -> str:
    """Bygg chipsrad för ett begrepps lagrum (guld = lagrum, alltid klickbar)."""
    chips = []
    for ref in refs:
        verifierad = validera_lagrum(ref) == STATUS_VERIFIERAD
        chips.append(
            render_lagrum_chip(
                ref=ref,
                url=lagen_nu_url(ref) if verifierad else None,
                verifierad=verifierad,
            )
        )
    return '<div class="jok-pipeline">' + "".join(chips) + "</div>" if chips else ""


def _rendera_begrepp(b, namn_for: dict[str, str]) -> None:
    """Rendera ett begreppskort med korslänkar och valfri LLM-fördjupning.

    LLM-lagret ligger i en popover, inte i en expander: kortet visas inuti
    en områdesexpander och Streamlit tillåter inte nästlade expanders.
    """
    st.html(
        render_begreppskort(
            term=b.term,
            kapitel=b.kapitel,
            definition=b.definition,
            forklaring=b.forklaring,
            exempel=b.exempel,
            igenkanning=b.igenkanning,
            skillnaden=b.skillnaden,
            lagrum_chips=_lagrum_chips(b.lagrum),
        )
    )

    kol_modul, kol_djupare = st.columns([1, 1])
    with kol_modul:
        if b.modul_sida:
            st.page_link(b.modul_sida, label="Öva i modulen →")
    with kol_djupare:
        # LLM-lagret ligger på topp och ersätter aldrig grunddatan ovan.
        with st.popover("Förklara djupare med tutorn", use_container_width=True):
            st.caption(
                "Tutorn bygger vidare på texten ovan. Grunddatan står kvar "
                "oförändrad och alla lagrum i svaret kontrolleras mot "
                "kursens lagrumslista."
            )
            las = st.radio(
                "Vad vill du ha?",
                options=(LAS_FORDJUPNING, LAS_OVNING),
                format_func=lambda v: (
                    "Längre förklaring"
                    if v == LAS_FORDJUPNING
                    else "Ett övningsscenario att lösa"
                ),
                key=f"begrepp_las_{b.id}",
            )
            system_prompt, user_prompt = build_begrepp_prompt(b, las=las)
            tutorknapp(
                nyckel=f"begrepp_{b.id}_{las}",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                etikett="Förklara djupare",
                knappnyckel=f"begrepp_knapp_{b.id}_{las}",
                underlag=b.lagrum,
                reservhanvisning="Begreppets grunddata står kvar ovan.",
            )

    if b.se_aven:
        relaterade = ", ".join(namn_for.get(r, r) for r in b.se_aven)
        st.caption(f"Se även: {relaterade}")

    st.divider()


with flik_begrepp:
    st.html(section_heading("NYCKELBEGREPP", "Begrepp du måste kunna"))
    st.caption(
        "Varje begrepp visas med definition, varför det spelar roll, ett "
        "konkret exempel och de signalord som avslöjar det i ett scenario. "
        "Grunddatan är verifierad mot kursens lagrumslista."
    )

    alla_begrepp = ladda_begrepp()
    per_omrade = begrepp_per_omrade()

    # Namnkarta delområdes-id -> visningsnamn för rubrikerna.
    omradesnamn = {lov.id: lov.namn for lov in delomraden()}

    kol_sok, kol_omrade = st.columns([2, 2])
    with kol_sok:
        sokfras = st.text_input(
            "Sök begrepp",
            key="begrepp_sok",
            placeholder="T.ex. uppsåt, fullmakt, bodelning",
            help="Söker i term, definition, signalord och lagrum.",
        )
    with kol_omrade:
        omraden = ["Alla områden"] + [
            omradesnamn.get(oid, oid) for oid in per_omrade
        ]
        valt_omrade = st.selectbox(
            "Rättsområde",
            options=omraden,
            key="begrepp_omrade",
            help="Begränsa till ett delområde.",
        )

    if st.button("Rensa filtren", help="Töm sökrutan och områdesfiltret."):
        for _nyckel in ("begrepp_sok", "begrepp_omrade"):
            st.session_state.pop(_nyckel, None)
        st.rerun()

    traffar = sok_begrepp(sokfras)
    if valt_omrade != "Alla områden":
        traffar = tuple(
            b for b in traffar if omradesnamn.get(b.omrade_id) == valt_omrade
        )

    if not traffar:
        render_info(
            "Inget begrepp matchade din sökning. Prova ett bredare ord, eller "
            "töm sökrutan för att bläddra bland alla begrepp."
        )
    else:
        # Aktiv sökning eller områdesfilter fäller ut träffarna direkt.
        # Utan filter visas områdena hopfällda: 52 begreppskort på rad vore
        # en vägg av text, och kapitelindelningen är själva orienteringen.
        filtrerar = bool((sokfras or "").strip()) or valt_omrade != "Alla områden"
        st.caption(
            f"Visar {len(traffar)} av {len(alla_begrepp)} begrepp."
            + ("" if filtrerar else " Fäll ut ett område för att läsa begreppen.")
        )

        # Gruppera träffarna per delområde, i kartans ordning.
        for oid, namn in omradesnamn.items():
            i_omrade = [b for b in traffar if b.omrade_id == oid]
            if not i_omrade:
                continue

            namn_for = {x.id: x.term for x in alla_begrepp}
            etikett = f"{namn} · {len(i_omrade)} begrepp"
            with st.expander(etikett, expanded=filtrerar):
                for b in i_omrade:
                    _rendera_begrepp(b, namn_for)

st.html(footer_note())
