'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { useNexusFlowStore } from '@/lib/nexusFlowStore';
import type { ResumeAnalyzeResponse, ResumeDashboardResponse, ResumeFileInfo } from '@/lib/types';
import AuthPage from '@/app/auth/page';
import { Upload, FileText } from 'lucide-react';

export default function NexusDashboardPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const { setAnalysis, setJobDescription, setSelectedResume } = useNexusFlowStore();
  const [isMounted, setIsMounted] = useState(false);
  const [resumes, setResumes] = useState<ResumeFileInfo[]>([]);
  const [dashboard, setDashboard] = useState<ResumeDashboardResponse | null>(null);
  const [history, setHistory] = useState<ResumeAnalyzeResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [navTarget, setNavTarget] = useState<string | null>(null);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const loadData = async (userId: number) => {
    setLoading(true);
    try {
      const [resumeData, dashboardData, historyData] = await Promise.all([
        apiClient.listResumes(userId),
        apiClient.getResumeDashboard(userId),
        apiClient.getResumeHistory(userId),
      ]);
      setResumes(resumeData.list);
      setDashboard(dashboardData);
      setHistory(historyData.list || []);
    } catch (error) {
      console.error('Failed to load resume dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isMounted || !isAuthenticated || !user) return;
    loadData(user.id);
  }, [isMounted, isAuthenticated, user]);

  const stats = dashboard?.resume_stats ?? { total: 0, analyzed: 0, pending: 0 };
  const formatDate = (value?: string) => {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const handleOpenReport = (entry: ResumeAnalyzeResponse) => {
    setAnalysis(entry);
    setJobDescription(entry.job_description ?? '');
    const matchedResume = resumes.find((resume) => resume.resume_id === entry.resume_id) || null;
    setSelectedResume(matchedResume);
    router.push('/nexus/report');
  };

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

      <Header />

      {navTarget ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-background/70 backdrop-blur-sm">
          <div className="glass-panel sheen-border rounded-3xl px-6 py-4 text-center">
            <p className="text-sm font-semibold">Opening {navTarget}</p>
            <p className="text-xs text-muted-foreground mt-1">Preparing Nexus workspace.</p>
          </div>
        </div>
      ) : null}

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-[1400px] mx-auto space-y-8">
          <section className="glass-panel sheen-border rounded-3xl p-6 md:p-10 bg-accent-soft">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <Badge className="bg-foreground text-background">Nexus Dashboard</Badge>
                <h1 className="text-3xl md:text-4xl font-black mt-3">Resume Scoring Command Center</h1>
                <p className="text-sm text-muted-foreground mt-2">
                  Track resume performance, review history, and launch a new scoring workflow.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button onClick={() => handleNavigate('/nexus/resumes', 'Resume Select')}>
                  <Upload className="h-4 w-4 mr-2" />Select Resume
                </Button>
                <Button variant="secondary" onClick={() => handleNavigate('/nexus/jd', 'Job Description')}>
                  Enter Job Description
                </Button>
                <Button variant="outline" onClick={() => handleNavigate('/nexus/generate', 'ResumeGen')}>
                  <FileText className="h-4 w-4 mr-2" />Build Resume (ResumeGen)
                </Button>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            {[
              { label: 'Total resumes', value: stats.total },
              { label: 'Analyzed', value: stats.analyzed },
              { label: 'Pending', value: stats.pending },
            ].map((stat) => (
              <div key={stat.label} className="glass-panel sheen-border border-border/60 bg-accent-soft rounded-2xl px-5 py-4 hover-glow transition-transform hover:-translate-y-0.5">
                <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">{stat.label}</p>
                <p className="text-3xl font-black">{stat.value}</p>
              </div>
            ))}
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
            <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
              <CardHeader>
                <CardTitle>Resume Library</CardTitle>
                <CardDescription>Upload resumes first, then select one to continue.</CardDescription>
              </CardHeader>
              <CardContent className="h-[520px]">
                <ScrollArea className="h-full pr-3">
                  {loading ? (
                    <p className="text-sm text-muted-foreground">Loading resumes...</p>
                  ) : resumes.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No resumes uploaded yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {resumes.map((resume) => (
                        <div key={resume.id} className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-semibold text-foreground line-clamp-1">
                                {resume.filename}
                              </p>
                              <p className="text-xs text-muted-foreground">Resume ID: {resume.resume_id}</p>
                            </div>
                            <Badge variant="secondary" className="bg-foreground/10 text-foreground">
                              {resume.status}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mt-2">Uploaded {resume.created_at}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>

            <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
              <CardHeader>
                <CardTitle>Next Actions</CardTitle>
                <CardDescription>Move into the resume selection flow.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Step 1</p>
                  <p className="text-sm mt-2">Upload resumes to build your Nexus knowledge base.</p>
                </div>
                <div className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Step 2</p>
                  <p className="text-sm mt-2">Select a resume and continue to the job description screen.</p>
                </div>
                <Button onClick={() => handleNavigate('/nexus/resumes', 'Resume Select')}>Go to Resume Select</Button>
              </CardContent>
            </Card>
          </section>

          <section className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft">
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <Badge className="bg-foreground text-background">Audit Trail</Badge>
                <h2 className="text-2xl font-black mt-3">Resume + JD History</h2>
                <p className="text-sm text-muted-foreground mt-2">Review past analyses and reopen any report.</p>
              </div>
              <Button variant="secondary" onClick={() => handleNavigate('/nexus/resumes', 'Resume Select')}>New Analysis</Button>
            </div>
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading history...</p>
            ) : history.length === 0 ? (
              <p className="text-sm text-muted-foreground">No analyses yet.</p>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {history
                  .slice()
                  .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                  .slice(0, 3)
                  .map((entry) => (
                  <button
                    key={entry.analysis_id}
                    type="button"
                    onClick={() => handleOpenReport(entry)}
                    className="rounded-2xl border border-border/60 bg-card/60 px-5 py-4 text-left transition-all hover:border-foreground/30 hover:bg-foreground/5"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">{formatDate(entry.created_at)}</p>
                        <p className="text-sm font-semibold text-foreground mt-2">Resume {entry.resume_id}</p>
                      </div>
                      <Badge variant="secondary" className="bg-foreground/10 text-foreground">
                        {entry.overall_score ?? '—'}%
                      </Badge>
                    </div>
                    <div className="mt-3 rounded-xl border border-border/40 bg-foreground/5 px-4 py-3">
                      <p className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Job Description</p>
                      <p className="text-sm text-foreground/80 mt-2 line-clamp-3">
                        {entry.job_description || '—'}
                      </p>
                    </div>
                    <div className="mt-3 text-xs text-muted-foreground">Click to reopen full report</div>
                  </button>
                ))}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
