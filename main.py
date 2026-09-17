from analyzer import (
    calculate_match_score,
)
from ai_service import (
    AIServiceError,
    analyze_cv_with_ai,
    extract_candidate_profile,
    extract_job_requirements,
)
from cv_parser import (
    CVParserError,
    extract_text_from_pdf,
)


def print_candidate_profile(
    candidate_profile,
):
    print("\nCandidate Profile:")

    print("\nTechnical Skills:")

    if candidate_profile.technical_skills:
        for skill in (
            candidate_profile
            .technical_skills
        ):
            print("-", skill)

    else:
        print("- None found")

    print("\nEducation:")

    if candidate_profile.education:
        for item in (
            candidate_profile.education
        ):
            print(
                "Degree Level:",
                item.degree_level,
            )

            print(
                "Field of Study:",
                item.field_of_study,
            )

            print(
                "Institution:",
                item.institution,
            )

            print(
                "Start Year:",
                item.start_year,
            )

            print(
                "End Year:",
                item.end_year,
            )

            print(
                "Status:",
                item.status,
            )

            print()

    else:
        print("- None found")

    print("\nExperience:")

    if candidate_profile.experience:
        for item in (
            candidate_profile.experience
        ):
            print(
                "Job Title:",
                item.job_title,
            )

            print(
                "Company:",
                item.company,
            )

            print(
                "Start Year:",
                item.start_year,
            )

            print(
                "End Year:",
                item.end_year,
            )

            print(
                "Current:",
                item.is_current,
            )

            print("Responsibilities:")

            if item.responsibilities:
                for responsibility in (
                    item.responsibilities
                ):
                    print(
                        "-",
                        responsibility,
                    )

            else:
                print("- None found")

            print()

    else:
        print("- None found")

    print("\nProjects:")

    if candidate_profile.projects:
        for item in (
            candidate_profile.projects
        ):
            print(
                "Project:",
                item.name,
            )

            print(
                "Description:",
                item.description,
            )

            print("Technologies:")

            if item.technologies:
                for technology in (
                    item.technologies
                ):
                    print(
                        "-",
                        technology,
                    )

            else:
                print("- None found")

            print()

    else:
        print("- None found")


def print_string_requirements(
    title,
    requirements,
):
    print(f"\n{title}:")

    if not requirements:
        print("- None specified")
        return

    for requirement in requirements:
        print(
            "-",
            requirement,
        )


def print_experience_requirements(
    requirements,
):
    print("\nExperience Requirements:")

    if not requirements:
        print("- None specified")
        return

    for requirement in requirements:
        print(
            "Requirement:",
            requirement.original_requirement,
        )

        print(
            "Minimum Years:",
            requirement.minimum_years,
        )

        print(
            "Accepted Experience Types:",
        )

        if (
            requirement
            .accepted_experience_types
        ):
            for experience_type in (
                requirement
                .accepted_experience_types
            ):
                print(
                    "-",
                    experience_type,
                )

        else:
            print("- None specified")

        print(
            "Projects Allowed:",
            requirement.projects_allowed,
        )

        print()


def print_education_requirements(
    requirements,
):
    print("\nEducation Requirements:")

    if not requirements:
        print("- None specified")
        return

    for requirement in requirements:
        print(
            "Requirement:",
            requirement.original_requirement,
        )

        print(
            "Minimum Degree Level:",
            requirement.minimum_degree_level,
        )

        print(
            "Accepted Fields:",
        )

        if requirement.accepted_fields:
            for field in (
                requirement.accepted_fields
            ):
                print(
                    "-",
                    field,
                )

        else:
            print("- None specified")

        print(
            "Related Field Allowed:",
            requirement.related_field_allowed,
        )

        print()


def print_job_requirements(
    requirements,
):
    print("\nJob Requirements:")

    print_string_requirements(
        "Technical Skills",
        requirements.technical_skills,
    )

    print_experience_requirements(
        requirements
        .experience_requirements
    )

    print_education_requirements(
        requirements
        .education_requirements
    )

    print_string_requirements(
        "Soft Skills",
        requirements.soft_skills,
    )


def print_requirement_analysis(
    title,
    analysis_items,
):
    print(f"\n{title}:")

    if not analysis_items:
        print("- None specified")
        return

    for item in analysis_items:
        print(
            "Requirement:",
            item.requirement,
        )

        print(
            "Status:",
            item.status.upper(),
        )

        print(
            "Evidence:",
            item.evidence,
        )

        if item.reason:
            print(
                "Reason:",
                item.reason,
            )

        print()


def print_category_score(
    title,
    analysis_items,
):
    score = calculate_match_score(
        analysis_items
    )

    if score is None:
        print(
            f"{title}: N/A"
        )
        return

    print(
        f"{title}: {score}%"
    )


def main():
    candidate_name = input(
        "Enter candidate name: "
    ).strip()

    cv_path = input(
        "Enter CV PDF path: "
    ).strip()

    job_description = input(
        "Enter job description: "
    ).strip()

    try:
        print(
            "\n[1/4] Reading CV...",
            flush=True,
        )

        cv_text = (
            extract_text_from_pdf(
                cv_path
            )
        )

        print(
            "[2/4] Extracting job requirements...",
            flush=True,
        )

        requirements = (
            extract_job_requirements(
                job_description
            )
        )

        print(
            "[3/4] Building candidate profile...",
            flush=True,
        )

        candidate_profile = (
            extract_candidate_profile(
                cv_text
            )
        )

        print(
            "[4/4] Matching candidate to job...",
            flush=True,
        )

        cv_analysis = (
            analyze_cv_with_ai(
                cv_text,
                requirements,
                candidate_profile,
            )
        )

        print(
            "Analysis complete.",
            flush=True,
        )

    except CVParserError as error:
        print(
            f"\nCV Error: {error}"
        )
        return

    except AIServiceError as error:
        print(
            f"\nAI Error: {error}"
        )
        return

    print(
        "\nCandidate:",
        candidate_name,
    )

    print_candidate_profile(
        candidate_profile
    )

    print_job_requirements(
        requirements
    )

    print_requirement_analysis(
        "Technical Skills Analysis",
        cv_analysis.technical_skills,
    )

    print_requirement_analysis(
        "Experience Analysis",
        cv_analysis
        .experience_requirements,
    )

    print_requirement_analysis(
        "Education Analysis",
        cv_analysis
        .education_requirements,
    )

    print_requirement_analysis(
        "Soft Skills Analysis",
        cv_analysis.soft_skills,
    )

    print("\nMatch Scores:")

    print_category_score(
        "Technical Skills",
        cv_analysis.technical_skills,
    )

    print_category_score(
        "Experience",
        cv_analysis
        .experience_requirements,
    )

    print_category_score(
        "Education",
        cv_analysis
        .education_requirements,
    )

    print_category_score(
        "Soft Skills",
        cv_analysis.soft_skills,
    )

    all_analysis = (
        cv_analysis.technical_skills
        + cv_analysis
        .experience_requirements
        + cv_analysis
        .education_requirements
        + cv_analysis.soft_skills
    )

    overall_score = (
        calculate_match_score(
            all_analysis
        )
    )

    if overall_score is not None:
        print(
            "Overall Match Score:",
            str(overall_score) + "%",
        )

    print(
        "\nScoring: "
        "FOUND = 1 point, "
        "PARTIAL = 0.5 points, "
        "MISSING = 0 points."
    )


if __name__ == "__main__":
    main()