import unittest
from unittest.mock import patch

from analysis_service import analyze_application
from models import (
    CVAnalysis,
    CandidateProfile,
    JobRequirements,
    RequirementAnalysis,
)


class AnalysisServiceTests(unittest.TestCase):
    @patch("analysis_service.analyze_cv_with_ai")
    @patch("analysis_service.extract_candidate_profile")
    @patch("analysis_service.extract_job_requirements")
    def test_pipeline_returns_scores_and_progress(
        self,
        extract_requirements,
        extract_profile,
        analyze_cv,
    ):
        requirements = JobRequirements(
            technical_skills=["Python"]
        )
        profile = CandidateProfile(
            technical_skills=["Python"]
        )
        analysis = CVAnalysis(
            technical_skills=[
                RequirementAnalysis(
                    requirement="Python",
                    status="found",
                    evidence="Python",
                )
            ],
            experience_requirements=[
                RequirementAnalysis(
                    requirement="AI experience",
                    status="partial",
                    evidence="AI project",
                )
            ],
        )
        extract_requirements.return_value = requirements
        extract_profile.return_value = profile
        analyze_cv.return_value = analysis
        progress = []

        result = analyze_application(
            candidate_name="Christos",
            cv_text="CV text",
            job_description="Job description",
            progress_callback=progress.append,
        )

        self.assertEqual(
            progress,
            [
                "extracting_job_requirements",
                "building_candidate_profile",
                "matching_candidate",
            ],
        )
        self.assertEqual(result.candidate_name, "Christos")
        self.assertEqual(result.scores.technical_skills, 100)
        self.assertEqual(result.scores.experience, 50)
        self.assertIsNone(result.scores.education)
        self.assertEqual(result.scores.overall_match, 75)


if __name__ == "__main__":
    unittest.main()
