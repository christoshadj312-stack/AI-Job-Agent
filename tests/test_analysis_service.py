import unittest
from unittest.mock import patch

from analysis_service import (
    _build_insights,
    analyze_application,
    analyze_uploaded_application,
)
from models import (
    CVAnalysis,
    CandidateProfile,
    JobRequirements,
    RequirementAnalysis,
)


class AnalysisServiceTests(unittest.TestCase):
    @patch("analysis_service.analyze_application")
    @patch("analysis_service.extract_cv_text_from_image")
    @patch("analysis_service.render_pdf_pages_as_png")
    @patch("analysis_service.extract_text_from_pdf_bytes")
    def test_scanned_pdf_uses_image_ocr(
        self,
        extract_pdf_text,
        render_pages,
        extract_image_text,
        analyze,
    ):
        from cv_parser import CVParserError

        extract_pdf_text.side_effect = CVParserError(
            "No readable text was found in the PDF."
        )
        render_pages.return_value = [
            b"page one",
            b"page two",
        ]
        extract_image_text.side_effect = [
            "First page",
            "Second page",
        ]

        analyze_uploaded_application(
            candidate_name="Christos",
            file_bytes=b"scanned pdf",
            content_type="application/pdf",
            job_description="Job description",
        )

        self.assertEqual(
            extract_image_text.call_count,
            2,
        )
        analyze.assert_called_once_with(
            candidate_name="Christos",
            cv_text="First page\n\nSecond page",
            job_description="Job description",
        )

    @patch("analysis_service.analyze_application")
    @patch("analysis_service.extract_cv_text_from_image")
    def test_image_upload_uses_ocr_text(
        self,
        extract_image_text,
        analyze,
    ):
        extract_image_text.return_value = "Python CV"

        analyze_uploaded_application(
            candidate_name="Christos",
            file_bytes=b"image bytes",
            content_type="image/png",
            job_description="Job description",
        )

        extract_image_text.assert_called_once_with(
            image_bytes=b"image bytes",
            mime_type="image/png",
        )
        analyze.assert_called_once_with(
            candidate_name="Christos",
            cv_text="Python CV",
            job_description="Job description",
        )

    @patch(
        "analysis_service.analyze_cv_with_ai"
    )
    @patch(
        "analysis_service.extract_candidate_profile"
    )
    @patch(
        "analysis_service.extract_job_requirements"
    )
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

        extract_requirements.return_value = (
            requirements
        )
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
                "building_candidate_profile",
                "extracting_job_requirements",
                "matching_candidate",
            ],
        )
        self.assertEqual(
            result.candidate_name,
            "Christos",
        )
        self.assertEqual(
            result.scores.technical_skills,
            100,
        )
        self.assertEqual(
            result.scores.experience,
            50,
        )
        self.assertIsNone(
            result.scores.education
        )
        self.assertEqual(
            result.scores.overall_match,
            75,
        )

        self.assertEqual(
            result.insights
            .strengths[0]
            .requirement,
            "Python",
        )
        self.assertEqual(
            result.insights.gaps[0].status,
            "partial",
        )
        self.assertEqual(
            result.insights
            .cv_improvement_suggestions[0]
            .priority,
            "medium",
        )

    def test_missing_skill_suggestion_is_conditional(
        self,
    ):
        analysis = CVAnalysis(
            technical_skills=[
                RequirementAnalysis(
                    requirement="Docker",
                    status="missing",
                    evidence=(
                        "No matching technical skill "
                        "found in the CV"
                    ),
                    reason=(
                        "No verified matching "
                        "technical skill was found."
                    ),
                )
            ]
        )

        insights = _build_insights(
            analysis
        )
        suggestion = (
            insights
            .cv_improvement_suggestions[0]
        )

        self.assertEqual(
            insights.strengths,
            [],
        )
        self.assertEqual(
            len(insights.gaps),
            1,
        )
        self.assertEqual(
            suggestion.priority,
            "high",
        )
        self.assertIn(
            "If you genuinely have experience",
            suggestion.suggestion,
        )
        self.assertIn(
            "Otherwise, leave it out",
            suggestion.suggestion,
        )
        self.assertTrue(
            insights.low_alignment
        )

    def test_low_alignment_ignores_soft_skill_only_match(
        self,
    ):
        analysis = CVAnalysis(
            technical_skills=[
                RequirementAnalysis(
                    requirement="Pastry production",
                    status="missing",
                    evidence="No matching skill found",
                )
            ],
            soft_skills=[
                RequirementAnalysis(
                    requirement="Teamwork",
                    status="found",
                    evidence="Worked with a sales team",
                )
            ],
        )

        insights = _build_insights(analysis)

        self.assertTrue(insights.low_alignment)
        self.assertIn(
            "does not contain verified evidence",
            insights.alignment_message,
        )


if __name__ == "__main__":
    unittest.main()
