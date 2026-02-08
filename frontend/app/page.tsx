'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Database, Sparkles, ArrowRight } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import AuthPage from '@/app/auth/page';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-12">
        <div className="max-w-6xl mx-auto space-y-10">
          <div className="glass-panel rounded-[32px] p-6 md:p-10 overflow-hidden relative">
            <div className="absolute -top-20 -right-24 h-64 w-64 rounded-full bg-accent-soft blur-2xl float-slow" />
            <div className="absolute -bottom-24 left-8 h-56 w-56 rounded-full bg-accent-soft blur-2xl float-slower" />
            <div className="relative grid gap-6 lg:grid-cols-[1.2fr_0.8fr] items-center">
              <div className="space-y-4">
                <Badge className="w-fit bg-foreground text-background">Workspace</Badge>
                <h1 className="text-4xl md:text-5xl font-black tracking-tight leading-tight">
                  Command your knowledge
                  <span className="text-accent"> in real time</span>
                </h1>
                <p className="text-muted-foreground max-w-xl text-base md:text-lg">
                  Switch between conversational RAG and SQL intelligence without losing context. Every query stays grounded in your data.
                </p>
                <div className="flex flex-wrap gap-3">
                  <Button className="px-6" onClick={() => router.push('/chat')}>
                    Launch RAG Chat
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Button>
                  <Button variant="outline" className="px-6" onClick={() => router.push('/aurasql')}>
                    Enter AuraSQL
                    <Sparkles className="h-4 w-4 ml-2" />
                  </Button>
                </div>
              </div>
              <div className="space-y-4">
                <div className="rounded-3xl border border-border/60 bg-card/70 p-5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Live Workspace</span>
                    <span className="text-xs text-muted-foreground">Ready</span>
                  </div>
                  <div className="mt-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="h-9 w-9 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                        <MessageSquare className="h-4 w-4 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">RAG Chat</p>
                        <p className="text-xs text-muted-foreground">Multi-document, fast + think modes</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="h-9 w-9 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                        <Database className="h-4 w-4 text-primary-foreground" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold">AuraSQL</p>
                        <p className="text-xs text-muted-foreground">Context-aware SQL generation</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="rounded-3xl border border-border/60 bg-card/70 p-5">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Focus Mode</p>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Keep your answers precise with context-aware generation and confidence cues.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Card className="glass-panel border-border/60">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                    <MessageSquare className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <CardTitle>RAG Chat</CardTitle>
                    <CardDescription>Ask questions over your documents.</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Hybrid retrieval with fast/think modes, confidence scoring, and citations.
                </p>
                <Button className="w-full justify-between" onClick={() => router.push('/chat')}>
                  Open Chat
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>

            <Card className="glass-panel border-border/60">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                    <Database className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <CardTitle>AuraSQL</CardTitle>
                    <CardDescription>Generate and run SQL on connected DBs.</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Save table contexts once, re-use them without re-fetching schemas.
                </p>
                <Button className="w-full justify-between" onClick={() => router.push('/aurasql')}>
                  Open AuraSQL
                  <Sparkles className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
