"""Promptbibliotek för juridiktutorn.

Alla prompts som används i appen ligger här. Varje byggarfunktion
returnerar en tupel (system_prompt, user_prompt). Ren Python: ingen
Streamlit, ingen LLM-klient. Ansvarar för:
- SYSTEM_PROMPT_BASE: roll, register, RNTS-struktur (Rättsfrågan, Norm,
  Tillämpning, Slutsats) och absoluta regler mot påhittade lagrum
- vitlista_block: bygger ett LAGRUMSBLOCK ur lagrumsregistret så att
  tutorn ENDAST får citera lagrum som anges i promptens vitlista
  (motsvarigheten till "hitta inte på tal" i ekonomistyrningrepot)
- build_case_prompt(scenario, studentens_svar): granska studentens egna
  RNTS-analys av ett rättsfall steg för steg
- build_quiz_prompt(fraga, valt_alternativ): förklara varför ett valt
  svarsalternativ är rätt eller fel

Systemprompten hålls modellagnostisk och på svenska. Den justeras mot
verkliga Qwen-svar i Dag 3 (uppgift 3.3).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from utils.lagrum import Lag, lagrum_register

# Maxlängd på tutorsvar. Injiceras i systemprompten och används av
# nedströms tester som en mjuk gräns.
MAX_SVARSLANGD_ORD = 400

# RNTS-rubrikerna i den ordning tutorn måste använda dem.
RNTS_RUBRIKER = ("Rättsfrågan", "Norm", "Tillämpning", "Slutsats")


SYSTEM_PROMPT_BASE = f"""Du är en svensk juridisk expert med över 30 års erfarenhet av att undervisa \
juridik på alla nivåer, från introduktionskurser till avancerad juristutbildning.
Du handleder just nu en student på Juridisk översiktskurs (JÖK).
Ditt uppdrag är att träna studenten i juridisk metod, inte att lösa uppgiften åt hen.

SPRÅK
- Skriv uteslutande på svenska juridisk facksvenska. Använd inga engelska ord.

STRUKTUR (obligatorisk)
Bygg alltid svaret med exakt dessa fyra rubriker, i denna ordning:
1. Rättsfrågan: vilken rättslig fråga som ska besvaras.
2. Norm: vilka lagrum som är tillämpliga.
3. Tillämpning: hur normen tillämpas på omständigheterna.
4. Slutsats: ett kort, motiverat svar på rättsfrågan.

ABSOLUT FÖRBUD MOT PÅHITT
- Du får ALDRIG hitta på lagar, paragrafer, kapitel eller rättsfall.
- Du får ENDAST hänvisa till lagrum som uttryckligen anges i LAGRUMSVITLISTAN
  i användarmeddelandet. Finns inte ett lagrum i vitlistan får du inte nämna det.
- Om du är osäker på exakt lagrum ska du skriva "jag är osäker på exakt lagrum"
  i stället för att gissa. Att gissa ett paragrafnummer är ett allvarligt fel.
- Hänvisa inte till rättsfall (t.ex. NJA) om de inte redan finns i underlaget.

LAGRUMSFORMAT (följ exakt, annars går verifieringen inte att göra)
- Skriv ALLTID paragrafnumret FÖRST och förkortningen SIST: "36 § AvtL".
  Skriv ALDRIG förkortningen först: "AvtL 36 §" är FEL.
- För kapitelindelade lagar: "N kap. M § FÖRK", t.ex. "2 kap. 1 § SkL"
  (ALDRIG "SkL 2 kap. 1 §").
- För intervall: "28–30 §§ AvtL" (paragrafnumren först, förkortningen sist).
- Använd endast de förkortningar som står i LAGRUMSVITLISTAN.

TUTORROLL (viktigast)
- Studentens eget svar bifogas. Bedöm det steg för steg mot RNTS-strukturen.
- Peka ut vad som är korrekt, vad som saknas och vad som är fel, men skriv
  INTE om hela lösningen åt studenten. Led hen till svaret i stället.
- Var konkret: hänvisa till vilket steg (Rättsfrågan/Norm/Tillämpning/Slutsats)
  som brister och varför.

LÄNGD
- Håll hela svaret under {MAX_SVARSLANGD_ORD} ord. Var koncis och pedagogisk.
"""


def _lag_vitlisterad(lag: Lag) -> str:
    """Formatera en lag till en rad i LAGRUMSVITLISTAN."""
    intervall = []
    for a in lag.kursavsnitt:
        if lag.kapitelindelad and a.kapitel is not None:
            intervall.append(f"{a.kapitel} kap. {a.paragraf_fran}–{a.paragraf_till} §§")
        else:
            intervall.append(f"{a.paragraf_fran}–{a.paragraf_till} §§")
    delar = "; ".join(intervall)
    return f"- {lag.forkortning} = {lag.namn} (SFS {lag.sfs}). Kursavsnitt: {delar}."


def vitlista_block(forkortningar: Iterable[str] | None = None) -> str:
    """Bygg LAGRUMSVITLISTAN ur registret.

    Om ``forkortningar`` anges tas endast dessa lagar med (fokuserad vitlista
    för ett visst scenario). Okända förkortningar hoppas tyst över. Utan
    argument tas hela registret med.
    """
    register = lagrum_register()
    if forkortningar is None:
        valda = list(register.values())
    else:
        # Bevara inmatningsordningen men ta bort dubbletter och okända lagar.
        sedda: set[str] = set()
        valda = []
        for fk in forkortningar:
            if fk in register and fk not in sedda:
                sedda.add(fk)
                valda.append(register[fk])

    if not valda:
        valda = list(register.values())

    rader = "\n".join(_lag_vitlisterad(lag) for lag in valda)
    return (
        "LAGRUMSVITLISTA (du får ENDAST hänvisa till lagrum i denna lista):\n"
        f"{rader}"
    )


def _forkortningar_ur(*refs: Iterable[str]) -> tuple[str, ...]:
    """Plocka ut lagförkortningen ur en samling lagrumsträngar.

    "2 kap. 1 § SkL" -> "SkL". Behåller ordningen, tar bort dubbletter.
    """
    ordnade: list[str] = []
    for grupp in refs:
        for ref in grupp:
            if not ref:
                continue
            fk = ref.split()[-1]
            if fk and fk not in ordnade:
                ordnade.append(fk)
    return tuple(ordnade)


def _formatera_studentsvar(studentens_svar: object) -> str:
    """Normalisera studentens RNTS-svar till en läsbar textblock.

    Accepterar antingen en mapping med RNTS-nycklar eller en färdig sträng.
    """
    if isinstance(studentens_svar, str):
        return studentens_svar.strip() or "(studenten har inte skrivit något svar)"

    if isinstance(studentens_svar, dict):
        nyckelkarta = {
            "rattsfragan": "Rättsfrågan",
            "norm": "Norm",
            "tillampning": "Tillämpning",
            "slutsats": "Slutsats",
        }
        rader = []
        for nyckel, rubrik in nyckelkarta.items():
            varde = str(studentens_svar.get(nyckel, "")).strip()
            rader.append(f"{rubrik}: {varde or '(tomt)'}")
        return "\n".join(rader)

    return str(studentens_svar)


def build_case_prompt(scenario: object, studentens_svar: object) -> tuple[str, str]:
    """Bygg (system, user) för granskning av en students RNTS-analys.

    ``scenario`` är ett Case-objekt (utils.scenarier) eller en dict med
    fälten scenariotext och facit. ``studentens_svar`` är en mapping med
    RNTS-nycklar eller en färdig text.
    """
    scenariotext = _hamta(scenario, "scenariotext")
    facit = _hamta(scenario, "facit")
    facit_lagrum = tuple(
        str(x) for x in cast("Iterable[object]", _hamta(facit, "lagrum", default=()))
    )
    rattsfraga = _hamta(facit, "rattsfraga", default="")

    vitlista = vitlista_block(_forkortningar_ur(facit_lagrum))
    student = _formatera_studentsvar(studentens_svar)

    user_prompt = (
        f"{vitlista}\n\n"
        "RÄTTSFALL:\n"
        f"{scenariotext}\n\n"
        f"RÄTTSFRÅGA (facit, till din vägledning): {rattsfraga}\n\n"
        "STUDENTENS EGET SVAR (RNTS):\n"
        f"{student}\n\n"
        "Granska studentens svar steg för steg enligt RNTS. Peka på vad som är "
        "rätt, vad som saknas och vad som bör förbättras. Skriv inte om hela "
        "lösningen. Led studenten vidare."
    )
    return SYSTEM_PROMPT_BASE, user_prompt


def build_quiz_prompt(fraga: object, valt_alternativ: object) -> tuple[str, str]:
    """Bygg (system, user) för förklaring av ett quizsvar.

    ``fraga`` är en Flervalsfraga (utils.scenarier) eller dict. ``valt_alternativ``
    är ett Alternativ-objekt, en dict eller en textsträng med studentens val.
    """
    fragetext = _hamta(fraga, "fraga", default=str(fraga))
    alternativ = cast("Iterable[object]", _hamta(fraga, "alternativ", default=()))

    valt_text = _hamta(valt_alternativ, "text", default=str(valt_alternativ))

    # Samla samtliga lagrum som förekommer i frågans alternativ för vitlistan.
    alt_lagrum = []
    alt_rader = []
    for a in alternativ:
        a_text = _hamta(a, "text", default="")
        a_lagrum = _hamta(a, "lagrum", default=None)
        if a_lagrum:
            alt_lagrum.append(str(a_lagrum))
        markor = "→ " if a_text == valt_text else "  "
        alt_rader.append(f"{markor}{a_text}")

    vitlista = vitlista_block(_forkortningar_ur(alt_lagrum))

    user_prompt = (
        f"{vitlista}\n\n"
        "FLERVALSFRÅGA:\n"
        f"{fragetext}\n\n"
        "SVARSALTERNATIV (studentens val markerat med →):\n"
        + "\n".join(alt_rader)
        + "\n\n"
        f"Studenten valde: {valt_text}\n\n"
        "Förklara kort om studentens val är rätt eller fel och varför, med "
        "hänvisning till rätt lagrum ur vitlistan. Följ RNTS-strukturen men "
        "håll det kort, detta är en flervalsfråga och inte ett fullt rättsfall."
    )
    return SYSTEM_PROMPT_BASE, user_prompt


def build_generate_prompt(
    modul_namn: str,
    forkortningar: Iterable[str] | None = None,
    striktare: bool = False,
    variation: int | None = None,
) -> tuple[str, str]:
    """Bygg (system, user) för att generera ett nytt fiktivt rättsfall.

    Modellen ombeds returnera ett JSON-scenario som ENDAST använder lagrum ur
    den bifogade vitlistan. ``striktare`` läggs på vid omförsök efter att ett
    genererat lagrum inte kunnat verifieras.

    ``variation`` är ett frö som gör varje förfrågan unik. Det behövs av två
    skäl: det ber modellen om ett annat scenario, och det gör prompten till en
    ny cachenyckel i utils.llm.cached_chat. Utan fröet returnerar cachen samma
    rättsfall vid varje knapptryck, eftersom prompten annars är identisk för
    en given modul.
    """
    vitlista = vitlista_block(forkortningar)

    variationsrad = ""
    if variation is not None:
        variationsrad = (
            f"\n\nVariationsfrö {variation}: hitta på ett scenario som tydligt "
            "skiljer sig från tidigare fall i samma modul. Variera parter, "
            "bransch, belopp och vilken tvistefråga som ställs på sin spets."
        )

    skarpning = ""
    if striktare:
        skarpning = (
            "\n\nVIKTIGT: Ditt förra försök innehöll ett lagrum som inte fanns i "
            "vitlistan eller hade fel paragrafnummer. Använd nu ENBART exakta "
            "lagrum ur vitlistan ovan. Dubbelkolla varje paragrafnummer."
        )

    user_prompt = (
        f"{vitlista}\n\n"
        f"Skapa ETT nytt, fiktivt och realistiskt rättsfall för modulen "
        f"\"{modul_namn}\" på JÖK-nivå. Fallet ska gå att lösa med juridisk metod "
        "och de lagrum som finns i vitlistan ovan.\n\n"
        "Svara med ENBART giltig JSON (ingen kod-markdown, ingen text runt om) "
        "enligt exakt detta schema:\n"
        "{\n"
        '  "id": "gen-<kort-slug>",\n'
        '  "rubrik": "<kort fallrubrik>",\n'
        '  "svarighetsgrad": "grund" | "medel" | "avancerad",\n'
        '  "uppskattad_tid_min": <heltal>,\n'
        '  "scenariotext": "<fiktiva omständigheter, 4-8 meningar>",\n'
        '  "facit": {\n'
        '    "rattsfraga": "<den rättsliga frågan>",\n'
        '    "lagrum": ["<lagrum i formatet N § FÖRK ur vitlistan>"],\n'
        '    "tillampningspunkter": ["<punkt>", "<punkt>"],\n'
        '    "slutsats": "<motiverad slutsats>"\n'
        "  }\n"
        "}\n\n"
        "Alla lagrum i facit.lagrum MÅSTE finnas i vitlistan och skrivas som "
        "\"N § FÖRK\" eller \"N kap. M § FÖRK\" (paragrafnummer först). Använd "
        "aldrig påhittade paragrafer." + variationsrad + skarpning
    )
    return SYSTEM_PROMPT_BASE, user_prompt


def _hamta(obj: object, namn: str, default: object = "") -> object:
    """Hämta ett attribut (dataclass) eller nyckel (dict) med gemensam åtkomst."""
    if isinstance(obj, dict):
        return obj.get(namn, default)
    return getattr(obj, namn, default)
