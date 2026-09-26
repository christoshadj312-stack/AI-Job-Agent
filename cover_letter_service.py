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

    role = _clean(request.job_title)
    company = _clean(request.company_name)
    name = _clean(request.analysis.candidate_name)
    destination = f" at {company}" if company else ""

    evidence_lines = [
        f"For {_clean(item.requirement)}, my CV records: "
        f"{_clean(item.evidence).rstrip('.')}."
        for item in selected
    ]

    paragraphs = [
        "Dear Hiring Manager,",
        (
            f"I am writing to apply for the {role} position{destination}. "
            "The following evidence in my CV relates to the "
            "requirements of this role."
        ),
        "\n".join(evidence_lines),
        (
            "I would welcome the opportunity to discuss how my "
            "background could contribute to your team. Thank you "
            "for considering my application."
        ),
        f"Sincerely,\n{name}",
    ]

    return CoverLetterResponse(
        text="\n\n".join(paragraphs),
        evidence_used=selected,
    )
