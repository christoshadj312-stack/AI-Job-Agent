import json
import re

from analyzer import (
    conservative_experience_months,
    extract_required_years,
    find_deterministic_education_match,
    find_direct_matches,
    format_experience_period,
    normalize_text,
    prepare_cv_lines,
    tokenize,
)
from models import (
    CandidateProfile,
    CVAnalysis,
    JobRequirements,
    RequirementAnalysis,
    SemanticBatchResult,
)


MODEL_NAME = "llama3.2:3b"


class AIServiceError(Exception):
    """Raised when the local AI service fails."""


def _requirement_text(requirement):
    return getattr(requirement, "original_requirement", requirement)


def _call_structured_ai(
    response_model,
    system_prompt,
    user_prompt,
):
    try:
        from ollama import chat

        response = chat(
            model=MODEL_NAME,
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
        raise AIServiceError(
            "The local AI model could "
            "not complete the request."
        ) from error


def extract_job_requirements(
    job_description,
):
    system_prompt = (
        "You are a strict job requirements extractor. "
        "Read the complete job description before answering. "
        "Return exactly one structured JobRequirements object. "
        "technical_skills contains explicit programming languages, "
        "frameworks, libraries, databases, APIs, cloud tools, "
        "DevOps tools, AI/ML technologies, and other technical skills. "
        "Each experience requirement is one compound condition with its full "
        "original wording, minimum years, all alternative accepted experience "
        "types, and whether projects explicitly count. "
        "Each education requirement is one compound condition with its full "
        "original wording, minimum degree level, all alternative accepted "
        "fields, and whether a related field is explicitly accepted. "
        "soft_skills contains communication, teamwork, problem-solving, "
        "leadership, adaptability, organization, and similar skills. "
        "Never turn the years, alternatives, degree, or fields belonging to "
        "one condition into separate requirements. "
        "Extract only requirements supported by the job description. "
        "Do not invent or strengthen requirements. "
        "Use an empty list when a category is absent."
    )

    extracted = _call_structured_ai(
        JobRequirements,
        system_prompt,
        job_description,
    )

    return _normalize_compound_requirements(
        extracted,
        job_description,
    )


def _sanitize_candidate_profile(
    profile,
    cv_text,
):
    normalized_cv = normalize_text(
        cv_text
    )

    verified_skills = []

    for skill in profile.technical_skills:
        normalized_skill = (
            normalize_text(skill)
        )

        if (
            normalized_skill
            and normalized_skill
            in normalized_cv
            and skill not in verified_skills
        ):
            verified_skills.append(
                skill
            )

    cleaned_experience = []

    for item in profile.experience:
        verified_responsibilities = []

        for responsibility in (
            item.responsibilities
        ):
            normalized = normalize_text(
                responsibility
            )

            if (
                normalized
                and normalized
                in normalized_cv
            ):
                verified_responsibilities.append(
                    responsibility
                )

        cleaned_experience.append(
            item.model_copy(
                update={
                    "responsibilities":
                        verified_responsibilities
                }
            )
        )

    cleaned_education = []

    for item in profile.education:
        normalized_source = normalize_text(item.source_text)
        source_is_verified = (
            bool(normalized_source)
            and normalized_source in normalized_cv
        )
        normalized_institution = normalize_text(item.institution)
        institution_is_linked = (
            source_is_verified
            and bool(normalized_institution)
            and normalized_institution in normalized_source
        )

        cleaned_education.append(
            item.model_copy(
                update={
                    "institution": item.institution if institution_is_linked else "",
                    "source_text": item.source_text if source_is_verified else "",
                }
            )
        )

    cleaned_projects = []

    for item in profile.projects:
        verified_technologies = []

        for technology in (
            item.technologies
        ):
            normalized = normalize_text(
                technology
            )

            if (
                normalized
                and normalized
                in normalized_cv
            ):
                verified_technologies.append(
                    technology
                )

        cleaned_projects.append(
            item.model_copy(
                update={
                    "technologies":
                        verified_technologies
                }
            )
        )

    return profile.model_copy(
        update={
            "technical_skills":
                verified_skills,
            "education":
                cleaned_education,
            "experience":
                cleaned_experience,
            "projects":
                cleaned_projects,
        }
    )


def extract_candidate_profile(
    cv_text,
):
    system_prompt = (
        "You are a strict CV information extractor. "
        "Read the complete CV before creating the CandidateProfile. "
        "Use only information explicitly supported by the CV. "
        "Never invent information. "
        "Extract explicit technical skills such as programming languages, "
        "frameworks, libraries, databases, APIs, AI/ML tools, platforms, "
        "and software technologies. "
        "Keep every education record separate. "
        "Keep degree level, field of study, institution, dates, and status "
        "associated with the correct education record. "
        "PDF text order may occasionally be imperfect. "
        "If you cannot confidently associate an institution or date with "
        "a specific degree, leave that field empty or null instead of guessing. "
        "For every education record, source_text must be one exact contiguous "
        "excerpt from the CV that links the degree to its institution. If no "
        "such excerpt exists, leave source_text and institution empty. "
        "Keep every work role separate and preserve job title, company, dates, "
        "current status, and responsibilities. "
        "Responsibilities must stay close to the wording of the CV. "
        "Keep every project separate. "
        "Extract only project technologies explicitly present in the CV. "
        "Use null when a year is unavailable."
    )

    profile = _call_structured_ai(
        CandidateProfile,
        system_prompt,
        cv_text,
    )

    return _sanitize_candidate_profile(
        profile,
        cv_text,
    )


def _add_direct_skills_to_profile(
    candidate_profile,
    direct_matches,
):
    existing = {
        normalize_text(skill)
        for skill in (
            candidate_profile
            .technical_skills
        )
    }

    for analysis in (
        direct_matches.values()
    ):
        normalized = normalize_text(
            analysis.requirement
        )

        if normalized not in existing:
            candidate_profile.technical_skills.append(
                analysis.requirement
            )

            existing.add(
                normalized
            )


def _format_semantic_input(
    requirements,
    candidate_profile,
    unresolved_technical,
    unresolved_education,
    cv_lines,
):
    technical = [
        {
            "requirement_index": index,
            "requirement":
                requirements
                .technical_skills[index],
        }
        for index in unresolved_technical
    ]

    education = [
        {
            "requirement_index": index,
            "requirement":
                requirements
                .education_requirements[index]
                .model_dump(),
        }
        for index in unresolved_education
    ]

    experience = [
        {
            "requirement_index": index,
            "requirement": requirement.model_dump(),
        }
        for index, requirement in enumerate(
            requirements
            .experience_requirements
        )
    ]

    soft_skills = [
        {
            "requirement_index": index,
            "requirement": requirement,
        }
        for index, requirement in enumerate(
            requirements.soft_skills
        )
    ]

    payload = {
        "requirements_to_analyze": {
            "technical": technical,
            "education": education,
            "experience": experience,
            "soft_skill": soft_skills,
        },
        "candidate": {
            "technical_skills": [
                {
                    "index": index,
                    "skill": skill,
                }
                for index, skill
                in enumerate(
                    candidate_profile
                    .technical_skills
                )
            ],
            "education": [
                {
                    "index": index,
                    **item.model_dump(),
                }
                for index, item
                in enumerate(
                    candidate_profile.education
                )
            ],
            "experience": [
                {
                    "index": index,
                    **item.model_dump(),
                }
                for index, item
                in enumerate(
                    candidate_profile.experience
                )
            ],
            "projects": [
                {
                    "index": index,
                    **item.model_dump(),
                }
                for index, item
                in enumerate(
                    candidate_profile.projects
                )
            ],
            "cv_lines": [
                {
                    "index": index,
                    "text": line,
                }
                for index, line
                in enumerate(cv_lines)
            ],
        },
    }

    return json.dumps(
        payload,
        indent=2,
        ensure_ascii=False,
    )


def _run_semantic_batch(
    requirements,
    candidate_profile,
    unresolved_technical,
    unresolved_education,
    cv_lines,
):
    has_work = any(
        (
            unresolved_technical,
            unresolved_education,
            requirements
            .experience_requirements,
            requirements.soft_skills,
        )
    )

    if not has_work:
        return SemanticBatchResult()

    system_prompt = (
        "You are a strict CV-to-job semantic matching engine. "
        "You will receive multiple requirements and structured candidate data. "
        "Return exactly one SemanticDecision for every requirement supplied. "
        "Use the category and requirement_index exactly as provided. "
        "Never create decisions for requirements that were not supplied. "
        "Never invent candidate evidence. "
        "\n\n"
        "TECHNICAL: "
        "Return found only for the same technology or a clearly equivalent "
        "technical capability. Related but different technologies are not equivalent. "
        "Use matched_skill_index. Technical requirements should normally be "
        "found or missing, not partial. "
        "\n\n"
        "EDUCATION: "
        "Compare degree level and academic field semantically. "
        "Specialized engineering degrees belong to Engineering. "
        "Use matched_degree_index. "
        "Return partial only when the qualification is genuinely related but "
        "does not clearly satisfy every required condition. "
        "\n\n"
        "EXPERIENCE: "
        "Identify relevant work roles and projects. "
        "Use matched_experience_indexes for roles that provide relevant evidence. "
        "Use matched_project_indexes for relevant projects. "
        "IMPORTANT: duration_experience_indexes must contain only work roles "
        "where the WHOLE ROLE can reasonably count toward the requested type "
        "of experience. "
        "Do not put a role in duration_experience_indexes merely because one "
        "responsibility inside an otherwise different role is relevant. "
        "For example, a Sales Engineer role containing one software project "
        "does not prove that the entire Sales Engineer role was software "
        "development experience. "
        "Do not calculate years yourself. Python validates duration. "
        "\n\n"
        "SOFT SKILLS: "
        "Be conservative. "
        "Use matched_line_index only for a real CV line supplied in cv_lines. "
        "Return found only for explicit or strong direct evidence. "
        "Return partial when the line reasonably suggests the skill but does "
        "not establish it strongly. "
        "Do not claim teamwork simply because the candidate had a job. "
        "Do not claim problem-solving simply because a technical project exists. "
        "\n\n"
        "For every decision, explain the reasoning briefly."
    )

    semantic_input = (
        _format_semantic_input(
            requirements,
            candidate_profile,
            unresolved_technical,
            unresolved_education,
            cv_lines,
        )
    )

    return _call_structured_ai(
        SemanticBatchResult,
        system_prompt,
        semantic_input,
    )


def _decision_map(
    batch_result,
):
    result = {}

    for decision in (
        batch_result.decisions
    ):
        key = (
            decision.category,
            decision.requirement_index,
        )

        if key not in result:
            result[key] = decision

    return result


def _valid_index(
    index,
    collection,
):
    return (
        index is not None
        and 0 <= index
        < len(collection)
    )


def _valid_indexes(
    indexes,
    collection,
):
    valid = []

    for index in indexes:
        if (
            0 <= index
            < len(collection)
            and index not in valid
        ):
            valid.append(index)

    return valid


def _analyze_technical(
    requirements,
    cv_text,
    candidate_profile,
    decisions,
):
    direct_matches, unresolved = (
        find_direct_matches(
            requirements,
            cv_text,
        )
    )

    _add_direct_skills_to_profile(
        candidate_profile,
        direct_matches,
    )

    results = []

    for index, requirement in enumerate(
        requirements
    ):
        if index in direct_matches:
            results.append(
                direct_matches[index]
            )
            continue

        decision = decisions.get(
            (
                "technical",
                index,
            )
        )

        if decision is None:
            results.append(
                RequirementAnalysis(
                    requirement=requirement,
                    status="missing",
                    evidence=(
                        "No matching technical "
                        "skill found in the CV"
                    ),
                    reason=(
                        "No verified semantic "
                        "match was returned."
                    ),
                )
            )
            continue

        skill_index = (
            decision.matched_skill_index
        )

        if (
            decision.status == "found"
            and _valid_index(
                skill_index,
                candidate_profile
                .technical_skills,
            )
        ):
            results.append(
                RequirementAnalysis(
                    requirement=requirement,
                    status="found",
                    evidence=(
                        candidate_profile
                        .technical_skills[
                            skill_index
                        ]
                    ),
                    reason=decision.reason,
                )
            )

        else:
            results.append(
                RequirementAnalysis(
                    requirement=requirement,
                    status="missing",
                    evidence=(
                        "No matching technical "
                        "skill found in the CV"
                    ),
                    reason=(
                        "No verified matching "
                        "technical skill was found."
                    ),
                )
            )

    return results


def _education_evidence(
    item,
):
    degree = item.degree_level.strip()
    field = item.field_of_study.strip()

    if degree and field:
        return (
            f"{degree} of {field}"
        )

    if field:
        return field

    if degree:
        return degree

    return "Verified education record"


def _get_unresolved_education(
    requirements,
    candidate_profile,
):
    deterministic = {}
    unresolved = []

    for index, requirement in enumerate(
        requirements
    ):
        match_index = (
            find_deterministic_education_match(
                requirement,
                candidate_profile.education,
            )
        )

        if match_index is None:
            unresolved.append(index)
            continue

        item = (
            candidate_profile
            .education[match_index]
        )

        deterministic[index] = (
            RequirementAnalysis(
                requirement=_requirement_text(requirement),
                status="found",
                evidence=(
                    _education_evidence(
                        item
                    )
                ),
                reason=(
                    "The verified degree level "
                    "and academic field satisfy "
                    "the requirement."
                ),
            )
        )

    return deterministic, unresolved


def _analyze_education(
    requirements,
    candidate_profile,
    deterministic,
    decisions,
):
    results = []

    for index, requirement in enumerate(
        requirements
    ):
        if index in deterministic:
            results.append(
                deterministic[index]
            )
            continue

        decision = decisions.get(
            (
                "education",
                index,
            )
        )

        if decision is None:
            results.append(
                RequirementAnalysis(
                    requirement=_requirement_text(requirement),
                    status="missing",
                    evidence=(
                        "No matching education "
                        "found in the CV"
                    ),
                )
            )
            continue

        degree_index = (
            decision.matched_degree_index
        )

        if (
            decision.status
            in ("found", "partial")
            and _valid_index(
                degree_index,
                candidate_profile.education,
            )
        ):
            item = (
                candidate_profile
                .education[
                    degree_index
                ]
            )

            results.append(
                RequirementAnalysis(
                    requirement=_requirement_text(requirement),
                    status=decision.status,
                    evidence=(
                        _education_evidence(
                            item
                        )
                    ),
                    reason=decision.reason,
                )
            )

        else:
            results.append(
                RequirementAnalysis(
                    requirement=_requirement_text(requirement),
                    status="missing",
                    evidence=(
                        "No matching education "
                        "found in the CV"
                    ),
                    reason=decision.reason,
                )
            )

    return results


def _best_responsibility(
    requirement,
    responsibilities,
):
    if not responsibilities:
        return ""

    requirement_tokens = tokenize(
        _requirement_text(requirement)
    )

    best = responsibilities[0]
    best_score = -1

    for responsibility in (
        responsibilities
    ):
        responsibility_tokens = tokenize(
            responsibility
        )

        score = len(
            requirement_tokens.intersection(
                responsibility_tokens
            )
        )

        if score > best_score:
            best = responsibility
            best_score = score

    return best


def _experience_evidence(
    requirement,
    candidate_profile,
    experience_indexes,
    project_indexes,
):
    parts = []

    for index in experience_indexes[:2]:
        item = (
            candidate_profile
            .experience[index]
        )

        text = item.job_title

        if item.company:
            text += (
                f" at {item.company}"
            )

        text += (
            " ("
            + format_experience_period(
                item
            )
            + ")"
        )

        responsibility = (
            _best_responsibility(
                requirement,
                item.responsibilities,
            )
        )

        if responsibility:
            text += (
                f": {responsibility}"
            )

        parts.append(text)

    for index in project_indexes[:2]:
        project = (
            candidate_profile
            .projects[index]
        )

        text = (
            f"Project: {project.name}"
        )

        if project.technologies:
            text += (
                " ["
                + ", ".join(
                    project.technologies
                )
                + "]"
            )

        parts.append(text)

    return " | ".join(parts)


def _experience_type_tokens(experience_type):
    normalized = normalize_text(experience_type)
    normalized = normalized.replace(
        "artificial intelligence",
        "ai",
    )

    generic_tokens = {
        "project",
        "projects",
        "related",
        "experience",
    }

    return (
        tokenize(normalized)
        - generic_tokens
    )


def _find_deterministic_project_matches(
    requirement,
    projects,
):
    if not requirement.projects_allowed:
        return []

    accepted_token_sets = [
        tokens
        for experience_type in (
            requirement
            .accepted_experience_types
        )
        if (
            tokens := _experience_type_tokens(
                experience_type
            )
        )
    ]

    if not accepted_token_sets:
        return []

    matched_indexes = []

    for index, project in enumerate(
        projects
    ):
        project_text = " ".join(
            [
                project.name,
                project.description,
                *project.technologies,
            ]
        )

        normalized_project = (
            normalize_text(project_text)
            .replace(
                "artificial intelligence",
                "ai",
            )
        )

        project_tokens = tokenize(
            normalized_project
        )

        if any(
            required_tokens.issubset(
                project_tokens
            )
            for required_tokens in (
                accepted_token_sets
            )
        ):
            matched_indexes.append(
                index
            )

    return matched_indexes


def _analyze_experience(
    requirements,
    candidate_profile,
    decisions,
):
    results = []

    for index, requirement in enumerate(
        requirements
    ):
        decision = decisions.get(
            (
                "experience",
                index,
            )
        )

        if decision is None:
            experience_indexes = []
            duration_indexes = []
            project_indexes = []
            decision_status = "missing"
            decision_reason = ""

        else:
            experience_indexes = (
                _valid_indexes(
                    decision
                    .matched_experience_indexes,
                    candidate_profile.experience,
                )
            )

            duration_indexes = (
                _valid_indexes(
                    decision
                    .duration_experience_indexes,
                    candidate_profile.experience,
                )
            )

            project_indexes = (
                _valid_indexes(
                    decision
                    .matched_project_indexes,
                    candidate_profile.projects,
                )
            )

            decision_status = decision.status
            decision_reason = decision.reason

        if not requirement.projects_allowed:
            project_indexes = []

        deterministic_projects = (
            _find_deterministic_project_matches(
                requirement,
                candidate_profile.projects,
            )
        )

        project_indexes = _valid_indexes(
            project_indexes
            + deterministic_projects,
            candidate_profile.projects,
        )

        if (
            not experience_indexes
            and not project_indexes
        ):
            results.append(
                RequirementAnalysis(
                    requirement=_requirement_text(requirement),
                    status="missing",
                    evidence=(
                        "No matching experience "
                        "found in the CV"
                    ),
                    reason=decision_reason,
                )
            )
            continue

        final_status = decision_status
        reason = decision_reason

        if (
            decision_status == "missing"
            and deterministic_projects
        ):
            final_status = "found"
            reason = (
                "A verified project explicitly "
                "matches an accepted experience type."
            )

        required_years = (
            extract_required_years(
                requirement
            )
        )

        if required_years is not None:
            verified_months = (
                conservative_experience_months(
                    candidate_profile
                    .experience,
                    duration_indexes,
                )
            )

            required_months = (
                required_years * 12
            )

            if (
                final_status == "found"
                and verified_months
                >= required_months
            ):
                final_status = "found"

                reason += (
                    " The required duration "
                    "is conservatively supported "
                    "by relevant dated roles."
                )

            else:
                final_status = "partial"

                reason += (
                    " Relevant experience exists, "
                    "but the required duration "
                    "cannot be fully verified "
                    "from roles whose entire "
                    "duration can safely count."
                )

        evidence = (
            _experience_evidence(
                requirement,
                candidate_profile,
                experience_indexes,
                project_indexes,
            )
        )

        if not evidence:
            evidence = (
                "Relevant structured CV "
                "evidence found"
            )

        results.append(
            RequirementAnalysis(
                requirement=_requirement_text(requirement),
                status=final_status,
                evidence=evidence,
                reason=reason.strip(),
            )
        )

    return results


def _analyze_soft_skills(
    requirements,
    cv_lines,
    decisions,
):
    results = []

    for index, requirement in enumerate(
        requirements
    ):
        decision = decisions.get(
            (
                "soft_skill",
                index,
            )
        )

        if decision is None:
            results.append(
                RequirementAnalysis(
                    requirement=requirement,
                    status="missing",
                    evidence=(
                        "No supporting evidence "
                        "found in the CV"
                    ),
                )
            )
            continue

        line_index = (
            decision.matched_line_index
        )

        if (
            decision.status
            in ("found", "partial")
            and _valid_index(
                line_index,
                cv_lines,
            )
        ):
            results.append(
                RequirementAnalysis(
                    requirement=requirement,
                    status=decision.status,
                    evidence=(
                        cv_lines[line_index]
                    ),
                    reason=decision.reason,
                )
            )

        else:
            results.append(
                RequirementAnalysis(
                    requirement=requirement,
                    status="missing",
                    evidence=(
                        "No supporting evidence "
                        "found in the CV"
                    ),
                    reason=decision.reason,
                )
            )

    return results


def analyze_cv_with_ai(
    cv_text,
    requirements,
    candidate_profile,
):
    direct_technical, (
        unresolved_technical
    ) = find_direct_matches(
        requirements.technical_skills,
        cv_text,
    )

    _add_direct_skills_to_profile(
        candidate_profile,
        direct_technical,
    )

    deterministic_education, (
        unresolved_education
    ) = _get_unresolved_education(
        requirements.education_requirements,
        candidate_profile,
    )

    cv_lines = prepare_cv_lines(
        cv_text
    )

    batch_result = _run_semantic_batch(
        requirements,
        candidate_profile,
        unresolved_technical,
        unresolved_education,
        cv_lines,
    )

    decisions = _decision_map(
        batch_result
    )

    technical_analysis = (
        _analyze_technical(
            requirements.technical_skills,
            cv_text,
            candidate_profile,
            decisions,
        )
    )

    education_analysis = (
        _analyze_education(
            requirements
            .education_requirements,
            candidate_profile,
            deterministic_education,
            decisions,
        )
    )

    experience_analysis = (
        _analyze_experience(
            requirements
            .experience_requirements,
            candidate_profile,
            decisions,
        )
    )

    soft_skills_analysis = (
        _analyze_soft_skills(
            requirements.soft_skills,
            cv_lines,
            decisions,
        )
    )

    return CVAnalysis(
        technical_skills=(
            technical_analysis
        ),
        experience_requirements=(
            experience_analysis
        ),
        education_requirements=(
            education_analysis
        ),
        soft_skills=(
            soft_skills_analysis
        ),
    )


def _containing_sentence(text, fragment):
    normalized_fragment = normalize_text(fragment)
    for sentence in re.split(r"(?<=[.!?;])\s+|\n+", text):
        cleaned = sentence.strip(" \t-•")
        if normalized_fragment and normalized_fragment in normalize_text(cleaned):
            return cleaned
    return ""


def _unique_strings(values):
    result = []
    seen = set()
    for value in values:
        cleaned = value.strip()
        normalized = normalize_text(cleaned)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(cleaned)
    return result


def _extract_minimum_years(source):
    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
    }
    match = re.search(
        r"\b(?:at\s+least|minimum(?:\s+of)?)?\s*"
        r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
        r"\s*\+?\s+years?\b",
        source,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    value = match.group(1).lower()
    return int(value) if value.isdigit() else number_words[value]


def _split_alternatives(text):
    parts = re.split(
        r"\s*(?:,|\band/or\b|\bor\b)\s*",
        text,
        flags=re.IGNORECASE,
    )
    return _unique_strings(parts)


def _clean_requirement_tail(text):
    return re.sub(
        r"\s+(?:is|are|will\s+be)?\s*"
        r"(?:required|preferred|essential)\b.*$",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip(" .;:")


def _extract_experience_types(source):
    match = re.search(
        r"\bexperience\s+(?:in|with|of)\s+(.+)$",
        source,
        flags=re.IGNORECASE,
    )
    if not match:
        return []

    value = _clean_requirement_tail(match.group(1))
    return _split_alternatives(value)


def _extract_degree_level(source):
    normalized = normalize_text(source)
    checks = (
        ("phd", ("phd", "doctorate", "doctoral")),
        ("master", ("master", "msc", "m sc", "meng", "m eng")),
        ("bachelor", ("bachelor", "bsc", "b sc", "beng", "b eng")),
        ("associate", ("associate",)),
    )
    for level, terms in checks:
        if any(term in normalized for term in terms):
            return level
    return None


def _extract_education_fields(source):
    match = re.search(
        r"\bdegree\s+(?:in|of)\s+(.+)$",
        source,
        flags=re.IGNORECASE,
    )
    if not match:
        return [], False

    value = _clean_requirement_tail(match.group(1))
    fields = []
    related_field_allowed = False

    for part in _split_alternatives(value):
        normalized = normalize_text(part)
        if "related field" in normalized or "relevant field" in normalized:
            related_field_allowed = True
            continue
        fields.append(part.strip())

    return _unique_strings(fields), related_field_allowed


def _enrich_experience_requirement(item):
    source = item.original_requirement
    extracted_types = _extract_experience_types(source)
    minimum_years = item.minimum_years
    if minimum_years is None:
        minimum_years = _extract_minimum_years(source)

    accepted_types = _unique_strings(
        item.accepted_experience_types + extracted_types
    )
    projects_allowed = (
        item.projects_allowed
        or any("project" in normalize_text(value) for value in accepted_types)
    )

    return item.model_copy(
        update={
            "minimum_years": minimum_years,
            "accepted_experience_types": accepted_types,
            "projects_allowed": projects_allowed,
        }
    )


def _enrich_education_requirement(item):
    source = item.original_requirement
    extracted_fields, related_allowed = _extract_education_fields(source)
    degree_level = item.minimum_degree_level or _extract_degree_level(source)

    return item.model_copy(
        update={
            "minimum_degree_level": degree_level,
            "accepted_fields": _unique_strings(
                item.accepted_fields + extracted_fields
            ),
            "related_field_allowed": (
                item.related_field_allowed or related_allowed
            ),
        }
    )


def _normalize_compound_requirements(requirements, job_description):
    """Anchor and merge compound requirements by their source sentence."""
    experience = {}
    for item in requirements.experience_requirements:
        source = _containing_sentence(job_description, item.original_requirement)
        key = normalize_text(source)
        if not key:
            continue
        if key not in experience:
            experience[key] = item.model_copy(update={"original_requirement": source})
        else:
            current = experience[key]
            years = [value for value in (current.minimum_years, item.minimum_years) if value is not None]
            experience[key] = current.model_copy(update={
                "minimum_years": max(years) if years else None,
                "accepted_experience_types": _unique_strings(
                    current.accepted_experience_types + item.accepted_experience_types
                ),
                "projects_allowed": current.projects_allowed or item.projects_allowed,
            })

    education = {}
    for item in requirements.education_requirements:
        source = _containing_sentence(job_description, item.original_requirement)
        key = normalize_text(source)
        if not key:
            continue
        if key not in education:
            education[key] = item.model_copy(update={"original_requirement": source})
        else:
            current = education[key]
            levels = [value for value in (current.minimum_degree_level, item.minimum_degree_level) if value]
            lowest_level = min(levels, key=lambda value: {"associate": 1, "bachelor": 2, "master": 3, "phd": 4}[value]) if levels else None
            education[key] = current.model_copy(update={
                "minimum_degree_level": lowest_level,
                "accepted_fields": _unique_strings(current.accepted_fields + item.accepted_fields),
                "related_field_allowed": current.related_field_allowed or item.related_field_allowed,
            })

    return requirements.model_copy(update={
        "experience_requirements": [
            _enrich_experience_requirement(item)
            for item in experience.values()
        ],
        "education_requirements": [
            _enrich_education_requirement(item)
            for item in education.values()
        ],
    })
