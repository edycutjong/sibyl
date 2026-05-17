"""Sibyl — Configuration via environment variables."""

from __future__ import annotations

from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env into os.environ so third-party libraries (like litellm) can access them
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Prophet Arena ───────────────────────────────────────────
    pa_server_api_key: str = ""
    pa_server_url: str = "https://api.aiprophet.dev"

    # ── LLM Providers ──────────────────────────────────────────
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""

    # ── Search / Retrieval ─────────────────────────────────────
    exa_api_key: str = ""
    brave_api_key: str = ""

    # ── Agent Auth ─────────────────────────────────────────────
    bearer_token: str = "sibyl-secret-token"

    # ── Operational ────────────────────────────────────────────
    log_level: str = "INFO"
    cache_dir: str = ".cache"

    # ── Model Selection Defaults ───────────────────────────────
    model_high_confidence: str = "gpt-4o-mini"
    model_medium_confidence: str = "gemini/gemini-3.1-flash"
    model_low_confidence: str = "claude-sonnet-4-20250514"
    model_classifier: str = "gpt-4o-mini"

    # ── Thresholds ─────────────────────────────────────────────
    high_confidence_threshold: float = 0.85
    low_confidence_threshold: float = 0.60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()
