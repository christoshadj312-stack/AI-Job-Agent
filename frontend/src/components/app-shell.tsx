import { Link } from "@tanstack/react-router";
import { BarChart3, Plus } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-3" aria-label="JobMatch AI home">
      <span className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground shadow-brand">
        <BarChart3 className="size-4" strokeWidth={2.4} />
      </span>
      <span className="text-[17px] font-semibold text-foreground">
        JobMatch <span className="text-primary">AI</span>
      </span>
    </Link>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6">
          <Brand />
          <Button asChild size="sm">
            <Link to="/new-analysis">
              <Plus />
              New analysis
            </Link>
          </Button>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
      <div>
        <h1 className="text-2xl font-semibold text-foreground sm:text-[28px]">{title}</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function NewAnalysisButton() {
  return (
    <Button asChild size="lg" className="shadow-brand">
      <Link to="/new-analysis">
        <Plus />
        Analyze my CV
      </Link>
    </Button>
  );
}
