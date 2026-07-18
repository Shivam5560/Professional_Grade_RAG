"use client";

import { motion } from "framer-motion";
import {
  BarChart3,
  Blocks,
  Briefcase,
  Code2,
  Database,
  LayoutDashboard,
  LogIn,
  LogOut,
  MessageSquare,
  User,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { JobCenter } from "@/components/layout/JobCenter";
import { ApplicationSwitcher } from "@/components/shell/ApplicationSwitcher";
import { AppearanceControl } from "@/components/theme/AppearanceControl";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { AppManifest } from "@/lib/apps/types";
import type { CatalogState } from "@/lib/apps/useAppCatalog";
import {
  directApplicationRoute,
  presentationForApp,
} from "@/lib/presentation/registry";
import type { ApplicationPresentation } from "@/lib/presentation/types";
import { useAuthStore } from "@/lib/store";
import { cn } from "@/lib/utils";

interface AdaptiveRailProps {
  catalog: CatalogState;
  pathname: string;
  presentation: ApplicationPresentation;
}

const safeRoute = /^\/(?!\/)/;

function iconForApp(app: AppManifest): LucideIcon {
  switch (presentationForApp(app).id) {
    case "knowledge-studio":
      return MessageSquare;
    case "aurasql":
      return Database;
    case "analysis":
      return BarChart3;
    case "career-studio":
      return Briefcase;
    default:
      return Blocks;
  }
}

function RailLink({
  active,
  href,
  icon: Icon,
  label,
}: {
  active: boolean;
  href: string;
  icon: LucideIcon;
  label: string;
}) {
  return (
    <Link
      aria-current={active ? "page" : undefined}
      aria-label={label}
      className={cn(
        "relative inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        active
          ? "text-background"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
      href={href}
      title={label}
    >
      {active ? (
        <motion.span
          className="absolute inset-0 rounded-md bg-foreground"
          layoutId="active-application"
          transition={{ type: "spring", stiffness: 260, damping: 30 }}
        />
      ) : null}
      <Icon aria-hidden="true" className="relative z-10 h-[18px] w-[18px]" />
    </Link>
  );
}

function AccountControl() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  if (!user) {
    return (
      <button
        aria-label="Log in"
        className="inline-flex h-10 w-10 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        onClick={() => router.push("/auth")}
        title="Log in"
        type="button"
      >
        <LogIn aria-hidden="true" className="h-[18px] w-[18px]" />
      </button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          aria-label={`Open account menu for ${user.email}`}
          className="inline-flex h-10 w-10 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          title="Account"
          type="button"
        >
          <User aria-hidden="true" className="h-[18px] w-[18px]" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="truncate">{user.email}</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          onSelect={() => {
            logout();
            router.push("/auth");
          }}
        >
          <LogOut aria-hidden="true" className="mr-2 h-4 w-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function AdaptiveRail({
  catalog,
  pathname,
  presentation,
}: AdaptiveRailProps) {
  const applications =
    catalog.status === "success"
      ? catalog.apps.filter((app) => safeRoute.test(app.frontend_route))
      : [];
  const activeApplication = applications.find(
    (app) => presentationForApp(app).id === presentation.id,
  );

  return (
    <>
      <aside className="fixed inset-y-3 left-3 z-50 hidden w-14 flex-col items-center rounded-md border border-border/70 bg-background/90 py-2 shadow-lg backdrop-blur-xl md:flex">
        <nav
          aria-label="Applications"
          className="flex min-h-0 flex-1 flex-col items-center gap-1 overflow-y-auto overscroll-contain px-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >
          <RailLink
            active={pathname === "/apps" || pathname.startsWith("/apps/")}
            href="/apps"
            icon={LayoutDashboard}
            label="Dashboard"
          />
          <div aria-hidden="true" className="my-1 h-px w-7 shrink-0 bg-border" />
          {applications.map((app) => (
            <RailLink
              active={presentationForApp(app).id === presentation.id}
              href={directApplicationRoute(app)}
              icon={iconForApp(app)}
              key={app.id}
              label={app.name}
            />
          ))}
        </nav>

        <div className="mt-2 flex shrink-0 flex-col items-center gap-1 px-2 [&_button]:h-10 [&_button]:w-10 [&_button]:p-0 [&_button>span]:hidden">
          <JobCenter />
          <AppearanceControl />
          <RailLink
            active={pathname === "/developer"}
            href="/developer"
            icon={Code2}
            label="Developer"
          />
          <AccountControl />
        </div>
      </aside>

      <aside className="fixed inset-x-0 bottom-0 z-50 border-t border-border/70 bg-background/90 pb-[env(safe-area-inset-bottom)] shadow-[0_-10px_32px_-20px_hsl(var(--foreground)/0.35)] backdrop-blur-xl md:hidden">
        <nav
          aria-label="Mobile applications"
          className="mx-auto grid h-16 max-w-lg grid-cols-5 items-center justify-items-center px-2"
        >
          <RailLink
            active={pathname === "/apps" || pathname.startsWith("/apps/")}
            href="/apps"
            icon={LayoutDashboard}
            label="Dashboard"
          />
          <RailLink
            active={presentation.id !== "platform"}
            href={presentation.mainRoute}
            icon={activeApplication ? iconForApp(activeApplication) : Blocks}
            label={presentation.shortName}
          />
          <ApplicationSwitcher
            activePresentation={presentation}
            catalog={catalog}
          />
          <div className="[&_button]:h-11 [&_button]:w-11 [&_button]:p-0 [&_button>span]:hidden [&>div>div]:bottom-full [&>div>div]:top-auto [&>div>div]:mb-2 [&>div>div]:mt-0">
            <JobCenter />
          </div>
          <AccountControl />
        </nav>
      </aside>
    </>
  );
}
