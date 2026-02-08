'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Database, BookOpen, Sparkles, ArrowRight } from 'lucide-react';
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

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-6xl mx-auto space-y-8">
          <div className="glass-panel rounded-3xl p-6 md:p-10">
            <div className="flex flex-col gap-3">
              <Badge className="w-fit bg-foreground text-background">Workspace</Badge>
              <h1 className="text-3xl md:text-4xl font-black tracking-tight">
                NexusMind Control Center
              </h1>
              <p className="text-muted-foreground max-w-2xl">
                Pick the right tool for the job. Switch between conversational RAG, SQL intelligence, and your knowledge base without re-indexing.
              </p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
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

            <Card className="glass-panel border-border/60">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-2xl logo-mark flex items-center justify-center ring-2 ring-foreground/10">
                    <BookOpen className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <CardTitle>Knowledge Base</CardTitle>
                    <CardDescription>Manage your indexed assets.</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Review documents and SQL contexts stored for quick reuse.
                </p>
                <Button variant="outline" className="w-full justify-between" onClick={() => router.push('/knowledge-base')}>
                  Open Knowledge Base
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
