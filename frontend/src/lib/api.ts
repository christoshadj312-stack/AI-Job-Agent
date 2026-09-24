export type MatchStatus =
  | "FOUND"
  | "PARTIAL"
  | "MISSING"
  | "found"
  | "partial"
  | "missing";

export interface Education {
  degree_level: string;
  field_of_study: string;
  institution: string;
  start_year: number | null;
  end_year: number | null;
  status: string;
  source_text: string;
}

export interface WorkExperience {
  job_title: string;
  company: string;
  start_year: number | null;
  end_year: number | null;
  is_current: boolean;
  responsibilities: string[];
}

export interface CandidateProject {
  name: string;
  description: string;
  technologies: string[];
}

export interface CandidateProfile {
  technical_skills: string[];
  education: Education[];
  experience: WorkExperience[];
  projects: CandidateProject[];
}

export interface ExperienceRequirement {
  original_requirement: string;
  minimum_years: number | null;
  accepted_experience_types: string[];
  projects_allowed: boolean;
}

export interface EducationRequirement {
  original_requirement: string;
  minimum_degree_level: string;
  accepted_fields: string[];
  related_field_allowed: boolean;
}

export interface JobRequirements {
  technical_skills: string[];
  experience_requirements: ExperienceRequirement[];
  education_requirements: EducationRequirement[];
  soft_skills: string[];
}

export interface RequirementMatch {
  requirement: string;
  status: MatchStatus;
  evidence: string;
  reason: string;
}

export interface MatchAnalysis {
  technical_skills: RequirementMatch[];
  experience_requirements: RequirementMatch[];
  education_requirements: RequirementMatch[];
  soft_skills: RequirementMatch[];
}

export interface MatchScores {
  technical_skills: number | null;
  experience: number | null;
  education: number | null;
  soft_skills: number | null;
  overall_match: number | null;
}

export interface ApplicationAnalysisResult {
  candidate_name: string;
  candidate_profile: CandidateProfile;
  job_requirements: JobRequirements;
  analysis: MatchAnalysis;
  scores: MatchScores;
}

export interface CreateAnalysisInput {
  candidateName: string;
  jobDescription: string;
  cvFile: File;
}

interface ErrorResponse {
  detail?: string;
}

const DEFAULT_API_URL = "http://localhost:8000";

const configuredApiUrl =
  import.meta.env["VITE_API_BASE_URL"];

const API_BASE_URL = (
  configuredApiUrl || DEFAULT_API_URL
).replace(/\/+$/, "");

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function createAnalysis(
  input: CreateAnalysisInput,
  signal?: AbortSignal,
): Promise<ApplicationAnalysisResult> {
  const formData = new FormData();

  formData.append(
    "candidate_name",
    input.candidateName.trim(),
  );
  formData.append(
    "job_description",
    input.jobDescription.trim(),
  );
  formData.append("cv_file", input.cvFile);

  const response = await fetch(
    `${API_BASE_URL}/api/v1/analyses`,
    {
      method: "POST",
      body: formData,
      signal: signal ?? null,
    },
  );

  if (!response.ok) {
    let message =
      "The analysis could not be completed.";

    try {
      const errorResponse =
        (await response.json()) as ErrorResponse;

      if (
        typeof errorResponse.detail === "string" &&
        errorResponse.detail.trim()
      ) {
        message = errorResponse.detail;
      }
    } catch {
      // Keep the safe default message when the server
      // does not return a JSON error response.
    }

    throw new ApiError(message, response.status);
  }

  return (
    await response.json()
  ) as ApplicationAnalysisResult;
}