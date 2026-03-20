'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Database, Sparkles, ArrowRight, Loader2, FileText } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);
  const [navTarget, setNavTarget] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted || !isAuthenticated) return;
    router.prefetch('/chat');
    router.prefetch('/aurasql');
    router.prefetch('/nexus');
  }, [isMounted, isAuthenticated, router]);

  const handleNavigate = (path: string, label: string) => {
    setNavTarget(label);
    router.push(path);
  };

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
      <div className="pointer-events-none absolute -top-32 right-[-10%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.16),transparent_65%)] blur-2xl float-slow" />
      <div className="pointer-events-none absolute top-[12%] left-[-12%] h-[460px] w-[460px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.18),transparent_65%)] blur-3xl float-slower" />
      <div className="pointer-events-none absolute bottom-[-18%] right-[6%] h-[440px] w-[440px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-4)/0.14),transparent_70%)] blur-3xl float-slowest" />

      <Header />

      {navTarget && (
        <div className="absolute inset-0 z-20 bg-background/70 backdrop-blur-sm flex items-center justify-center">
          <div className="glass-panel rounded-3xl px-6 py-4 flex items-center gap-3">
            <Loader2 className="h-5 w-5 animate-spin" />
            <div>
              <p className="text-sm font-semibold">Opening {navTarget}</p>
              <p className="text-xs text-muted-foreground">Optimizing workspace data...</p>
            </div>
          </div>
        </div>
      )}

      <main className="relative z-10 px-4 md:px-8 py-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <section className="lux-card sheen-border rounded-[34px] p-6 md:p-8 overflow-hidden reveal-up">
            <div className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr] items-end">
              <div className="space-y-4">
                <Badge className="w-fit bg-foreground text-background">NexusMind Studio</Badge>
                <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-[1.02]">
                  One workspace for chat, SQL, and resume intelligence
                </h1>
                <p className="text-sm md:text-base text-muted-foreground max-w-3xl">
                  Launch the tool you need in one click. Every flow is grounded with context-aware retrieval, confidence signals, and production-ready outputs.
                </p>
              </div>
              <div className="grid grid-cols-1 gap-2">
                {[
                  'Hybrid BM25 + semantic retrieval',
                  'Rerank + source citations',
                  'Schema-aware SQL + context memory',
                ].map((item) => (
                  <div key={item} className="rounded-xl border border-border/60 bg-card/70 px-3 py-2 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                    {item}
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 reveal-up delay-1">
            {[
              {
                title: 'RAG Chat',
                description: 'Grounded answers with citations and confidence scoring.',
                icon: MessageSquare,
                path: '/chat',
                tone: 'bg-[hsl(var(--chart-1)/0.12)] border-[hsl(var(--chart-1)/0.28)] text-[hsl(var(--chart-1))]',
              },
              {
                title: 'AuraSQL',
                description: 'Schema-aware SQL generation and refinement.',
                icon: Database,
                path: '/aurasql',
                tone: 'bg-[hsl(var(--chart-2)/0.12)] border-[hsl(var(--chart-2)/0.28)] text-[hsl(var(--chart-2))]',
              },
              {
                title: 'Resume Studio',
                description: 'ATS alignment and JD-based resume scoring.',
                icon: Sparkles,
                path: '/nexus',
                tone: 'bg-[hsl(var(--chart-4)/0.12)] border-[hsl(var(--chart-4)/0.28)] text-[hsl(var(--chart-4))]',
              },
              {
                title: 'ResumeGen',
                description: 'Structured resume builder with LaTeX PDF output.',
                icon: FileText,
                path: '/nexus/generate',
                tone: 'bg-[hsl(var(--chart-5)/0.12)] border-[hsl(var(--chart-5)/0.28)] text-[hsl(var(--chart-5))]',
              },
            ].map((card) => (
              <article
                key={card.title}
                role="button"
                tabIndex={0}
                onClick={() => handleNavigate(card.path, card.title)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    handleNavigate(card.path, card.title);
                  }
                }}
                className="lux-card sheen-border rounded-2xl p-5 flex flex-col justify-between hover-glow cursor-pointer transition-transform hover:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div className="space-y-3">
                  <div className={`h-11 w-11 rounded-xl flex items-center justify-center border ${card.tone}`}>
                    <card.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-lg font-bold">{card.title}</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{card.description}</p>
                  </div>
                </div>
                <div className="mt-5 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                  Open tool
                  <ArrowRight className="h-3.5 w-3.5" />
                </div>
              </article>
            ))}
          </section>

          <section className="lux-card rounded-2xl p-4 md:p-5 overflow-hidden reveal-up delay-2">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Live capabilities</p>
              <Badge variant="outline" className="border-border/60">Ready to launch</Badge>
            </div>
            <div className="marquee overflow-hidden mt-3">
              <div className="flex gap-2 whitespace-nowrap marquee-track">
                {['Hybrid BM25 + semantic', 'Rerank + citations', 'Context memory', 'Groq LLMs', 'pgvector storage', 'Confidence scoring'].map((item) => (
                  <span key={item} className="px-3 py-1 rounded-full border border-border/60 bg-card/70 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                    {item}
                  </span>
                ))}
                {['Hybrid BM25 + semantic', 'Rerank + citations', 'Context memory', 'Groq LLMs', 'pgvector storage', 'Confidence scoring'].map((item) => (
                  <span key={`${item}-dup`} className="px-3 py-1 rounded-full border border-border/60 bg-card/70 text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
