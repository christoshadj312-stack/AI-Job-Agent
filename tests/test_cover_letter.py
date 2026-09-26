import unittest

from fastapi.testclient import TestClient

from api.main import app
from cover_letter_service import (
    NoVerifiedEvidenceError,
    compose_cover_letter,
)
from models import (
    ApplicationAnalysisResult,
    ApplicationInsights,
    CVAnalysis,
    CandidateProfile,
    CoverLetterRequest,
    JobRequirements,
    MatchInsight,
    MatchScores,
)


def request_with(strengths):
    return CoverLetterRequest(
        analysis=ApplicationAnalysisResult(
            candidate_name="Alex Candidate",
            candidate_profile=CandidateProfile(),
            job_requirements=JobRequirements(),
            analysis=CVAnalysis(),
            scores=MatchScores(),
            insights=ApplicationInsights(strengths=strengths),
        ),
        job_title="AI Engineer",
        company_name="Example Co",
    )


class CoverLetterTests(unittest.TestCase):
    def test_endpoint_returns_draft_for_current_analysis(self):
        request = request_with([
            MatchInsight(
                category="technical_skill",
                requirement="Python",
                status="found",
                evidence="Built a Python project",
            ),
        ])
        response = TestClient(app).post(
            "/api/v1/cover-letters",
            json=request.model_dump(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Built a Python project", response.json()["text"])

    def test_uses_verified_evidence_without_claiming_unverified_skills(self):
        request = request_with([
            MatchInsight(
                category="technical_skill",
                requirement="Python",
                status="found",
                evidence="Built a Python project",
            ),
            MatchInsight(
                category="technical_skill",
                requirement="Docker",
                status="missing",
                evidence="",
            ),
            MatchInsight(
                category="technical_skill",
                requirement="SQL",
                status="partial",
                evidence="Related database experience",
            ),
        ])

        result = compose_cover_letter(request)

        self.assertIn("Built a Python project", result.text)
        self.assertIn("AI Engineer position at Example Co", result.text)
        self.assertNotIn("Docker", result.text)
        self.assertNotIn("SQL", result.text)
        self.assertEqual(len(result.evidence_used), 1)

    def test_groups_skills_into_natural_sentence(self):
        request = request_with([
            MatchInsight(
                category="technical_skill",
                requirement="Python",
                status="found",
                evidence="Python",
            ),
            MatchInsight(
                category="technical_skill",
                requirement="machine learning",
                status="found",
                evidence="Machine Learning",
            ),
            MatchInsight(
                category="technical_skill",
                requirement="scikit-learn",
                status="found",
                evidence="Scikit-learn",
            ),
        ])

        result = compose_cover_letter(request)

        self.assertIn(
            "includes Python, machine learning, and scikit-learn",
            result.text,
        )
        self.assertNotIn("my CV records", result.text)

    def test_rejects_analysis_without_verified_evidence(self):
        with self.assertRaises(NoVerifiedEvidenceError):
            compose_cover_letter(request_with([]))


if __name__ == "__main__":
    unittest.main()
