"""
Configuration module for Klein AI — ResearchMate AI.
Handles environment variables, API key discovery, and system defaults.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = BASE_DIR / "research_history.db"

# Application Branding
APP_NAME = "Klein AI — ResearchMate AI"
APP_TAGLINE = "One Topic. Complete Research. Powered by AI."

# API Keys from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()

# Gemini Model defaults
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

# Search depth configurations
SEARCH_DEPTH_CONFIG = {
    "Quick": {"queries": 3, "results_per_query": 3, "max_extract": 5},
    "Standard": {"queries": 4, "results_per_query": 5, "max_extract": 8},
    "Deep": {"queries": 6, "results_per_query": 6, "max_extract": 12},
}

DEFAULT_SEARCH_DEPTH = "Standard"
MAX_CONTENT_CHARS_PER_SOURCE = 4000
API_TIMEOUT_SECONDS = 15
MAX_RETRIES = 2

def is_gemini_available(api_key: str = None) -> bool:
    key = api_key if api_key is not None else GEMINI_API_KEY
    return bool(key and len(key) > 5)

def is_tavily_available(api_key: str = None) -> bool:
    key = api_key if api_key is not None else TAVILY_API_KEY
    return bool(key and len(key) > 5)

def is_demo_mode(gemini_key: str = None, tavily_key: str = None) -> bool:
    return not (is_gemini_available(gemini_key) and is_tavily_available(tavily_key))
