from typing import Annotated

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from starlette.concurrency import run_in_threadpool

from ai_service import AIServiceError
from analysis_service import analyze_uploaded_application
from cv_parser import CVParserError
from models import ApplicationAnalysisResult
from settings import get_settings


router = APIRouter(
    prefix="/api/v1",
    tags=["analyses"],
)


_ALLOWED_UPLOADS = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


@router.post(
    "/analyses",
    response_model=ApplicationAnalysisResult,
    status_code=status.HTTP_200_OK,
)
async def create_analysis(
    candidate_name: Annotated[
        str,
        Form(min_length=1, max_length=200),
    ],
    job_description: Annotated[
        str,
        Form(min_length=20, max_length=50_000),
    ],
    cv_file: Annotated[
        UploadFile,
        File(description="Candidate CV as PDF, PNG, JPG, or JPEG"),
    ],
) -> ApplicationAnalysisResult:
    filename = cv_file.filename or ""
    content_type = cv_file.content_type or ""
    suffix = next(
        (
            extension
            for extension in _ALLOWED_UPLOADS
            if filename.lower().endswith(extension)
        ),
        "",
    )

    if (
        not suffix
        or content_type != _ALLOWED_UPLOADS[suffix]
    ):
        await cv_file.close()
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "The CV must be uploaded as a PDF, PNG, JPG, or JPEG file."
            ),
        )

    max_size = get_settings().max_cv_size_bytes

    try:
        file_bytes = await cv_file.read(
            max_size + 1
        )
    finally:
        await cv_file.close()

    if len(file_bytes) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The uploaded CV exceeds the allowed size.",
        )

    try:
        return await run_in_threadpool(
            analyze_uploaded_application,
            candidate_name.strip(),
            file_bytes,
            content_type,
            job_description.strip(),
        )
    except CVParserError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    except AIServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
