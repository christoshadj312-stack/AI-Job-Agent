from collections.abc import Callable

from ai_service import (
    analyze_cv_with_ai,
    extract_cv_text_from_image,
    extract_candidate_profile,
    extract_job_requirements,
)
from analyzer import calculate_match_score
from cv_parser import (
    CVParserError,
    extract_text_from_pdf_bytes,
    render_pdf_pages_as_png,
)
from models import (
    ApplicationAnalysisResult,
    ApplicationInsights,
    CVAnalysis,
    CVImprovementSuggestion,
    MatchInsight,
    MatchScores,
    RequirementAnalysis,
    RequirementCategory,
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


def _suggestion_text(
    category: RequirementCategory,
    item: RequirementAnalysis,
) -> str:
    is_partial = item.status == "partial"

    if category == "technical_skill":
        if is_partial:
            return (
                f'Clarify where and how you used '
                f'"{item.requirement}" in an existing '
                "role or project, using only "
                "verifiable details."
            )

        return (
            f'If you genuinely have experience with '
            f'"{item.requirement}", add the exact '
            "skill to your skills section and "
            "support it with a role or project "
            "bullet. Otherwise, leave it out."
        )

    if category == "experience":
        if is_partial:
            return (
                f'Strengthen the existing evidence '
                f'for "{item.requirement}" by adding '
                "verifiable dates, duration, "
                "responsibilities, or outcomes."
            )

        return (
            "If accurate, add a role or project "
            f'bullet that demonstrates '
            f'"{item.requirement}", including dates '
            "or duration when they can be verified."
        )

    if category == "education":
        if is_partial:
            return (
                "Clarify the verified degree level, "
                "field of study, institution, and "
                "completion status relevant to "
                f'"{item.requirement}".'
            )

        return (
            "Check that your CV states the exact "
            "degree level and field relevant to "
            f'"{item.requirement}". Add only '
            "qualifications you have earned or are "
            "currently completing."
        )

    if is_partial:
        return (
            "Make the existing evidence for "
            f'"{item.requirement}" more explicit by '
            "describing the action you took and the "
            "verifiable outcome."
        )

    return (
        "If true, add a concrete role or project "
        f'example that demonstrates '
        f'"{item.requirement}" through an action or '
        "outcome. Do not list the skill without "
        "evidence."
    )


def _build_insights(
    analysis: CVAnalysis,
) -> ApplicationInsights:
    groups: tuple[
        tuple[
            RequirementCategory,
            list[RequirementAnalysis],
        ],
        ...,
    ] = (
        (
            "technical_skill",
            analysis.technical_skills,
        ),
        (
            "experience",
            analysis.experience_requirements,
        ),
        (
            "education",
            analysis.education_requirements,
        ),
        (
            "soft_skill",
            analysis.soft_skills,
        ),
    )

    strengths: list[MatchInsight] = []
    gaps: list[MatchInsight] = []
    suggestions: list[
        CVImprovementSuggestion
    ] = []

    for category, items in groups:
        for item in items:
            insight = MatchInsight(
                category=category,
                requirement=item.requirement,
                status=item.status,
                evidence=item.evidence,
                reason=item.reason,
            )

            if item.status == "found":
                strengths.append(insight)
                continue

            gaps.append(insight)

            suggestions.append(
                CVImprovementSuggestion(
                    category=category,
                    requirement=item.requirement,
                    priority=(
                        "high"
                        if item.status == "missing"
                        else "medium"
                    ),
                    suggestion=_suggestion_text(
                        category,
                        item,
                    ),
                    evidence_basis=(
                        item.evidence
                        if item.evidence.strip()
                        else item.reason
                    ),
                )
            )

    core_items = (
        analysis.technical_skills
        + analysis.experience_requirements
        + analysis.education_requirements
    )
    low_alignment = bool(core_items) and all(
        item.status == "missing"
        for item in core_items
    )

    return ApplicationInsights(
        strengths=strengths,
        gaps=gaps,
        cv_improvement_suggestions=(
            suggestions
        ),
        low_alignment=low_alignment,
        alignment_message=(
            "This CV does not contain verified evidence for the role's "
            "main skills, experience, or education requirements. Consider "
            "using a CV relevant to this field or choosing a role closer "
            "to the candidate's background."
            if low_alignment
            else ""
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
        "building_candidate_profile",
    )
    candidate_profile = extract_candidate_profile(
        cv_text
    )

    _notify(
        progress_callback,
        "extracting_job_requirements",
    )
    requirements = extract_job_requirements(
        job_description
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
        insights=_build_insights(analysis),
    )


def analyze_uploaded_application(
    candidate_name: str,
    file_bytes: bytes,
    content_type: str,
    job_description: str,
) -> ApplicationAnalysisResult:
    if content_type == "application/pdf":
        try:
            cv_text = extract_text_from_pdf_bytes(
                file_bytes
            )
        except CVParserError as error:
            if "No readable text" not in str(error):
                raise

            page_images = render_pdf_pages_as_png(
                file_bytes
            )
            page_texts = [
                extract_cv_text_from_image(
                    image_bytes=page_image,
                    mime_type="image/png",
                )
                for page_image in page_images
            ]
            cv_text = "\n\n".join(page_texts)
    else:
        cv_text = extract_cv_text_from_image(
            image_bytes=file_bytes,
            mime_type=content_type,
        )

    return analyze_application(
        candidate_name=candidate_name,
        cv_text=cv_text,
        job_description=job_description,
    )


def analyze_pdf_application(
    candidate_name: str,
    pdf_bytes: bytes,
    job_description: str,
) -> ApplicationAnalysisResult:
    """Keep the original PDF-only entry point for compatibility."""
    return analyze_uploaded_application(
        candidate_name=candidate_name,
        file_bytes=pdf_bytes,
        content_type="application/pdf",
        job_description=job_description,
    )
