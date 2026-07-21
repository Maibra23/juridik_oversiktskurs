"""Promptbibliotek för juridiktutorn.

Alla prompts som används i appen ligger här. Varje byggarfunktion
returnerar en tupel (system_prompt, user_prompt). Ren Python: ingen
Streamlit, ingen LLM-klient. Ansvarar för:
- SYSTEM_PROMPT_BASE: roll, register, RNTS-struktur (Rättsfrågan, Norm,
  Tillämpning, Slutsats) och absoluta regler mot påhittade lagrum
- SYSTEM_PROMPT_BEGREPP: samma källregler, men för begreppsförklaringar,
  som varken har ett studentsvar att bedöma eller ska följa RNTS. Båda
  sätts ihop av delade block, se "Systempromptens byggstenar" nedan
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

# Begreppsfördjupningar hålls kortare än fallgranskningar: de kompletterar
# en text studenten redan har framför sig.
MAX_BEGREPPSSVAR_ORD = 250

# Inriktning för build_begrepp_prompt.
LAS_FORDJUPNING = "fordjupning"   # längre förklaring av begreppet
LAS_OVNING = "ovning"             # färskt övningsscenario att träna RNTS på


# --- Systempromptens byggstenar --------------------------------------------
#
# Systemprompterna sätts ihop av block i stället för att skrivas ut i sin
# helhet per uppgift. Skälet är att KÄLLREGLERNA (rollen, förbudet mot påhitt
# och lagrumsformatet) måste vara ordagrant identiska överallt: det är de som
# gör utils.lagrum.verify_lagrum möjlig att lita på nedströms. Uppgiftsspecifika
# block (RNTS-strukturen, tutorrollen) varierar i stället per byggare.
#
# Regel vid ändring: rör aldrig källregelblocken för att lösa ett problem i en
# enskild uppgift. Lägg till ett uppgiftsblock i stället.

_ROLL = """Du är en svensk juridisk expert med över 30 års erfarenhet av att undervisa \
juridik på alla nivåer, från introduktionskurser till avancerad juristutbildning.
Du handleder just nu en student på Juridisk översiktskurs (JÖK).
Ditt uppdrag är att träna studenten i juridisk metod, inte att lösa uppgiften åt hen."""

_SPRAK = """SPRÅK
- Skriv uteslutande på svenska juridisk facksvenska. Använd inga engelska ord.
- Svara på svenska även om studentens svar är skrivet på ett annat språk.
- Använd endast vedertagna svenska juridiska termer. Översätt ALDRIG en
  utländsk term till något svenskliknande, och hitta aldrig på en term.
  Skriv "adekvat kausalitet", aldrig "proxim meningskausalitet"; skriv
  "oaktsamhet", aldrig "negligens".
- Är du osäker på den vedertagna termen: beskriv begreppet med vanliga ord
  i stället för att konstruera en term som ser juridisk ut."""

_STRUKTUR_RNTS = """STRUKTUR (obligatorisk)
Bygg alltid svaret med exakt dessa fyra rubriker, i denna ordning:
1. Rättsfrågan: vilken rättslig fråga som ska besvaras.
2. Norm: vilka lagrum som är tillämpliga.
3. Tillämpning: hur normen tillämpas på omständigheterna.
4. Slutsats: ett kort, motiverat svar på rättsfrågan."""

# KÄLLREGLERNA. Delas ordagrant av alla systemprompter. Ändra aldrig dessa två
# block för en enskild uppgifts skull: verifieringen av lagrum hänger på dem.
_FORBUD_MOT_PAHITT = """ABSOLUT FÖRBUD MOT PÅHITT
- Du får ALDRIG hitta på lagar, paragrafer, kapitel eller rättsfall.
- Du får ENDAST hänvisa till lagrum som uttryckligen anges i LAGRUMSVITLISTAN
  i användarmeddelandet. Finns inte ett lagrum i vitlistan får du inte nämna det.
- Om du är osäker på exakt lagrum ska du skriva "jag är osäker på exakt lagrum"
  i stället för att gissa. Att gissa ett paragrafnummer är ett allvarligt fel.
- Hänvisa inte till rättsfall (t.ex. NJA) om de inte redan finns i underlaget."""

_LAGRUMSFORMAT = """LAGRUMSFORMAT (följ exakt, annars går verifieringen inte att göra)
- Skriv ALLTID paragrafnumret FÖRST och förkortningen SIST: "36 § AvtL".
  Skriv ALDRIG förkortningen först: "AvtL 36 §" är FEL.
- För kapitelindelade lagar: "N kap. M § FÖRK", t.ex. "2 kap. 1 § SkL"
  (ALDRIG "SkL 2 kap. 1 §").
- För intervall: "28–30 §§ AvtL" (paragrafnumren först, förkortningen sist).
- Använd endast de förkortningar som står i LAGRUMSVITLISTAN."""

_TUTORROLL_FALL = """TUTORROLL (viktigast)
- Studentens eget svar bifogas. Bedöm det steg för steg mot RNTS-strukturen.
- Peka ut vad som är korrekt, vad som saknas och vad som är fel, men skriv
  INTE om hela lösningen åt studenten. Led hen till svaret i stället.
- Var konkret: hänvisa till vilket steg (Rättsfrågan/Norm/Tillämpning/Slutsats)
  som brister och varför."""

# Begreppsfördjupningens motsvarighet till _TUTORROLL_FALL. Här finns inget
# studentsvar att bedöma: studenten har den verifierade grunddatan framför sig
# och ber om en påbyggnad av den.
_TUTORROLL_BEGREPP = """UPPGIFTSROLL (viktigast)
- Detta är en begreppsförklaring, inte en fallanalys. Det finns inget
  studentsvar att bedöma, och du ska inte använda RNTS-rubrikerna.
- Begreppets verifierade grunddata bifogas i användarmeddelandet och visas för
  studenten bredvid ditt svar. Bygg vidare på den. Motsäg den aldrig, och
  upprepa den inte ordagrant.
- Skriv sammanhängande stycken. Förklara hellre ett gränsfall ordentligt än
  fem ytligt."""


def _langd_block(maxord: int) -> str:
    """Längdblocket, som är det enda som skiljer sig i ordgräns per uppgift."""
    return f"""LÄNGD
- Håll hela svaret under {maxord} ord. Var koncis och pedagogisk."""


def _bygg_systemprompt(*block: str) -> str:
    """Sätt ihop en systemprompt av block, separerade med en blankrad."""
    return "\n\n".join(block) + "\n"


# Fallgranskning, quiz och scenariogenerering: RNTS-struktur och ett bifogat
# studentsvar att bedöma.
SYSTEM_PROMPT_BASE = _bygg_systemprompt(
    _ROLL,
    _SPRAK,
    _STRUKTUR_RNTS,
    _FORBUD_MOT_PAHITT,
    _LAGRUMSFORMAT,
    _TUTORROLL_FALL,
    _langd_block(MAX_SVARSLANGD_ORD),
)

# Begreppsfördjupning: exakt samma källregler, men utan RNTS-kravet och utan
# antagandet om ett bifogat studentsvar.
SYSTEM_PROMPT_BEGREPP = _bygg_systemprompt(
    _ROLL,
    _SPRAK,
    _FORBUD_MOT_PAHITT,
    _LAGRUMSFORMAT,
    _TUTORROLL_BEGREPP,
    _langd_block(MAX_BEGREPPSSVAR_ORD),
)


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

    Hela facit injiceras som sanningsunderlag, inte bara rättsfrågan. Skälet
    är mätt: utan facit måste modellen härleda svensk rätt ur sina egna
    vikter, och en 8B-modell gör det dåligt. Med kursens lösning i prompten
    blir uppgiften jämförelse i stället för återgivning, vilket är avsevärt
    lättare. Mätt mot Qwen3-8B över fyra fall gick träffbilden från 2 av 9
    korrekta lagrum till 9 av 9, och modellen slutade intyga påhittade
    paragrafer som rätt norm.

    Facit är samtidigt en lösningsnyckel som studenten inte ska få. Prompten
    förbjuder därför uttryckligen att den nämns eller lämnas ut.
    """
    scenariotext = _hamta(scenario, "scenariotext")
    facit = _hamta(scenario, "facit")
    facit_lagrum = tuple(
        str(x) for x in cast("Iterable[object]", _hamta(facit, "lagrum", default=()))
    )
    rattsfraga = _hamta(facit, "rattsfraga", default="")
    punkter = tuple(
        str(x)
        for x in cast(
            "Iterable[object]", _hamta(facit, "tillampningspunkter", default=())
        )
    )
    slutsats = _hamta(facit, "slutsats", default="")

    vitlista = vitlista_block(_forkortningar_ur(facit_lagrum))
    student = _formatera_studentsvar(studentens_svar)

    punktrader = "\n".join(f"- {p}" for p in punkter) or "- (inga angivna)"
    lagrumsrad = ", ".join(facit_lagrum) if facit_lagrum else "(inga angivna)"

    # Lagtext för facits lagrum OCH studentens egna. Studentens tas med för
    # att tutorn ska kunna säga *varför* en felaktig paragraf inte passar,
    # i stället för att bara konstatera att den saknas i underlaget.
    lagtext = _lagtext_for(facit_lagrum, _studentens_lagrum(student))

    user_prompt = (
        f"{vitlista}\n\n"
        f"{lagtext}"
        "RÄTTSFALL:\n"
        f"{scenariotext}\n\n"
        "KURSENS LÖSNING (ditt sanningsunderlag, endast för din bedömning):\n"
        f"Rättsfråga: {rattsfraga}\n"
        f"Tillämpliga lagrum: {lagrumsrad}\n"
        f"Tillämpning:\n{punktrader}\n"
        f"Slutsats: {slutsats}\n\n"
        "SÅ ANVÄNDER DU KURSENS LÖSNING:\n"
        "- Lösningen är korrekt. Avviker studentens svar från den är det "
        "studenten som har fel.\n"
        "- Anger studenten andra lagrum än lösningens: säg att de inte är "
        "tillämpliga här, och ange vilka lagrum som är det.\n"
        "- Nämner studenten ett lagrum som varken står i lösningen eller i "
        "LAGRUMSVITLISTAN: slå fast att det inte är tillämpligt. Gissa aldrig "
        "på vad ett sådant lagrum innehåller.\n"
        "- Nämn ALDRIG ordet facit, lösningsnyckel eller att en färdig lösning "
        "finns. Skriv som om bedömningen vore ditt eget omdöme.\n"
        "- Servera inte ut lösningen. Studenten ska ledas fram till svaret. "
        "Avslöja de lagrum som behövs för att peka i rätt riktning, men skriv "
        "inte tillämpningen och slutsatsen åt studenten.\n"
        "- Svara alltid på svenska, även om studentens svar är på ett annat "
        "språk eller innehåller engelska uttryck.\n\n"
        "STUDENTENS EGET SVAR (RNTS):\n"
        f"{student}\n\n"
        "Granska studentens svar steg för steg enligt RNTS. Peka på vad som är "
        "rätt, vad som saknas och vad som är fel. Led studenten vidare i "
        "stället för att skriva om lösningen."
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
    lagtext = _lagtext_for(alt_lagrum)

    user_prompt = (
        f"{vitlista}\n\n"
        f"{lagtext}"
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


def build_begrepp_prompt(begrepp: object, las: str = LAS_FORDJUPNING) -> tuple[str, str]:
    """Bygg (system, user) för en fördjupning av ett nyckelbegrepp.

    ``begrepp`` är ett Begrepp (utils.nyckelbegrepp) eller en dict med samma
    fält. Begreppets grunddata injiceras i prompten och modellen instrueras
    uttryckligen att bygga vidare på den, aldrig att skriva om den: fliken
    Nyckelbegrepp visar alltid den deterministiska texten, och LLM-svaret
    läggs till under den.

    ``las`` väljer fördjupningens inriktning: LAS_FORDJUPNING ger en längre
    förklaring, LAS_OVNING ger ett färskt övningsscenario att träna RNTS på.

    Vitlistan begränsas till begreppets egna lagar, så att modellen inte
    frestas att dra in paragrafer från andra rättsområden.
    """
    term = str(_hamta(begrepp, "term", default=""))
    definition = str(_hamta(begrepp, "definition", default=""))
    forklaring = str(_hamta(begrepp, "forklaring", default=""))
    exempel = str(_hamta(begrepp, "exempel", default=""))
    igenkanning = str(_hamta(begrepp, "igenkanning", default=""))
    lagrum = tuple(
        str(x) for x in cast("Iterable[object]", _hamta(begrepp, "lagrum", default=()))
    )

    vitlista = vitlista_block(_forkortningar_ur(lagrum))
    lagrumsrad = ", ".join(lagrum) if lagrum else "(inga angivna)"

    # Begreppsfördjupningen saknade all faktagrund innan lagtexten kom in.
    # Den är den enda LLM-ytan utan facit, så paragrafernas ordalydelse är
    # det närmaste ett sanningsunderlag den kan få.
    lagtext = _lagtext_for(lagrum)

    if las == LAS_OVNING:
        uppdrag = (
            "Skriv ETT kort, fiktivt övningsscenario (4-6 meningar) där just "
            f"begreppet {term} ställs på sin spets. Avsluta med en enda rad: "
            "\"Rättsfrågan att besvara: ...\". Ge INTE lösningen, studenten ska "
            "själv göra RNTS-analysen."
        )
    else:
        uppdrag = (
            f"Fördjupa förklaringen av {term} för en student på JÖK-nivå. "
            "Bygg vidare på grunddatan ovan: förklara gränsfall, vanliga "
            "missförstånd och hur begreppet skiljs från närliggande begrepp. "
            "Upprepa inte definitionen ordagrant."
        )

    user_prompt = (
        f"{vitlista}\n\n"
        f"{lagtext}"
        "BEGREPPETS GRUNDDATA (kursens verifierade underlag, får inte "
        "motsägas):\n"
        f"Term: {term}\n"
        f"Definition: {definition}\n"
        f"Förklaring: {forklaring}\n"
        f"Exempel: {exempel}\n"
        f"Så känns det igen i ett scenario: {igenkanning}\n"
        f"Lagrum: {lagrumsrad}\n\n"
        "KÄLLREGLER (samma som alltid):\n"
        "- Du får ENDAST hänvisa till lagrum ur LAGRUMSVITLISTAN ovan.\n"
        "- Du får ALDRIG hitta på paragrafer, kapitel eller rättsfall.\n"
        "- Motsäg aldrig grunddatan. Den är verifierad mot kursens "
        "lagrumsregister och visas för studenten bredvid ditt svar.\n"
        "- Skriv lagrum som \"36 § AvtL\" eller \"2 kap. 1 § SkL\", alltid med "
        "paragrafnumret först.\n\n"
        f"UPPDRAG:\n{uppdrag}\n\n"
        f"Håll svaret under {MAX_BEGREPPSSVAR_ORD} ord. Skriv på svenska."
    )
    # SYSTEM_PROMPT_BEGREPP, inte SYSTEM_PROMPT_BASE: basprompten kräver
    # RNTS-rubriker och förutsätter ett bifogat studentsvar, vilket skulle
    # säga emot uppdraget ovan.
    return SYSTEM_PROMPT_BEGREPP, user_prompt


def _studentens_lagrum(text: str) -> tuple[str, ...]:
    """Plocka ut de lagrum studenten själv skrivit, i den ordning de står."""
    from utils.lagrum import extrahera_lagrum

    return tuple(ref.ra for ref in extrahera_lagrum(text or ""))


def _lagtext_for(*grupper: Iterable[str]) -> str:
    """Bygg lagtextblocket för flera grupper av lagrum, med avslutande radbryt.

    Returnerar tom sträng när ingen av referenserna har lagtext, så att
    prompten inte får en rubrik utan innehåll. Grunden är utils.lagtext, som
    hellre utelämnar en paragraf än gissar dess innehåll.
    """
    from utils.lagtext import lagtext_block

    refs: list[str] = []
    for grupp in grupper:
        refs.extend(grupp)

    block = lagtext_block(refs)
    return f"{block}\n\n" if block else ""


def _hamta(obj: object, namn: str, default: object = "") -> object:
    """Hämta ett attribut (dataclass) eller nyckel (dict) med gemensam åtkomst."""
    if isinstance(obj, dict):
        return obj.get(namn, default)
    return getattr(obj, namn, default)
