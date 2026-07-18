"use client";

import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { CinematicBackdrop } from "@/components/cinematic/CinematicBackdrop";
import { MotionRoute } from "@/components/motion/MotionRoute";
import { AdaptiveRail } from "@/components/shell/AdaptiveRail";
import { LocalSubmenu } from "@/components/shell/LocalSubmenu";
import type { CatalogState } from "@/lib/apps/useAppCatalog";
import { presentationForPath } from "@/lib/presentation/registry";

interface CinematicAppShellProps {
  catalog: CatalogState;
  children: ReactNode;
}

export function CinematicAppShell({
  catalog,
  children,
}: CinematicAppShellProps) {
  const pathname = usePathname() || "/apps";
  const presentation = presentationForPath(pathname);

  return (
    <div className="relative isolate min-h-screen text-foreground">
      <CinematicBackdrop media={presentation.media} />
      <AdaptiveRail
        catalog={catalog}
        pathname={pathname}
        presentation={presentation}
      />
      <div className="min-h-screen pb-16 md:pb-0">
        <LocalSubmenu pathname={pathname} presentation={presentation} />
        <MotionRoute routeKey={pathname}>{children}</MotionRoute>
      </div>
    </div>
  );
}
