import unittest

from ai_service import _analyze_experience, _normalize_compound_requirements
from analyzer import find_deterministic_education_match
from models import (
    CandidateProfile,
    EducationItem,
    EducationRequirement,
    ExperienceRequirement,
    JobRequirements,
    ProjectItem,
    SemanticDecision,
)


JOB_DESCRIPTION = (
    "We are looking for a Junior AI Engineer with experience in Python, "
    "Machine Learning, Scikit-learn, REST APIs, Docker and SQL. "
    "Candidates should have at least 1 year of experience in software "
    "development or AI-related projects. A Bachelor's degree in Computer "
    "Science, Engineering or a related field is required. Strong "
    "communication, teamwork and problem-solving skills are essential."
)


class CompoundRequirementTests(unittest.TestCase):
    def test_split_experience_fragments_are_merged(self):
        requirements = JobRequirements(
            experience_requirements=[
                ExperienceRequirement(
                    original_requirement="at least 1 year",
                    minimum_years=1,
                ),
                ExperienceRequirement(
                    original_requirement="software development",
                    accepted_experience_types=["software development"],
                ),
                ExperienceRequirement(
                    original_requirement="AI-related projects",
                    accepted_experience_types=["AI-related projects"],
                    projects_allowed=True,
                ),
            ]
        )

        normalized = _normalize_compound_requirements(
            requirements, JOB_DESCRIPTION
        )

        self.assertEqual(len(normalized.experience_requirements), 1)
        item = normalized.experience_requirements[0]
        self.assertEqual(item.minimum_years, 1)
        self.assertEqual(
            item.accepted_experience_types,
            ["software development", "AI-related projects"],
        )
        self.assertTrue(item.projects_allowed)

    def test_unanchored_requirement_is_rejected(self):
        requirements = JobRequirements(
            experience_requirements=[
                ExperienceRequirement(
                    original_requirement="five years of cybersecurity experience",
                    minimum_years=5,
                    accepted_experience_types=["cybersecurity"],
                )
            ]
        )

        normalized = _normalize_compound_requirements(
            requirements, JOB_DESCRIPTION
        )

        self.assertEqual(normalized.experience_requirements, [])

    def test_empty_experience_fields_are_enriched_from_source(self):
        requirements = JobRequirements(
            experience_requirements=[
                ExperienceRequirement(
                    original_requirement=(
                        "Candidates should have at least 1 year of experience "
                        "in software development or AI-related projects."
                    ),
                    projects_allowed=True,
                )
            ]
        )

        normalized = _normalize_compound_requirements(
            requirements, JOB_DESCRIPTION
        )
        item = normalized.experience_requirements[0]

        self.assertEqual(item.minimum_years, 1)
        self.assertEqual(
            item.accepted_experience_types,
            ["software development", "AI-related projects"],
        )
        self.assertTrue(item.projects_allowed)

    def test_empty_education_fields_are_enriched_from_source(self):
        requirements = JobRequirements(
            education_requirements=[
                EducationRequirement(
                    original_requirement=(
                        "A Bachelor's degree in Computer Science, Engineering "
                        "or a related field is required."
                    ),
                    related_field_allowed=True,
                )
            ]
        )

        normalized = _normalize_compound_requirements(
            requirements, JOB_DESCRIPTION
        )
        item = normalized.education_requirements[0]

        self.assertEqual(item.minimum_degree_level, "bachelor")
        self.assertEqual(item.accepted_fields, ["Computer Science", "Engineering"])
        self.assertTrue(item.related_field_allowed)

    def test_split_education_fragments_are_merged(self):
        requirements = JobRequirements(
            education_requirements=[
                EducationRequirement(
                    original_requirement="Bachelor's degree",
                    minimum_degree_level="bachelor",
                ),
                EducationRequirement(
                    original_requirement="Computer Science",
                    accepted_fields=["Computer Science"],
                ),
                EducationRequirement(
                    original_requirement="Engineering",
                    accepted_fields=["Engineering"],
                    related_field_allowed=True,
                ),
            ]
        )

        normalized = _normalize_compound_requirements(
            requirements, JOB_DESCRIPTION
        )

        self.assertEqual(len(normalized.education_requirements), 1)
        item = normalized.education_requirements[0]
        self.assertEqual(item.minimum_degree_level, "bachelor")
        self.assertEqual(item.accepted_fields, ["Computer Science", "Engineering"])
        self.assertTrue(item.related_field_allowed)

    def test_mechanical_engineering_satisfies_engineering(self):
        requirement = EducationRequirement(
            original_requirement="Bachelor's degree in Computer Science or Engineering",
            minimum_degree_level="bachelor",
            accepted_fields=["Computer Science", "Engineering"],
        )
        education = [
            EducationItem(
                degree_level="Bachelor",
                field_of_study="Mechanical Engineering",
            )
        ]

        self.assertEqual(
            find_deterministic_education_match(requirement, education), 0
        )

    def test_project_without_verified_duration_is_partial(self):
        requirement = ExperienceRequirement(
            original_requirement=(
                "At least 1 year of experience in software development "
                "or AI-related projects"
            ),
            minimum_years=1,
            accepted_experience_types=["software development", "AI-related projects"],
            projects_allowed=True,
        )
        profile = CandidateProfile(
            projects=[
                ProjectItem(
                    name="PV Visit Planner",
                    technologies=["React", "REST APIs"],
                )
            ]
        )
        decisions = {
            ("experience", 0): SemanticDecision(
                category="experience",
                requirement_index=0,
                status="found",
                matched_project_indexes=[0],
            )
        }

        result = _analyze_experience([requirement], profile, decisions)

        self.assertEqual(result[0].status, "partial")
        self.assertIn("PV Visit Planner", result[0].evidence)

    def test_deterministic_project_fallback_corrects_llm_miss(self):
        requirement = ExperienceRequirement(
            original_requirement=(
                "At least 1 year of experience in software development "
                "or AI-related projects"
            ),
            minimum_years=1,
            accepted_experience_types=[
                "software development",
                "AI-related projects",
            ],
            projects_allowed=True,
        )
        profile = CandidateProfile(
            projects=[
                ProjectItem(
                    name="PV Visit Planner — AI-Powered Web Application",
                    technologies=["React", "REST APIs", "AI Integration"],
                )
            ]
        )
        decisions = {
            ("experience", 0): SemanticDecision(
                category="experience",
                requirement_index=0,
                status="missing",
            )
        }

        result = _analyze_experience([requirement], profile, decisions)

        self.assertEqual(result[0].status, "partial")
        self.assertIn("PV Visit Planner", result[0].evidence)

    def test_deterministic_project_fallback_handles_missing_decision(self):
        requirement = ExperienceRequirement(
            original_requirement=(
                "At least 1 year of experience in software development "
                "or AI-related projects"
            ),
            minimum_years=1,
            accepted_experience_types=[
                "software development",
                "AI-related projects",
            ],
            projects_allowed=True,
        )
        profile = CandidateProfile(
            projects=[
                ProjectItem(
                    name="PV Visit Planner — AI-Powered Web Application",
                    technologies=["React", "REST APIs", "AI Integration"],
                )
            ]
        )

        result = _analyze_experience([requirement], profile, {})

        self.assertEqual(result[0].status, "partial")
        self.assertIn("PV Visit Planner", result[0].evidence)


if __name__ == "__main__":
    unittest.main()
