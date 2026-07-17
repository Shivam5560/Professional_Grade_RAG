'use client';

import { Bell, User, LogOut, PanelLeftOpen, PanelLeftClose, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/store";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { JobCenter } from "@/components/layout/JobCenter";
import { AppNavigation } from "@/components/platform/AppNavigation";
import { useAppCatalog } from "@/lib/apps/useAppCatalog";
import { AppearanceControl } from "@/components/theme/AppearanceControl";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface HeaderProps {
  showSidebarToggle?: boolean;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
}

export function Header({
  showSidebarToggle = false,
  isSidebarOpen = true,
  onToggleSidebar,
}: HeaderProps) {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const isAuraSql = pathname?.startsWith('/aurasql');
  const isResume = pathname?.startsWith('/nexus');
  const isResumeGen = pathname?.startsWith('/nexus/generate');
  const isAnalysis = pathname?.startsWith('/analysis');
  const isWorkflows = pathname?.startsWith('/workflows') || isAnalysis;
  const brandTitle = isAuraSql ? 'AuraSQL' : isResumeGen ? 'ResumeGen' : isResume ? 'Nexus' : isWorkflows ? 'Workflows' : 'NexusMind';
  const brandSubtitle = isAuraSql ? 'SQL Studio' : isResumeGen ? 'PDF Builder' : isResume ? 'Resume Studio' : isWorkflows ? 'Agents & Workflows' : 'Studio';
  const brandMark = isAuraSql ? 'AS' : isResumeGen ? 'RG' : isResume ? 'RS' : isWorkflows ? 'WF' : 'NX';
  const [llmHealthy, setLlmHealthy] = useState(true);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const appCatalog = useAppCatalog();

  useEffect(() => {
    // Listen for custom events from chat component about LLM health.
    // Navigation status intentionally reflects live LLM/chat outcome only
    // (not backend ping health such as BM25 index warmup state).
    const handleLlmHealth = (event: Event) => {
      if (event instanceof CustomEvent && typeof event.detail?.healthy === 'boolean') {
        setLlmHealthy(event.detail.healthy);
      }
    };
    window.addEventListener('llm-health-update', handleLlmHealth);

    return () => {
      window.removeEventListener('llm-health-update', handleLlmHealth);
    };
  }, []);

  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  const handleLogout = () => {
    logout();
    router.push("/auth");
  };

  return (
    <header className="sticky top-0 z-50 flex h-16 items-center justify-between border-b border-border bg-background/90 px-4 backdrop-blur-md md:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        {showSidebarToggle && (
          <Button
            variant="ghost"
            size="icon"
            className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
            onClick={onToggleSidebar}
            aria-label={isSidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
          >
            {isSidebarOpen ? (
              <PanelLeftClose className="h-5 w-5" />
            ) : (
              <PanelLeftOpen className="h-5 w-5" />
            )}
          </Button>
        )}
        <div className="h-9 w-9 rounded-lg logo-mark flex items-center justify-center ring-1 ring-foreground/10">
          <span className="text-primary-foreground font-semibold text-xs">{brandMark}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-base font-semibold tracking-tight text-foreground">{brandTitle}</span>
          <span className="text-[11px] text-muted-foreground">
            {brandSubtitle}
          </span>
        </div>
        <div className="ml-6 hidden min-w-0 overflow-x-auto whitespace-nowrap lg:block">
          <AppNavigation catalog={appCatalog} pathname={pathname ?? "/"} />
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <div className="relative lg:hidden">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setMobileNavOpen((prev) => !prev)}
            aria-controls="mobile-application-navigation"
            aria-expanded={mobileNavOpen}
            aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
          >
            {mobileNavOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          {mobileNavOpen ? (
            <div
              className="absolute right-0 top-full z-50 mt-2 max-h-[calc(100vh-5rem)] w-64 overflow-y-auto rounded-lg border border-border bg-background p-2 shadow-xl"
              id="mobile-application-navigation"
            >
              <AppNavigation
                catalog={appCatalog}
                mobile
                onNavigate={() => setMobileNavOpen(false)}
                pathname={pathname ?? "/"}
              />
            </div>
          ) : null}
        </div>

        <div
          className="mr-2 flex items-center gap-1.5"
          role="status"
          aria-live="polite"
          aria-atomic="true"
        >
          <div
            className={`h-2 w-2 rounded-full transition-all ${
              llmHealthy
                ? 'bg-green-400 shadow-sm shadow-green-400/50 animate-pulse'
                : 'bg-red-400 shadow-sm shadow-red-400/50'
            }`}
            title={llmHealthy ? 'LLM healthy' : 'LLM unhealthy'}
            aria-hidden="true"
          />
          <span className="sr-only">
            {llmHealthy ? 'LLM status: healthy' : 'LLM status: unhealthy'}
          </span>
        </div>

        <JobCenter />

        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-all"
          aria-label="Notifications"
        >
          <Bell className="h-5 w-5" />
        </Button>

        <AppearanceControl />

        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full bg-foreground text-background hover:bg-foreground/90 shadow-lg"
                aria-label={`Open account menu for ${user.email}`}
              >
                <User className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-background/95 border-border/70 backdrop-blur-xl">
              <DropdownMenuLabel className="text-foreground">My Account</DropdownMenuLabel>
              <DropdownMenuSeparator className="bg-border/60" />
              <DropdownMenuItem className="text-xs text-muted-foreground focus:text-foreground focus:bg-muted/60">
                {user.email}
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-border/60" />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-red-500 focus:text-red-500 focus:bg-red-500/10"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Button onClick={() => router.push("/auth")} className="bg-foreground text-background hover:bg-foreground/90 shadow-lg">
            Login
          </Button>
        )}
      </div>
    </header>
  );
}
