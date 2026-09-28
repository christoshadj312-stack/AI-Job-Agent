from ai_providers.base import (
    AIProvider,
    AIProviderError,
    ResponseModel,
)


class OllamaProvider(AIProvider):
    def __init__(
        self,
        model_name: str,
        vision_model_name: str,
        host: str | None = None,
    ):
        from ollama import Client

        self.model_name = model_name
        self.vision_model_name = vision_model_name
        self.client = (
            Client(host=host)
            if host
            else Client()
        )

    def extract_text_from_image(
        self,
        image_bytes: bytes,
        mime_type: str,
    ) -> str:
        try:
            response = self.client.chat(
                model=self.vision_model_name,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Transcribe all readable CV text from this image. "
                            "Preserve headings, dates, bullet points, and line breaks. "
                            "Return only the transcription. Do not explain, summarize, "
                            "correct, or invent any content."
                        ),
                        "images": [image_bytes],
                    }
                ],
                options={"temperature": 0},
            )

            content = response.message.content
            if not content or not content.strip():
                raise ValueError(
                    "Ollama returned no readable image text."
                )

            return content.strip()

        except Exception as error:
            raise AIProviderError(
                "Ollama could not read the uploaded CV image. "
                "Make sure the configured vision model is installed."
            ) from error

    def generate_structured(
        self,
        response_model: type[ResponseModel],
        system_prompt: str,
        user_prompt: str,
    ) -> ResponseModel:
        try:
            response = self.client.chat(
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
                format=(
                    response_model
                    .model_json_schema()
                ),
                options={
                    "temperature": 0,
                },
            )

            return (
                response_model
                .model_validate_json(
                    response.message.content
                )
            )

        except Exception as error:
            raise AIProviderError(
                "Ollama could not complete "
                "the structured AI request."
            ) from error
