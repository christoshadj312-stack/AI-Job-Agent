import base64
import logging
import re
from typing import Any

from ai_providers.base import (
    AIProvider,
    AIProviderError,
    ResponseModel,
)


logger = logging.getLogger(__name__)


_UNSUPPORTED_STRICT_SCHEMA_KEYS = {
    "default",
    "examples",
    "exclusiveMaximum",
    "exclusiveMinimum",
    "format",
    "maxItems",
    "maxLength",
    "maximum",
    "minItems",
    "minLength",
    "minimum",
    "multipleOf",
    "pattern",
    "title",
    "uniqueItems",
}


def build_strict_json_schema(
    schema: dict[str, Any],
) -> dict[str, Any]:
    """Convert a Pydantic schema to Groq strict-mode JSON Schema."""

    def transform(value: Any) -> Any:
        if isinstance(value, list):
            return [transform(item) for item in value]

        if not isinstance(value, dict):
            return value

        transformed = {
            key: transform(item)
            for key, item in value.items()
            if key not in _UNSUPPORTED_STRICT_SCHEMA_KEYS
        }

        properties = transformed.get("properties")
        if isinstance(properties, dict):
            transformed["required"] = list(properties)
            transformed["additionalProperties"] = False

        return transformed

    return transform(schema)


def _schema_name(
    response_model: type[ResponseModel],
) -> str:
    name = re.sub(
        r"(?<!^)(?=[A-Z])",
        "_",
        response_model.__name__,
    ).lower()
    return re.sub(r"[^a-z0-9_-]", "_", name)


class GroqProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        model_name: str,
        vision_model_name: str,
    ):
        from groq import Groq

        self.model_name = model_name
        self.vision_model_name = vision_model_name
        self.client = Groq(
            api_key=api_key,
            timeout=90.0,
            max_retries=2,
        )

    def extract_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        encoded_image = base64.b64encode(
            image_bytes
        ).decode("ascii")

        try:
            response = self.client.chat.completions.create(
                model=self.vision_model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Transcribe all readable CV text from this image. "
                                    "Preserve headings, dates, bullet points, and line breaks. "
                                    "Return only the transcription. Do not explain, summarize, "
                                    "correct, or invent any content."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": (
                                        f"data:{mime_type};base64,{encoded_image}"
                                    )
                                },
                            },
                        ],
                    }
                ],
                temperature=0,
                max_completion_tokens=8192,
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ValueError(
                    "Groq returned no readable image text."
                )

            return content.strip()

        except Exception as error:
            logger.exception(
                "Groq vision request failed for model %s.",
                self.vision_model_name,
            )
            raise AIProviderError(
                "Groq could not read the uploaded CV image."
            ) from error

    def generate_structured(
        self,
        response_model: type[ResponseModel],
        system_prompt: str,
        user_prompt: str,
    ) -> ResponseModel:
        schema = build_strict_json_schema(
            response_model.model_json_schema()
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0,
                max_completion_tokens=8192,
                reasoning_effort="low",
                include_reasoning=False,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": _schema_name(response_model),
                        "strict": True,
                        "schema": schema,
                    },
                },
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError(
                    "Groq returned an empty response."
                )

            return response_model.model_validate_json(
                content
            )

        except Exception as error:
            logger.exception(
                "Groq structured request failed for model %s.",
                self.model_name,
            )
            raise AIProviderError(
                "Groq could not complete the "
                "structured AI request."
            ) from error
