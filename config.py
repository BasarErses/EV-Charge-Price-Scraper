"""Load settings from environment."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env optional; use env vars or defaults

# AI provider: "claude" | "gemini" | "ollama" (ollama = local, no API key)
AI_PROVIDER = os.getenv("AI_PROVIDER", "claude").strip().lower()
if AI_PROVIDER not in ("claude", "gemini", "ollama"):
    AI_PROVIDER = "claude"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Ollama (local LLM, no API key)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip().rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1").strip() or "llama3.1"

# Paths (project root = directory containing this file)
PROJECT_ROOT = Path(__file__).resolve().parent
LINKS_FILE = PROJECT_ROOT / os.getenv("LINKS_FILE", "links copy.txt").strip()
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_BY_URL = RESULTS_DIR / "by_url"
STATE_DIR = PROJECT_ROOT / "state"

# Scraper
REQUEST_TIMEOUT = 25
MAX_PAGE_CHARS = 120_000  # trim HTML/text to avoid token limits
RATE_LIMIT_DELAY_SEC = 2.0
EXTRACTION_RETRIES = 3
EXTRACTION_RETRY_DELAY_SEC = 5.0
