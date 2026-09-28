import { createFileRoute } from "@tanstack/react-router";
import { CheckCircle2, FileSearch, FileText, Sparkles } from "lucide-react";

import { AppShell, NewAnalysisButton } from "@/components/app-shell";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "JobMatch AI — Evidence-based CV matching" },
      {
        name: "description",
        content:
          "Compare your CV with a job description, find verified strengths and gaps, and create a tailored cover letter.",
      },
      {
        property: "og:title",
        content: "JobMatch AI — Evidence-based CV matching",
      },
      {
        property: "og:description",
        content: "Compare your CV with a job description using evidence found in your CV.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Home,
});

const steps = [
  {
    title: "Upload your CV",
    description: "Choose your current CV as a PDF, PNG, or JPG file.",
    icon: FileText,
  },
  {
    title: "Add the job description",
    description: "Paste the role and requirements you want to compare.",
    icon: FileSearch,
  },
  {
    title: "Review your match",
    description: "See supported strengths, gaps, suggestions, and a cover letter draft.",
    icon: CheckCircle2,
  },
] as const;

function Home() {
  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6 sm:py-20">
        <section className="mx-auto max-w-3xl text-center">
          <div className="mx-auto mb-5 flex w-fit items-center gap-2 rounded-full bg-accent px-3 py-1.5 text-sm font-medium text-primary">
            <Sparkles className="size-4" />
            Evidence-based CV matching
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            See how your CV matches a job
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base leading-7 text-muted-foreground sm:text-lg">
            Upload your CV and paste a job description. JobMatch AI finds verified strengths and
            gaps, then helps you prepare a tailored cover letter without inventing experience.
          </p>
          <div className="mt-8 flex justify-center">
            <NewAnalysisButton />
          </div>
          <p className="mt-3 text-xs text-muted-foreground">
            PDF, PNG or JPG · Your CV is analyzed for this session and is not stored.
          </p>
        </section>

        <section className="mt-16" aria-labelledby="how-it-works">
          <h2 id="how-it-works" className="text-center text-2xl font-semibold text-foreground">
            How it works
          </h2>
          <div className="mt-7 grid gap-4 md:grid-cols-3">
            {steps.map((step, index) => (
              <article key={step.title} className="surface p-6">
                <div className="flex items-center justify-between">
                  <span className="grid size-10 place-items-center rounded-lg bg-accent text-primary">
                    <step.icon className="size-5" />
                  </span>
                  <span className="text-sm font-semibold text-muted-foreground">{index + 1}</span>
                </div>
                <h3 className="mt-5 font-semibold text-foreground">{step.title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{step.description}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </AppShell>
  );
}
