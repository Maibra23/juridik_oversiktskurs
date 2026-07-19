"""Delad modulsidevy: Rättsfall, Quiz och Lagrumsjakt.

Varje modulsida i pages/ är ett tunt skal som sätter st.set_page_config och
anropar rendera_modulsida(...). Själva innehållet – tre flikar med RNTS-
formulär, deterministiskt rättad quiz och lagrumsjakt – bor här så att alla
åtta moduler delar exakt samma flöde.

Verifieringsprincip: Normfältet och lagrumsjakten rättas deterministiskt med
utils.lagrum INNAN någon LLM alls anropas. Tutorn (utils.tutor) körs endast
på uttryckligt knapptryck och dess svar renderas med verifierade lagrumschips.
"""

from __future__ import annotations

import streamlit as st

from utils.lagrum import (
    STATUS_OKAND_LAG,
    STATUS_VERIFIERAD,
    extrahera_lagrum,
    lagen_nu_url,
    validera_lagrum,
)
from utils.export import registrera_case_genomford
from utils.obsidian import registrera_case_analys
from utils.prompts import build_case_prompt, build_quiz_prompt
from utils.quiz import (
    modulresultat,
    ratta_flervalsfraga,
    ratta_lagrumsjakt,
    registrera_mc_svar,
)
from utils.scenarier import Case, Flervalsfraga, Lagrumsjakt, Modulscenarier, ladda_modul
from utils.tutor import tutorknapp
from utils.ui import (
    RNTS_STATUS_BEHOVER_MER,
    RNTS_STATUS_EJ_PABORJAD,
    RNTS_STATUS_GODKAND,
    RNTS_STATUS_PAGAR,
    footer_note,
    hero,
    inject_css,
    render_case,
    render_lagrum_chip,
    render_rnts_steg,
    render_sidebar,
    render_varning,
)

RNTS_FALT = (
    ("rattsfragan", "Rättsfrågan", "Vilken rättslig fråga ska besvaras?"),
    ("norm", "Norm (ange lagrum)", "Vilka lagrum är tillämpliga? T.ex. 4 § AvtL"),
    ("tillampning", "Tillämpning", "Hur tillämpas normen på omständigheterna?"),
    ("slutsats", "Slutsats", "Vad blir svaret på rättsfrågan?"),
)


# --- Publik ingång ----------------------------------------------------------


def rendera_modulsida(filnamn: str, titel: str, undertitel: str = "") -> None:
    """Rendera en komplett modulsida från en scenariofil.

    ``filnamn`` är scenariofilens namn utan suffix, t.ex. "avtalsratt".
    ``titel``/``undertitel`` visas i sidhuvudet.
    """
    inject_css()
    render_sidebar(filnamn)

    st.html(hero(eyebrow=undertitel or "MODUL", title=titel, lead=_ingress(filnamn)))

    try:
        modul = ladda_modul(filnamn)
    except Exception as exc:  # noqa: BLE001 – vi vill visa ett vänligt fel i UI:t
        render_varning(
            f"Kunde inte läsa övningsinnehållet för modulen ({exc}). "
            "Kontrollera scenariofilen."
        )
        st.html(footer_note())
        return

    if not (modul.case or modul.flervalsfragor or modul.lagrumsjakt):
        render_varning(
            "Den här modulen har inget övningsinnehåll ännu. Kom tillbaka senare."
        )
        st.html(footer_note())
        return

    flik_case, flik_quiz, flik_jakt = st.tabs(["Rättsfall", "Quiz", "Lagrumsjakt"])
    with flik_case:
        _rendera_rattsfall(modul)
    with flik_quiz:
        _rendera_quiz(modul)
    with flik_jakt:
        _rendera_lagrumsjakt(modul)

    st.html(footer_note())


def _ingress(filnamn: str) -> str:
    return (
        "Läs scenariot, skriv din egen RNTS-analys och be tutorn granska den. "
        "Varje lagrum du och tutorn anger kontrolleras mot kursens lagrumslista."
    )


# --- Flik 1: Rättsfall (RNTS-formulär) --------------------------------------


def _rendera_rattsfall(modul: Modulscenarier) -> None:
    if not modul.case:
        st.info("Inga rättsfall i den här modulen ännu.")
        return

    rubriker = [c.rubrik for c in modul.case]
    val = st.selectbox("Välj rättsfall", options=rubriker, key=f"case_val_{modul.modul}")
    case = next(c for c in modul.case if c.rubrik == val)

    rendera_case_ovning(modul.modul, case)


def rendera_case_ovning(modul: str, case: Case) -> None:
    """Rendera ett rättsfall som RNTS-övning: kort, formulär, tutor och facit.

    Delas av modulsidorna och Kunskapsutmaningen (utils.generator) så att både
    kuraterade och genererade fall får exakt samma flöde och verifiering.
    ``modul`` är modulens visningsnamn (används för framsteg och Obsidianexport).
    """
    st.html(
        render_case(
            rubrik=case.rubrik,
            metadata=(
                f"Svårighetsgrad: {case.svarighetsgrad} · "
                f"ca {case.uppskattad_tid_min} min"
            ),
            scenariotext=case.scenariotext,
        )
    )

    # Stepper till vänster om formuläret på bred skärm (design_system.md 4).
    kol_stepper, kol_formular = st.columns([1, 3])
    with kol_formular:
        svar = _rnts_formular(case)
    with kol_stepper:
        st.html(render_rnts_steg(_rnts_statusar(svar)))

    # Ett rättsfall räknas som genomfört när hela RNTS-analysen är ifylld
    # (deterministiskt, ingen LLM krävs). Läses av framstegsvyn och exporten.
    if all((svar.get(nyckel) or "").strip() for nyckel, _e, _h in RNTS_FALT):
        registrera_case_genomford(modul, case.id)
        # Fånga hela analysen för Obsidianexporten (studentens RNTS-svar + facit).
        registrera_case_analys(modul, case, svar)

    st.caption(
        "Tutorn granskar din analys steg för steg – den skriver inte lösningen åt dig."
    )
    system_prompt, user_prompt = build_case_prompt(case, svar)
    tutorknapp(
        nyckel=f"case_{modul}_{case.id}",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        etikett="Be tutorn granska min analys",
    )

    with st.expander("Visa facit (utan tutor)"):
        _rendera_facit(case)


def _rnts_formular(case: Case) -> dict[str, str]:
    """Rita RNTS-fälten och returnera studentens svar som en dict."""
    svar: dict[str, str] = {}
    for nyckel, etikett, hjalp in RNTS_FALT:
        varde = st.text_area(
            etikett,
            key=f"rnts_{case.id}_{nyckel}",
            placeholder=hjalp,
            height=90,
        )
        svar[nyckel] = varde
        if nyckel == "norm":
            _norm_feedback(varde)
    return svar


def _rnts_statusar(svar: dict[str, str]) -> tuple[tuple[str, str], ...]:
    """Deterministisk status per RNTS-steg utifrån studentens ifyllda fält.

    Tomt fält = ej påbörjad, ifyllt = under arbete. Normfältet bedöms
    hårdare: alla lagrum verifierade = godkänd, annars behöver mer.
    """
    statusar = []
    for nyckel, etikett, _hjalp in RNTS_FALT:
        text = (svar.get(nyckel) or "").strip()
        if not text:
            status = RNTS_STATUS_EJ_PABORJAD
        elif nyckel == "norm":
            refs = extrahera_lagrum(text)
            alla_ok = bool(refs) and all(
                validera_lagrum(r) == STATUS_VERIFIERAD for r in refs
            )
            status = RNTS_STATUS_GODKAND if alla_ok else RNTS_STATUS_BEHOVER_MER
        else:
            status = RNTS_STATUS_PAGAR
        statusar.append((etikett, status))
    return tuple(statusar)


def _norm_feedback(norm_text: str) -> None:
    """Validera Normfältets lagrum direkt (grönt/gult) innan LLM anropas."""
    refs = extrahera_lagrum(norm_text or "")
    if not refs:
        if (norm_text or "").strip():
            render_varning(
                "Inget giltigt lagrum hittades i Normfältet. Skriv på formen "
                "\"4 § AvtL\" eller \"2 kap. 1 § SkL\"."
            )
        return

    chips = []
    ovarifierade = 0
    for ref in refs:
        status = validera_lagrum(ref)
        verifierad = status == STATUS_VERIFIERAD
        if not verifierad:
            ovarifierade += 1
        chips.append(
            render_lagrum_chip(
                ref=ref.ra,
                url=lagen_nu_url(ref) if verifierad else None,
                verifierad=verifierad,
            )
        )
    st.html('<div class="jok-pipeline">' + "".join(chips) + "</div>")
    if ovarifierade:
        render_varning(
            "Minst ett lagrum i Normfältet kunde inte verifieras mot kursens "
            "lagrumslista. Kontrollera det mot lagen.nu innan du bygger vidare."
        )


def _rendera_facit(case: Case) -> None:
    """Deterministisk RNTS-facit, helt utan LLM."""
    st.markdown(f"**Rättsfrågan.** {case.facit.rattsfraga}")

    st.markdown("**Norm.**")
    chips = []
    for ref in case.facit.lagrum:
        status = validera_lagrum(ref)
        verifierad = status == STATUS_VERIFIERAD
        chips.append(
            render_lagrum_chip(
                ref=ref,
                url=lagen_nu_url(ref) if verifierad else None,
                verifierad=verifierad,
            )
        )
    if chips:
        st.html('<div class="jok-pipeline">' + "".join(chips) + "</div>")

    st.markdown("**Tillämpning.**")
    for punkt in case.facit.tillampningspunkter:
        st.markdown(f"- {punkt}")

    st.markdown(f"**Slutsats.** {case.facit.slutsats}")


# --- Flik 2: Quiz -----------------------------------------------------------


def _rendera_quiz(modul: Modulscenarier) -> None:
    if not modul.flervalsfragor:
        st.info("Inga quizfrågor i den här modulen ännu.")
        return

    ratt, besvarade = modulresultat(modul.modul)
    st.markdown(f"**Resultat:** {ratt} rätt av {besvarade} besvarade.")
    st.divider()

    for i, fraga in enumerate(modul.flervalsfragor, 1):
        _rendera_quizfraga(modul.modul, i, fraga)
        st.divider()


def _rendera_quizfraga(modul: str, nr: int, fraga: Flervalsfraga) -> None:
    st.markdown(f"**Fråga {nr}.** {fraga.fraga}")
    alternativtexter = [a.text for a in fraga.alternativ]
    valt = st.radio(
        "Välj ett svar",
        options=list(range(len(fraga.alternativ))),
        format_func=lambda idx: alternativtexter[idx],
        index=None,
        key=f"quiz_val_{modul}_{fraga.id}",
        label_visibility="collapsed",
    )

    svara = st.button("Svara", key=f"quiz_svara_{modul}_{fraga.id}")
    if svara:
        if valt is None:
            st.warning("Välj ett alternativ först.")
        else:
            res = ratta_flervalsfraga(fraga, valt)
            registrera_mc_svar(modul, fraga.id, res.korrekt)
            st.session_state[f"quiz_klart_{modul}_{fraga.id}"] = True

    if st.session_state.get(f"quiz_klart_{modul}_{fraga.id}") and valt is not None:
        res = ratta_flervalsfraga(fraga, valt)
        alt = fraga.alternativ[valt]
        if res.korrekt:
            st.success(f"Rätt! {res.forklaring}")
        else:
            ratt_text = fraga.alternativ[res.ratt_index].text
            st.error(f"Inte riktigt. {res.forklaring}")
            st.caption(f"Rätt svar: {ratt_text}")
        if alt.lagrum:
            _lagrum_chip_rad(alt.lagrum)

        system_prompt, user_prompt = build_quiz_prompt(fraga, alt)
        tutorknapp(
            nyckel=f"quiz_{modul}_{fraga.id}",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            etikett="Förklara med tutorn",
            knappnyckel=f"quiz_forklara_{modul}_{fraga.id}",
        )


# --- Flik 3: Lagrumsjakt ----------------------------------------------------


def _rendera_lagrumsjakt(modul: Modulscenarier) -> None:
    if not modul.lagrumsjakt:
        st.info("Ingen lagrumsjakt i den här modulen ännu.")
        return

    st.caption(
        "Skriv vilket lagrum situationen handlar om. Rättningen är deterministisk "
        "och kräver ingen tutor."
    )
    for i, jakt in enumerate(modul.lagrumsjakt, 1):
        _rendera_jaktfraga(modul.modul, i, jakt)
        st.divider()


def _rendera_jaktfraga(modul: str, nr: int, jakt: Lagrumsjakt) -> None:
    st.markdown(f"**{nr}.** {jakt.situation}")
    svar = st.text_input(
        "Ditt lagrum",
        key=f"jakt_svar_{modul}_{jakt.id}",
        placeholder="T.ex. 4 § AvtL eller 2 kap. 1 § SkL",
    )
    if st.button("Rätta", key=f"jakt_ratta_{modul}_{jakt.id}"):
        res = ratta_lagrumsjakt(jakt, svar)
        if res.korrekt:
            st.success("Rätt lagrum!")
            for ref in res.traffade:
                _lagrum_chip_rad(ref)
        else:
            if res.status == STATUS_OKAND_LAG:
                st.error("Den lagen finns inte i kursens lagrumslista. Försök igen.")
            elif not svar.strip():
                st.warning("Skriv ett lagrum först.")
            else:
                st.error("Inte rätt lagrum ännu.")
            if jakt.ledtrad:
                st.caption(f"Ledtråd: {jakt.ledtrad}")
        with st.expander("Visa facit"):
            for ref in jakt.facit_lagrum:
                _lagrum_chip_rad(ref)


# --- Hjälpare ---------------------------------------------------------------


def _lagrum_chip_rad(ref: str) -> None:
    """Rendera ett enskilt lagrum som en (klickbar om verifierad) chip."""
    status = validera_lagrum(ref)
    verifierad = status == STATUS_VERIFIERAD
    st.html(
        render_lagrum_chip(
            ref=ref,
            url=lagen_nu_url(ref) if verifierad else None,
            verifierad=verifierad,
        )
    )


def _esc(text: str) -> str:
    import html

    return html.escape(text or "")
