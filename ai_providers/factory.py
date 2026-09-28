from functools import lru_cache

from ai_providers.base import (
    AIProvider,
    AIProviderError,
)
from ai_providers.groq_provider import GroqProvider
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
            vision_model_name=(
                settings.ollama_vision_model
            ),
            host=settings.ollama_host,
        )

    if settings.ai_provider == "groq":
        if not settings.groq_api_key:
            raise AIProviderError(
                "GROQ_API_KEY is required when "
                "AI_PROVIDER=groq."
            )

        return GroqProvider(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            vision_model_name=(
                settings.groq_vision_model
            ),
        )

    raise AIProviderError(
        "Unsupported AI provider: "
        f"{settings.ai_provider}"
    )
