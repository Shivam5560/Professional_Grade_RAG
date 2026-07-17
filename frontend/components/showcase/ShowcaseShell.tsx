import Link from "next/link";
import { AppearanceControl } from "@/components/theme/AppearanceControl";

const routes = [
  ["Knowledge", "knowledge"],
  ["AuraSQL", "aurasql"],
  ["Analysis", "analysis"],
  ["Career", "career"],
] as const;

export function ShowcaseShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div
        role="status"
        className="bg-[hsl(var(--copper))] px-4 py-2 text-center font-mono text-xs font-bold uppercase tracking-[.18em] text-black"
      >
        Showcase mode · Precomputed demonstration
      </div>
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-4">
          <Link href="/" className="font-black tracking-[.16em]">
            NEXUSMIND
          </Link>
          <nav aria-label="Showcase experiences" className="ml-auto hidden gap-4 text-sm md:flex">
            {routes.map(([label, id]) => (
              <Link key={id} href={`/showcase/${id}`}>
                {label}
              </Link>
            ))}
          </nav>
          <AppearanceControl />
          <Link
            className="rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
            href="/auth"
          >
            Use the live workspace
          </Link>
        </div>
      </header>
      {children}
    </div>
  );
}
