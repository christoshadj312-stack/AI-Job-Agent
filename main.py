from analyzer import (
    calculate_match_score,
)
from ai_service import AIServiceError
from analysis_service import analyze_application
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


def print_job_requirements(
    requirements,
):
    print("\nJob Requirements:")

    categories = [
        (
            "Technical Skills",
            requirements.technical_skills,
        ),
        (
            "Experience Requirements",
            requirements
            .experience_requirements,
        ),
        (
            "Education Requirements",
            requirements
            .education_requirements,
        ),
        (
            "Soft Skills",
            requirements.soft_skills,
        ),
    ]

    for title, items in categories:
        print(f"\n{title}:")

        if items:
            for item in items:
                if hasattr(item, "original_requirement"):
                    print("-", item.original_requirement)
                    details = item.model_dump(exclude={"original_requirement"})
                    for name, value in details.items():
                        print(f"  {name}: {value}")
                else:
                    print("-", item)
        else:
            print("- None specified")


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

        progress_messages = {
            "extracting_job_requirements": (
                "[2/4] Extracting job requirements..."
            ),
            "building_candidate_profile": (
                "[3/4] Building candidate profile..."
            ),
            "matching_candidate": (
                "[4/4] Matching candidate to job..."
            ),
        }

        def print_progress(stage):
            print(
                progress_messages[stage],
                flush=True,
            )

        result = analyze_application(
            candidate_name=candidate_name,
            cv_text=cv_text,
            job_description=job_description,
            progress_callback=print_progress,
        )

        candidate_profile = result.candidate_profile
        requirements = result.job_requirements
        cv_analysis = result.analysis

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

    overall_score = result.scores.overall_match

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
