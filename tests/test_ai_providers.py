import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import BaseModel

from ai_providers.base import AIProviderError
from ai_providers.factory import get_ai_provider
from ai_providers.groq_provider import (
    GroqProvider,
    build_strict_json_schema,
)


class ExampleResponse(BaseModel):
    name: str
    year: int | None = None


class FakeCompletions:
    def __init__(self, content: str | None):
        self.content = content
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=self.content
                    )
                )
            ]
        )


def build_provider(
    content: str | None,
) -> tuple[GroqProvider, FakeCompletions]:
    completions = FakeCompletions(content)
    provider = GroqProvider.__new__(GroqProvider)
    provider.model_name = "openai/gpt-oss-20b"
    provider.vision_model_name = "qwen/qwen3.8-27b"
    provider.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=completions
        )
    )
    return provider, completions


class GroqProviderTests(unittest.TestCase):
    def tearDown(self):
        get_ai_provider.cache_clear()

    def test_strict_schema_requires_every_object_field(self):
        schema = build_strict_json_schema(
            ExampleResponse.model_json_schema()
        )

        self.assertEqual(
            schema["required"],
            ["name", "year"],
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertNotIn(
            "default",
            schema["properties"]["year"],
        )

    def test_groq_response_is_validated_by_pydantic(self):
        provider, completions = build_provider(
            json.dumps(
                {
                    "name": "AI Job Agent",
                    "year": None,
                }
            )
        )

        result = provider.generate_structured(
            ExampleResponse,
            "System instructions",
            "User input",
        )

        self.assertEqual(result.name, "AI Job Agent")
        self.assertIsNone(result.year)
        self.assertTrue(
            completions.request["response_format"]
            ["json_schema"]["strict"]
        )
        self.assertEqual(
            completions.request["max_completion_tokens"],
            8192,
        )
        self.assertEqual(
            completions.request["reasoning_effort"],
            "low",
        )
        self.assertFalse(
            completions.request["include_reasoning"]
        )

    def test_empty_groq_response_is_wrapped(self):
        provider, _ = build_provider(None)

        with self.assertRaises(AIProviderError):
            provider.generate_structured(
                ExampleResponse,
                "System instructions",
                "User input",
            )

    def test_factory_rejects_missing_groq_key(self):
        settings = SimpleNamespace(
            ai_provider="groq",
            groq_api_key=None,
            groq_model="openai/gpt-oss-20b",
            groq_vision_model="qwen/qwen3.8-27b",
        )

        with patch(
            "ai_providers.factory.get_settings",
            return_value=settings,
        ):
            with self.assertRaises(AIProviderError):
                get_ai_provider()

    def test_groq_extracts_text_from_image(self):
        provider, completions = build_provider(
            "SKILLS\nPython"
        )

        result = provider.extract_text_from_image(
            b"image bytes",
            "image/png",
        )

        self.assertEqual(result, "SKILLS\nPython")
        self.assertEqual(
            completions.request["model"],
            "qwen/qwen3.8-27b",
        )
        image_url = (
            completions.request["messages"][0]
            ["content"][1]["image_url"]["url"]
        )
        self.assertTrue(
            image_url.startswith(
                "data:image/png;base64,"
            )
        )


if __name__ == "__main__":
    unittest.main()
