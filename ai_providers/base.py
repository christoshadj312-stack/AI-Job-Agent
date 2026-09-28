from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel


ResponseModel = TypeVar(
    "ResponseModel",
    bound=BaseModel,
)


class AIProviderError(Exception):
    """Raised when an AI provider cannot complete a request."""


class AIProvider(ABC):
    @abstractmethod
    def extract_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        """Extract CV text from an uploaded image."""

    @abstractmethod
    def generate_structured(
        self,
        response_model: type[ResponseModel],
        system_prompt: str,
        user_prompt: str,
    ) -> ResponseModel:
        """Generate and validate a structured model response."""
