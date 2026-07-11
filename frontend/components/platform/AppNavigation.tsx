"use client";

import Link from "next/link";

import type { CatalogState } from "@/lib/apps/useAppCatalog";
import { cn } from "@/lib/utils";

interface AppNavigationProps {
  catalog: CatalogState;
  pathname: string;
  mobile?: boolean;
  onNavigate?: () => void;
}

interface NavigationEntry {
  label: string;
  route: string;
}

const SAFE_NAVIGATION_ROUTE = /^\/(?!\/)[a-z0-9/_\-\[\]]*$/;

function normalizeRoute(route: string): string {
  return route.replace(/\/+$/, "") || "/";
}

function compareText(left: string, right: string): number {
  if (left === right) {
    return 0;
  }

  return left < right ? -1 : 1;
}

function navigationEntries(catalog: CatalogState): NavigationEntry[] {
  if (catalog.status !== "success") {
    return [];
  }

  const namesByRoute = new Map<string, string[]>();

  for (const app of catalog.apps) {
    if (!SAFE_NAVIGATION_ROUTE.test(app.frontend_route)) {
      continue;
    }

    const route = normalizeRoute(app.frontend_route);

    if (route === "/" || route === "/apps") {
      continue;
    }

    const names = namesByRoute.get(route) ?? [];
    names.push(app.name);
    namesByRoute.set(route, names);
  }

  return Array.from(namesByRoute, ([route, names]) => ({
    route,
    label: Array.from(new Set(names)).sort(compareText).join(" / "),
  }));
}

function matchesRoute(pathname: string, route: string): boolean {
  if (route === "/") {
    return pathname === "/";
  }

  const normalizedRoute = route.replace(/\/+$/, "");
  return (
    pathname === normalizedRoute || pathname.startsWith(`${normalizedRoute}/`)
  );
}

export function AppNavigation({
  catalog,
  pathname,
  mobile = false,
  onNavigate,
}: AppNavigationProps) {
  const entries = navigationEntries(catalog);
  const activeAppRoute = entries
    .filter((entry) => matchesRoute(pathname, entry.route))
    .sort((left, right) => right.route.length - left.route.length)[0]?.route;
  const baseClass = mobile
    ? "block min-w-0 rounded-md px-3 py-2 text-sm"
    : "block max-w-48 rounded-md px-3 py-2 text-sm";
  const linkClass = (active: boolean) =>
    cn(
      baseClass,
      active
        ? "bg-muted text-foreground"
        : "text-muted-foreground hover:text-foreground",
    );

  return (
    <nav
      aria-label="Primary applications"
      className={mobile ? "space-y-1" : "flex min-w-max items-center gap-1"}
    >
      <Link
        aria-current={pathname === "/" ? "page" : undefined}
        className={linkClass(pathname === "/")}
        href="/"
        onClick={onNavigate}
      >
        Dashboard
      </Link>
      <Link
        aria-current={
          !activeAppRoute && matchesRoute(pathname, "/apps")
            ? "page"
            : undefined
        }
        className={linkClass(
          !activeAppRoute && matchesRoute(pathname, "/apps"),
        )}
        href="/apps"
        onClick={onNavigate}
      >
        Applications
      </Link>
      {entries.map((entry) => {
        const active = entry.route === activeAppRoute;

        return (
          <Link
            aria-current={active ? "page" : undefined}
            className={cn(linkClass(active), "truncate")}
            href={entry.route}
            key={entry.route}
            onClick={onNavigate}
            title={entry.label}
          >
            {entry.label}
          </Link>
        );
      })}
      {catalog.status === "error" ? (
        <span className="sr-only">Application navigation unavailable</span>
      ) : null}
    </nav>
  );
}
