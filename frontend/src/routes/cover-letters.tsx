import { createFileRoute, Link } from "@tanstack/react-router";
import { AlertTriangle, Copy, Download, FilePenLine, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { AppShell, PageHeader } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { loadAnalysisSession, type AnalysisSession } from "@/lib/analysis-storage";
import { ApiError, createCoverLetter } from "@/lib/api";

export const Route = createFileRoute("/cover-letters")({
  head: () => ({
    meta: [{ title: "Cover Letters — JobMatch AI" }],
  }),
  component: CoverLetters,
});

const DRAFT_KEY = "jobmatch-ai:cover-letter-draft";

function CoverLetters() {
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [letter, setLetter] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const current = loadAnalysisSession();
    setSession(current);
    if (current) {
      try {
        const saved = JSON.parse(sessionStorage.getItem(DRAFT_KEY) || "null") as {
          analysisDate?: string;
          text?: string;
        } | null;
        if (saved?.analysisDate === current.createdAt && typeof saved.text === "string") {
          setLetter(saved.text);
        }
      } catch {
        sessionStorage.removeItem(DRAFT_KEY);
      }
    }
    setLoaded(true);
  }, []);

  function updateLetter(text: string): void {
    setLetter(text);
    setCopied(false);
    if (session) {
      sessionStorage.setItem(DRAFT_KEY, JSON.stringify({ analysisDate: session.createdAt, text }));
    }
  }

  async function generate(): Promise<void> {
    if (!session || busy) return;
    setBusy(true);
    setError(null);
    try {
      const response = await createCoverLetter({
        analysis: session.result,
        jobTitle: session.jobTitle,
        companyName: session.companyName,
      });
      updateLetter(response.text);
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause.message
          : "The API could not be reached. Make sure the FastAPI server is running.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(letter);
      setCopied(true);
    } catch {
      setError("Could not copy the letter. Please select and copy its text.");
    }
  }

  function download(): void {
    const blob = new Blob([letter], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "cover-letter.txt";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-[1100px] px-4 py-8 sm:px-7 lg:px-10 lg:py-10">
        <PageHeader
          title="Cover letter"
          description="A draft based on verified matches in your latest CV analysis."
          action={
            <Button asChild variant="outline">
              <Link to="/new-analysis">
                <Plus />
                New analysis
              </Link>
            </Button>
          }
        />

        {loaded && !session ? (
          <section className="surface p-7">
            <FilePenLine className="size-8 text-primary" />
            <h2 className="mt-4 text-lg font-semibold">Start with a CV analysis</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Upload a CV and job description first. The letter will use verified matches from that
              analysis.
            </p>
            <Button asChild className="mt-5">
              <Link to="/new-analysis">Analyze a job</Link>
            </Button>
          </section>
        ) : session ? (
          <section className="surface p-5 sm:p-7">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="font-semibold">{session.jobTitle}</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {session.companyName || "Company not provided"} · {session.result.candidate_name}
                </p>
              </div>
              <Button onClick={generate} disabled={busy}>
                <FilePenLine />
                {busy ? "Generating..." : letter ? "Regenerate" : "Generate letter"}
              </Button>
            </div>

            {error && (
              <p role="alert" className="mt-5 flex items-start gap-2 text-sm text-status-missing">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                {error}
              </p>
            )}

            {letter && (
              <div className="mt-6">
                <label htmlFor="cover-letter-text" className="text-sm font-medium">
                  Edit your letter before applying
                </label>
                <Textarea
                  id="cover-letter-text"
                  className="mt-2 min-h-[460px] leading-7"
                  value={letter}
                  onChange={(event) => {
                    updateLetter(event.target.value);
                  }}
                />
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="outline" onClick={copy} disabled={!letter.trim()}>
                    <Copy />
                    {copied ? "Copied" : "Copy"}
                  </Button>
                  <Button variant="outline" onClick={download} disabled={!letter.trim()}>
                    <Download />
                    Download .txt
                  </Button>
                </div>
                <p className="mt-4 text-xs text-muted-foreground">
                  Review every claim before sending. The draft uses only requirements marked as
                  found with CV evidence.
                </p>
              </div>
            )}
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}
