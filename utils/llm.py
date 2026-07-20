"""LLM-klient för Hugging Face Inference Providers.

Centraliserar all LLM-åtkomst för appen. Ansvarar för:
- Läsning av HF_TOKEN och modellval från st.secrets eller miljövariabler
- LLMClient: tunt lager runt InferenceClient med chat och stream_chat,
  inklusive strippning av Qwen3:s <think>-block
- cached_chat: st.cache_data-cachad chatt, nyckelad på hash av
  systemprompt + användarprompt + parametrar + modell
- Sessionstak (40 anrop) räknat i st.session_state; endast nya
  prompt-hashar debiteras, cacheträffar är gratis
- Enhetlig felhierarki: LLMUnavailableError, LLMSessionCapError,
  LLMDailyCapError så att alla sidor kan falla tillbaka deterministiskt

Ersätter ekonomistyrnings sifferverifiering: lagrumsverifieringen ligger
i utils.lagrum. verify_lagrum här är en tunn delegering dit.
"""

from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass

# Läs in .env om python-dotenv finns installerat.
try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv()
except ImportError:
    pass

DEFAULT_MODEL = "Qwen/Qwen3-8B"
ALTERNATIVE_MODEL = "Qwen/Qwen3-14B"
# Appen kör på exakt dessa två modeller: 8B som standard, 14B som
# alternativ. Allt annat avvisas och faller tillbaka till standardmodellen.
SUPPORTED_MODELS = (DEFAULT_MODEL, ALTERNATIVE_MODEL)
# Session-state-nyckel som sidopanelens modellväljare sätter för att byta
# modell i runtime utan att röra secrets eller env.
MODEL_SESSION_KEY = "llm_model"
DEFAULT_PROVIDER = "auto"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_TOKENS = 4096
DEFAULT_TEMPERATURE = 0.4
SESSION_CALL_CAP = 40

# Qwen3-modeller sänder <think>...</think>-block före själva svaret.
# Detta mönster strippar dem så att anroparna bara ser slutsvaret.
THINK_TAG_PATTERN = re.compile(r"<think>[\s\S]*?</think>\s*", flags=re.DOTALL)


def _strip_think_tags(text: str) -> str:
    """Ta bort Qwen3:s <think>...</think>-resonemang ur svaret.

    Om modellen tog slut på tokens mitt i tänkandet (ingen </think>),
    strippa allt från <think> och framåt.
    """
    cleaned = THINK_TAG_PATTERN.sub("", text)
    if "<think>" in cleaned:
        cleaned = cleaned.split("<think>")[0]
    return cleaned.strip()


class LLMUnavailableError(RuntimeError):
    """Kastas när LLM:en inte kan betjäna en förfrågan.

    Orsaker: saknad token, nätverksfel, rate limit eller sessionstak.
    Anroparna ska fånga detta och visa den deterministiska fallbacken.
    """


class LLMSessionCapError(LLMUnavailableError):
    """Kastas när sessionens tak på 40 anrop har nåtts.

    Ärver LLMUnavailableError så att befintliga fångstställen fortfarande
    hanterar den, men sidor som vill visa det vänliga svenska infokortet
    kan fånga just denna typ först.
    """


class LLMDailyCapError(LLMUnavailableError):
    """Kastas när den gemensamma dagsbudgeten är förbrukad.

    Ärver LLMUnavailableError så att varje befintligt fångstställe
    degraderar till den deterministiska fallbacken utan kodändringar.
    """


SESSION_CAP_MESSAGE = (
    "Sessionens gräns för förklaringar är uppnådd. Rättning, quiz, "
    "lagrumslänkar och export fungerar som vanligt. Gränsen nollställs "
    "när du börjar en ny session."
)


@dataclass
class LLMConfig:
    """LLM-konfiguration inläst från secrets eller env."""

    token: str | None
    model: str
    provider: str


def get_hf_token() -> str | None:
    """Returnera HF-token från Streamlit-secrets eller env.

    Prioritet: st.secrets["HF_TOKEN"], sedan miljövariabeln HF_TOKEN.
    Returnerar None om ingen är satt; anroparna måste hantera det fallet.
    """
    try:
        import streamlit as st

        if "HF_TOKEN" in st.secrets:
            value = st.secrets["HF_TOKEN"]
            if value and isinstance(value, str):
                return value
    except (ImportError, FileNotFoundError, Exception):
        pass

    env_value = os.environ.get("HF_TOKEN")
    return env_value if env_value else None


def _read_setting(key: str, default: str | None = None) -> str | None:
    """Läs en inställning från Streamlit-secrets först, sedan env."""
    try:
        import streamlit as st

        if key in st.secrets:
            return str(st.secrets[key])
    except (ImportError, FileNotFoundError, Exception):
        pass
    return os.environ.get(key, default)


def normalize_model(model: str | None) -> str | None:
    """Mappa valfritt namn till en av de två stödda modellerna, annars None.

    Accepterar både fullt id ("Qwen/Qwen3-14B") och kort visningsnamn
    ("Qwen3-14B", skiftlägesokänsligt). Returnerar None för allt som inte
    är en stödd modell.
    """
    if not model:
        return None
    candidate = model.strip()
    if candidate in SUPPORTED_MODELS:
        return candidate
    short = candidate.split("/")[-1].lower()
    for supported in SUPPORTED_MODELS:
        if supported.split("/")[-1].lower() == short:
            return supported
    return None


def get_active_model() -> str:
    """Avgör vilken modell appen ska använda just nu.

    Prioritet: sidopanelens runtime-override (session state) > LLM_MODEL
    > standardmodellen. Ogiltiga värden ignoreras så att appen alltid kör
    på antingen Qwen3-8B eller Qwen3-14B.
    """
    try:
        import streamlit as st

        override = normalize_model(st.session_state.get(MODEL_SESSION_KEY))
        if override:
            return override
    except (ImportError, Exception):
        pass

    configured = normalize_model(_read_setting("LLM_MODEL"))
    return configured or DEFAULT_MODEL


def get_llm_config() -> LLMConfig:
    """Läs in full LLM-konfiguration från secrets eller env."""
    token = get_hf_token()
    model = get_active_model()
    provider = _read_setting("LLM_PROVIDER", DEFAULT_PROVIDER) or DEFAULT_PROVIDER
    return LLMConfig(token=token, model=model, provider=provider)


def is_llm_available() -> bool:
    """Returnerar True om en token är konfigurerad. Anropar inte API:t."""
    return get_hf_token() is not None


def _hash_prompt(system_prompt: str, user_prompt: str, **kwargs) -> str:
    """Stabil hash av prompt + relevanta kwargs, för cachning."""
    payload = f"{system_prompt}\n||\n{user_prompt}\n||\n"
    payload += "&".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LLMClient:
    """Tunt lager runt huggingface_hub.InferenceClient.

    Alla undantag fångas och kastas om som LLMUnavailableError så att
    anroparna har en enda feltyp att hantera.
    """

    def __init__(
        self,
        token: str | None = None,
        model: str = DEFAULT_MODEL,
        provider: str = DEFAULT_PROVIDER,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if token is None:
            token = get_hf_token()
        if not token:
            raise LLMUnavailableError("HF-token saknas. Kontrollera secrets eller env.")

        try:
            from huggingface_hub import InferenceClient
        except ImportError as exc:
            raise LLMUnavailableError(f"huggingface_hub saknas: {exc}") from exc

        self.model = model
        self.provider = provider
        self.timeout = timeout
        self._client = InferenceClient(token=token, timeout=timeout)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> str:
        """Enkelt chat-anrop. Returnerar textinnehållet."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = self._client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            raw = response.choices[0].message.content or ""
            return _strip_think_tags(raw)
        except Exception as exc:
            raise LLMUnavailableError(f"LLM-anrop misslyckades: {exc}") from exc

    def stream_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        max_new_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ) -> Iterator[str]:
        """Strömmande chat-anrop. Yieldar textbitar.

        Buffrar bort eventuella <think>...</think>-block och yieldar bara
        innehållet efter tänkandet.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            stream = self._client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=max_new_tokens,
                temperature=temperature,
                stream=True,
            )
            in_think = False
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content
                    if not delta:
                        continue
                    if "<think>" in delta:
                        in_think = True
                        delta = delta.split("<think>")[0]
                        if delta.strip():
                            yield delta
                        continue
                    if in_think:
                        if "</think>" in delta:
                            in_think = False
                            delta = delta.split("</think>", 1)[1]
                            if delta.strip():
                                yield delta
                        continue
                    yield delta
        except Exception as exc:
            raise LLMUnavailableError(f"LLM-strömmen misslyckades: {exc}") from exc


def cached_chat(
    system_prompt: str,
    user_prompt: str,
    max_new_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    """Cachat enkelt chat-anrop. Används inifrån Streamlit-sidor.

    Cachen nyckas på promptinnehåll så att identiska inputs träffar cachen.

    Räkningen är centraliserad här: varje distinkt prompt debiteras
    sessionstaket exakt en gång, på den körning som faktiskt når API:t.
    Cacheträffar och tillfälliga reruns återanvänder det lagrade svaret
    utan att förbruka taket. Anroparna ska därför INTE själva anropa
    increment_session_calls.

    Kastar LLMSessionCapError endast när ett *nytt* anrop krävs och taket
    är slut, så att svar som redan genererats i sessionen fortsätter visas.
    """
    from utils.llm_budget import (
        DAILY_CAP_MESSAGE,
        get_daily_calls_remaining,
        record_daily_call,
    )

    config = get_llm_config()
    try:
        import streamlit as st
    except ImportError:
        # Ingen Streamlit-runtime (t.ex. pytest): anropa direkt, utan
        # cache/räkning.
        if get_session_calls_remaining() <= 0:
            raise LLMSessionCapError(SESSION_CAP_MESSAGE) from None
        if get_daily_calls_remaining() <= 0:
            raise LLMDailyCapError(DAILY_CAP_MESSAGE) from None
        client = LLMClient(token=config.token, model=config.model, provider=config.provider)
        result = client.chat(
            system_prompt, user_prompt, max_new_tokens=max_new_tokens, temperature=temperature
        )
        record_daily_call()
        return result

    @st.cache_data(ttl=3600, show_spinner=False)
    def _call(prompt_hash: str, sp: str, up: str, mt: int, t: float, model: str) -> str:
        cfg = get_llm_config()
        client = LLMClient(token=cfg.token, model=model, provider=cfg.provider)
        return client.chat(sp, up, max_new_tokens=mt, temperature=t)

    # Modellen är del av cache-nyckeln så att modellbyte aldrig serverar
    # ett svar som genererats av den andra modellen.
    prompt_hash = _hash_prompt(
        system_prompt, user_prompt, mt=max_new_tokens, t=temperature, model=config.model
    )

    # En prompt som redan debiterats denna session är gratis: _call
    # returnerar det cachade svaret, så vi får inte räkna det igen.
    try:
        counted: set | None = st.session_state.setdefault("llm_counted_hashes", set())
    except Exception:
        counted = None
    is_new = counted is None or prompt_hash not in counted
    if is_new and get_session_calls_remaining() <= 0:
        raise LLMSessionCapError(SESSION_CAP_MESSAGE)
    # Serverskydd: den gemensamma dagsbudgeten är oberoende av session
    # state, överlever omladdningar och skyddar HF-token på publika deployer.
    if is_new and get_daily_calls_remaining() <= 0:
        raise LLMDailyCapError(DAILY_CAP_MESSAGE)

    result = _call(
        prompt_hash, system_prompt, user_prompt, max_new_tokens, temperature, config.model
    )

    if is_new and counted is not None:
        counted.add(prompt_hash)
        increment_session_calls()
        record_daily_call()
    return result


def get_session_calls_remaining() -> int:
    """Återstående LLM-anrop för denna Streamlit-session."""
    try:
        import streamlit as st

        used = st.session_state.get("llm_calls_used", 0)
        return max(0, SESSION_CALL_CAP - used)
    except (ImportError, Exception):
        return SESSION_CALL_CAP


def increment_session_calls() -> int:
    """Registrera ett LLM-anrop för denna session. Returnerar antal kvar."""
    try:
        import streamlit as st

        used = st.session_state.get("llm_calls_used", 0)
        st.session_state["llm_calls_used"] = used + 1
        return max(0, SESSION_CALL_CAP - (used + 1))
    except (ImportError, Exception):
        return SESSION_CALL_CAP


def verify_lagrum(text: str):
    """Juridikappens motsvarighet till ekonomistyrnings verify_grounding.

    Delegerar till utils.lagrum för deterministisk lagrumsverifiering så
    att all grounding-logik bor på ett ställe.
    """
    from utils.lagrum import verify_lagrum as _verify_lagrum

    return _verify_lagrum(text)
