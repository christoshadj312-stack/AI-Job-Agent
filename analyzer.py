import re
from datetime import date

from models import EducationRequirement, RequirementAnalysis


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


TECHNICAL_SKILL_EQUIVALENCE_GROUPS = (
    (
        "scikit learn",
        "sklearn",
    ),
    (
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
    ),
    (
        "machine learning",
        "ml",
    ),
    (
        "artificial intelligence",
        "ai",
    ),
    (
        "postgresql",
        "postgres",
    ),
    (
        "javascript",
        "js",
    ),
    (
        "typescript",
        "ts",
    ),
    (
        "node js",
        "nodejs",
    ),
    (
        "react",
        "react js",
        "reactjs",
    ),
    (
        "amazon web services",
        "aws",
    ),
    (
        "google cloud platform",
        "gcp",
    ),
    (
        "microsoft azure",
        "azure",
    ),
    (
        "continuous integration continuous delivery",
        "ci cd",
        "cicd",
    ),
    (
        "c sharp",
        "c#",
    ),
    (
        "c plus plus",
        "c++",
    ),
)


def normalize_text(text):
    text = text.lower()

    text = re.sub(
        r"[^a-z0-9+#]+",
        " ",
        text,
    )

    return " ".join(
        text.split()
    )


def contains_normalized_phrase(
    text,
    phrase,
):
    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)

    if not normalized_phrase:
        return False

    pattern = (
        rf"(?:^| )"
        rf"{re.escape(normalized_phrase)}"
        rf"(?:$| )"
    )

    return re.search(
        pattern,
        normalized_text,
    ) is not None


def canonical_technical_skill(skill):
    normalized = normalize_text(skill)

    for group in TECHNICAL_SKILL_EQUIVALENCE_GROUPS:
        if normalized in group:
            return group[0]

    return normalized


def technical_skills_are_equivalent(
    requirement,
    candidate_skill,
):
    canonical_requirement = (
        canonical_technical_skill(
            requirement
        )
    )
    canonical_candidate = (
        canonical_technical_skill(
            candidate_skill
        )
    )

    return (
        bool(canonical_requirement)
        and canonical_requirement
        == canonical_candidate
    )


def tokenize(text):
    normalized_text = normalize_text(
        text
    )

    return {
        word
        for word in normalized_text.split()
        if len(word) > 1
        and word not in STOP_WORDS
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

        if contains_normalized_phrase(
            cleaned_line,
            normalized_requirement,
        ):
            return cleaned_line

    if contains_normalized_phrase(
        cv_text,
        normalized_requirement,
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
                        "The role-specific skill "
                        "appears explicitly in "
                        "the CV."
                    ),
                )
            )
        else:
            unresolved.append(index)

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


def get_required_degree_levels(
    requirement,
):
    normalized = normalize_text(
        requirement
    )

    levels = set()

    checks = {
        "phd": (
            "phd",
            "doctorate",
            "doctoral",
        ),
        "master": (
            "master",
            "msc",
            "m sc",
            "meng",
            "m eng",
        ),
        "bachelor": (
            "bachelor",
            "bsc",
            "b sc",
            "beng",
            "b eng",
        ),
        "associate": (
            "associate",
        ),
    }

    for level, terms in checks.items():
        if any(
            term in normalized
            for term in terms
        ):
            levels.add(level)

    return levels


def degree_level_satisfies(
    candidate_level,
    required_levels,
):
    if not required_levels:
        return True

    if candidate_level is None:
        return False

    if candidate_level in required_levels:
        return True

    if (
        "bachelor" in required_levels
        and DEGREE_RANKS.get(
            candidate_level,
            0,
        )
        >= DEGREE_RANKS["bachelor"]
    ):
        return True

    return False


def get_requirement_field_families(
    requirement,
):
    normalized = normalize_text(
        requirement
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


def candidate_matches_field_family(
    field_of_study,
    family,
):
    normalized_field = (
        normalize_text(
            field_of_study
        )
    )

    terms = FIELD_FAMILIES.get(
        family,
        (),
    )

    return any(
        term in normalized_field
        for term in terms
    )


def find_deterministic_education_match(
    requirement: EducationRequirement,
    education,
):
    required_levels = (
        {requirement.minimum_degree_level}
        if requirement.minimum_degree_level
        else set()
    )

    required_families = []
    for accepted_field in requirement.accepted_fields:
        families = get_requirement_field_families(accepted_field)
        if families:
            required_families.extend(families)

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
            required_levels,
        ):
            continue

        normalized_field = (
            normalize_text(
                item.field_of_study
            )
        )

        for accepted_field in requirement.accepted_fields:
            normalized_accepted = normalize_text(accepted_field)
            if (
                normalized_field
                and normalized_accepted
                and (
                    normalized_field in normalized_accepted
                    or normalized_accepted in normalized_field
                )
            ):
                return index

        for family in required_families:
            if candidate_matches_field_family(
                item.field_of_study,
                family,
            ):
                return index

        if not requirement.accepted_fields:
            return index

    return None


def extract_required_years(requirement):
    if hasattr(requirement, "minimum_years"):
        return requirement.minimum_years

    text = requirement.lower()

    patterns = (
        r"at least\s+(\d+)\s+years?",
        r"minimum(?:\s+of)?\s+(\d+)\s+years?",
        r"(\d+)\s*\+\s*years?",
        r"(\d+)\s+years?\s+of\s+experience",
        r"(\d+)\s+years?\s+experience",
    )

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
        )

        if match:
            return int(
                match.group(1)
            )

    range_match = re.search(
        r"(\d+)\s*[-–]\s*(\d+)"
        r"\s+years?",
        text,
    )

    if range_match:
        return int(
            range_match.group(1)
        )

    return None


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
):
    current_date = date.today()

    intervals = []

    for index in sorted(
        set(indexes)
    ):
        if (
            index < 0
            or index
            >= len(experience_items)
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
