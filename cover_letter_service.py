"""Compose a cover letter from requirements already verified against a CV."""

import re

from models import (
    CoverLetterRequest,
    CoverLetterResponse,
    MatchInsight,
)


class NoVerifiedEvidenceError(ValueError):
    """No supported claims are available for a cover letter."""


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _select_evidence(
    strengths: list[MatchInsight],
) -> list[MatchInsight]:
    selected: list[MatchInsight] = []
    seen: set[str] = set()

    for item in strengths:
        if item.status != "found":
            continue

        requirement = _clean(item.requirement)
        evidence = _clean(item.evidence)
        if not requirement or not evidence:
            continue

        key = requirement.casefold()
        if key in seen:
            continue

        selected.append(item)
        seen.add(key)
        if len(selected) == 3:
            break

    return selected


def _join_naturally(values: list[str]) -> str:
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"


def _unique_values(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = _clean(value).rstrip(".")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            result.append(cleaned)
            seen.add(key)

    return result


def _body_paragraphs(
    selected: list[MatchInsight],
) -> list[str]:
    sentences: list[str] = []

    technical = _unique_values([
        item.requirement
        for item in selected
        if item.category == "technical_skill"
    ])
    if technical:
        sentences.append(
            "My background includes "
            f"{_join_naturally(technical)}, which align with "
            "the role-specific requirements of the position."
        )

    experience = _unique_values([
        item.evidence
        for item in selected
        if item.category == "experience"
    ])
    if experience:
        sentences.append(
            "My CV also shows relevant experience in "
            f"{_join_naturally(experience)}."
        )

    education = _unique_values([
        item.evidence
        for item in selected
        if item.category == "education"
    ])
    if education:
        sentences.append(
            "My academic background includes "
            f"{_join_naturally(education)}."
        )

    soft_skills = _unique_values([
        item.requirement
        for item in selected
        if item.category == "soft_skill"
    ])
    if soft_skills:
        sentences.append(
            f"I also bring {_join_naturally(soft_skills)}."
        )

    detailed_evidence = _unique_values([
        item.evidence
        for item in selected
        if item.category == "technical_skill"
        and _clean(item.evidence).casefold()
        != _clean(item.requirement).casefold()
    ])
    if detailed_evidence:
        sentences.append(
            "Examples noted in my CV include "
            f"{_join_naturally(detailed_evidence)}."
        )

    return [" ".join(sentences)]


def compose_cover_letter(
    request: CoverLetterRequest,
) -> CoverLetterResponse:
    selected = _select_evidence(
        request.analysis.insights.strengths
    )
    if not selected:
        raise NoVerifiedEvidenceError(
            "No verified CV matches are available for a cover letter."
        )

    if request.analysis.insights.low_alignment or not any(
        item.category in {
            "technical_skill",
            "experience",
            "education",
        }
        for item in selected
    ):
        raise NoVerifiedEvidenceError(
            "The CV and job are not sufficiently aligned for an "
            "evidence-based cover letter."
        )

    role = _clean(request.job_title)
    company = _clean(request.company_name)
    name = _clean(request.analysis.candidate_name)
    destination = f" at {company}" if company else ""

    paragraphs = [
        "Dear Hiring Manager,",
        (
            f"I am writing to apply for the {role} position{destination}. "
            "I am interested in the opportunity to contribute my "
            "background while continuing to grow in this role."
        ),
        *_body_paragraphs(selected),
        (
            "I would welcome the opportunity to discuss how my skills "
            "and background could contribute to your team. Thank you "
            "for your time and consideration."
        ),
        f"Sincerely,\n{name}",
    ]

    return CoverLetterResponse(
        text="\n\n".join(paragraphs),
        evidence_used=selected,
    )
