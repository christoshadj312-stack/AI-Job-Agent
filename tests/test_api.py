import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from models import (
    ApplicationAnalysisResult,
    CVAnalysis,
    CandidateProfile,
    JobRequirements,
    MatchScores,
)


class APITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok"},
        )

    def test_analysis_rejects_non_pdf_upload(self):
        response = self.client.post(
            "/api/v1/analyses",
            data={
                "candidate_name": "Christos",
                "job_description": (
                    "A sufficiently long job description."
                ),
            },
            files={
                "cv_file": (
                    "cv.txt",
                    b"not a pdf",
                    "text/plain",
                )
            },
        )

        self.assertEqual(response.status_code, 415)

    @patch(
        "api.routes.analysis.analyze_pdf_application"
    )
    def test_analysis_returns_structured_result(
        self,
        analyze_pdf,
    ):
        analyze_pdf.return_value = (
            ApplicationAnalysisResult(
                candidate_name="Christos",
                candidate_profile=CandidateProfile(),
                job_requirements=JobRequirements(),
                analysis=CVAnalysis(),
                scores=MatchScores(),
            )
        )

        response = self.client.post(
            "/api/v1/analyses",
            data={
                "candidate_name": "Christos",
                "job_description": (
                    "A sufficiently long job description."
                ),
            },
            files={
                "cv_file": (
                    "CV.pdf",
                    b"mock pdf bytes",
                    "application/pdf",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["candidate_name"],
            "Christos",
        )
        self.assertIn("scores", response.json())


if __name__ == "__main__":
    unittest.main()
