import { ArrowUpRight, Braces, DatabaseZap, Radar, Route } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

import { CinematicBackdrop } from "@/components/cinematic/CinematicBackdrop";
import { PublicFooter } from "@/components/flagship/PublicFooter";
import { PublicHeader } from "@/components/flagship/PublicHeader";
import { CREATOR_PROFILE } from "@/lib/creator-profile";

const platformMedia = {
  dark: "/images/cinematic/platform-dark.jpg",
  light: "/images/cinematic/platform-light.jpg",
  alt: "Monumental connected architecture representing the NexusMind platform",
  focalPoint: "72% 48%",
};

const disciplines = [
  { icon: Route, name: "Product design", detail: "Focused workflows, progressive disclosure, responsive interaction, and accessible navigation." },
  { icon: Radar, name: "RAG systems", detail: "Hybrid retrieval, reranking, citations, and confidence." },
  { icon: DatabaseZap, name: "Data intelligence", detail: "Schema-aware SQL, durable analysis, visualization, and reports." },
  { icon: Braces, name: "Platform engineering", detail: "Typed interfaces, FastAPI services, PostgreSQL, containers, and MCP." },
] as const;

export default function DeveloperPage() {
  return (
    <div className="relative isolate min-h-screen overflow-x-clip bg-background text-foreground">
      <CinematicBackdrop media={platformMedia} />
      <PublicHeader />

      <main className="pt-16">
        <section className="flex min-h-[82svh] items-end px-5 pb-14 pt-24 sm:px-8 lg:px-14 lg:pb-20">
          <div className="mx-auto grid w-full max-w-7xl items-end gap-10 lg:grid-cols-[minmax(0,1fr)_18rem]">
            <div className="max-w-4xl">
              <p className="font-mono text-xs font-semibold uppercase text-[hsl(var(--signal))]">
                Developer / 01
              </p>
              <h1 className="mt-6 text-balance text-5xl font-semibold leading-[.98] sm:text-7xl lg:text-8xl">
                Shivam Sourav
              </h1>
              <p className="mt-5 text-base font-medium text-[hsl(var(--copper))] sm:text-lg">
                {CREATOR_PROFILE.role}
              </p>
              <p className="mt-7 max-w-3xl text-base leading-7 text-foreground/75 sm:text-lg sm:leading-8">
                {CREATOR_PROFILE.ownership}
              </p>
              <nav aria-label="Creator links" className="mt-9 flex flex-wrap gap-3">
                {CREATOR_PROFILE.links.map((item) => (
                  <a
                    key={item.label}
                    href={item.href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex h-11 items-center gap-2 rounded-md border border-border/70 bg-background/65 px-4 text-sm font-semibold backdrop-blur-xl transition-colors hover:bg-foreground hover:text-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {item.label}
                    <ArrowUpRight aria-hidden className="size-4" />
                  </a>
                ))}
              </nav>
            </div>

            <div className="relative hidden aspect-[4/5] overflow-hidden rounded-md border border-border/70 bg-muted shadow-2xl lg:block">
              <Image
                alt="Shivam Sourav"
                className="object-cover grayscale-[.2]"
                fill
                priority
                sizes="288px"
                src="/images/developer/profile-main.png"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/25 to-transparent" />
            </div>
          </div>
        </section>

        <section className="border-y border-border/60 bg-background/[.78] px-5 py-16 backdrop-blur-2xl sm:px-8 lg:px-14 lg:py-20">
          <div className="mx-auto max-w-7xl">
            <div className="grid gap-6 border-b border-border/60 pb-10 lg:grid-cols-[.55fr_1fr] lg:items-end">
              <p className="font-mono text-xs font-semibold uppercase text-muted-foreground">System ownership / 02</p>
              <h2 className="max-w-3xl text-3xl font-semibold leading-tight sm:text-5xl">
                One authored product, from interaction model to production infrastructure.
              </h2>
            </div>
            <div className="grid md:grid-cols-2">
              {disciplines.map(({ icon: Icon, name, detail }, index) => (
                <article
                  key={name}
                  className="grid min-h-48 grid-cols-[2.5rem_1fr] gap-5 border-b border-border/60 py-8 md:px-7 md:odd:border-r md:first:pl-0"
                >
                  <span className="grid size-10 place-items-center rounded-md border border-border/70 text-[hsl(var(--data))]">
                    <Icon aria-hidden className="size-4" />
                  </span>
                  <div>
                    <p className="font-mono text-[10px] font-semibold text-muted-foreground">0{index + 1}</p>
                    <h3 className="mt-3 text-xl font-semibold">{name}</h3>
                    <p className="mt-3 max-w-md text-sm leading-6 text-muted-foreground">{detail}</p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-foreground px-5 py-16 text-background sm:px-8 lg:px-14 lg:py-20">
          <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_auto] lg:items-end">
            <div>
              <p className="font-mono text-xs font-semibold uppercase opacity-55">Engineering posture / 03</p>
              <h2 className="mt-5 max-w-3xl text-3xl font-semibold leading-tight sm:text-5xl">
                Evidence over spectacle. Performance by design.
              </h2>
              <div className="mt-9 flex max-w-3xl flex-wrap gap-x-8 gap-y-3 text-sm opacity-70">
                {CREATOR_PROFILE.principles.map((principle) => <span key={principle}>{principle}</span>)}
              </div>
            </div>
            <Link
              href="/"
              className="inline-flex h-11 items-center gap-2 rounded-md bg-background px-5 text-sm font-semibold text-foreground transition-opacity hover:opacity-85 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-background"
            >
              View product
              <ArrowUpRight aria-hidden className="size-4" />
            </Link>
          </div>
        </section>
      </main>
      <PublicFooter />
    </div>
  );
}
