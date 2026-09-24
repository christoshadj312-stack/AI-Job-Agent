import os
from dataclasses import dataclass
from functools import lru_cache

@dataclass(frozen=True)
class Settings:
    ai_provider: str
    ollama_model: str
    ollama_host: str | None
    groq_api_key: str | None
    groq_model: str


@lru_cache(maxsize=1)
def get_settings():
    from dotenv import load_dotenv

    load_dotenv()

    provider = os.getenv(
        "AI_PROVIDER",
        "ollama",
    ).strip().lower()

    ollama_model = os.getenv(
        "OLLAMA_MODEL",
        "llama3.2:3b",
    ).strip()

    ollama_host = (
        os.getenv("OLLAMA_HOST", "").strip()
        or None
    )

    groq_api_key = (
        os.getenv("GROQ_API_KEY", "").strip()
        or None
    )

    groq_model = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b",
    ).strip()

    return Settings(
        ai_provider=provider,
        ollama_model=ollama_model,
        ollama_host=ollama_host,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
    )
