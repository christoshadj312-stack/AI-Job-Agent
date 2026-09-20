from ai_providers.base import (
    AIProvider,
    AIProviderError,
    ResponseModel,
)


class OllamaProvider(AIProvider):
    def __init__(
        self,
        model_name: str,
        host: str | None = None,
    ):
        from ollama import Client

        self.model_name = model_name
        self.client = (
            Client(host=host)
            if host
            else Client()
        )

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
