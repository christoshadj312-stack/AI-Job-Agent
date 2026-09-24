import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, BriefcaseBusiness, CalendarDays, CheckCircle2, Gauge, Plus, Sparkles, TrendingUp } from "lucide-react";
import { AppShell, NewAnalysisButton } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { recentAnalyses } from "@/lib/mock-data";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Dashboard — JobMatch AI" },
    { name: "description", content: "Review your job search progress and recent CV match analyses." },
    { property: "og:title", content: "Dashboard — JobMatch AI" },
    { property: "og:description", content: "Review your job search progress and recent CV match analyses." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary_large_image" },
  ]}),
  component: Dashboard,
});

const stats = [
  { label: "Applications Tracked", value: "12", note: "+3 this month", icon: BriefcaseBusiness },
  { label: "Average Match Score", value: "74%", note: "+6% from August", icon: Gauge },
  { label: "Strong Matches", value: "5", note: "Score above 75%", icon: CheckCircle2 },
  { label: "Applications This Month", value: "4", note: "On track with your goal", icon: CalendarDays },
];

function Dashboard() {
  return (
    <AppShell>
      <div className="mx-auto max-w-[1450px] px-4 py-8 sm:px-7 lg:px-10 lg:py-10">
        <section className="mb-9 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div>
            <div className="mb-3 flex items-center gap-2 text-sm font-medium text-primary"><Sparkles className="size-4" />Your job search workspace</div>
            <h1 className="text-3xl font-semibold text-foreground sm:text-4xl">Good afternoon, Christos</h1>
            <p className="mt-2 text-base text-muted-foreground">Find out how well your CV matches your next opportunity.</p>
          </div>
          <NewAnalysisButton />
        </section>

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Application summary">
          {stats.map((stat) => <article key={stat.label} className="surface p-5">
            <div className="flex items-start justify-between"><p className="text-sm font-medium text-muted-foreground">{stat.label}</p><span className="grid size-9 place-items-center rounded-lg bg-accent text-primary"><stat.icon className="size-[18px]" /></span></div>
            <p className="mt-5 text-3xl font-semibold text-foreground">{stat.value}</p>
            <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">{stat.label === "Average Match Score" && <TrendingUp className="size-3 text-status-found" />}{stat.note}</p>
          </article>)}
        </section>

        <div className="mt-7 grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(280px,.75fr)]">
          <section className="surface overflow-hidden">
            <div className="flex items-center justify-between border-b border-border px-5 py-4 sm:px-6">
              <div><h2 className="font-semibold text-foreground">Recent analyses</h2><p className="mt-0.5 text-xs text-muted-foreground">Your latest CV-to-role comparisons</p></div>
              <Button variant="ghost" size="sm" asChild><Link to="/history">View all <ArrowRight /></Link></Button>
            </div>
            <div className="divide-y divide-border">
              {recentAnalyses.map((item) => <Link key={item.id} to="/analysis-results" className="group grid gap-3 px-5 py-4 transition-colors hover:bg-accent/40 sm:grid-cols-[1fr_auto_auto] sm:items-center sm:px-6">
                <div><p className="text-sm font-semibold text-foreground group-hover:text-primary">{item.role}</p><p className="mt-1 text-xs text-muted-foreground">{item.company} · {item.date}</p></div>
                <span className="w-fit rounded-md bg-status-found-bg px-2.5 py-1 text-xs font-medium text-status-found">{item.status}</span>
                <div className="flex items-center gap-3 sm:justify-end"><div className="h-1.5 w-20 overflow-hidden rounded-full bg-secondary"><div className="h-full rounded-full bg-primary" style={{ width: `${item.match}%` }} /></div><span className="w-9 text-right text-sm font-semibold text-foreground">{item.match}%</span><ArrowRight className="size-4 text-muted-foreground" /></div>
              </Link>)}
            </div>
          </section>

          <aside className="surface relative overflow-hidden p-6">
            <div className="subtle-grid absolute inset-0 opacity-25" />
            <div className="relative">
              <span className="grid size-10 place-items-center rounded-lg bg-primary text-primary-foreground shadow-brand"><Sparkles className="size-5" /></span>
              <h2 className="mt-6 text-xl font-semibold text-foreground">Ready for your next role?</h2>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">Compare your CV with a job description and get evidence-based recommendations in moments.</p>
              <Button className="mt-6 w-full" asChild><Link to="/new-analysis"><Plus />Start an analysis</Link></Button>
              <p className="mt-3 text-center text-[11px] text-muted-foreground">Takes less than two minutes</p>
            </div>
          </aside>
        </div>
      </div>
    </AppShell>
  );
}
