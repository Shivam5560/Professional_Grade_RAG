"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { JobProvider } from "@/components/providers/JobProvider";
import { AppCatalogProvider } from "@/lib/apps/useAppCatalog";
import { isPublicRoute } from "@/lib/public-routes";

export function RouteProviders({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  if (isPublicRoute(pathname)) {
    return children;
  }

  return (
    <AppCatalogProvider>
      <JobProvider>{children}</JobProvider>
    </AppCatalogProvider>
  );
}
