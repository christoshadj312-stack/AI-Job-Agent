from functools import lru_cache

from ai_providers.base import (
    AIProvider,
    AIProviderError,
)
from ai_providers.ollama_provider import (
    OllamaProvider,
)
from settings import get_settings


@lru_cache(maxsize=1)
def get_ai_provider() -> AIProvider:
    settings = get_settings()

    if settings.ai_provider == "ollama":
        return OllamaProvider(
            model_name=settings.ollama_model,
            host=settings.ollama_host,
        )

    raise AIProviderError(
        "Unsupported AI provider: "
        f"{settings.ai_provider}"
    )
