'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertTriangle,
  Award,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Gauge,
  Hash,
  Lightbulb,
  Mail,
  Phone,
  ShieldCheck,
  Sparkles,
  TrendingUp,
  User,
  XCircle,
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { useNexusFlowStore } from '@/lib/nexusFlowStore';
import AuthPage from '@/app/auth/page';
 
export default function NexusReportPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { analysis, selectedResume, jobDescription, reset } = useNexusFlowStore();
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const refinedRecommendations = useMemo(() => {
    const raw = analysis?.analysis?.refined_recommendations;
    if (Array.isArray(raw)) return raw;
    if (raw && typeof raw === 'object') return Object.values(raw).filter((item) => typeof item === 'string');
    return [];
  }, [analysis]);

  const refinedJustifications = useMemo(() => {
    const raw = analysis?.analysis?.refined_justifications;
    if (Array.isArray(raw)) return raw;
    if (raw && typeof raw === 'object') return Object.values(raw).filter((item) => typeof item === 'string');
    return [];
  }, [analysis]);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  if (!analysis) {
    return (
      <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 app-aurora" />
        <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
        <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

        <Header />

        <main className="relative z-10 px-4 md:px-8 py-10">
          <div className="max-w-[900px] mx-auto space-y-6">
            <Card className="glass-panel sheen-border border-border/60">
              <CardHeader>
                <CardTitle>No report found</CardTitle>
                <CardDescription>Run an analysis to generate a Nexus report.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button onClick={() => router.push('/nexus/jd')}>Return to Job Description</Button>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  const technicalScore = analysis.analysis?.technical_score?.similarity_score ?? analysis.analysis?.technical_score;
  const grammarScore = analysis.analysis?.grammar_analysis?.score ?? null;
  const hybridScore = analysis.analysis?.technical_score?.similarity_score ?? analysis.overall_score ?? null;
  const vectorScore = analysis.analysis?.technical_score?.vector_similarity_score ?? null;
  const bm25Score = analysis.analysis?.technical_score?.bm25_similarity_score ?? null;
  const skillsMissing = analysis.analysis?.technical_score?.required_skills_missing ?? [];
  const skillsFound = analysis.analysis?.technical_score?.required_skills_found ?? [];
  const responsibilitiesMissing =
    analysis.analysis?.technical_score?.key_responsibilities_comparison?.missing_responsibilities ?? [];
  const resumeData = analysis.analysis?.resume_data ?? {};
  const resumeName = resumeData?.personal_info?.name ?? 'Resume';
  const resumeEmail = resumeData?.personal_info?.email ?? null;
  const resumePhone = resumeData?.personal_info?.phone ?? null;
  const resumeKeywords = Array.isArray(resumeData?.keywords) ? resumeData.keywords : [];
  const grammarSectionScores = analysis.analysis?.grammar_analysis?.section_scores ?? {};
  const jobDescriptionText = analysis.job_description || jobDescription || '';
  
  const getScoreColor = (score: number | null) => {
    if (!score) return 'text-muted-foreground';
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };
  
  const getScoreGradient = (score: number | null) => {
    if (!score) return 'from-gray-500 to-gray-600';
    if (score >= 80) return 'from-green-500 to-emerald-600';
    if (score >= 60) return 'from-yellow-500 to-orange-600';
    return 'from-red-500 to-rose-600';
  };

  const clampScore = (score?: number | null) => {
    if (typeof score !== 'number' || Number.isNaN(score)) return 0;
    return Math.max(0, Math.min(100, score));
  };

  const formatSectionLabel = (value: string) =>
    value
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());

  const grammarBreakdown = Object.entries(grammarSectionScores)
    .map(([key, value]) => {
      const entry = value as { score?: number; category?: string } | null;
      return {
        key,
        label: formatSectionLabel(key),
        score: typeof entry?.score === 'number' ? entry.score : null,
        category: typeof entry?.category === 'string' ? entry.category : '—',
      };
    })
    .slice(0, 8);

  const getReadiness = (score: number | null) => {
    const value = clampScore(score);
    if (value >= 85) return { key: 'elite', label: 'Elite Fit', sub: 'Top percentile match' };
    if (value >= 70) return { key: 'strong', label: 'Strong Fit', sub: 'High alignment' };
    if (value >= 55) return { key: 'developing', label: 'Developing Fit', sub: 'Good potential' };
    return { key: 'early', label: 'Early Fit', sub: 'Growth opportunity' };
  };

  const containerVariants: any = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.08,
        delayChildren: 0.05,
      },
    },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 18 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
      },
    },
  };

  const toneStyles = {
    green: {
      card: 'border-green-500/20 bg-green-500/5',
      glow: 'bg-green-500/10',
      iconWrap: 'bg-green-500/20 border-green-500/30',
      icon: 'text-green-500',
      value: 'text-green-500',
    },
    red: {
      card: 'border-red-500/20 bg-red-500/5',
      glow: 'bg-red-500/10',
      iconWrap: 'bg-red-500/20 border-red-500/30',
      icon: 'text-red-500',
      value: 'text-red-500',
    },
    blue: {
      card: 'border-blue-500/20 bg-blue-500/5',
      glow: 'bg-blue-500/10',
      iconWrap: 'bg-blue-500/20 border-blue-500/30',
      icon: 'text-blue-500',
      value: 'text-blue-500',
    },
    purple: {
      card: 'border-purple-500/20 bg-purple-500/5',
      glow: 'bg-purple-500/10',
      iconWrap: 'bg-purple-500/20 border-purple-500/30',
      icon: 'text-purple-500',
      value: 'text-purple-500',
    },
  } as const;

  const readinessStyles = {
    elite: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
    strong: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-700 dark:text-cyan-300',
    developing: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
    early: 'border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300',
  } as const;

  const readiness = getReadiness(analysis.overall_score ?? 0);

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none fixed inset-0 app-aurora" />
      <div className="pointer-events-none fixed inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none fixed inset-0 bg-noise opacity-40" />
      <motion.div
        className="pointer-events-none fixed -top-40 right-[-10%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.22),transparent_65%)] blur-2xl"
        animate={{ y: [0, 20, 0], x: [0, -12, 0], opacity: [0.6, 0.8, 0.6] }}
        transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="pointer-events-none fixed top-[20%] left-[-12%] h-[520px] w-[520px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.2),transparent_65%)] blur-3xl"
        animate={{ y: [0, -30, 0], x: [0, 16, 0], opacity: [0.5, 0.75, 0.5] }}
        transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        className="pointer-events-none fixed bottom-[-20%] right-[10%] h-[460px] w-[460px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-4)/0.18),transparent_70%)] blur-3xl"
        animate={{ y: [0, 25, 0], x: [0, -18, 0], opacity: [0.45, 0.7, 0.45] }}
        transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
      />

      <div className="fixed top-0 left-0 right-0 z-40 border-b border-white/10 bg-background/70 backdrop-blur-xl">
        <Header />
      </div>

      <main className="relative z-10 px-4 md:px-8 py-10 pt-28">
        <motion.div
          className="max-w-[1600px] mx-auto space-y-8 w-full"
          variants={containerVariants}
          initial="hidden"
          animate="show"
        >
          <motion.section className="glass-panel sheen-border rounded-3xl p-6 md:p-10 bg-accent-soft" variants={itemVariants}>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              <div>
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                  Nexus Report
                </div>
                <h1 className="text-3xl md:text-4xl font-black mt-3 tracking-tight text-foreground">
                  Detailed Resume Report
                </h1>
                <div className="mt-3 h-1 w-20 rounded-full bg-gradient-to-r from-emerald-400/70 to-sky-400/60" />
                <p className="text-sm text-muted-foreground mt-2">
                  Hybrid relevance + grammar analysis in a single view.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  className="bg-foreground text-background hover:bg-foreground/90 shadow-lg shadow-black/10"
                  onClick={() => router.push('/nexus/jd')}
                >
                  Update Job Description
                </Button>
                <Button
                  variant="secondary"
                  className="border border-foreground/20 bg-foreground/5 text-foreground hover:bg-foreground/10"
                  onClick={() => {
                    reset();
                    router.push('/nexus/resumes');
                  }}
                >
                  Start New Report
                </Button>
              </div>
            </div>
            <motion.div
              className="mt-8 rounded-2xl border border-foreground/10 bg-accent-soft p-4 md:p-5 shadow-xl shadow-black/10 relative overflow-hidden sheen-border"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            >
              <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-[hsl(var(--chart-1)/0.12)] blur-2xl" />
              <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[hsl(var(--chart-1)/0.35)] to-transparent" />
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="h-12 w-12 rounded-2xl bg-[hsl(var(--chart-1)/0.15)] border border-[hsl(var(--chart-1)/0.35)] flex items-center justify-center">
                    <Gauge className="h-5 w-5 text-[hsl(var(--chart-1))]" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Readiness</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${readinessStyles[readiness.key as keyof typeof readinessStyles]}`}>
                        {readiness.label}
                      </span>
                      <span className="text-xs text-muted-foreground">{readiness.sub}</span>
                    </div>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="px-2.5 py-1 rounded-full border border-foreground/10 bg-foreground/5 flex items-center gap-1">
                    <Award className="h-3 w-3" /> Overall
                  </span>
                </div>
              </div>
              <div className="mt-5 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-2xl lux-card px-5 py-4 shadow-sm shadow-black/5">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                      <User className="h-3.5 w-3.5 text-[hsl(var(--chart-1))]" />
                      Candidate
                    </div>
                    <p className="text-base font-semibold text-foreground mt-2">{resumeName}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {resumeData?.personal_info?.title || 'Role focus unavailable'}
                    </p>
                  </div>
                  <div className="rounded-2xl lux-card px-5 py-4 shadow-sm shadow-black/5">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                      <Hash className="h-3.5 w-3.5 text-[hsl(var(--chart-2))]" />
                      Resume ID
                    </div>
                    <p className="text-sm text-foreground/80 mt-2">{selectedResume?.resume_id ?? '—'}</p>
                  </div>
                  <div className="rounded-2xl lux-card px-5 py-4 shadow-sm shadow-black/5">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                      <Mail className="h-3.5 w-3.5 text-[hsl(var(--chart-3))]" />
                      Email
                    </div>
                    <p className="text-sm text-foreground/80 mt-2">{resumeEmail ?? '—'}</p>
                  </div>
                  <div className="rounded-2xl lux-card px-5 py-4 shadow-sm shadow-black/5">
                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                      <Phone className="h-3.5 w-3.5 text-[hsl(var(--chart-4))]" />
                      Phone
                    </div>
                    <p className="text-sm text-foreground/80 mt-2">{resumePhone ?? '—'}</p>
                  </div>
                  <div className="rounded-2xl lux-card px-5 py-4 shadow-sm shadow-black/5 md:col-span-2">
                    <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                      <span className="px-2.5 py-1 rounded-full border border-foreground/10 bg-foreground/5 flex items-center gap-1">
                        <ShieldCheck className="h-3 w-3 text-[hsl(var(--chart-1))]" /> Verified analysis
                      </span>
                      <span className="px-2.5 py-1 rounded-full border border-foreground/10 bg-foreground/5 flex items-center gap-1">
                        <Sparkles className="h-3 w-3 text-[hsl(var(--chart-2))]" /> Nexus insight profile
                      </span>
                    </div>
                  </div>
                </div>
                <div className="rounded-2xl border border-foreground/10 bg-accent-soft px-5 py-4 shadow-lg shadow-black/10 sheen-border">
                  <p className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">Overall Score</p>
                  <div className="mt-2 flex items-end gap-2">
                    <p className="text-5xl font-black text-foreground">{clampScore(analysis.overall_score ?? null)}</p>
                    <span className="text-lg text-muted-foreground mb-1">%</span>
                  </div>
                  <div className="mt-3 h-2 w-full rounded-full bg-muted/30 overflow-hidden">
                    <div
                      className={`h-full bg-gradient-to-r ${getScoreGradient(analysis.overall_score ?? null)}`}
                      style={{ width: `${clampScore(analysis.overall_score ?? null)}%` }}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.section>

          <motion.section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]" variants={itemVariants}>
            <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft relative overflow-hidden flex flex-col">
              <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-indigo-500/10 blur-2xl" />
              <div className="mb-6 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                    <Gauge className="h-6 w-6 text-indigo-400" />
                    Technical Match Detail
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">Hybrid scoring breakdown</p>
                </div>
                <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
                  <TrendingUp className="h-4 w-4" />
                  Live scoring
                </div>
              </div>
              <div className="space-y-4 flex-1">
                <div className="rounded-2xl border-2 border-border/60 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 px-6 py-5">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground font-semibold">Technical Score</p>
                    <span className={`text-3xl font-black ${getScoreColor(technicalScore)}`}>
                      {clampScore(technicalScore)}%
                    </span>
                  </div>
                  <div className="w-full bg-muted/30 rounded-full h-2 overflow-hidden">
                    <motion.div
                      className={`h-full bg-gradient-to-r ${getScoreGradient(technicalScore)}`}
                      initial={{ width: 0 }}
                      animate={{ width: `${clampScore(technicalScore)}%` }}
                      transition={{ duration: 1.2, ease: 'easeOut' }}
                    />
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-2xl border border-sky-500/20 bg-card/60 px-5 py-4 shadow-sm shadow-black/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="h-8 w-8 rounded-xl bg-sky-500/15 border border-sky-500/30 flex items-center justify-center">
                        <BarChart3 className="h-4 w-4 text-sky-500" />
                      </div>
                      <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Semantic Similarity</p>
                    </div>
                    <div className="flex items-end gap-2">
                      <p className={`text-3xl font-black ${getScoreColor(vectorScore)}`}>
                        {vectorScore?.toFixed(1) ?? '—'}
                      </p>
                      <span className="text-lg text-muted-foreground mb-1">%</span>
                    </div>
                    <div className="w-full bg-muted/30 rounded-full h-1.5 overflow-hidden mt-3">
                      <motion.div
                        className={`h-full bg-gradient-to-r ${getScoreGradient(vectorScore)}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${clampScore(vectorScore)}%` }}
                        transition={{ duration: 1.1, ease: 'easeOut' }}
                      />
                    </div>
                  </div>
                  <div className="rounded-2xl border border-amber-500/20 bg-card/60 px-5 py-4 shadow-sm shadow-black/5">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="h-8 w-8 rounded-xl bg-amber-500/15 border border-amber-500/30 flex items-center justify-center">
                        <Hash className="h-4 w-4 text-amber-500" />
                      </div>
                      <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Keyword Matching</p>
                    </div>
                    <div className="flex items-end gap-2">
                      <p className={`text-3xl font-black ${getScoreColor(bm25Score)}`}>
                        {bm25Score?.toFixed(1) ?? '—'}
                      </p>
                      <span className="text-lg text-muted-foreground mb-1">%</span>
                    </div>
                    <div className="w-full bg-muted/30 rounded-full h-1.5 overflow-hidden mt-3">
                      <motion.div
                        className={`h-full bg-gradient-to-r ${getScoreGradient(bm25Score)}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${clampScore(bm25Score)}%` }}
                        transition={{ duration: 1.1, ease: 'easeOut' }}
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4">
                    <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground mb-2">Resume File</p>
                    <p className="text-sm font-medium text-foreground">{selectedResume?.filename ?? '—'}</p>
                  </div>
                  <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4">
                    <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground mb-2">Job Description</p>
                    <ScrollArea className="max-h-24">
                      <p className="text-sm text-foreground/80 leading-relaxed pr-4">{jobDescriptionText || '—'}</p>
                    </ScrollArea>
                  </div>
                </div>
              </div>
            </div>

            <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft flex flex-col">
              <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                    <FileText className="h-6 w-6 text-foreground/70" />
                    Grammar Breakdown
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">Compact readability insights</p>
                </div>
                <div className="text-xs text-muted-foreground">{grammarBreakdown.length} sections</div>
              </div>
              {grammarBreakdown.length === 0 ? (
                <p className="text-sm text-muted-foreground">No grammar breakdown available.</p>
              ) : (
                <div className="grid gap-4 grid-cols-2 md:grid-cols-2 flex-1">
                  {grammarBreakdown.map((item) => (
                    <div
                      key={item.key}
                      className="rounded-2xl border border-foreground/10 bg-gradient-to-br from-foreground/5 to-foreground/10 px-5 py-4 transition-transform duration-300 hover:-translate-y-1 hover:shadow-lg hover:shadow-foreground/10"
                    >
                      <p className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">{item.label}</p>
                      <div className="flex items-end justify-between mt-2">
                        <p className="text-sm text-foreground/70">{item.category}</p>
                        <p className="text-xl font-black text-foreground">
                          {item.score ?? '—'}
                        </p>
                      </div>
                      <div className="mt-3 h-2 w-full rounded-full bg-muted/30 overflow-hidden">
                        <div
                          className={`h-full bg-gradient-to-r ${getScoreGradient(item.score ?? null)}`}
                          style={{ width: `${clampScore(item.score ?? null)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.section>

          {/* Report Snapshot with Key Metrics */}
          <motion.section className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft" variants={itemVariants}>
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black tracking-tight">Report Snapshot</h2>
                <p className="text-sm text-muted-foreground mt-1">Quick overview of analysis highlights</p>
              </div>
              <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
                <TrendingUp className="h-4 w-4" />
                Live metrics
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              {[
                {
                  label: 'Skills Matched',
                  value: skillsFound.length,
                  icon: CheckCircle2,
                  tone: 'green',
                },
                {
                  label: 'Skills Missing',
                  value: skillsMissing.length,
                  icon: XCircle,
                  tone: 'red',
                },
                {
                  label: 'Keywords Found',
                  value: resumeKeywords.length,
                  icon: Hash,
                  tone: 'blue',
                },
                {
                  label: 'Semantic Similarity',
                  value: `${clampScore(vectorScore).toFixed(0)}%`,
                  icon: BarChart3,
                  tone: 'purple',
                },
              ].map((tile) => {
                const tone = toneStyles[tile.tone as keyof typeof toneStyles];
                const Icon = tile.icon;
                return (
                  <motion.div
                    key={tile.label}
                    whileHover={{ y: -4, scale: 1.01 }}
                    transition={{ type: 'spring', stiffness: 250, damping: 20 }}
                    className={`rounded-2xl border-2 px-5 py-4 relative overflow-hidden ${tone.card}`}
                  >
                    <div className={`absolute -right-6 -top-6 h-20 w-20 rounded-full blur-2xl ${tone.glow}`} />
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${tone.iconWrap}`}>
                        <Icon className={`h-5 w-5 ${tone.icon}`} />
                      </div>
                      <div>
                        <p className={`text-2xl font-black ${tone.value}`}>{tile.value}</p>
                        <p className="text-xs text-muted-foreground">{tile.label}</p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-foreground/10 bg-foreground/5 px-5 py-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Matched Skills</p>
                  <span className="text-xs text-muted-foreground">{skillsFound.length} total</span>
                </div>
                {skillsFound.length === 0 ? (
                  <p className="text-sm text-muted-foreground mt-3">No skills matched yet.</p>
                ) : (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {skillsFound.slice(0, 16).map((skill: string, idx: number) => (
                      <Badge
                        key={`${skill}-${idx}`}
                        className="bg-emerald-500/15 text-emerald-700 dark:text-emerald-200 border border-emerald-500/30 px-3 py-1 text-xs"
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="rounded-2xl border border-foreground/10 bg-foreground/5 px-5 py-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Skill Gaps</p>
                  <span className="text-xs text-muted-foreground">{skillsMissing.length} total</span>
                </div>
                {skillsMissing.length === 0 ? (
                  <p className="text-sm text-muted-foreground mt-3">No missing skills detected.</p>
                ) : (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {skillsMissing.slice(0, 16).map((skill: string, idx: number) => (
                      <Badge
                        key={`${skill}-${idx}`}
                        className="bg-rose-500/15 text-rose-700 dark:text-rose-200 border border-rose-500/30 px-3 py-1 text-xs"
                      >
                        {skill}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="rounded-2xl border border-foreground/10 bg-foreground/5 px-5 py-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Top Keywords</p>
                  <span className="text-xs text-muted-foreground">{resumeKeywords.length} total</span>
                </div>
                {resumeKeywords.length === 0 ? (
                  <p className="text-sm text-muted-foreground mt-3">No keywords extracted.</p>
                ) : (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {resumeKeywords.slice(0, 16).map((keyword: string, idx: number) => (
                      <Badge
                        key={`${keyword}-${idx}`}
                        variant="secondary"
                        className="bg-gradient-to-r from-sky-500/10 to-emerald-500/10 text-foreground/80 border border-foreground/10 px-3 py-1 text-xs hover:from-sky-500/20 hover:to-emerald-500/20 transition-colors"
                      >
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </motion.section>

          {/* Recommendations Section */}
          <motion.section className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft" variants={itemVariants}>
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                  <Lightbulb className="h-6 w-6 text-blue-500" />
                  Recommendations
                </h2>
                <p className="text-sm text-muted-foreground mt-1">Actionable improvements to boost your resume score</p>
              </div>
              <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
                <Sparkles className="h-4 w-4" />
                Prioritized insights
              </div>
            </div>
            {refinedRecommendations.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No recommendations available yet.</p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                {refinedRecommendations.slice(0, 12).map((item: string, idx: number) => (
                  <motion.div
                    key={`${item}-${idx}`}
                    whileHover={{ y: -6, scale: 1.01 }}
                    transition={{ type: 'spring', stiffness: 220, damping: 18 }}
                    className="group rounded-2xl border-2 border-border/60 bg-gradient-to-br from-blue-500/10 via-indigo-500/5 to-purple-500/10 px-5 py-4 hover:border-blue-500/40 hover:shadow-2xl hover:shadow-blue-500/10"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-10 h-10 rounded-2xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-500 font-bold text-sm group-hover:bg-blue-500 group-hover:text-white transition-colors">
                        {idx + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-[15px] text-foreground/90 leading-7">{item}</p>
                        <div className="mt-3 h-1 w-16 rounded-full bg-gradient-to-r from-blue-500/40 to-purple-500/40" />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.section>

          {/* Responsibility Gaps */}
          {responsibilitiesMissing.length > 0 && (
            <motion.section className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft" variants={itemVariants}>
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                    <ClipboardCheck className="h-6 w-6 text-orange-500" />
                    Responsibility Gaps
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">Key responsibilities missing from your resume</p>
                </div>
                <div className="text-xs text-muted-foreground">{responsibilitiesMissing.length} items</div>
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {responsibilitiesMissing.map((item: string, index: number) => (
                  <motion.div
                    key={`${item}-${index}`}
                    whileHover={{ y: -4 }}
                    transition={{ type: 'spring', stiffness: 220, damping: 18 }}
                    className="rounded-xl border border-orange-500/30 bg-orange-500/5 px-5 py-4"
                  >
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="h-4 w-4 text-orange-500 mt-1" />
                      <p className="text-sm text-foreground/90 leading-relaxed">{item}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.section>
          )}

          {/* Justifications Section */}
          <motion.section className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft" variants={itemVariants}>
            <div className="mb-6 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-black tracking-tight flex items-center gap-2">
                  <ClipboardCheck className="h-6 w-6 text-foreground/70" />
                  Score Justifications
                </h2>
                <p className="text-sm text-muted-foreground mt-1">Why your resume received this score</p>
              </div>
              <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
                <BarChart3 className="h-4 w-4" />
                Evidence trail
              </div>
            </div>
            {refinedJustifications.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No justifications available yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {refinedJustifications.slice(0, 12).map((item: string, idx: number) => (
                  <motion.div
                    key={`${item}-${idx}`}
                    whileHover={{ y: -4 }}
                    transition={{ type: 'spring', stiffness: 220, damping: 18 }}
                    className="group rounded-2xl border border-foreground/10 bg-gradient-to-r from-foreground/5 via-foreground/10 to-foreground/5 px-5 py-4 hover:border-foreground/20 hover:shadow-lg"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center">
                        <span className="text-xs font-bold text-indigo-500">{idx + 1}</span>
                      </div>
                      <div className="flex-1">
                        <p className="text-[15px] text-foreground/85 leading-7">{item}</p>
                        <div className="mt-3 h-1 w-12 rounded-full bg-gradient-to-r from-indigo-500/40 to-rose-400/30" />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.section>
        </motion.div>
      </main>
    </div>
  );
}
