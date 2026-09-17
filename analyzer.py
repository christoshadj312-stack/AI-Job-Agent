import re
from datetime import date

from models import (
    EducationRequirement,
    ExperienceRequirement,
    RequirementAnalysis,
)


PARTIAL_MATCH_CREDIT = 0.5


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "have",
    "in",
    "is",
    "of",
    "or",
    "the",
    "to",
    "with",
    "related",
    "required",
    "requirement",
    "requirements",
    "skill",
    "skills",
    "experience",
    "candidate",
}


DEGREE_RANKS = {
    "associate": 1,
    "bachelor": 2,
    "master": 3,
    "phd": 4,
}


FIELD_FAMILIES = {
    "engineering": (
        "engineering",
    ),
    "computer science": (
        "computer science",
        "computing",
        "informatics",
    ),
    "artificial intelligence": (
        "artificial intelligence",
        "machine learning",
    ),
    "data science": (
        "data science",
        "data analytics",
    ),
    "mathematics": (
        "mathematics",
        "math",
    ),
    "statistics": (
        "statistics",
        "statistical",
    ),
    "physics": (
        "physics",
    ),
    "chemistry": (
        "chemistry",
        "chemical science",
    ),
    "information technology": (
        "information technology",
        "information systems",
    ),
}


def normalize_text(text):
    if not text:
        return ""

    normalized = str(text).lower()

    normalized = re.sub(
        r"[^a-z0-9+#]+",
        " ",
        normalized,
    )

    return " ".join(
        normalized.split()
    )


def tokenize(text):
    normalized_text = normalize_text(
        text
    )

    return {
        word
        for word in normalized_text.split()
        if (
            len(word) > 1
            and word not in STOP_WORDS
        )
    }


def calculate_match_score(
    analysis_items,
):
    if not analysis_items:
        return None

    total_points = 0.0

    for item in analysis_items:
        if item.status == "found":
            total_points += 1.0

        elif item.status == "partial":
            total_points += (
                PARTIAL_MATCH_CREDIT
            )

    score = (
        total_points
        / len(analysis_items)
    ) * 100

    return round(score)


def find_direct_evidence(
    requirement,
    cv_text,
):
    normalized_requirement = (
        normalize_text(
            requirement
        )
    )

    if not normalized_requirement:
        return None

    for line in cv_text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        normalized_line = (
            normalize_text(
                cleaned_line
            )
        )

        if (
            normalized_requirement
            in normalized_line
        ):
            return cleaned_line

    normalized_cv = normalize_text(
        cv_text
    )

    if (
        normalized_requirement
        in normalized_cv
    ):
        return requirement

    return None


def find_direct_matches(
    requirements,
    cv_text,
):
    matched = {}
    unresolved = []

    for index, requirement in enumerate(
        requirements
    ):
        evidence = (
            find_direct_evidence(
                requirement,
                cv_text,
            )
        )

        if evidence:
            matched[index] = (
                RequirementAnalysis(
                    requirement=requirement,
                    status="found",
                    evidence=evidence,
                    reason=(
                        "The technical skill "
                        "appears explicitly in "
                        "the CV."
                    ),
                )
            )

        else:
            unresolved.append(
                index
            )

    return matched, unresolved


def canonical_degree_level(
    text,
):
    normalized = normalize_text(
        text
    )

    if any(
        term in normalized
        for term in (
            "phd",
            "doctorate",
            "doctoral",
            "doctor of philosophy",
        )
    ):
        return "phd"

    if any(
        term in normalized
        for term in (
            "master",
            "msc",
            "m sc",
            "meng",
            "m eng",
        )
    ):
        return "master"

    if any(
        term in normalized
        for term in (
            "bachelor",
            "bsc",
            "b sc",
            "beng",
            "b eng",
        )
    ):
        return "bachelor"

    if "associate" in normalized:
        return "associate"

    return None


def degree_level_satisfies(
    candidate_level,
    required_level,
):
    if required_level is None:
        return True

    if candidate_level is None:
        return False

    candidate_rank = (
        DEGREE_RANKS.get(
            candidate_level
        )
    )

    required_rank = (
        DEGREE_RANKS.get(
            required_level
        )
    )

    if (
        candidate_rank is None
        or required_rank is None
    ):
        return False

    return (
        candidate_rank
        >= required_rank
    )


def get_field_families(
    field_text,
):
    normalized = normalize_text(
        field_text
    )

    families = []

    for family, terms in (
        FIELD_FAMILIES.items()
    ):
        if any(
            term in normalized
            for term in terms
        ):
            families.append(
                family
            )

    return families


def fields_match_directly(
    candidate_field,
    accepted_field,
):
    normalized_candidate = (
        normalize_text(
            candidate_field
        )
    )

    normalized_accepted = (
        normalize_text(
            accepted_field
        )
    )

    if (
        not normalized_candidate
        or not normalized_accepted
    ):
        return False

    return (
        normalized_candidate
        in normalized_accepted
        or normalized_accepted
        in normalized_candidate
    )


def fields_share_family(
    candidate_field,
    accepted_field,
):
    candidate_families = set(
        get_field_families(
            candidate_field
        )
    )

    accepted_families = set(
        get_field_families(
            accepted_field
        )
    )

    return bool(
        candidate_families.intersection(
            accepted_families
        )
    )


def find_deterministic_education_match(
    requirement: EducationRequirement,
    education,
):
    for index, item in enumerate(
        education
    ):
        candidate_level = (
            canonical_degree_level(
                item.degree_level
            )
        )

        if not degree_level_satisfies(
            candidate_level,
            requirement.minimum_degree_level,
        ):
            continue

        if not requirement.accepted_fields:
            return index

        for accepted_field in (
            requirement.accepted_fields
        ):
            if fields_match_directly(
                item.field_of_study,
                accepted_field,
            ):
                return index

            if fields_share_family(
                item.field_of_study,
                accepted_field,
            ):
                return index

    return None


def extract_required_years(
    requirement: ExperienceRequirement,
):
    return requirement.minimum_years


def _conservative_role_interval(
    experience_item,
    current_date,
):
    if (
        experience_item.start_year
        is None
    ):
        return None

    start_month = (
        experience_item.start_year
        * 12
        + 11
    )

    if experience_item.is_current:
        end_month = (
            current_date.year
            * 12
            + current_date.month
            - 1
        )

    elif (
        experience_item.end_year
        is not None
    ):
        end_month = (
            experience_item.end_year
            * 12
        )

    else:
        return None

    if end_month <= start_month:
        return None

    return (
        start_month,
        end_month,
    )


def conservative_experience_months(
    experience_items,
    indexes,
    current_date=None,
):
    if current_date is None:
        current_date = date.today()

    intervals = []

    for index in sorted(
        set(indexes)
    ):
        if (
            index < 0
            or index >= len(
                experience_items
            )
        ):
            continue

        interval = (
            _conservative_role_interval(
                experience_items[index],
                current_date,
            )
        )

        if interval is not None:
            intervals.append(
                interval
            )

    if not intervals:
        return 0

    intervals.sort(
        key=lambda item: item[0]
    )

    merged = [
        intervals[0]
    ]

    for start, end in intervals[1:]:
        previous_start, previous_end = (
            merged[-1]
        )

        if start <= previous_end:
            merged[-1] = (
                previous_start,
                max(
                    previous_end,
                    end,
                ),
            )

        else:
            merged.append(
                (
                    start,
                    end,
                )
            )

    return sum(
        end - start
        for start, end in merged
    )


def format_experience_period(
    experience_item,
):
    if (
        experience_item.start_year
        is None
    ):
        start = "Unknown"

    else:
        start = str(
            experience_item.start_year
        )

    if experience_item.is_current:
        end = "Present"

    elif (
        experience_item.end_year
        is not None
    ):
        end = str(
            experience_item.end_year
        )

    else:
        end = "Unknown"

    return f"{start}–{end}"


def prepare_cv_lines(
    cv_text,
    max_lines=80,
):
    lines = []

    for raw_line in (
        cv_text.splitlines()
    ):
        cleaned_line = (
            raw_line.strip()
        )

        if not cleaned_line:
            continue

        if cleaned_line in lines:
            continue

        lines.append(
            cleaned_line[:300]
        )

        if len(lines) >= max_lines:
            break

    return lines