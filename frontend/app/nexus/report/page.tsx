'use client';

import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  AlertTriangle,
  Award,
  BarChart3,
  BookOpen,
  Briefcase,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock,
  FileSearch,
  FileText,
  Gauge,
  GraduationCap,
  Hash,
  Lightbulb,
  Mail,
  Phone,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  TrendingUp,
  User,
  XCircle,
  Zap,
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { useNexusFlowStore } from '@/lib/nexusFlowStore';
import AuthPage from '@/app/auth/page';

/* ─────────────────────────── helpers ─────────────────────────── */

const clamp = (v?: number | null) => {
  if (typeof v !== 'number' || Number.isNaN(v)) return 0;
  return Math.max(0, Math.min(100, v));
};

const fmt = (v?: number | null, decimals = 1) => {
  if (typeof v !== 'number' || Number.isNaN(v)) return '—';
  return v.toFixed(decimals);
};

const color = (v?: number | null) => {
  if (typeof v !== 'number') return 'text-muted-foreground';
  if (v >= 80) return 'text-emerald-500';
  if (v >= 60) return 'text-amber-500';
  return 'text-rose-500';
};

const gradient = (v?: number | null) => {
  if (typeof v !== 'number') return 'from-gray-500 to-gray-600';
  if (v >= 80) return 'from-emerald-500 to-emerald-600';
  if (v >= 60) return 'from-amber-500 to-orange-500';
  return 'from-rose-500 to-red-600';
};

const label = (s: string) =>
  s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

const toArr = (v: unknown): string[] => {
  if (!Array.isArray(v)) return [];
  return v
    .map((x) => {
      if (typeof x === 'string') return x;
      if (x && typeof x === 'object') {
        const o = x as Record<string, unknown>;
        if (typeof o.action === 'string') return o.action;
        return JSON.stringify(x);
      }
      return String(x ?? '');
    })
    .filter(Boolean);
};

/* ─────────────────────────── animated bar ────────────────────── */
const Bar = ({ value, className = '' }: { value: number; className?: string }) => (
  <div className="h-2 w-full rounded-full bg-muted/30 overflow-hidden mt-2">
    <motion.div
      className={`h-full rounded-full bg-gradient-to-r ${gradient(value)} ${className}`}
      initial={{ width: 0 }}
      animate={{ width: `${clamp(value)}%` }}
      transition={{ duration: 1, ease: 'easeOut' }}
    />
  </div>
);

/* ─────────────────────────── score ring  ─────────────────────── */
const ScoreRing = ({ score, size = 120, stroke = 10 }: { score: number; size?: number; stroke?: number }) => {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const pct = clamp(score);
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" strokeWidth={stroke} className="stroke-muted/30" />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          strokeWidth={stroke}
          strokeLinecap="round"
          className={`${pct >= 80 ? 'stroke-emerald-500' : pct >= 60 ? 'stroke-amber-500' : 'stroke-rose-500'}`}
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - (circ * pct) / 100 }}
          transition={{ duration: 1.4, ease: 'easeOut' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-black ${color(score)}`}>{fmt(score, 1)}</span>
        <span className="text-[10px] text-muted-foreground tracking-wider">/ 100</span>
      </div>
    </div>
  );
};

/* ────────────────────────── mini score card ──────────────────── */
const MiniScore = ({
  icon: Icon,
  title,
  score,
  accent,
}: {
  icon: React.ElementType;
  title: string;
  score: number | null;
  accent: string;
}) => (
  <div className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm px-5 py-4 shadow-sm transition-transform hover:-translate-y-1 hover:shadow-md">
    <div className="flex items-center gap-2 mb-3">
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center ${accent}`}>
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">{title}</p>
    </div>
    <p className={`text-3xl font-black ${color(score)}`}>{fmt(score)}%</p>
    <Bar value={clamp(score)} />
  </div>
);

/* ──────────────────── section variants ───────────────────────── */
const container: any = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07, delayChildren: 0.04 } },
};
const item: any = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55 } },
};

/* ═════════════════════════════════════════════════════════════════
   MAIN PAGE
   ═════════════════════════════════════════════════════════════════ */
export default function NexusReportPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const { analysis, selectedResume, jobDescription, reset } = useNexusFlowStore();
  const [isMounted, setIsMounted] = useState(false);
  useEffect(() => setIsMounted(true), []);

  /* ── unwrap analysis payload ─────────────────────────────────── */
  const d = useMemo<Record<string, any>>(() => {
    const raw = analysis?.analysis ?? analysis ?? {};
    if (typeof raw === 'string') {
      try { return JSON.parse(raw); } catch { return {}; }
    }
    return raw ?? {};
  }, [analysis]);

  /* ── extract fields ──────────────────────────────────────────── */
  const overallScore: number | null   = d.overall_score ?? analysis?.overall_score ?? null;
  const fitCategory: string           = d.fit_category ?? '';
  const sb                            = d.score_breakdown ?? {};
  const techMatchScore: number | null = sb.technical_match ?? d.technical_score?.similarity_score ?? null;
  const atsScore: number | null       = sb.ats_compatibility ?? d.ats_analysis?.score ?? null;
  const writingScore: number | null   = sb.writing_quality ?? d.grammar_analysis?.score ?? null;
  const sectionScore: number | null   = sb.section_completeness ?? d.section_analysis?.score ?? null;

  const ts       = d.technical_score ?? {};
  const matched  = toArr(ts.matched_skills);
  const missing  = toArr(ts.missing_skills);

  const ats      = d.ats_analysis ?? {};
  const atsComp  = ats.components ?? {};
  const atsLlm   = ats.llm_feedback ?? {};
  const sa       = d.section_analysis ?? {};
  const sections = sa.sections ?? {};

  const ma       = d.match_analysis ?? {};
  const rd       = d.resume_data ?? {};
  const jd       = d.jd_data ?? {};

  const recs     = useMemo(() => {
    const raw = d.refined_recommendations ?? d.recommendations ?? [];
    if (!Array.isArray(raw)) return [];
    return raw.filter((x: any) => x && (typeof x === 'object' || typeof x === 'string'));
  }, [d]);

  const justifications = useMemo(() => {
    const raw = d.refined_justifications ?? [];
    if (!Array.isArray(raw)) return [];
    return raw.map((x: any) => (typeof x === 'string' ? x : JSON.stringify(x))).filter(Boolean);
  }, [d]);

  const resumeName  = rd.name ?? '';
  const resumeEmail = rd.email ?? null;
  const resumePhone = rd.phone ?? null;
  const resumeSkills = toArr(rd.skills);
  const experience   = Array.isArray(rd.experience) ? rd.experience : [];
  const education    = Array.isArray(rd.education) ? rd.education : [];

  const jdText = analysis?.job_description || jobDescription || '';

  /* ── readiness badge  ────────────────────────────────────────── */
  const readiness = (() => {
    const v = clamp(overallScore);
    if (v >= 85) return { label: 'Elite Fit',      badge: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' };
    if (v >= 70) return { label: 'Strong Fit',     badge: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-300 border-cyan-500/30' };
    if (v >= 55) return { label: 'Good Potential',  badge: 'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30' };
    return           { label: 'Needs Improvement', badge: 'bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30' };
  })();

  /* ── guard ───────────────────────────────────────────────────── */
  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;
  if (!analysis) {
    return (
      <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 app-aurora" />
        <Header />
        <main className="relative z-10 px-4 md:px-8 py-10">
          <div className="max-w-[900px] mx-auto space-y-6">
            <Card className="glass-panel sheen-border border-border/60">
              <CardHeader><CardTitle>No report found</CardTitle></CardHeader>
              <CardContent><Button onClick={() => router.push('/nexus/jd')}>Return to Job Description</Button></CardContent>
            </Card>
          </div>
        </main>
      </div>
    );
  }

  /* ═══════════════════════════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════════════════════════ */
  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      {/* Background effects */}
      <div className="pointer-events-none fixed inset-0 app-aurora" />
      <div className="pointer-events-none fixed inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none fixed inset-0 bg-noise opacity-40" />
      <motion.div className="pointer-events-none fixed -top-40 right-[-10%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.22),transparent_65%)] blur-2xl" animate={{ y: [0, 20, 0], opacity: [0.6, 0.8, 0.6] }} transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }} />
      <motion.div className="pointer-events-none fixed top-[20%] left-[-12%] h-[520px] w-[520px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.2),transparent_65%)] blur-3xl" animate={{ y: [0, -30, 0], opacity: [0.5, 0.75, 0.5] }} transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }} />

      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-40 border-b border-white/10 bg-background/70 backdrop-blur-xl">
        <Header />
      </div>

      <main className="relative z-10 px-4 md:px-8 py-10 pt-28">
        <motion.div className="max-w-[1600px] mx-auto space-y-8 w-full" variants={container} initial="hidden" animate="show">

          {/* ═══════════════════ 1. HERO BANNER ═══════════════════ */}
          <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-10 relative overflow-hidden">
            <div className="absolute -right-16 -top-16 h-40 w-40 rounded-full bg-[hsl(var(--chart-1)/0.12)] blur-3xl" />
            <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[hsl(var(--chart-1)/0.35)] to-transparent" />

            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-8">
              <div>
                <div className="flex items-center gap-2 text-xs uppercase tracking-[0.3em] text-muted-foreground mb-2">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-400" /> Nexus Report
                </div>
                <h1 className="text-3xl md:text-4xl font-black tracking-tight">Resume Analysis Report</h1>
                <div className="mt-2 h-1 w-20 rounded-full bg-gradient-to-r from-emerald-400/70 to-sky-400/60" />
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button className="bg-foreground text-background hover:bg-foreground/90 shadow-lg shadow-black/10" onClick={() => router.push('/nexus/jd')}>
                  Update Job Description
                </Button>
                <Button variant="secondary" className="border border-foreground/20 bg-foreground/5 text-foreground hover:bg-foreground/10" onClick={() => { reset(); router.push('/nexus/resumes'); }}>
                  Start New Report
                </Button>
              </div>
            </div>

            {/* Hero content: Candidate + Overall Score */}
            <div className="grid gap-6 lg:grid-cols-[1fr_auto]">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-2xl lux-card px-5 py-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                    <User className="h-3.5 w-3.5 text-[hsl(var(--chart-1))]" /> Candidate
                  </div>
                  <p className="text-lg font-semibold text-foreground mt-2">{resumeName || '—'}</p>
                  {jd.title && <p className="text-xs text-muted-foreground mt-0.5">Applying for: {jd.title}</p>}
                </div>
                <div className="rounded-2xl lux-card px-5 py-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                    <Mail className="h-3.5 w-3.5 text-[hsl(var(--chart-3))]" /> Contact
                  </div>
                  <p className="text-sm text-foreground/80 mt-2">{resumeEmail ?? '—'}</p>
                  {resumePhone && <p className="text-xs text-muted-foreground mt-0.5">{resumePhone}</p>}
                </div>
                <div className="rounded-2xl lux-card px-5 py-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                    <Hash className="h-3.5 w-3.5 text-[hsl(var(--chart-2))]" /> Resume
                  </div>
                  <p className="text-sm text-foreground/80 mt-2 truncate">{selectedResume?.filename ?? '—'}</p>
                </div>
                <div className="rounded-2xl lux-card px-5 py-4">
                  <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                    <Target className="h-3.5 w-3.5 text-[hsl(var(--chart-4))]" /> Fit Category
                  </div>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`text-xs font-semibold px-3 py-1 rounded-full border ${readiness.badge}`}>
                      {fitCategory || readiness.label}
                    </span>
                  </div>
                </div>
              </div>

              {/* Overall score ring */}
              <div className="flex flex-col items-center justify-center rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm px-8 py-6 shadow-lg">
                <p className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground mb-3">Overall Score</p>
                <ScoreRing score={overallScore ?? 0} size={130} stroke={10} />
                {fitCategory && (
                  <Badge className={`mt-3 text-xs ${readiness.badge}`}>{fitCategory}</Badge>
                )}
              </div>
            </div>
          </motion.section>

          {/* ═══════════════════ 2. SCORE BREAKDOWN (4 cards) ═══════════════════ */}
          <motion.section variants={item} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MiniScore icon={Gauge}        title="Technical Match"      score={techMatchScore} accent="bg-indigo-500/15 text-indigo-500" />
            <MiniScore icon={FileSearch}    title="ATS Compatibility"    score={atsScore}       accent="bg-emerald-500/15 text-emerald-500" />
            <MiniScore icon={FileText}      title="Writing Quality"      score={writingScore}   accent="bg-amber-500/15 text-amber-500" />
            <MiniScore icon={ClipboardCheck} title="Section Complete"    score={sectionScore}   accent="bg-sky-500/15 text-sky-500" />
          </motion.section>

          {/* ═══════════════════ 3. SKILLS MATCH ═══════════════════ */}
          <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
            <div className="absolute -left-10 -top-10 h-32 w-32 rounded-full bg-indigo-500/10 blur-2xl" />
            <h2 className="text-2xl font-black tracking-tight flex items-center gap-2 mb-1">
              <Target className="h-6 w-6 text-indigo-400" /> Technical Skills Match
            </h2>
            <p className="text-sm text-muted-foreground mb-6">
              Similarity score: <span className={`font-bold ${color(ts.similarity_score)}`}>{fmt(ts.similarity_score)}%</span>
              {' · '}{matched.length} matched · {missing.length} missing
            </p>

            <div className="grid gap-6 md:grid-cols-2">
              {/* Matched */}
              <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 dark:bg-emerald-500/[0.03] px-5 py-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                    <p className="text-xs uppercase tracking-[0.2em] text-emerald-600 dark:text-emerald-400 font-medium">Matched Skills</p>
                  </div>
                  <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30 text-[10px]">{matched.length}</Badge>
                </div>
                {matched.length === 0 ? (
                  <p className="text-sm text-muted-foreground">None detected</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {matched.map((s, i) => (
                      <Badge key={`m-${i}`} className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-200 border border-emerald-500/25 px-2.5 py-1 text-xs">{s}</Badge>
                    ))}
                  </div>
                )}
              </div>
              {/* Missing */}
              <div className="rounded-2xl border border-rose-500/20 bg-rose-500/5 dark:bg-rose-500/[0.03] px-5 py-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-rose-500" />
                    <p className="text-xs uppercase tracking-[0.2em] text-rose-600 dark:text-rose-400 font-medium">Missing Skills</p>
                  </div>
                  <Badge className="bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30 text-[10px]">{missing.length}</Badge>
                </div>
                {missing.length === 0 ? (
                  <p className="text-sm text-muted-foreground">All required skills present!</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {missing.map((s, i) => (
                      <Badge key={`x-${i}`} className="bg-rose-500/10 text-rose-700 dark:text-rose-200 border border-rose-500/25 px-2.5 py-1 text-xs">{s}</Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Match Analysis: Preferred */}
            {(toArr(ma.matched_preferred).length > 0 || toArr(ma.missing_preferred).length > 0) && (
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                {toArr(ma.matched_preferred).length > 0 && (
                  <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 dark:bg-cyan-500/[0.03] px-5 py-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-cyan-600 dark:text-cyan-400 font-medium mb-3">Preferred Skills Matched</p>
                    <div className="flex flex-wrap gap-2">
                      {toArr(ma.matched_preferred).map((s, i) => (
                        <Badge key={`mp-${i}`} className="bg-cyan-500/10 text-cyan-700 dark:text-cyan-200 border border-cyan-500/25 px-2.5 py-1 text-xs">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {toArr(ma.missing_preferred).length > 0 && (
                  <div className="rounded-2xl border border-orange-500/20 bg-orange-500/5 dark:bg-orange-500/[0.03] px-5 py-4">
                    <p className="text-xs uppercase tracking-[0.2em] text-orange-600 dark:text-orange-400 font-medium mb-3">Preferred Skills Missing</p>
                    <div className="flex flex-wrap gap-2">
                      {toArr(ma.missing_preferred).map((s, i) => (
                        <Badge key={`xp-${i}`} className="bg-orange-500/10 text-orange-700 dark:text-orange-200 border border-orange-500/25 px-2.5 py-1 text-xs">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </motion.section>

          {/* ═══════════════════ 4. ATS ANALYSIS (Detailed) ═══════════════════ */}
          <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
            <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-emerald-500/10 blur-2xl" />
            <h2 className="text-2xl font-black tracking-tight flex items-center gap-2 mb-1">
              <FileSearch className="h-6 w-6 text-emerald-500" /> ATS Compatibility Analysis
            </h2>
            <div className="flex items-center gap-3 mb-6">
              <span className={`text-sm font-bold ${color(ats.score)}`}>{fmt(ats.score)}% overall</span>
              {atsLlm.overall_ats_readiness && (
                <Badge className={`text-[10px] uppercase tracking-wider ${
                  atsLlm.overall_ats_readiness === 'high' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                  atsLlm.overall_ats_readiness === 'medium' ? 'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30' :
                  'bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30'
                }`}>
                  {atsLlm.overall_ats_readiness} readiness
                </Badge>
              )}
            </div>

            {/* ATS Component scores */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5 mb-6">
              {[
                { label: 'Keyword Match', value: ats.keyword_match, weight: atsComp.keyword_density?.weight },
                { label: 'Section Coverage', value: ats.section_coverage, weight: atsComp.section_structure?.weight },
                { label: 'Formatting', value: ats.formatting_score, weight: atsComp.formatting?.weight },
                { label: 'Contact Info', value: ats.contact_score, weight: atsComp.contact_info?.weight },
                { label: 'Date Consistency', value: atsComp.date_consistency?.score, weight: atsComp.date_consistency?.weight },
              ].map((c) => (
                <div key={c.label} className="rounded-xl border border-border/60 bg-card/60 px-4 py-3 text-center">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">{c.label}</p>
                  <p className={`text-2xl font-black ${color(c.value)}`}>{fmt(c.value, 0)}<span className="text-sm">%</span></p>
                  {c.weight && <p className="text-[9px] text-muted-foreground">{c.weight} weight</p>}
                  <Bar value={clamp(c.value)} />
                </div>
              ))}
            </div>

            {/* Keywords matched & missing */}
            <div className="grid gap-4 md:grid-cols-2 mb-6">
              <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3 flex items-center gap-2">
                  <Search className="h-3.5 w-3.5" /> ATS Keywords Matched
                </p>
                {toArr(ats.matched_keywords).length === 0 ? (
                  <p className="text-sm text-muted-foreground">No keywords matched</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {toArr(ats.matched_keywords).map((k, i) => (
                      <Badge key={`ak-${i}`} variant="secondary" className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-200 border border-emerald-500/20 text-xs px-2.5 py-1">{k}</Badge>
                    ))}
                  </div>
                )}
              </div>
              <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3 flex items-center gap-2">
                  <XCircle className="h-3.5 w-3.5" /> Missing Keywords (Top 10)
                </p>
                {toArr(atsComp.keyword_density?.missing).length === 0 ? (
                  <p className="text-sm text-muted-foreground">No critical keywords missing</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {toArr(atsComp.keyword_density?.missing).slice(0, 10).map((k, i) => (
                      <Badge key={`km-${i}`} variant="secondary" className="bg-rose-500/10 text-rose-700 dark:text-rose-200 border border-rose-500/20 text-xs px-2.5 py-1">{k}</Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Sections Found / Missing */}
            <div className="grid gap-4 md:grid-cols-2 mb-6">
              <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Sections Found</p>
                <div className="flex flex-wrap gap-2">
                  {toArr(atsComp.section_structure?.found).map((s, i) => (
                    <Badge key={`sf-${i}`} className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-200 border border-emerald-500/20 text-xs px-2.5 py-1 capitalize">{s}</Badge>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground mb-3">Sections Missing</p>
                {toArr(ats.sections_missing).length === 0 ? (
                  <p className="text-sm text-muted-foreground">All essential sections present</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {toArr(ats.sections_missing).map((s, i) => (
                      <Badge key={`sm-${i}`} className="bg-rose-500/10 text-rose-700 dark:text-rose-200 border border-rose-500/20 text-xs px-2.5 py-1 capitalize">{s}</Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Resume Length */}
            {atsComp.resume_length && (
              <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4 mb-6">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Resume Length</p>
                  <Badge className={`text-[10px] ${
                    atsComp.resume_length.assessment === 'optimal' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                    'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30'
                  }`}>
                    {atsComp.resume_length.assessment}
                  </Badge>
                </div>
                <div className="flex items-center gap-6 mt-2 text-sm">
                  <span className="text-foreground/80">{atsComp.resume_length.word_count} words</span>
                  <span className="text-muted-foreground">{'\u2248'} {atsComp.resume_length.pages} pages</span>
                  <span className={`font-bold ${color(atsComp.resume_length.score)}`}>{atsComp.resume_length.score}%</span>
                </div>
              </div>
            )}

            {/* Issues */}
            {toArr(ats.all_issues).length > 0 && (
              <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 dark:bg-amber-500/[0.03] px-5 py-4 mb-6">
                <p className="text-xs uppercase tracking-[0.2em] text-amber-600 dark:text-amber-400 font-medium mb-3 flex items-center gap-2">
                  <AlertTriangle className="h-3.5 w-3.5" /> Issues Detected
                </p>
                <ul className="space-y-2">
                  {toArr(ats.all_issues).map((issue, i) => (
                    <li key={`issue-${i}`} className="flex items-start gap-2 text-sm text-foreground/80">
                      <ChevronRight className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                      {issue}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* LLM Keyword Optimization Feedback */}
            {atsLlm.keyword_optimization && (
              <div className="rounded-2xl border border-border/60 bg-card/40 px-5 py-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground flex items-center gap-2">
                    <Sparkles className="h-3.5 w-3.5 text-indigo-500" /> AI Keyword Optimization
                  </p>
                  <Badge className={`text-[10px] ${
                    atsLlm.keyword_optimization.status === 'good' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                    'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30'
                  }`}>
                    {atsLlm.keyword_optimization.status?.replace(/_/g, ' ')}
                  </Badge>
                </div>
                {toArr(atsLlm.keyword_optimization.missing_keywords).length > 0 && (
                  <div className="mb-3">
                    <p className="text-xs text-muted-foreground mb-2">Keywords to add:</p>
                    <div className="flex flex-wrap gap-2">
                      {toArr(atsLlm.keyword_optimization.missing_keywords).map((k, i) => (
                        <Badge key={`lk-${i}`} className="bg-indigo-500/10 text-indigo-700 dark:text-indigo-200 border border-indigo-500/20 text-xs px-2.5 py-1">{k}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {toArr(atsLlm.keyword_optimization.suggestions).length > 0 && (
                  <ul className="space-y-1.5">
                    {toArr(atsLlm.keyword_optimization.suggestions).map((s, i) => (
                      <li key={`ls-${i}`} className="text-sm text-foreground/70 flex items-start gap-2">
                        <Lightbulb className="h-3.5 w-3.5 text-amber-500 mt-0.5 flex-shrink-0" /> {s}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </motion.section>

          {/* ═══════════════════ 5. SECTION ANALYSIS ═══════════════════ */}
          {Object.keys(sections).length > 0 && (
            <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
              <div className="absolute -right-10 -bottom-10 h-32 w-32 rounded-full bg-sky-500/10 blur-2xl" />
              <h2 className="text-2xl font-black tracking-tight flex items-center gap-2 mb-1">
                <ClipboardCheck className="h-6 w-6 text-sky-500" /> Section Analysis
              </h2>
              <p className="text-sm text-muted-foreground mb-6">
                Overall section score: <span className={`font-bold ${color(sa.score)}`}>{fmt(sa.score)}%</span>
                {sa.summary && <> · {sa.summary}</>}
              </p>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(sections).map(([key, val]: [string, any]) => {
                  const q = val.quality ?? '';
                  const qualityColor = q === 'good' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                                       q === 'fair' ? 'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30' :
                                       'bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30';
                  return (
                    <div key={key} className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-sm px-5 py-4 hover:shadow-md transition-shadow">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-semibold capitalize">{label(key)}</p>
                        <div className="flex items-center gap-2">
                          {val.present ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                          ) : (
                            <XCircle className="h-4 w-4 text-rose-500" />
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`text-2xl font-black ${color(val.score)}`}>{val.score ?? '—'}<span className="text-sm">%</span></span>
                        <Badge className={`text-[10px] capitalize border ${qualityColor}`}>{q || '—'}</Badge>
                        {val.weight && <span className="text-[10px] text-muted-foreground">{val.weight}</span>}
                      </div>
                      <Bar value={clamp(val.score)} />
                      {val.feedback && (
                        <p className="text-xs text-muted-foreground mt-2 leading-relaxed">{val.feedback}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </motion.section>
          )}

          {/* ═══════════════════ 6. MATCH ANALYSIS ═══════════════════ */}
          {(ma.experience_match || ma.education_match || ma.seniority_match) && (
            <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
              <div className="absolute -left-10 -top-10 h-32 w-32 rounded-full bg-purple-500/10 blur-2xl" />
              <h2 className="text-2xl font-black tracking-tight flex items-center gap-2 mb-1">
                <Award className="h-6 w-6 text-purple-500" /> Match Analysis
              </h2>
              <p className="text-sm text-muted-foreground mb-6">How your profile aligns with the job requirements</p>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {/* Experience */}
                {ma.experience_match && (
                  <div className="rounded-2xl border border-border/60 bg-card/60 px-5 py-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Briefcase className="h-4 w-4 text-purple-500" />
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Experience</p>
                    </div>
                    <Badge className={`text-xs mb-2 ${
                      ma.experience_match.status === 'meets' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                      ma.experience_match.status === 'exceeds' ? 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-300 border-cyan-500/30' :
                      'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30'
                    }`}>
                      {ma.experience_match.status}
                    </Badge>
                    <div className="text-sm text-foreground/80">
                      <span className="font-semibold">{ma.experience_match.candidate_years}</span> yrs candidate ·{' '}
                      <span className="font-semibold">{ma.experience_match.required_years}</span> yrs required
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{ma.experience_match.explanation}</p>
                  </div>
                )}

                {/* Education */}
                {ma.education_match && (
                  <div className="rounded-2xl border border-border/60 bg-card/60 px-5 py-4">
                    <div className="flex items-center gap-2 mb-2">
                      <GraduationCap className="h-4 w-4 text-purple-500" />
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Education</p>
                    </div>
                    <Badge className={`text-xs mb-2 ${
                      ma.education_match.status === 'meets' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                      'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30'
                    }`}>
                      {ma.education_match.status}
                    </Badge>
                    <p className="text-xs text-foreground/80">{ma.education_match.explanation}</p>
                  </div>
                )}

                {/* Seniority */}
                {ma.seniority_match && (
                  <div className="rounded-2xl border border-border/60 bg-card/60 px-5 py-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Star className="h-4 w-4 text-purple-500" />
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Seniority</p>
                    </div>
                    <Badge className={`text-xs mb-2 ${
                      ma.seniority_match.status === 'match' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                      'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30'
                    }`}>
                      {ma.seniority_match.status}
                    </Badge>
                    <div className="text-sm text-foreground/80 capitalize">
                      {ma.seniority_match.candidate_level} → {ma.seniority_match.required_level}
                    </div>
                  </div>
                )}

                {/* Overall Fit */}
                {ma.overall_fit && (
                  <div className="rounded-2xl border border-border/60 bg-card/60 px-5 py-4 sm:col-span-2 lg:col-span-3">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="h-4 w-4 text-purple-500" />
                      <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground font-medium">Overall Fit Assessment</p>
                    </div>
                    <div className="flex items-center gap-3 mb-2">
                      <Badge className={`text-xs capitalize ${
                        ma.overall_fit.category === 'strong' ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30' :
                        ma.overall_fit.category === 'moderate' ? 'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30' :
                        'bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30'
                      }`}>
                        {ma.overall_fit.category}
                      </Badge>
                      <span className={`text-lg font-bold ${color(ma.overall_fit.score_estimate)}`}>{ma.overall_fit.score_estimate}%</span>
                    </div>
                    <p className="text-sm text-foreground/70">{ma.overall_fit.explanation}</p>
                  </div>
                )}
              </div>
            </motion.section>
          )}

          {/* ═══════════════════ 7. JD SUMMARY + RESUME DETAILS ═══════════════════ */}
          <motion.section variants={item} className="grid gap-6 lg:grid-cols-2">
            {/* Job Description Details */}
            {jd.title && (
              <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
                <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-cyan-500/10 blur-2xl" />
                <h2 className="text-xl font-black tracking-tight flex items-center gap-2 mb-4">
                  <Briefcase className="h-5 w-5 text-cyan-500" /> Job Requirements
                </h2>
                <div className="space-y-4">
                  <div>
                    <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Position</p>
                    <p className="text-base font-semibold">{jd.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      {jd.seniority_level && <Badge variant="secondary" className="text-[10px] capitalize">{jd.seniority_level}</Badge>}
                      {jd.industry && <Badge variant="secondary" className="text-[10px] capitalize">{jd.industry}</Badge>}
                    </div>
                  </div>
                  {jd.experience_required && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Experience</p>
                      <p className="text-sm text-foreground/80">{jd.experience_required}</p>
                    </div>
                  )}
                  {jd.education_required && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-1">Education</p>
                      <p className="text-sm text-foreground/80">{jd.education_required}</p>
                    </div>
                  )}
                  {toArr(jd.required_skills).length > 0 && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Required Skills</p>
                      <div className="flex flex-wrap gap-1.5">
                        {toArr(jd.required_skills).map((s, i) => (
                          <Badge key={`jr-${i}`} variant="secondary" className="text-[10px] px-2 py-0.5 bg-foreground/5 border border-foreground/10">{s}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {toArr(jd.preferred_skills).length > 0 && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Preferred Skills</p>
                      <div className="flex flex-wrap gap-1.5">
                        {toArr(jd.preferred_skills).map((s, i) => (
                          <Badge key={`jp-${i}`} variant="secondary" className="text-[10px] px-2 py-0.5 bg-cyan-500/5 border border-cyan-500/15 text-cyan-700 dark:text-cyan-300">{s}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  {toArr(jd.key_responsibilities).length > 0 && (
                    <div>
                      <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Key Responsibilities</p>
                      <ul className="space-y-1.5">
                        {toArr(jd.key_responsibilities).map((r, i) => (
                          <li key={`kr-${i}`} className="text-sm text-foreground/70 flex items-start gap-2">
                            <ChevronRight className="h-3.5 w-3.5 text-cyan-500 mt-0.5 flex-shrink-0" /> {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Resume Summary */}
            <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
              <div className="absolute -left-10 -top-10 h-32 w-32 rounded-full bg-amber-500/10 blur-2xl" />
              <h2 className="text-xl font-black tracking-tight flex items-center gap-2 mb-4">
                <BookOpen className="h-5 w-5 text-amber-500" /> Resume Summary
              </h2>
              <div className="space-y-4">
                {/* Experience */}
                {experience.length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Experience</p>
                    <div className="space-y-3">
                      {experience.map((exp: any, i: number) => (
                        <div key={`exp-${i}`} className="rounded-xl border border-border/60 bg-card/40 px-4 py-3">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-sm font-semibold">{exp.title}</p>
                            {exp.is_current && <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30 text-[9px]">Current</Badge>}
                          </div>
                          <p className="text-xs text-muted-foreground">{exp.company} · {exp.duration}</p>
                          {toArr(exp.highlights).length > 0 && (
                            <ul className="mt-2 space-y-1">
                              {toArr(exp.highlights).slice(0, 3).map((h, j) => (
                                <li key={`eh-${j}`} className="text-xs text-foreground/60 flex items-start gap-1.5">
                                  <span className="text-emerald-500 mt-0.5">•</span> {h}
                                </li>
                              ))}
                              {toArr(exp.highlights).length > 3 && (
                                <li className="text-xs text-muted-foreground">+{toArr(exp.highlights).length - 3} more</li>
                              )}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Education */}
                {education.length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">Education</p>
                    {education.map((edu: any, i: number) => (
                      <div key={`edu-${i}`} className="rounded-xl border border-border/60 bg-card/40 px-4 py-3">
                        <p className="text-sm font-semibold">{edu.degree}</p>
                        <p className="text-xs text-muted-foreground">{edu.institution} · {edu.year}</p>
                        {edu.gpa && <p className="text-xs text-foreground/60 mt-1">GPA: {edu.gpa}</p>}
                      </div>
                    ))}
                  </div>
                )}

                {/* Skills */}
                {resumeSkills.length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">All Skills ({resumeSkills.length})</p>
                    <div className="flex flex-wrap gap-1.5">
                      {resumeSkills.map((s, i) => (
                        <Badge key={`rs-${i}`} variant="secondary" className="text-[10px] px-2 py-0.5 bg-foreground/5 border border-foreground/10">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </motion.section>

          {/* ═══════════════════ 8. RECOMMENDATIONS ═══════════════════ */}
          {recs.length > 0 && (
            <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
              <div className="absolute -right-10 -top-10 h-32 w-32 rounded-full bg-blue-500/10 blur-2xl" />
              <h2 className="text-2xl font-black tracking-tight flex items-center gap-2 mb-1">
                <Lightbulb className="h-6 w-6 text-blue-500" /> Recommendations
              </h2>
              <p className="text-sm text-muted-foreground mb-6">Actionable improvements prioritized by impact</p>

              <div className="grid gap-4 md:grid-cols-2">
                {recs.map((rec: any, idx: number) => {
                  if (typeof rec === 'string') {
                    return (
                      <div key={`rec-${idx}`} className="rounded-2xl border border-border/60 bg-card/60 px-5 py-4">
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-blue-500/15 border border-blue-500/20 flex items-center justify-center text-blue-500 font-bold text-sm">{idx + 1}</div>
                          <p className="text-sm text-foreground/80 leading-relaxed">{rec}</p>
                        </div>
                      </div>
                    );
                  }
                  const priority = rec.priority ?? 'medium';
                  const category = rec.category ?? 'general';
                  const pColor: Record<string, string> = {
                    high: 'bg-rose-500/15 text-rose-600 dark:text-rose-300 border-rose-500/30',
                    medium: 'bg-amber-500/15 text-amber-600 dark:text-amber-300 border-amber-500/30',
                    low: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-300 border-emerald-500/30',
                  };
                  const cColor: Record<string, string> = {
                    skills: 'bg-purple-500/10 text-purple-600 dark:text-purple-300',
                    content: 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-300',
                    formatting: 'bg-pink-500/10 text-pink-600 dark:text-pink-300',
                    experience: 'bg-blue-500/10 text-blue-600 dark:text-blue-300',
                    ats: 'bg-orange-500/10 text-orange-600 dark:text-orange-300',
                    general: 'bg-gray-500/10 text-muted-foreground',
                  };
                  return (
                    <motion.div
                      key={`rec-${idx}`}
                      whileHover={{ y: -4, scale: 1.01 }}
                      transition={{ type: 'spring', stiffness: 240, damping: 20 }}
                      className="group rounded-2xl border border-border/60 bg-gradient-to-br from-blue-500/[0.06] via-indigo-500/[0.03] to-purple-500/[0.06] px-5 py-4 hover:border-blue-500/30 hover:shadow-lg hover:shadow-blue-500/10"
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-blue-500/15 border border-blue-500/20 flex items-center justify-center text-blue-500 font-bold text-sm group-hover:bg-blue-500 group-hover:text-white transition-colors">
                          {idx + 1}
                        </div>
                        <div className="flex-1 space-y-2">
                          <div className="flex flex-wrap gap-1.5 mb-1">
                            <Badge className={`text-[10px] uppercase tracking-wider px-2 py-0.5 border ${pColor[priority] ?? pColor.medium}`}>{priority}</Badge>
                            <Badge className={`text-[10px] uppercase tracking-wider px-2 py-0.5 ${cColor[category] ?? cColor.general}`}>{category}</Badge>
                          </div>
                          <p className="text-sm text-foreground/90 leading-relaxed font-medium">{rec.action}</p>
                          {rec.reason && <p className="text-xs text-muted-foreground leading-relaxed">{rec.reason}</p>}
                          {(rec.impact || rec.effort || rec.timeframe) && (
                            <div className="flex flex-wrap gap-3 text-[11px] text-muted-foreground pt-1">
                              {rec.impact && (
                                <span className="flex items-center gap-1">
                                  <TrendingUp className="h-3 w-3 text-emerald-500" /> {rec.impact}
                                </span>
                              )}
                              {rec.effort && (
                                <span className="flex items-center gap-1">
                                  <Zap className="h-3 w-3 text-amber-500" /> {rec.effort} effort
                                </span>
                              )}
                              {rec.timeframe && (
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3 text-blue-500" /> {rec.timeframe}
                                </span>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.section>
          )}

          {/* ═══════════════════ 9. JUSTIFICATIONS ═══════════════════ */}
          {justifications.length > 0 && (
            <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-8 relative overflow-hidden">
              <div className="absolute -left-10 -bottom-10 h-32 w-32 rounded-full bg-indigo-500/10 blur-2xl" />
              <h2 className="text-2xl font-black tracking-tight flex items-center gap-2 mb-1">
                <ShieldCheck className="h-6 w-6 text-indigo-500" /> Score Justifications
              </h2>
              <p className="text-sm text-muted-foreground mb-6">Evidence-based reasoning behind the scores</p>

              <div className="space-y-3">
                {justifications.map((j, idx) => (
                  <div key={`j-${idx}`} className="rounded-2xl border border-border/60 bg-card/60 px-5 py-4 hover:shadow-sm transition-shadow">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center">
                        <span className="text-[11px] font-bold text-indigo-500">{idx + 1}</span>
                      </div>
                      <p className="text-sm text-foreground/80 leading-relaxed">{j}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.section>
          )}

          {/* ═══════════════════ 10. JOB DESCRIPTION TEXT ═══════════════════ */}
          {jdText && (
            <motion.section variants={item} className="glass-panel sheen-border rounded-3xl p-6 md:p-8">
              <h2 className="text-xl font-black tracking-tight flex items-center gap-2 mb-4">
                <FileText className="h-5 w-5 text-foreground/60" /> Full Job Description
              </h2>
              <ScrollArea className="max-h-48">
                <p className="text-sm text-foreground/70 leading-relaxed whitespace-pre-line pr-4">{jdText}</p>
              </ScrollArea>
            </motion.section>
          )}

        </motion.div>
      </main>
    </div>
  );
}
