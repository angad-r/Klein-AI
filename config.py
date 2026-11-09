"""
Configuration module for KLEIN AI.
Handles environment variables, API key discovery, and system defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv, set_key

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = BASE_DIR / "research_history.db"
ENV_FILE = BASE_DIR / ".env"

# Official Application Branding
APP_NAME = "KLEIN AI"
APP_TAGLINE = "One Topic. Complete Research. Powered by AI."

# API Keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

# Gemini Model configuration
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
ALTERNATIVE_GEMINI_MODEL = "gemini-3.5-flash-lite"
SUPPORTED_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

_raw_env_model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
# Sanitize outdated or deprecated model references (e.g. 2.5-flash)
if "2.5" in _raw_env_model or not _raw_env_model:
    GEMINI_MODEL = DEFAULT_GEMINI_MODEL
else:
    GEMINI_MODEL = _raw_env_model

# Search depth configurations
SEARCH_DEPTH_CONFIG = {
    "Quick": {
        "initial_queries": 4,
        "max_queries": 6,
        "results_per_query": 3,
        "max_rounds": 2,
        "max_sources": 15,
        "max_extract": 8,
        "queries": 4,
    },
    "Standard": {
        "initial_queries": 8,
        "max_queries": 12,
        "results_per_query": 5,
        "max_rounds": 3,
        "max_sources": 35,
        "max_extract": 18,
        "queries": 8,
    },
    "Deep": {
        "initial_queries": 12,
        "max_queries": 16,
        "results_per_query": 6,
        "max_rounds": 4,
        "max_sources": 50,
        "max_extract": 30,
        "queries": 12,
    },
}

DEFAULT_SEARCH_DEPTH = "Standard"
MAX_SOURCES_PER_DOMAIN = 3
MAX_CONTENT_CHARS_PER_SOURCE = 4000
API_TIMEOUT_SECONDS = 15
GEMINI_VERIFICATION_TIMEOUT_SECONDS = 25.0
TAVILY_EXTRACT_TIMEOUT = 25
MAX_RETRIES = 2

def get_gemini_api_key() -> str:
    """Dynamically gets Gemini key from environment or .env file."""
    load_dotenv(override=False)
    return os.getenv("GEMINI_API_KEY", GEMINI_API_KEY).strip()

def get_tavily_api_key() -> str:
    """Dynamically gets Tavily key from environment or .env file."""
    load_dotenv(override=False)
    return os.getenv("TAVILY_API_KEY", TAVILY_API_KEY).strip()

def get_gemini_model() -> str:
    """Dynamically gets Gemini model, sanitizing any deprecated references."""
    load_dotenv(override=False)
    m = os.getenv("GEMINI_MODEL", GEMINI_MODEL).strip()
    if "2.5" in m or not m:
        return DEFAULT_GEMINI_MODEL
    return m

def is_gemini_available(api_key: str = None) -> bool:
    key = api_key if api_key is not None else get_gemini_api_key()
    return bool(key and len(key) > 5)

def is_tavily_available(api_key: str = None) -> bool:
    key = api_key if api_key is not None else get_tavily_api_key()
    return bool(key and len(key) > 5)

def is_demo_mode(gemini_key: str = None, tavily_key: str = None) -> bool:
    return not (is_gemini_available(gemini_key) and is_tavily_available(tavily_key))

def save_api_keys_to_env(gemini_key: str = "", tavily_key: str = "", env_path: Path = None, gemini_model: str = "") -> bool:
    """Saves user-entered keys to local .env only with explicit user action."""
    global GEMINI_API_KEY, TAVILY_API_KEY, GEMINI_MODEL
    env_file = env_path or ENV_FILE
    try:
        if not env_file.exists():
            env_file.touch(mode=0o600)
        if gemini_key:
            set_key(str(env_file), "GEMINI_API_KEY", gemini_key.strip())
            os.environ["GEMINI_API_KEY"] = gemini_key.strip()
            GEMINI_API_KEY = gemini_key.strip()
        if tavily_key:
            set_key(str(env_file), "TAVILY_API_KEY", tavily_key.strip())
            os.environ["TAVILY_API_KEY"] = tavily_key.strip()
            TAVILY_API_KEY = tavily_key.strip()
        chosen_model = gemini_model.strip() if gemini_model else DEFAULT_GEMINI_MODEL
        if "2.5" in chosen_model or not chosen_model:
            chosen_model = DEFAULT_GEMINI_MODEL
        set_key(str(env_file), "GEMINI_MODEL", chosen_model)
        os.environ["GEMINI_MODEL"] = chosen_model
        GEMINI_MODEL = chosen_model
        load_dotenv(override=True)
        return True
    except Exception:
        return False
