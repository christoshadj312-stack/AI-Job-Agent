import { Link, useRouterState } from "@tanstack/react-router";
import {
  BarChart3,
  BriefcaseBusiness,
  ChevronRight,
  Clock3,
  FilePenLine,
  LayoutDashboard,
  Menu,
  Plus,
  Settings,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import type { ReactNode } from "react";

const navigation = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard },
  { label: "New Analysis", to: "/new-analysis", icon: Sparkles },
  { label: "Application Tracker", to: "/applications", icon: BriefcaseBusiness },
  { label: "Cover Letters", to: "/cover-letters", icon: FilePenLine },
  { label: "History", to: "/history", icon: Clock3 },
  { label: "Settings", to: "/settings", icon: Settings },
] as const;

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-3" aria-label="JobMatch AI dashboard">
      <span className="grid size-9 place-items-center rounded-lg bg-primary text-primary-foreground shadow-brand">
        <BarChart3 className="size-4" strokeWidth={2.4} />
      </span>
      <span className="text-[17px] font-semibold text-foreground">JobMatch <span className="text-primary">AI</span></span>
    </Link>
  );
}

function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  return (
    <nav className="space-y-1" aria-label="Primary navigation">
      {navigation.map((item) => {
        const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
        const Icon = item.icon;
        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={`flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors ${active ? "bg-sidebar-accent text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground"}`}
          >
            <Icon className="size-[18px]" strokeWidth={1.9} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

function Profile() {
  return (
    <div className="border-t border-sidebar-border pt-4">
      <Link to="/settings" className="flex items-center gap-3 rounded-lg p-2 transition-colors hover:bg-accent">
        <span className="grid size-9 place-items-center rounded-full bg-avatar text-xs font-semibold text-primary">CH</span>
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium text-foreground">Christos H.</span>
          <span className="block truncate text-xs text-muted-foreground">Free plan</span>
        </span>
        <ChevronRight className="size-4 text-muted-foreground" />
      </Link>
    </div>
  );
}

function SidebarContent() {
  return (
    <div className="flex h-full flex-col">
      <Brand />
      <div className="mt-9 flex-1"><Navigation /></div>
      <div className="mb-4 rounded-lg border border-sidebar-border bg-sidebar-accent/60 p-3">
        <div className="mb-2 flex items-center gap-2 text-xs font-semibold text-foreground"><Sparkles className="size-3.5 text-primary" />2 analyses left</div>
        <div className="h-1.5 overflow-hidden rounded-full bg-secondary"><div className="h-full w-3/5 rounded-full bg-primary" /></div>
        <p className="mt-2 text-[11px] leading-4 text-muted-foreground">Resets October 1</p>
      </div>
      <Profile />
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-sidebar-border bg-sidebar p-5 lg:block">
        <SidebarContent />
      </aside>
      <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur lg:hidden">
        <Brand />
        <Sheet>
          <SheetTrigger asChild><Button variant="ghost" size="icon" aria-label="Open navigation"><Menu /></Button></SheetTrigger>
          <SheetContent side="left" className="w-[290px] p-5"><SheetTitle className="sr-only">Navigation</SheetTitle><SidebarContent /></SheetContent>
        </Sheet>
      </header>
      <main className="min-w-0 lg:pl-64">{children}</main>
    </div>
  );
}

export function PageHeader({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
      <div><h1 className="text-2xl font-semibold text-foreground sm:text-[28px]">{title}</h1><p className="mt-1.5 text-sm text-muted-foreground">{description}</p></div>
      {action}
    </div>
  );
}

export function NewAnalysisButton() {
  return <Button asChild size="lg" className="shadow-brand"><Link to="/new-analysis"><Plus />New Job Analysis</Link></Button>;
}
