from typing import Literal

from pydantic import BaseModel, Field


RequirementStatus = Literal[
    "found",
    "partial",
    "missing",
]


DegreeLevel = Literal[
    "associate",
    "bachelor",
    "master",
    "phd",
]


class ExperienceRequirement(BaseModel):
    original_requirement: str = Field(min_length=1)
    minimum_years: int | None = Field(default=None, ge=0)
    accepted_experience_types: list[str] = Field(default_factory=list)
    projects_allowed: bool = False


class EducationRequirement(BaseModel):
    original_requirement: str = Field(min_length=1)
    minimum_degree_level: DegreeLevel | None = None
    accepted_fields: list[str] = Field(default_factory=list)
    related_field_allowed: bool = False


class JobRequirements(BaseModel):
    technical_skills: list[str] = Field(default_factory=list)
    experience_requirements: list[ExperienceRequirement] = Field(default_factory=list)
    education_requirements: list[EducationRequirement] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)


class RequirementAnalysis(BaseModel):
    requirement: str
    status: RequirementStatus
    evidence: str
    reason: str = ""


class EducationItem(BaseModel):
    degree_level: str
    field_of_study: str
    institution: str = ""
    start_year: int | None = None
    end_year: int | None = None
    status: str = ""
    source_text: str = ""


class ExperienceItem(BaseModel):
    job_title: str
    company: str = ""
    start_year: int | None = None
    end_year: int | None = None
    is_current: bool = False
    responsibilities: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    technical_skills: list[str] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)


class SemanticDecision(BaseModel):
    category: Literal[
        "technical",
        "education",
        "experience",
        "soft_skill",
    ]

    requirement_index: int

    status: RequirementStatus

    matched_skill_index: int | None = None

    matched_degree_index: int | None = None

    matched_experience_indexes: list[int] = Field(
        default_factory=list
    )

    duration_experience_indexes: list[int] = Field(
        default_factory=list
    )

    matched_project_indexes: list[int] = Field(
        default_factory=list
    )

    matched_line_index: int | None = None

    reason: str = ""


class SemanticBatchResult(BaseModel):
    decisions: list[SemanticDecision] = Field(
        default_factory=list
    )


class CVAnalysis(BaseModel):
    technical_skills: list[RequirementAnalysis] = Field(
        default_factory=list
    )

    experience_requirements: list[RequirementAnalysis] = Field(
        default_factory=list
    )

    education_requirements: list[RequirementAnalysis] = Field(
        default_factory=list
    )

    soft_skills: list[RequirementAnalysis] = Field(
        default_factory=list
    )


class MatchScores(BaseModel):
    technical_skills: int | None = None
    experience: int | None = None
    education: int | None = None
    soft_skills: int | None = None
    overall_match: int | None = None


class ApplicationAnalysisResult(BaseModel):
    candidate_name: str
    candidate_profile: CandidateProfile
    job_requirements: JobRequirements
    analysis: CVAnalysis
    scores: MatchScores
