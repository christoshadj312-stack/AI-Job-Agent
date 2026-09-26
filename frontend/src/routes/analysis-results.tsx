import {
  createFileRoute,
  Link,
} from "@tanstack/react-router";
import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CheckCircle2,
  FileText,
  Lightbulb,
  Sparkles,
  Target,
  X,
} from "lucide-react";
import {
  useEffect,
  useState,
} from "react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import {
  loadAnalysisSession,
  type AnalysisSession,
} from "@/lib/analysis-storage";
import type {
  MatchStatus,
  RequirementMatch,
} from "@/lib/api";

export const Route = createFileRoute(
  "/analysis-results",
)({
  head: () => ({
    meta: [
      {
        title:
          "CV Match Results — JobMatch AI",
      },
      {
        name: "description",
        content:
          "Evidence-based CV and job-description match results.",
      },
      {
        property: "og:title",
        content:
          "CV Match Results — JobMatch AI",
      },
      {
        property: "og:description",
        content:
          "Evidence-based CV and job-description match results.",
      },
      {
        property: "og:type",
        content: "website",
      },
      {
        name: "twitter:card",
        content: "summary_large_image",
      },
    ],
  }),
  component: AnalysisResults,
});

type NormalizedStatus =
  | "Found"
  | "Partial"
  | "Missing";

interface ScoreCategory {
  label: string;
  score: number | null;
}

function StatusPill({
  status,
}: {
  status: MatchStatus;
}) {
  const normalizedStatus =
    normalizeStatus(status);

  const styles =
    normalizedStatus === "Found"
      ? "bg-status-found-bg text-status-found"
      : normalizedStatus === "Partial"
        ? "bg-status-partial-bg text-status-partial"
        : "bg-status-missing-bg text-status-missing";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] font-semibold uppercase ${styles}`}
    >
      {normalizedStatus === "Found" ? (
        <Check className="size-3" />
      ) : normalizedStatus === "Missing" ? (
        <X className="size-3" />
      ) : (
        <AlertTriangle className="size-3" />
      )}

      {normalizedStatus}
    </span>
  );
}

function AnalysisResults() {
  const [session, setSession] =
    useState<AnalysisSession | null>(null);
  const [hasLoaded, setHasLoaded] =
    useState(false);

  useEffect(() => {
    setSession(loadAnalysisSession());
    setHasLoaded(true);
  }, []);

  if (!hasLoaded) {
    return (
      <AppShell>
        <div className="mx-auto flex min-h-[calc(100vh-64px)] max-w-xl items-center justify-center px-5 py-12">
          <div className="surface w-full p-8 text-center">
            <Sparkles className="mx-auto size-7 animate-pulse text-primary" />
            <p className="mt-4 text-sm text-muted-foreground">
              Loading your analysis...
            </p>
          </div>
        </div>
      </AppShell>
    );
  }

  if (!session) {
    return (
      <AppShell>
        <div className="mx-auto flex min-h-[calc(100vh-64px)] max-w-xl items-center justify-center px-5 py-12">
          <div className="surface w-full p-8 text-center">
            <AlertTriangle className="mx-auto size-8 text-status-partial" />

            <h1 className="mt-5 text-2xl font-semibold">
              No analysis found
            </h1>

            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Start a new analysis by uploading
              your CV and adding a job
              description.
            </p>

            <Button
              asChild
              className="mt-6"
            >
              <Link to="/new-analysis">
                New job analysis
              </Link>
            </Button>
          </div>
        </div>
      </AppShell>
    );
  }

  if (!session.result.insights) {
    return (
      <AppShell>
        <div className="mx-auto flex min-h-[calc(100vh-64px)] max-w-xl items-center justify-center px-5 py-12">
          <div className="surface w-full p-8 text-center">
            <AlertTriangle className="mx-auto size-8 text-status-partial" />
            <h1 className="mt-5 text-2xl font-semibold">
              Run a new analysis
            </h1>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              This saved analysis was created before CV insights were available.
              Run it again to see your strengths, gaps, and suggestions.
            </p>
            <Button asChild className="mt-6">
              <Link to="/new-analysis">New job analysis</Link>
            </Button>
          </div>
        </div>
      </AppShell>
    );
  }

  const { result } = session;
  const overallScore =
    normalizeScore(
      result.scores.overall_match,
    );

  const categories: ScoreCategory[] = [
    {
      label: "Technical Skills",
      score:
        result.scores.technical_skills,
    },
    {
      label: "Experience",
      score: result.scores.experience,
    },
    {
      label: "Education",
      score: result.scores.education,
    },
    {
      label: "Soft Skills",
      score: result.scores.soft_skills,
    },
  ];

  const {
    strengths,
    gaps,
    cv_improvement_suggestions: recommendations,
  } = result.insights;

  return (
    <AppShell>
      <div className="mx-auto max-w-[1450px] px-4 py-7 sm:px-7 lg:px-10 lg:py-9">
        <Button
          variant="ghost"
          size="sm"
          asChild
          className="mb-5 -ml-2"
        >
          <Link to="/new-analysis">
            <ArrowLeft />
            Back to analysis
          </Link>
        </Button>

        <header className="mb-7 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span
                className={`rounded-md px-2.5 py-1 text-xs font-semibold ${getMatchLabelStyles(
                  overallScore,
                )}`}
              >
                {getMatchLabel(overallScore)}
              </span>

              <span className="text-xs text-muted-foreground">
                Analyzed{" "}
                {formatAnalysisDate(
                  session.createdAt,
                )}
              </span>
            </div>

            <h1 className="text-3xl font-semibold">
              {session.jobTitle}
            </h1>

            <p className="mt-1 text-sm text-muted-foreground">
              {session.companyName ||
                "Company not provided"}
              {" · "}
              Candidate:{" "}
              {result.candidate_name}
            </p>
          </div>

          <Button
            variant="outline"
            disabled
            title="Application tracker persistence will be added in the tracker milestone."
          >
            Save to tracker
          </Button>
        </header>

        <section className="surface grid overflow-hidden lg:grid-cols-[320px_1fr]">
          <div className="flex flex-col items-center justify-center border-b border-border bg-accent/35 p-8 lg:border-b-0 lg:border-r">
            <div
              className="relative grid size-44 place-items-center rounded-full"
              style={{
                background: `conic-gradient(var(--primary) 0 ${overallScore}%, var(--secondary) ${overallScore}% 100%)`,
              }}
            >
              <div className="grid size-36 place-items-center rounded-full bg-card text-center shadow-sm">
                <div>
                  <span className="block text-4xl font-semibold">
                    {overallScore}%
                  </span>

                  <span className="text-xs font-medium text-muted-foreground">
                    Overall match
                  </span>
                </div>
              </div>
            </div>

            <p className="mt-5 text-center text-sm leading-6 text-muted-foreground">
              The score is calculated from
              verified evidence found in the CV.
            </p>
          </div>

          <div className="grid gap-4 p-5 sm:grid-cols-2 sm:p-7">
            {categories.map((item) => {
              const score =
                normalizeScore(item.score);

              return (
                <div
                  key={item.label}
                  className="rounded-lg border border-border p-4"
                >
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium">
                      {item.label}
                    </span>

                    <span className="font-semibold">
                      {item.score === null
                        ? "N/A"
                        : `${score}%`}
                    </span>
                  </div>

                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-secondary">
                    <div
                      className="animate-progress h-full rounded-full bg-primary"
                      style={{
                        width: `${score}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        <div className="mt-6 grid gap-6 xl:grid-cols-[1.4fr_.8fr]">
          <div className="space-y-6">
            <section className="surface overflow-hidden">
              <div className="border-b border-border px-5 py-4 sm:px-6">
                <h2 className="font-semibold">
                  Technical skills
                </h2>

                <p className="mt-1 text-xs text-muted-foreground">
                  Technical requirements verified
                  against evidence in the CV.
                </p>
              </div>

              {result.analysis
                .technical_skills.length >
              0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] text-left text-sm">
                    <thead className="bg-muted/60 text-xs uppercase text-muted-foreground">
                      <tr>
                        <th className="px-6 py-3 font-semibold">
                          Requirement
                        </th>
                        <th className="px-6 py-3 font-semibold">
                          Status
                        </th>
                        <th className="px-6 py-3 font-semibold">
                          Evidence from CV
                        </th>
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-border">
                      {result.analysis.technical_skills.map(
                        (item, index) => (
                          <tr
                            key={`${item.requirement}-${index}`}
                          >
                            <td className="px-6 py-4 font-medium">
                              {item.requirement}
                            </td>

                            <td className="px-6 py-4">
                              <StatusPill
                                status={
                                  item.status
                                }
                              />
                            </td>

                            <td className="px-6 py-4">
                              <p>
                                {item.evidence}
                              </p>

                              {item.reason && (
                                <p className="mt-1 text-xs leading-5 text-muted-foreground">
                                  {item.reason}
                                </p>
                              )}
                            </td>
                          </tr>
                        ),
                      )}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyCategoryMessage message="No technical requirements were extracted from this job description." />
              )}
            </section>

            <RequirementSection
              title="Education"
              icon={
                <FileText className="size-4" />
              }
              iconStyles="bg-info-bg text-info"
              matches={
                result.analysis
                  .education_requirements
              }
              emptyMessage="No education requirement was extracted from this job description."
            />

            <RequirementSection
              title="Experience"
              icon={
                <Target className="size-4" />
              }
              iconStyles="bg-status-partial-bg text-status-partial"
              matches={
                result.analysis
                  .experience_requirements
              }
              emptyMessage="No experience requirement was extracted from this job description."
            />

            <RequirementSection
              title="Soft skills"
              icon={
                <CheckCircle2 className="size-4" />
              }
              iconStyles="bg-accent text-primary"
              matches={
                result.analysis.soft_skills
              }
              emptyMessage="No soft-skill requirements were extracted from this job description."
            />
          </div>

          <div className="space-y-6">
            <section className="surface p-5">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="size-5 text-status-found" />
                <h2 className="font-semibold">
                  Your strengths
                </h2>
              </div>

              {strengths.length > 0 ? (
                <ul className="mt-4 space-y-4">
                  {strengths.map(
                    (item, index) => (
                      <li
                        key={`${item.category}-${item.requirement}-${index}`}
                        className="flex gap-2.5 text-sm"
                      >
                        <Check className="mt-0.5 size-4 shrink-0 text-status-found" />

                        <div>
                          <p className="font-medium">
                            {item.requirement}
                          </p>

                          <p className="mt-1 text-xs leading-5 text-muted-foreground">
                            {item.evidence}
                          </p>
                        </div>
                      </li>
                    ),
                  )}
                </ul>
              ) : (
                <p className="mt-4 text-sm leading-6 text-muted-foreground">
                  No fully verified strengths were
                  found for these requirements.
                </p>
              )}
            </section>

            <section className="surface p-5">
              <div className="flex items-center gap-2">
                <AlertTriangle className="size-5 text-status-missing" />
                <h2 className="font-semibold">
                  Gaps to address
                </h2>
              </div>

              {gaps.length > 0 ? (
                <ul className="mt-4 space-y-4">
                  {gaps.map(
                    (item, index) => (
                      <li
                        key={`${item.category}-${item.requirement}-${index}`}
                        className="flex gap-2.5 text-sm leading-5"
                      >
                        <span
                          className={`mt-2 size-1.5 shrink-0 rounded-full ${normalizeStatus(item.status) === "Partial" ? "bg-status-partial" : "bg-status-missing"}`}
                        />

                        <div>
                          <p className="font-medium">
                            {item.requirement}
                          </p>

                          <p className="mt-1 text-xs font-semibold text-muted-foreground">
                            {normalizeStatus(item.status) === "Partial" ? "Partial match" : "Missing"}
                          </p>

                          {item.reason && (
                            <p className="mt-1 text-xs leading-5 text-muted-foreground">
                              {item.reason}
                            </p>
                          )}
                        </div>
                      </li>
                    ),
                  )}
                </ul>
              ) : (
                <p className="mt-4 text-sm leading-6 text-muted-foreground">
                  No missing or partial requirements were identified.
                </p>
              )}
            </section>
          </div>
        </div>

        <section className="surface mt-6 p-5 sm:p-6">
          <div className="flex items-center gap-2">
            <span className="grid size-9 place-items-center rounded-lg bg-accent text-primary">
              <Lightbulb className="size-4" />
            </span>

            <div>
              <h2 className="font-semibold">
                Evidence-based CV recommendations
              </h2>

              <p className="text-xs text-muted-foreground">
                Suggestions are derived only from
                missing or partial requirements.
              </p>
            </div>
          </div>

          {recommendations.length > 0 ? (
            <div className="mt-5 grid gap-3 lg:grid-cols-3">
              {recommendations.map(
                (recommendation, index) => (
                  <div
                    key={`${recommendation.category}-${recommendation.requirement}-${index}`}
                    className="rounded-lg border border-border p-4"
                  >
                    <div className="flex items-center justify-between gap-2 text-xs font-semibold">
                      <span className="text-primary">
                        {String(index + 1).padStart(2, "0")}
                      </span>
                      <span className="text-muted-foreground">
                        {recommendation.priority === "high" ? "High priority" : "Medium priority"}
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-6">
                      {recommendation.suggestion}
                    </p>
                    {recommendation.evidence_basis && (
                      <p className="mt-2 text-xs leading-5 text-muted-foreground">
                        CV evidence: {recommendation.evidence_basis}
                      </p>
                    )}
                  </div>
                ),
              )}
            </div>
          ) : (
            <p className="mt-5 text-sm leading-6 text-muted-foreground">
              No additional evidence-based CV
              recommendations were generated for
              this match.
            </p>
          )}

          <div className="mt-5 flex gap-2.5 rounded-lg bg-info-bg p-4 text-xs leading-5 text-info">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />

            <p>
              Only add experience, skills, or
              tools you genuinely have. JobMatch
              AI never recommends inventing
              qualifications.
            </p>
          </div>
        </section>
      </div>
    </AppShell>
  );
}

function RequirementSection({
  title,
  icon,
  iconStyles,
  matches,
  emptyMessage,
}: {
  title: string;
  icon: React.ReactNode;
  iconStyles: string;
  matches: RequirementMatch[];
  emptyMessage: string;
}) {
  return (
    <section className="surface p-5 sm:p-6">
      <div className="flex items-center gap-2">
        <span
          className={`grid size-8 place-items-center rounded-md ${iconStyles}`}
        >
          {icon}
        </span>

        <h2 className="font-semibold">
          {title}
        </h2>
      </div>

      {matches.length > 0 ? (
        <div className="mt-5 space-y-5">
          {matches.map((item, index) => (
            <div
              key={`${item.requirement}-${index}`}
              className="rounded-lg border border-border p-4"
            >
              <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                <div>
                  <p className="text-xs font-semibold uppercase text-muted-foreground">
                    Requirement
                  </p>

                  <p className="mt-2 text-sm leading-6">
                    {item.requirement}
                  </p>
                </div>

                <StatusPill
                  status={item.status}
                />
              </div>

              <div className="mt-4 rounded-lg bg-muted/60 p-4">
                <p className="text-xs font-semibold uppercase text-muted-foreground">
                  Evidence
                </p>

                <p className="mt-2 text-sm font-medium">
                  {item.evidence}
                </p>
              </div>

              {item.reason && (
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  {item.reason}
                </p>
              )}
            </div>
          ))}
        </div>
      ) : (
        <EmptyCategoryMessage
          message={emptyMessage}
        />
      )}
    </section>
  );
}

function EmptyCategoryMessage({
  message,
}: {
  message: string;
}) {
  return (
    <p className="p-5 text-sm leading-6 text-muted-foreground sm:p-6">
      {message}
    </p>
  );
}

function normalizeStatus(
  status: MatchStatus,
): NormalizedStatus {
  const normalized =
    status.toUpperCase();

  if (normalized === "FOUND") {
    return "Found";
  }

  if (normalized === "PARTIAL") {
    return "Partial";
  }

  return "Missing";
}

function normalizeScore(
  score: number | null,
): number {
  if (
    score === null ||
    !Number.isFinite(score)
  ) {
    return 0;
  }

  return Math.min(
    100,
    Math.max(0, Math.round(score)),
  );
}

function getMatchLabel(
  score: number,
): string {
  if (score >= 75) {
    return "Strong Match";
  }

  if (score >= 50) {
    return "Moderate Match";
  }

  return "Low Match";
}

function getMatchLabelStyles(
  score: number,
): string {
  if (score >= 75) {
    return "bg-status-found-bg text-status-found";
  }

  if (score >= 50) {
    return "bg-status-partial-bg text-status-partial";
  }

  return "bg-status-missing-bg text-status-missing";
}

function formatAnalysisDate(
  isoDate: string,
): string {
  const date = new Date(isoDate);

  if (Number.isNaN(date.getTime())) {
    return "recently";
  }

  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    },
  ).format(date);
}
