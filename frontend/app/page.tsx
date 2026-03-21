'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Badge } from '@/components/ui/badge';
import { ShaderAnimation } from '@/components/ui/shader-animation';
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
      <div className="pointer-events-none absolute inset-0 opacity-35">
        <ShaderAnimation className="w-full h-full" speed={0.08} />
      </div>
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
          <section className="grid gap-4 lg:grid-cols-2 reveal-up">
            <article className="lux-card sheen-border rounded-[30px] p-6 md:p-8 overflow-hidden min-h-[560px] md:min-h-[600px] lg:min-h-[620px] flex flex-col justify-between">
              <div className="space-y-5">
                <Badge className="w-fit bg-foreground text-background">NexusMind Story</Badge>
                <h1 className="text-3xl md:text-5xl font-black tracking-tight leading-[1.02]">
                  Build, validate, and ship AI outcomes from one command center
                </h1>
                <p className="text-sm md:text-base text-muted-foreground max-w-2xl">
                  Start with grounded retrieval, transition into schema-aware analytics, then finish with resume intelligence and export-ready documents. Every stage carries context forward so decisions stay explainable.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                  {[
                    'Hybrid BM25 + semantic retrieval',
                    'Rerank + source citations',
                    'Schema-aware SQL + context memory',
                    'Confidence scoring + reasoning modes',
                  ].map((item) => (
                    <div key={item} className="rounded-xl border border-border/60 bg-card/70 px-3 py-2 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      {item}
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-1 gap-2 pt-2">
                  {[
                    { step: '01', title: 'Discover', desc: 'Interrogate sources with hybrid retrieval and cite-backed answers.' },
                    { step: '02', title: 'Decide', desc: 'Convert intent to SQL, run analysis, and preserve context history.' },
                    { step: '03', title: 'Deliver', desc: 'Score resumes, optimize content, and generate polished outputs.' },
                  ].map((item) => (
                    <div key={item.step} className="rounded-xl border border-border/60 bg-card/65 px-3 py-3">
                      <div className="flex items-center gap-2">
                        <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-border/70 text-[10px] font-semibold tracking-[0.15em] text-muted-foreground">{item.step}</span>
                        <p className="text-sm font-semibold">{item.title}</p>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </article>

            <article className="lux-card sheen-border rounded-[30px] p-6 md:p-8 overflow-hidden min-h-[560px] md:min-h-[600px] lg:min-h-[620px]">
              <div className="flex items-center justify-between gap-3 mb-4">
                <Badge variant="outline" className="border-border/60">Tools</Badge>
                <p className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">4 Launchers</p>
              </div>

              <div className="flex flex-wrap gap-2 mb-4">
                {['Production Ready', 'Context Aware', 'Traceable', 'Fast Mode'].map((item) => (
                  <Badge key={item} variant="outline" className="h-6 px-2.5 text-[9px] uppercase tracking-[0.16em] border-border/70">
                    {item}
                  </Badge>
                ))}
              </div>

              <div className="space-y-3">
                {[
                  {
                    title: 'RAG Chat',
                    description: 'Grounded answers with citations and confidence scoring.',
                    icon: MessageSquare,
                    path: '/chat',
                    tone: 'bg-[hsl(var(--chart-1)/0.12)] border-[hsl(var(--chart-1)/0.28)] text-[hsl(var(--chart-1))]',
                    badge: 'RAG',
                    badge2: 'Cited',
                  },
                  {
                    title: 'AuraSQL',
                    description: 'Schema-aware SQL generation and refinement.',
                    icon: Database,
                    path: '/aurasql',
                    tone: 'bg-[hsl(var(--chart-2)/0.12)] border-[hsl(var(--chart-2)/0.28)] text-[hsl(var(--chart-2))]',
                    badge: 'SQL',
                    badge2: 'Schema',
                  },
                  {
                    title: 'Resume Studio',
                    description: 'ATS alignment and JD-based resume scoring.',
                    icon: Sparkles,
                    path: '/nexus',
                    tone: 'bg-[hsl(var(--chart-4)/0.12)] border-[hsl(var(--chart-4)/0.28)] text-[hsl(var(--chart-4))]',
                    badge: 'Nexus',
                    badge2: 'Scoring',
                  },
                  {
                    title: 'ResumeGen',
                    description: 'Structured resume builder with LaTeX PDF output.',
                    icon: FileText,
                    path: '/nexus/generate',
                    tone: 'bg-[hsl(var(--chart-5)/0.12)] border-[hsl(var(--chart-5)/0.28)] text-[hsl(var(--chart-5))]',
                    badge: 'PDF',
                    badge2: 'LaTeX',
                  },
                ].map((tool) => (
                  <article
                    key={tool.title}
                    role="button"
                    tabIndex={0}
                    onClick={() => handleNavigate(tool.path, tool.title)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        handleNavigate(tool.path, tool.title);
                      }
                    }}
                    className="rounded-2xl border border-border/60 bg-card/70 p-4 hover-glow cursor-pointer transition-transform hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3 min-w-0">
                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center border shrink-0 ${tool.tone}`}>
                          <tool.icon className="h-4.5 w-4.5" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-bold truncate">{tool.title}</p>
                            <Badge variant="outline" className="h-5 px-2 text-[9px] uppercase tracking-[0.16em] border-border/70">
                              {tool.badge}
                            </Badge>
                            <Badge variant="outline" className="h-5 px-2 text-[9px] uppercase tracking-[0.16em] border-border/70">
                              {tool.badge2}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{tool.description}</p>
                        </div>
                      </div>
                      <div className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground shrink-0 pt-1">
                        Open
                        <ArrowRight className="h-3.5 w-3.5" />
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </article>
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
