from collections.abc import Callable

from ai_service import (
    analyze_cv_with_ai,
    extract_candidate_profile,
    extract_job_requirements,
)
from analyzer import calculate_match_score
from cv_parser import extract_text_from_pdf_bytes
from models import (
    ApplicationAnalysisResult,
    CVAnalysis,
    MatchScores,
)


ProgressCallback = Callable[[str], None]


def _notify(
    callback: ProgressCallback | None,
    stage: str,
) -> None:
    if callback is not None:
        callback(stage)


def _build_scores(
    analysis: CVAnalysis,
) -> MatchScores:
    all_items = (
        analysis.technical_skills
        + analysis.experience_requirements
        + analysis.education_requirements
        + analysis.soft_skills
    )

    return MatchScores(
        technical_skills=calculate_match_score(
            analysis.technical_skills
        ),
        experience=calculate_match_score(
            analysis.experience_requirements
        ),
        education=calculate_match_score(
            analysis.education_requirements
        ),
        soft_skills=calculate_match_score(
            analysis.soft_skills
        ),
        overall_match=calculate_match_score(
            all_items
        ),
    )


def analyze_application(
    candidate_name: str,
    cv_text: str,
    job_description: str,
    progress_callback: ProgressCallback | None = None,
) -> ApplicationAnalysisResult:
    _notify(
        progress_callback,
        "extracting_job_requirements",
    )
    requirements = extract_job_requirements(
        job_description
    )

    _notify(
        progress_callback,
        "building_candidate_profile",
    )
    candidate_profile = extract_candidate_profile(
        cv_text
    )

    _notify(
        progress_callback,
        "matching_candidate",
    )
    analysis = analyze_cv_with_ai(
        cv_text,
        requirements,
        candidate_profile,
    )

    return ApplicationAnalysisResult(
        candidate_name=candidate_name,
        candidate_profile=candidate_profile,
        job_requirements=requirements,
        analysis=analysis,
        scores=_build_scores(analysis),
    )


def analyze_pdf_application(
    candidate_name: str,
    pdf_bytes: bytes,
    job_description: str,
) -> ApplicationAnalysisResult:
    cv_text = extract_text_from_pdf_bytes(
        pdf_bytes
    )

    return analyze_application(
        candidate_name=candidate_name,
        cv_text=cv_text,
        job_description=job_description,
    )
