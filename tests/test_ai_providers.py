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
        )

        with patch(
            "ai_providers.factory.get_settings",
            return_value=settings,
        ):
            with self.assertRaises(AIProviderError):
                get_ai_provider()


if __name__ == "__main__":
    unittest.main()
