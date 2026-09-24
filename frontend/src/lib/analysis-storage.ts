import type { ApplicationAnalysisResult } from "@/lib/api";

export interface AnalysisSession {
  result: ApplicationAnalysisResult;
  jobTitle: string;
  companyName: string;
  jobDescription: string;
  createdAt: string;
}

const STORAGE_KEY =
  "jobmatch-ai:current-analysis";

export function saveAnalysisSession(
  analysis: AnalysisSession,
): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(analysis),
  );
}

export function loadAnalysisSession():
  | AnalysisSession
  | null {
  if (typeof window === "undefined") {
    return null;
  }

  const storedValue =
    window.sessionStorage.getItem(STORAGE_KEY);

  if (!storedValue) {
    return null;
  }

  try {
    const parsedValue: unknown =
      JSON.parse(storedValue);

    if (!isAnalysisSession(parsedValue)) {
      window.sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }

    return parsedValue;
  } catch {
    window.sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function clearAnalysisSession(): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(STORAGE_KEY);
}

function isAnalysisSession(
  value: unknown,
): value is AnalysisSession {
  if (!isRecord(value)) {
    return false;
  }

  if (
    typeof value["jobTitle"] !== "string" ||
    typeof value["companyName"] !== "string" ||
    typeof value["jobDescription"] !== "string" ||
    typeof value["createdAt"] !== "string"
  ) {
    return false;
  }

  const result = value["result"];

  if (!isRecord(result)) {
    return false;
  }

  return (
    typeof result["candidate_name"] === "string" &&
    isRecord(result["candidate_profile"]) &&
    isRecord(result["job_requirements"]) &&
    isRecord(result["analysis"]) &&
    isRecord(result["scores"])
  );
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value)
  );
}