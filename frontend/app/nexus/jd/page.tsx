'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { ClipboardList, FileCheck, ArrowRight, Sparkles } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { useNexusFlowStore } from '@/lib/nexusFlowStore';
import { useToast } from '@/hooks/useToast';
import AuthPage from '@/app/auth/page';

export default function NexusJobDescriptionPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const {
    selectedResume,
    jobDescription,
    setJobDescription,
    setAnalysis,
  } = useNexusFlowStore();
  const [isMounted, setIsMounted] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    if (!isMounted) return;
    if (!selectedResume) {
      router.replace('/nexus/resumes');
    }
  }, [isMounted, selectedResume, router]);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  const handleAnalyze = async () => {
    if (!selectedResume || !user || !jobDescription.trim()) return;
    setAnalyzing(true);
    try {
      const result = await apiClient.analyzeResume({
        user_id: user.id,
        resume_id: selectedResume.resume_id,
        job_description: jobDescription,
      });
      setAnalysis(result);
      router.push('/nexus/report');
    } catch (error) {
      console.error('Analyze failed:', error);
      toast({ title: 'Analysis failed', description: error instanceof Error ? error.message : 'Could not analyze resume', variant: 'destructive' });
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      {analyzing ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/70 backdrop-blur-sm">
          <div className="relative w-[340px] rounded-3xl border border-foreground/10 bg-card/80 px-6 py-6 text-center shadow-2xl shadow-black/10">
            <div className="absolute -top-10 left-1/2 h-24 w-24 -translate-x-1/2 rounded-full bg-emerald-500/20 blur-2xl" />
            <div className="relative">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-emerald-500/30 bg-emerald-500/10">
                <div className="h-7 w-7 rounded-full border-2 border-emerald-300 border-t-transparent animate-spin" />
              </div>
              <p className="mt-4 text-sm font-semibold text-foreground">Generating Nexus report</p>
              <p className="mt-1 text-xs text-muted-foreground">Analyzing alignment, gaps, and language quality.</p>
              <div className="mt-4 h-1.5 w-full rounded-full bg-foreground/10 overflow-hidden">
                <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-emerald-400/70 via-emerald-300/40 to-transparent animate-pulse" />
              </div>
              <div className="mt-4 grid gap-2 text-left text-[11px] text-muted-foreground">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  Parsing resume and JD context
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-foreground/30" />
                  Running hybrid similarity scoring
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-foreground/30" />
                  Generating recommendations
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-[1200px] mx-auto space-y-8">
          <section className="glass-panel rounded-3xl p-6 md:p-10">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <Badge className="bg-foreground text-background">Job Description</Badge>
                <h1 className="text-3xl md:text-4xl font-black mt-3">Add the JD for this role</h1>
                <p className="text-sm text-muted-foreground mt-2">
                  Paste the role requirements to generate the report on the next screen.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Button variant="ghost" onClick={() => router.push('/nexus/resumes')}>
                  Back to Resume Select
                </Button>
              </div>
            </div>
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <Card className="glass-panel border-border/60">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center">
                    <ClipboardList className="h-5 w-5 text-indigo-500" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">Job Description Input</p>
                    <p className="text-xs text-muted-foreground">Use the full JD or key requirements for the role.</p>
                  </div>
                </div>
                <Textarea
                  placeholder="Paste the job description here..."
                  value={jobDescription}
                  onChange={(event) => setJobDescription(event.target.value)}
                  className="min-h-[300px]"
                />
                <Button onClick={handleAnalyze} disabled={!jobDescription.trim() || analyzing} className="gap-2">
                  <Sparkles className="h-4 w-4" />
                  {analyzing ? 'Analyzing...' : 'Generate Report'}
                </Button>
              </CardContent>
            </Card>

            <Card className="glass-panel border-border/60">
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/20 flex items-center justify-center">
                    <FileCheck className="h-5 w-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">Selected Resume</p>
                    <p className="text-xs text-muted-foreground">Confirm the resume before analyzing.</p>
                  </div>
                </div>
                {selectedResume ? (
                  <div className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                    <p className="text-sm font-semibold">{selectedResume.filename}</p>
                    <p className="text-xs text-muted-foreground">Resume ID: {selectedResume.resume_id}</p>
                    <p className="text-xs text-muted-foreground mt-2">Status: {selectedResume.status}</p>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No resume selected.</p>
                )}
                <div className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                  <div className="flex items-center gap-2">
                    <ArrowRight className="h-3.5 w-3.5 text-amber-500" />
                    <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Next Step</p>
                  </div>
                  <p className="text-sm mt-2">
                    Generate the report to review hybrid similarity, grammar feedback, and recommendations.
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>
        </div>
      </main>
    </div>
  );
}
