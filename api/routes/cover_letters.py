from fastapi import APIRouter, HTTPException, status

from cover_letter_service import (
    NoVerifiedEvidenceError,
    compose_cover_letter,
)
from models import CoverLetterRequest, CoverLetterResponse


router = APIRouter(
    prefix="/api/v1",
    tags=["cover-letters"],
)


@router.post(
    "/cover-letters",
    response_model=CoverLetterResponse,
    status_code=status.HTTP_200_OK,
)
def create_cover_letter(
    request: CoverLetterRequest,
) -> CoverLetterResponse:
    try:
        return compose_cover_letter(request)
    except NoVerifiedEvidenceError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
