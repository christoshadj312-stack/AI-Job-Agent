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
    cors_origins: tuple[str, ...]
    max_cv_size_bytes: int


def _read_positive_int(
    variable_name: str,
    default: int,
) -> int:
    raw_value = os.getenv(
        variable_name,
        str(default),
    ).strip()

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(
            f"{variable_name} must be an integer."
        ) from error

    if value <= 0:
        raise ValueError(
            f"{variable_name} must be greater than zero."
        )

    return value


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

    cors_origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173",
        ).split(",")
        if origin.strip()
    )

    max_cv_size_mb = _read_positive_int(
        "MAX_CV_SIZE_MB",
        5,
    )

    return Settings(
        ai_provider=provider,
        ollama_model=ollama_model,
        ollama_host=ollama_host,
        groq_api_key=groq_api_key,
        groq_model=groq_model,
        cors_origins=cors_origins,
        max_cv_size_bytes=(
            max_cv_size_mb * 1024 * 1024
        ),
    )
