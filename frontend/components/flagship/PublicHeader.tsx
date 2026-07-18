"use client";

import Link from "next/link";

import { AppearanceControl } from "@/components/theme/AppearanceControl";
import { useAuthStore } from "@/lib/store";

const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background";

export function PublicHeader() {
  const { isAuthenticated } = useAuthStore();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-6 px-4 sm:px-6">
        <Link
          href="/"
          className={`rounded-sm font-black tracking-[.18em] ${focusRing}`}
        >
          NEXUSMIND
        </Link>
        <nav
          aria-label="Public"
          className="ml-auto hidden items-center gap-5 text-sm text-muted-foreground md:flex"
        >
          <Link className={`rounded-sm hover:text-foreground ${focusRing}`} href="/#capabilities">
            Capabilities
          </Link>
          <Link className={`rounded-sm hover:text-foreground ${focusRing}`} href="/#proof">
            Proof
          </Link>
          <Link className={`rounded-sm hover:text-foreground ${focusRing}`} href="/#creator">
            Creator
          </Link>
        </nav>
        <AppearanceControl />
        {isAuthenticated ? (
          <Link
            className={`rounded-full bg-foreground px-4 py-2 text-sm font-semibold text-background transition-opacity hover:opacity-85 ${focusRing}`}
            href="/apps"
          >
            Open workspace
          </Link>
        ) : (
          <Link
            href="/?auth=login"
            className={`rounded-full bg-foreground px-4 py-2 text-sm font-semibold text-background transition-opacity hover:opacity-85 ${focusRing}`}
          >
            Log in
          </Link>
        )}
      </div>
    </header>
  );
}
