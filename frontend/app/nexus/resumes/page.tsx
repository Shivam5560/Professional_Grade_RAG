'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { CheckCircle2, Upload, Trash2 } from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { useNexusFlowStore } from '@/lib/nexusFlowStore';
import { useToast } from '@/hooks/useToast';
import type { ResumeDashboardResponse, ResumeFileInfo, ResumeHistoryResponse } from '@/lib/types';
import AuthPage from '@/app/auth/page';

export default function NexusResumeSelectPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const { selectedResume, setSelectedResume, setJobDescription, setAnalysis } = useNexusFlowStore();
  const { toast, confirm } = useToast();
  const [isMounted, setIsMounted] = useState(false);
  const [resumes, setResumes] = useState<ResumeFileInfo[]>([]);
  const [dashboard, setDashboard] = useState<ResumeDashboardResponse | null>(null);
  const [history, setHistory] = useState<ResumeHistoryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const fileRef = useRef<HTMLInputElement | null>(null);

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
      setHistory(historyData);
    } catch (error) {
      console.error('Failed to load resume data:', error);
      toast({ title: 'Failed to load resumes', description: error instanceof Error ? error.message : 'Unknown error', variant: 'destructive' });
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

  const recentHistory = useMemo(() => {
    const list = history?.list ? [...history.list] : [];
    return list
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 3);
  }, [history]);
  const filteredResumes = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) return resumes;
    return resumes.filter((resume) =>
      [resume.filename, resume.resume_id, resume.status].some((value) =>
        value?.toLowerCase().includes(normalized)
      )
    );
  }, [query, resumes]);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  const handleUpload = async () => {
    if (!fileRef.current?.files?.[0] || !user) return;
    setUploading(true);
    try {
      await apiClient.uploadResume(fileRef.current.files[0], user.id);
      fileRef.current.value = '';
      toast({ title: 'Resume uploaded', description: 'Your resume has been uploaded successfully.' });
      await loadData(user.id);
    } catch (error) {
      console.error('Upload failed:', error);
      toast({ title: 'Upload failed', description: error instanceof Error ? error.message : 'Could not upload resume', variant: 'destructive' });
    } finally {
      setUploading(false);
    }
  };

  const handleSelectResume = (resume: ResumeFileInfo) => {
    setSelectedResume(resume);
    setJobDescription('');
    setAnalysis(null);
  };

  const handleContinue = () => {
    if (!selectedResume) return;
    router.push('/nexus/jd');
  };

  const handleDelete = async (resume: ResumeFileInfo, e: React.MouseEvent) => {
    e.stopPropagation(); // Don't select the resume when clicking delete
    if (!user) return;
    const confirmed = await confirm({
      title: `Delete "${resume.filename}"?`,
      description: 'This will remove the resume and all its analyses.',
      confirmLabel: 'Delete',
      variant: 'destructive',
    });
    if (!confirmed) return;
    
    setDeleting(resume.resume_id);
    try {
      await apiClient.deleteResume(user.id, resume.resume_id);
      // Clear selection if the deleted resume was selected
      if (selectedResume?.resume_id === resume.resume_id) {
        setSelectedResume(null);
      }
      toast({ title: 'Resume deleted', description: `"${resume.filename}" has been removed.` });
      await loadData(user.id);
    } catch (error) {
      console.error('Delete failed:', error);
      toast({ title: 'Delete failed', description: error instanceof Error ? error.message : 'Could not delete resume', variant: 'destructive' });
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
      <div className="pointer-events-none absolute -top-32 right-[-10%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.18),transparent_65%)] blur-2xl float-slow" />
      <div className="pointer-events-none absolute top-[10%] left-[-12%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.2),transparent_65%)] blur-3xl float-slower" />
      <div className="pointer-events-none absolute bottom-[-18%] right-[8%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-4)/0.16),transparent_70%)] blur-3xl float-slowest" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-[1400px] mx-auto space-y-8">
          <section className="glass-panel sheen-border rounded-3xl p-6 md:p-10 bg-accent-soft">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <Badge className="bg-foreground text-background">Resume Select</Badge>
                <h1 className="text-3xl md:text-4xl font-black mt-3">Choose a resume to score</h1>
                <p className="text-sm text-muted-foreground mt-2">
                  Select from your resume knowledge base or upload a new file before moving to the JD screen.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                <Input ref={fileRef} type="file" accept=".pdf,.doc,.docx,.txt" className="sm:max-w-[260px]" />
                <Button onClick={handleUpload} disabled={uploading} className="gap-2">
                  <Upload className="h-4 w-4" />
                  {uploading ? 'Uploading...' : 'Upload Resume'}
                </Button>
              </div>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-3">
            {[
              { label: 'Total resumes', value: stats.total },
              { label: 'Analyzed resumes', value: stats.analyzed },
              { label: 'Pending reviews', value: stats.pending },
            ].map((stat) => (
              <Card key={stat.label} className="glass-panel sheen-border border-border/60 bg-accent-soft">
                <CardHeader>
                  <CardTitle>{stat.label}</CardTitle>
                  <CardDescription>Portfolio status</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-black">{stat.value}</p>
                </CardContent>
              </Card>
            ))}
          </section>

          <section className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
            <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
              <CardHeader>
                <CardTitle>Resume Knowledge Base</CardTitle>
                <CardDescription>Pick a resume and continue to the job description screen.</CardDescription>
              </CardHeader>
              <CardContent className="h-[520px]">
                <div className="mb-4">
                  <Input
                    placeholder="Search by filename, ID, or status..."
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                </div>
                <ScrollArea className="h-full pr-3">
                  {loading ? (
                    <p className="text-sm text-muted-foreground">Loading resumes...</p>
                  ) : filteredResumes.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No resumes uploaded yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {filteredResumes.map((resume) => (
                        <button
                          key={resume.id}
                          type="button"
                          onClick={() => handleSelectResume(resume)}
                          className={`w-full text-left rounded-2xl border px-4 py-3 transition-all hover-glow ${
                            selectedResume?.id === resume.id
                              ? 'border-foreground/30 bg-foreground/5'
                              : 'border-border/60 bg-card/60 hover:border-border'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="text-sm font-semibold text-foreground line-clamp-1">
                                {resume.filename}
                              </p>
                              <p className="text-xs text-muted-foreground">Resume ID: {resume.resume_id}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              {selectedResume?.id === resume.id ? (
                                <span className="inline-flex items-center gap-1 rounded-full border border-foreground/20 bg-foreground/10 px-2.5 py-1 text-[11px] font-semibold text-foreground">
                                  <CheckCircle2 className="h-3.5 w-3.5" /> Selected
                                </span>
                              ) : null}
                              <Badge variant="secondary" className="bg-foreground/10 text-foreground">
                                {resume.status}
                              </Badge>
                              <button
                                type="button"
                                onClick={(e) => handleDelete(resume, e)}
                                disabled={deleting === resume.resume_id}
                                className="p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                                title="Delete resume"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground mt-2">Uploaded {formatDate(resume.created_at)}</p>
                        </button>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>

            <div className="space-y-6">
              <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
                <CardHeader>
                  <CardTitle>Flow Control</CardTitle>
                  <CardDescription>Move to the job description screen when ready.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {selectedResume ? (
                    <div className="rounded-2xl border border-foreground/10 bg-foreground/5 px-4 py-3">
                      <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Selected Resume</p>
                      <p className="text-sm font-semibold mt-2">{selectedResume.filename}</p>
                      <p className="text-xs text-muted-foreground mt-1">Resume ID: {selectedResume.resume_id}</p>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Select a resume to enable the next step.</p>
                  )}
                  <Button onClick={handleContinue} disabled={!selectedResume} className="w-full">
                    Continue to Job Description
                  </Button>
                  <Button variant="ghost" onClick={() => router.push('/nexus')} className="w-full">
                    Back to Nexus Dashboard
                  </Button>
                </CardContent>
              </Card>

              <Card className="glass-panel sheen-border border-border/60 bg-accent-soft">
                <CardHeader>
                  <CardTitle>Latest Nexus Activity</CardTitle>
                  <CardDescription>Recent analysis snapshots from the workspace.</CardDescription>
                </CardHeader>
                <CardContent>
                  {recentHistory.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No analyses yet.</p>
                  ) : (
                    <div className="space-y-3">
                      {recentHistory.map((entry) => (
                        <div key={entry.analysis_id} className="rounded-2xl border border-border/60 bg-card/60 px-4 py-3">
                          <div className="flex items-center justify-between">
                            <p className="text-sm font-semibold">Resume {entry.resume_id}</p>
                            <Badge variant="secondary" className="bg-foreground/10 text-foreground">
                              {entry.overall_score ?? '—'}%
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">{formatDate(entry.created_at)}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
