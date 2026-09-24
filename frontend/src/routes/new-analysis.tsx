import {
  createFileRoute,
  useNavigate,
} from "@tanstack/react-router";
import {
  AlertTriangle,
  Check,
  FileText,
  Info,
  Sparkles,
  Trash2,
  UploadCloud,
} from "lucide-react";
import {
  type ChangeEvent,
  type DragEvent,
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  AppShell,
  PageHeader,
} from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ApiError,
  createAnalysis,
} from "@/lib/api";
import { saveAnalysisSession } from "@/lib/analysis-storage";

export const Route = createFileRoute("/new-analysis")({
  head: () => ({
    meta: [
      {
        title: "New CV Analysis — JobMatch AI",
      },
      {
        name: "description",
        content:
          "Compare your CV with a job description using evidence-based AI analysis.",
      },
      {
        property: "og:title",
        content: "New CV Analysis — JobMatch AI",
      },
      {
        property: "og:description",
        content:
          "Compare your CV with a job description using evidence-based AI analysis.",
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
  component: NewAnalysis,
});

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

const analysisSteps = [
  "Reading CV...",
  "Extracting job requirements...",
  "Building candidate profile...",
  "Matching candidate to job...",
];

function NewAnalysis() {
  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);
  const abortControllerRef =
    useRef<AbortController | null>(null);

  const [cvFile, setCvFile] =
    useState<File | null>(null);
  const [candidateName, setCandidateName] =
    useState("");
  const [jobTitle, setJobTitle] =
    useState("");
  const [companyName, setCompanyName] =
    useState("");
  const [jobDescription, setJobDescription] =
    useState("");

  const [loading, setLoading] =
    useState(false);
  const [currentStep, setCurrentStep] =
    useState(0);
  const [fileError, setFileError] =
    useState<string | null>(null);
  const [submitError, setSubmitError] =
    useState<string | null>(null);

  useEffect(() => {
    if (!loading) {
      return;
    }

    const timer = window.setInterval(() => {
      setCurrentStep((step) =>
        Math.min(
          step + 1,
          analysisSteps.length - 1,
        ),
      );
    }, 1800);

    return () => {
      window.clearInterval(timer);
    };
  }, [loading]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  function validateAndSetFile(
    selectedFile: File,
  ): void {
    const hasPdfExtension =
      selectedFile.name
        .toLowerCase()
        .endsWith(".pdf");

    if (
      selectedFile.type !== "application/pdf" ||
      !hasPdfExtension
    ) {
      setCvFile(null);
      setFileError(
        "Please select a valid PDF file.",
      );
      return;
    }

    if (
      selectedFile.size > MAX_FILE_SIZE_BYTES
    ) {
      setCvFile(null);
      setFileError(
        "The PDF must be 5 MB or smaller.",
      );
      return;
    }

    setCvFile(selectedFile);
    setFileError(null);
    setSubmitError(null);
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ): void {
    const selectedFile =
      event.target.files?.[0];

    if (selectedFile) {
      validateAndSetFile(selectedFile);
    }
  }

  function handleDrop(
    event: DragEvent<HTMLButtonElement>,
  ): void {
    event.preventDefault();

    const droppedFile =
      event.dataTransfer.files[0];

    if (droppedFile) {
      validateAndSetFile(droppedFile);
    }
  }

  function removeFile(): void {
    setCvFile(null);
    setFileError(null);
    setSubmitError(null);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setSubmitError(null);

    if (!cvFile) {
      setSubmitError(
        "Please upload your CV before starting the analysis.",
      );
      return;
    }

    if (!candidateName.trim()) {
      setSubmitError(
        "Please enter the candidate name.",
      );
      return;
    }

    if (!jobTitle.trim()) {
      setSubmitError(
        "Please enter the job title.",
      );
      return;
    }

    if (jobDescription.trim().length < 20) {
      setSubmitError(
        "Please paste a job description of at least 20 characters.",
      );
      return;
    }

    const abortController =
      new AbortController();

    abortControllerRef.current =
      abortController;

    setLoading(true);
    setCurrentStep(0);

    try {
      const result = await createAnalysis(
        {
          candidateName,
          jobDescription,
          cvFile,
        },
        abortController.signal,
      );

      saveAnalysisSession({
        result,
        jobTitle: jobTitle.trim(),
        companyName: companyName.trim(),
        jobDescription:
          jobDescription.trim(),
        createdAt: new Date().toISOString(),
      });

      await navigate({
        to: "/analysis-results",
      });
    } catch (error) {
      if (
        error instanceof DOMException &&
        error.name === "AbortError"
      ) {
        return;
      }

      if (error instanceof ApiError) {
        setSubmitError(error.message);
      } else if (error instanceof TypeError) {
        setSubmitError(
          "The API could not be reached. Make sure the FastAPI server is running.",
        );
      } else {
        setSubmitError(
          "An unexpected error occurred. Please try again.",
        );
      }
    } finally {
      abortControllerRef.current = null;
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <div className="mx-auto flex min-h-[calc(100vh-64px)] max-w-2xl items-center px-5 py-12 lg:min-h-screen">
          <div className="surface w-full p-7 sm:p-10">
            <div className="mx-auto grid size-14 place-items-center rounded-xl bg-accent text-primary">
              <Sparkles className="size-6 animate-pulse" />
            </div>

            <h1 className="mt-6 text-center text-2xl font-semibold">
              Analyzing your match
            </h1>

            <p className="mt-2 text-center text-sm text-muted-foreground">
              We’re comparing your CV with the{" "}
              {jobTitle.trim()} role.
            </p>

            <div className="mt-8 space-y-3">
              {analysisSteps.map(
                (label, index) => {
                  const isComplete =
                    index < currentStep;
                  const isCurrent =
                    index === currentStep;

                  return (
                    <div
                      key={label}
                      className={`flex items-center gap-3 rounded-lg border p-4 transition-all ${
                        isComplete
                          ? "border-status-found/20 bg-status-found-bg"
                          : isCurrent
                            ? "border-primary/30 bg-accent"
                            : "bg-card opacity-50"
                      }`}
                    >
                      <span
                        className={`grid size-6 place-items-center rounded-full ${
                          isComplete
                            ? "bg-status-found text-primary-foreground"
                            : isCurrent
                              ? "bg-primary text-primary-foreground"
                              : "bg-secondary text-muted-foreground"
                        }`}
                      >
                        {isComplete ? (
                          <Check className="size-3.5" />
                        ) : (
                          <span className="text-[11px] font-semibold">
                            {index + 1}
                          </span>
                        )}
                      </span>

                      <span className="text-sm font-medium">
                        {label}
                      </span>

                      {isCurrent && (
                        <span className="ml-auto size-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                      )}
                    </div>
                  );
                },
              )}
            </div>

            <div className="mt-7 h-2 overflow-hidden rounded-full bg-secondary">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{
                  width: `${
                    ((currentStep + 1) /
                      analysisSteps.length) *
                    100
                  }%`,
                }}
              />
            </div>

            <p className="mt-4 text-center text-xs text-muted-foreground">
              AI analysis can take a little time.
              Please keep this page open.
            </p>
          </div>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-[1450px] px-4 py-8 sm:px-7 lg:px-10 lg:py-10">
        <PageHeader
          title="New job analysis"
          description="Compare your experience with a role and uncover the strongest evidence in your CV."
        />

        <form onSubmit={handleSubmit}>
          <div className="grid gap-6 xl:grid-cols-[.88fr_1.12fr]">
            <section className="surface p-5 sm:p-6">
              <div className="mb-5">
                <h2 className="font-semibold">
                  CV upload
                </h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  We’ll analyze the document you
                  provide.
                </p>
              </div>

              <input
                ref={inputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileChange}
              />

              {!cvFile ? (
                <button
                  type="button"
                  onClick={() =>
                    inputRef.current?.click()
                  }
                  onDragOver={(event) =>
                    event.preventDefault()
                  }
                  onDrop={handleDrop}
                  className="flex min-h-64 w-full flex-col items-center justify-center rounded-lg border border-dashed border-input bg-muted/40 p-8 text-center transition-colors hover:border-primary hover:bg-accent"
                >
                  <span className="grid size-12 place-items-center rounded-lg bg-card text-primary shadow-sm">
                    <UploadCloud />
                  </span>

                  <span className="mt-4 text-sm font-semibold">
                    Upload your CV
                  </span>

                  <span className="mt-1 text-xs text-muted-foreground">
                    Drag and drop or click to browse
                  </span>

                  <span className="mt-4 rounded-md bg-secondary px-2 py-1 text-[11px] font-medium text-muted-foreground">
                    PDF only · Maximum 5 MB
                  </span>
                </button>
              ) : (
                <div>
                  <button
                    type="button"
                    onClick={() =>
                      inputRef.current?.click()
                    }
                    onDragOver={(event) =>
                      event.preventDefault()
                    }
                    onDrop={handleDrop}
                    className="flex min-h-52 w-full flex-col items-center justify-center rounded-lg border border-dashed border-primary/30 bg-accent/60 p-8 text-center"
                  >
                    <span className="grid size-12 place-items-center rounded-lg bg-card text-primary shadow-sm">
                      <Check />
                    </span>

                    <span className="mt-4 text-sm font-semibold">
                      CV ready for analysis
                    </span>

                    <span className="mt-1 text-xs text-muted-foreground">
                      Click or drop another PDF to
                      replace it
                    </span>
                  </button>

                  <div className="mt-4 flex items-center gap-3 rounded-lg border border-border p-3">
                    <span className="grid size-10 place-items-center rounded-md bg-status-missing-bg text-status-missing">
                      <FileText className="size-5" />
                    </span>

                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">
                        {cvFile.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(cvFile.size)} ·
                        PDF
                      </p>
                    </div>

                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={removeFile}
                      aria-label="Remove CV"
                    >
                      <Trash2 />
                    </Button>
                  </div>
                </div>
              )}

              {fileError && (
                <div className="mt-4 flex gap-2 rounded-lg border border-status-missing/20 bg-status-missing-bg p-3 text-sm text-status-missing">
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                  <p>{fileError}</p>
                </div>
              )}

              <label className="mt-5 block space-y-2 text-sm font-medium">
                Candidate name
                <Input
                  value={candidateName}
                  onChange={(event) => {
                    setCandidateName(
                      event.target.value,
                    );
                    setSubmitError(null);
                  }}
                  placeholder="e.g. Christos Hadjikyriakou"
                  maxLength={200}
                  autoComplete="name"
                  required
                />
              </label>
            </section>

            <section className="surface p-5 sm:p-6">
              <div className="mb-5">
                <h2 className="font-semibold">
                  Job description
                </h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  Paste the complete listing for the
                  most useful comparison.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <label className="space-y-2 text-sm font-medium">
                  Job title
                  <Input
                    value={jobTitle}
                    onChange={(event) => {
                      setJobTitle(
                        event.target.value,
                      );
                      setSubmitError(null);
                    }}
                    placeholder="e.g. Junior AI Engineer"
                    maxLength={200}
                    required
                  />
                </label>

                <label className="space-y-2 text-sm font-medium">
                  Company name
                  <Input
                    value={companyName}
                    onChange={(event) => {
                      setCompanyName(
                        event.target.value,
                      );
                      setSubmitError(null);
                    }}
                    placeholder="e.g. Example Company"
                    maxLength={200}
                  />
                </label>
              </div>

              <label className="mt-4 block space-y-2 text-sm font-medium">
                Job description
                <Textarea
                  className="min-h-72 resize-y leading-6"
                  value={jobDescription}
                  onChange={(event) => {
                    setJobDescription(
                      event.target.value,
                    );
                    setSubmitError(null);
                  }}
                  placeholder="Paste the complete job description here..."
                  minLength={20}
                  maxLength={50_000}
                  required
                />
              </label>

              <div className="mt-5 flex gap-2.5 rounded-lg bg-info-bg p-3 text-xs leading-5 text-info">
                <Info className="mt-0.5 size-4 shrink-0" />
                <p>
                  Your CV is compared only with
                  information in your document.
                  JobMatch AI will never invent
                  experience or skills.
                </p>
              </div>

              {submitError && (
                <div
                  role="alert"
                  className="mt-5 flex gap-2.5 rounded-lg border border-status-missing/20 bg-status-missing-bg p-3 text-sm leading-5 text-status-missing"
                >
                  <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                  <p>{submitError}</p>
                </div>
              )}

              <Button
                type="submit"
                size="lg"
                className="mt-5 w-full"
                disabled={
                  !cvFile ||
                  !candidateName.trim() ||
                  !jobTitle.trim() ||
                  jobDescription.trim().length < 20
                }
              >
                <Sparkles />
                Analyze Match
              </Button>
            </section>
          </div>
        </form>
      </div>
    </AppShell>
  );
}

function formatFileSize(
  sizeInBytes: number,
): string {
  if (sizeInBytes < 1024 * 1024) {
    return `${Math.max(
      1,
      Math.round(sizeInBytes / 1024),
    )} KB`;
  }

  return `${(
    sizeInBytes /
    (1024 * 1024)
  ).toFixed(1)} MB`;
}