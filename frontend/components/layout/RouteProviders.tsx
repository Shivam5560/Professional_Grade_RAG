"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { JobProvider } from "@/components/providers/JobProvider";
import { CinematicAppShell } from "@/components/shell/CinematicAppShell";
import {
  AppCatalogProvider,
  useAppCatalog,
} from "@/lib/apps/useAppCatalog";
import { isPublicRoute } from "@/lib/public-routes";

export function RouteProviders({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (isPublicRoute(pathname)) {
    return children;
  }

  return (
    <AppCatalogProvider>
      <JobProvider>
        <AuthenticatedShellBoundary>{children}</AuthenticatedShellBoundary>
      </JobProvider>
    </AppCatalogProvider>
  );
}

function AuthenticatedShellBoundary({ children }: { children: ReactNode }) {
  const catalog = useAppCatalog();

  return (
    <CinematicAppShell catalog={catalog}>{children}</CinematicAppShell>
  );
}
