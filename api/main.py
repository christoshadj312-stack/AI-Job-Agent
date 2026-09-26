from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.analysis import router as analysis_router
from api.routes.cover_letters import router as cover_letters_router
from settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="AI Job Application Agent API",
        description=(
            "Evidence-based CV and job-description "
            "matching API."
        ),
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(
        analysis_router
    )
    application.include_router(
        cover_letters_router
    )

    @application.get(
        "/health",
        tags=["health"],
    )
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
