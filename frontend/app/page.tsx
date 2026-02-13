'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Database, Sparkles, ArrowRight, Loader2, FileText, BookOpen, Code2 } from 'lucide-react';
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

      <main className="relative z-10 px-4 md:px-8 py-12">
        <div className="max-w-6xl mx-auto space-y-10">
          <section className="lux-card sheen-border rounded-[36px] p-6 md:p-10 relative overflow-hidden reveal-up">
            <div className="absolute -top-24 -right-24 h-72 w-72 rounded-full bg-accent-soft blur-3xl float-slow" />
            <div className="absolute -bottom-24 left-8 h-64 w-64 rounded-full bg-accent-soft blur-3xl float-slower" />
            <div className="absolute inset-0 intro-sheen" />

            <div className="relative grid gap-10 lg:grid-cols-[1.15fr_0.85fr] items-center">
              <div className="space-y-5">
                <Badge className="w-fit bg-foreground text-background">NexusMind Studio</Badge>
                <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-[1.05]">
                  Orchestrate answers
                  <span className="text-accent"> with clarity</span>
                </h1>
                <p className="text-muted-foreground max-w-xl text-base md:text-lg">
                  A premium RAG workspace that blends conversational intelligence, SQL automation, and grounded citations into one command center.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button className="px-6" onClick={() => handleNavigate('/chat', 'RAG Chat')}>
                    Launch RAG Chat
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                  <Button variant="outline" className="px-6" onClick={() => handleNavigate('/aurasql', 'AuraSQL')}>
                    Enter AuraSQL
                    <Sparkles className="h-4 w-4 ml-2" />
                  </Button>
                  <Button variant="secondary" className="px-6" onClick={() => handleNavigate('/nexus', 'Resume Studio')}>
                    Open Resume Studio
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary" className="bg-foreground/10 text-foreground">Hybrid retrieval</Badge>
                  <Badge variant="secondary" className="bg-foreground/10 text-foreground">Confidence scoring</Badge>
                  <Badge variant="secondary" className="bg-foreground/10 text-foreground">Source grounded</Badge>
                </div>
              </div>

              <div className="space-y-4">
                <div className="lux-card rounded-3xl p-5 glow-ring hover-glow reveal-up delay-1">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Command Pillars</p>
                  <div className="mt-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                        <MessageSquare className="h-4 w-4 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">RAG Chat</p>
                        <p className="text-xs text-muted-foreground">Fast + think modes, live citations</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                        <Database className="h-4 w-4 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">AuraSQL</p>
                        <p className="text-xs text-muted-foreground">Schema-aware SQL generation</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                        <Sparkles className="h-4 w-4 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">Resume Studio</p>
                        <p className="text-xs text-muted-foreground">Score + align with JD targets</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                        <FileText className="h-4 w-4 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">ResumeGen</p>
                        <p className="text-xs text-muted-foreground">LaTeX-compiled PDF builder</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="lux-card rounded-3xl p-5 hover-glow reveal-up delay-2">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Focus</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Multi-factor relevance scoring keeps answers precise while context memory stays intact across sessions.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="lux-card rounded-[28px] p-4 md:p-6 overflow-hidden reveal-up delay-2">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Signal Stream</p>
              <Badge variant="outline" className="border-border/60">Live capabilities</Badge>
            </div>
            <div className="marquee overflow-hidden">
              <div className="flex gap-3 whitespace-nowrap marquee-track">
                {['Hybrid BM25 + semantic', 'Rerank + citations', 'Context memory', 'Groq LLMs', 'pgvector storage', 'Confidence scoring'].map((item) => (
                  <span key={item} className="px-4 py-2 rounded-full border border-border/60 bg-card/70 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                    {item}
                  </span>
                ))}
                {['Hybrid BM25 + semantic', 'Rerank + citations', 'Context memory', 'Groq LLMs', 'pgvector storage', 'Confidence scoring'].map((item) => (
                  <span key={`${item}-dup`} className="px-4 py-2 rounded-full border border-border/60 bg-card/70 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          </section>

          <section className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                title: 'RAG Chat',
                description: 'Grounded answers with citations and confidence scoring.',
                cta: 'Open Chat',
                icon: MessageSquare,
                path: '/chat',
                tone: 'bg-[hsl(var(--chart-1)/0.12)] border-[hsl(var(--chart-1)/0.28)] text-[hsl(var(--chart-1))]',
              },
              {
                title: 'AuraSQL',
                description: 'Schema-aware SQL generation, refinement, and execution.',
                cta: 'Open AuraSQL',
                icon: Database,
                path: '/aurasql',
                tone: 'bg-[hsl(var(--chart-2)/0.12)] border-[hsl(var(--chart-2)/0.28)] text-[hsl(var(--chart-2))]',
              },
              {
                title: 'Resume Studio',
                description: 'Score resumes against job descriptions with ATS alignment.',
                cta: 'Nexus Studio',
                icon: Sparkles,
                path: '/nexus',
                tone: 'bg-[hsl(var(--chart-4)/0.12)] border-[hsl(var(--chart-4)/0.28)] text-[hsl(var(--chart-4))]',
              },
              {
                title: 'ResumeGen',
                description: 'Build polished, LaTeX-compiled PDF resumes step by step.',
                cta: 'Generate Resume',
                icon: FileText,
                path: '/nexus/generate',
                tone: 'bg-[hsl(var(--chart-5)/0.12)] border-[hsl(var(--chart-5)/0.28)] text-[hsl(var(--chart-5))]',
              },
            ].map((card, index) => (
              <div key={card.title} className={`lux-card sheen-border rounded-3xl p-5 space-y-3 hover-glow reveal-up delay-${index + 1}`}>
                <div className={`h-11 w-11 rounded-xl flex items-center justify-center border ${card.tone}`}>
                  <card.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-lg font-bold">{card.title}</p>
                  <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{card.description}</p>
                </div>
                <Button size="sm" className="w-full justify-between" onClick={() => handleNavigate(card.path, card.title)}>
                  {card.cta}
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              </div>
            ))}
          </section>

          <section className="grid gap-4 md:grid-cols-4 reveal-up delay-3">
            {[
              { label: 'Response precision', value: 'Multi-factor scoring', icon: Sparkles },
              { label: 'Execution flow', value: 'RAG + SQL unified', icon: Database },
              { label: 'Knowledge base', value: 'Document-grounded', icon: BookOpen },
              { label: 'Developer tools', value: 'Profile + portfolio', icon: Code2 },
            ].map((stat) => (
              <div key={stat.label} className="lux-card rounded-2xl p-4 hover-glow">
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className="h-3.5 w-3.5 text-muted-foreground" />
                  <p className="text-[10px] uppercase tracking-[0.25em] text-muted-foreground">{stat.label}</p>
                </div>
                <p className="text-sm font-semibold">{stat.value}</p>
              </div>
            ))}
          </section>
        </div>
      </main>
    </div>
  );
}
