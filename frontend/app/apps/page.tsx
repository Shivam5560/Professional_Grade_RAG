import { AppCatalog } from "@/components/platform/AppCatalog";

export default function AppsPage() {
  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-primary">
        NexusMind
      </p>
      <h1 className="mt-3 text-4xl font-semibold tracking-tight text-foreground">
        Application showcase
      </h1>
      <p className="mt-4 max-w-3xl text-base leading-7 text-muted-foreground">
        Production-grade AI reference applications built on reusable Nexus Core
        capabilities.
      </p>

      <section className="mt-10" aria-label="Enabled applications">
        <AppCatalog />
      </section>
    </main>
  );
}
