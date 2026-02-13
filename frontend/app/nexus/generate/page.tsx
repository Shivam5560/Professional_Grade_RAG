'use client';

import { useEffect, useState, useCallback } from 'react';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  User, Briefcase, GraduationCap, FolderKanban, Wrench, Eye,
  Plus, Trash2, Download, FileText, ChevronLeft, ChevronRight,
  CheckCircle2, Loader2, AlertCircle,
} from 'lucide-react';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { useToast } from '@/hooks/useToast';
import type {
  ResumeGenData,
  ResumeGenExperience,
  ResumeGenEducation,
  ResumeGenProject,
} from '@/lib/types';
import AuthPage from '@/app/auth/page';

/* ── Step definitions ──────────────────────────────────── */
const STEPS = [
  { id: 'personal', label: 'Personal', icon: User },
  { id: 'experience', label: 'Experience', icon: Briefcase },
  { id: 'education', label: 'Education', icon: GraduationCap },
  { id: 'projects', label: 'Projects', icon: FolderKanban },
  { id: 'skills', label: 'Skills', icon: Wrench },
  { id: 'preview', label: 'Preview', icon: Eye },
] as const;

/* ── Blank entries ─────────────────────────────────────── */
const blankExperience: ResumeGenExperience = { company: '', position: '', duration: '', responsibilities: [''] };
const blankEducation: ResumeGenEducation = { institution: '', degree: '', duration: '', gpa: '' };
const blankProject: ResumeGenProject = { name: '', descriptions: [''], technologies: '' };

export default function ResumeGenPage() {
  const { isAuthenticated } = useAuthStore();
  const { toast } = useToast();
  const [isMounted, setIsMounted] = useState(false);
  const [step, setStep] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [latexAvailable, setLatexAvailable] = useState<boolean | null>(null);

  /* ── Form state ─────────────────────────────────────── */
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [location, setLocation] = useState('');
  const [linkedin, setLinkedin] = useState('');
  const [github, setGithub] = useState('');

  const [experiences, setExperiences] = useState<ResumeGenExperience[]>([{ ...blankExperience }]);
  const [educations, setEducations] = useState<ResumeGenEducation[]>([{ ...blankEducation }]);
  const [projects, setProjects] = useState<ResumeGenProject[]>([{ ...blankProject }]);

  const [skillCategories, setSkillCategories] = useState<{ category: string; skills: string[] }[]>([
    { category: 'Programming', skills: [''] },
  ]);

  useEffect(() => { setIsMounted(true); }, []);

  /* ── Check PDF API health once ──────────────────────── */
  useEffect(() => {
    if (!isAuthenticated) return;
    fetch('/api/latex-to-pdf')
      .then((r) => setLatexAvailable(r.ok))
      .catch(() => setLatexAvailable(false));
  }, [isAuthenticated]);

  /* ── Build payload ──────────────────────────────────── */
  const buildPayload = useCallback((): ResumeGenData => {
    const skills: Record<string, string[]> = {};
    skillCategories.forEach((cat) => {
      const filtered = cat.skills.filter(Boolean);
      if (cat.category && filtered.length) skills[cat.category] = filtered;
    });
    return {
      name, email, location, linkedin, github,
      experience: experiences.map((e) => ({ ...e, responsibilities: e.responsibilities.filter(Boolean) })),
      education: educations,
      projects: projects.map((p) => ({ ...p, descriptions: p.descriptions.filter(Boolean) })),
      skills,
    };
  }, [name, email, location, linkedin, github, experiences, educations, projects, skillCategories]);

  /* ── Generators ─────────────────────────────────────── */
  const handleDownloadPdf = async () => {
    setGenerating(true);
    try {
      const blob = await apiClient.generateResumePdf(buildPayload());
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name.replace(/\s+/g, '_') || 'resume'}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast({ title: 'Resume downloaded', description: 'PDF saved to your downloads folder.' });
    } catch (err) {
      toast({ title: 'PDF generation failed', description: err instanceof Error ? err.message : 'Unknown error', variant: 'destructive' });
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadLatex = async () => {
    setGenerating(true);
    try {
      const tex = await apiClient.generateResumeLatex(buildPayload());
      const blob = new Blob([tex], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${name.replace(/\s+/g, '_') || 'resume'}.tex`;
      a.click();
      URL.revokeObjectURL(url);
      toast({ title: 'LaTeX source downloaded' });
    } catch (err) {
      toast({ title: 'LaTeX generation failed', description: err instanceof Error ? err.message : 'Unknown error', variant: 'destructive' });
    } finally {
      setGenerating(false);
    }
  };

  /* ── Helpers for list mutation ───────────────────────── */
  const updateExp = (i: number, patch: Partial<ResumeGenExperience>) =>
    setExperiences((prev) => prev.map((e, idx) => (idx === i ? { ...e, ...patch } : e)));
  const updateEdu = (i: number, patch: Partial<ResumeGenEducation>) =>
    setEducations((prev) => prev.map((e, idx) => (idx === i ? { ...e, ...patch } : e)));
  const updateProj = (i: number, patch: Partial<ResumeGenProject>) =>
    setProjects((prev) => prev.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  const StepIcon = STEPS[step].icon;
  const isFirstStep = step === 0;
  const isLastStep = step === STEPS.length - 1;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      {/* Aurora background */}
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />
      <div className="pointer-events-none absolute -top-32 right-[-10%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-1)/0.18),transparent_65%)] blur-2xl float-slow" />
      <div className="pointer-events-none absolute top-[10%] left-[-12%] h-[420px] w-[420px] rounded-full bg-[radial-gradient(circle_at_center,hsl(var(--chart-2)/0.2),transparent_65%)] blur-3xl float-slower" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-10">
        <div className="max-w-5xl mx-auto space-y-6">

          {/* ── Hero banner ─────────────────────────────── */}
          <section className="glass-panel sheen-border rounded-3xl p-6 md:p-8 bg-accent-soft">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <Badge className="bg-foreground text-background">ResumeGen</Badge>
                <h1 className="text-3xl md:text-4xl font-black mt-2">Build your resume</h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Fill each section and download a polished, LaTeX-compiled PDF.
                </p>
              </div>
              <div className="flex items-center gap-2">
                {latexAvailable === false && (
                  <Badge variant="outline" className="border-amber-500/40 text-amber-600 dark:text-amber-400 gap-1.5">
                    <AlertCircle className="h-3 w-3" /> PDF API unavailable
                  </Badge>
                )}
                {latexAvailable === true && (
                  <Badge variant="outline" className="border-emerald-500/40 text-emerald-600 dark:text-emerald-400 gap-1.5">
                    <CheckCircle2 className="h-3 w-3" /> PDF API ready
                  </Badge>
                )}
              </div>
            </div>
          </section>

          {/* ── Step indicator ──────────────────────────── */}
          <div className="glass-panel rounded-2xl p-3 flex items-center gap-1 overflow-x-auto">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const done = i < step;
              const active = i === step;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setStep(i)}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all whitespace-nowrap ${
                    active
                      ? 'bg-foreground text-background shadow-lg'
                      : done
                      ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/60'
                  }`}
                >
                  {done ? <CheckCircle2 className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />}
                  <span className="hidden sm:inline">{s.label}</span>
                </button>
              );
            })}
          </div>

          {/* ── Step content ────────────────────────────── */}
          <Card className="glass-panel sheen-border border-border/60 bg-accent-soft overflow-hidden">
            <CardHeader className="border-b border-border/40 bg-card/40">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-foreground/10 flex items-center justify-center">
                  <StepIcon className="h-5 w-5" />
                </div>
                <div>
                  <CardTitle>{STEPS[step].label} Details</CardTitle>
                  <CardDescription>Step {step + 1} of {STEPS.length}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-6">
              <ScrollArea className="max-h-[60vh]">
                {/* ── Step 0: Personal ──────────────────── */}
                {step === 0 && (
                  <div className="grid gap-5 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Full Name *</Label>
                      <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" />
                    </div>
                    <div className="space-y-2">
                      <Label>Email *</Label>
                      <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="jane@email.com" type="email" />
                    </div>
                    <div className="space-y-2">
                      <Label>Location</Label>
                      <Input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="San Francisco, CA" />
                    </div>
                    <div className="space-y-2">
                      <Label>LinkedIn URL</Label>
                      <Input value={linkedin} onChange={(e) => setLinkedin(e.target.value)} placeholder="linkedin.com/in/..." />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <Label>GitHub URL</Label>
                      <Input value={github} onChange={(e) => setGithub(e.target.value)} placeholder="github.com/..." />
                    </div>
                  </div>
                )}

                {/* ── Step 1: Experience ────────────────── */}
                {step === 1 && (
                  <div className="space-y-6">
                    {experiences.map((exp, i) => (
                      <div key={i} className="rounded-2xl border border-border/60 bg-card/60 p-5 space-y-4 relative">
                        {experiences.length > 1 && (
                          <button type="button" onClick={() => setExperiences((p) => p.filter((_, idx) => idx !== i))} className="absolute top-3 right-3 p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Company</Label>
                            <Input value={exp.company} onChange={(e) => updateExp(i, { company: e.target.value })} />
                          </div>
                          <div className="space-y-2">
                            <Label>Position</Label>
                            <Input value={exp.position} onChange={(e) => updateExp(i, { position: e.target.value })} />
                          </div>
                          <div className="space-y-2 md:col-span-2">
                            <Label>Duration</Label>
                            <Input value={exp.duration} onChange={(e) => updateExp(i, { duration: e.target.value })} placeholder="Jan 2022 – Present" />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Responsibilities</Label>
                          {exp.responsibilities.map((r, ri) => (
                            <div key={ri} className="flex gap-2">
                              <Input value={r} onChange={(e) => {
                                const updated = [...exp.responsibilities];
                                updated[ri] = e.target.value;
                                updateExp(i, { responsibilities: updated });
                              }} placeholder={`Responsibility ${ri + 1}`} />
                              {exp.responsibilities.length > 1 && (
                                <Button size="icon" variant="ghost" onClick={() => {
                                  updateExp(i, { responsibilities: exp.responsibilities.filter((_, idx) => idx !== ri) });
                                }}><Trash2 className="h-3.5 w-3.5" /></Button>
                              )}
                            </div>
                          ))}
                          <Button variant="ghost" size="sm" onClick={() => updateExp(i, { responsibilities: [...exp.responsibilities, ''] })}>
                            <Plus className="h-3.5 w-3.5 mr-1" /> Add Responsibility
                          </Button>
                        </div>
                      </div>
                    ))}
                    <Button variant="outline" onClick={() => setExperiences((p) => [...p, { ...blankExperience }])}>
                      <Plus className="h-4 w-4 mr-2" /> Add Experience
                    </Button>
                  </div>
                )}

                {/* ── Step 2: Education ─────────────────── */}
                {step === 2 && (
                  <div className="space-y-6">
                    {educations.map((edu, i) => (
                      <div key={i} className="rounded-2xl border border-border/60 bg-card/60 p-5 space-y-4 relative">
                        {educations.length > 1 && (
                          <button type="button" onClick={() => setEducations((p) => p.filter((_, idx) => idx !== i))} className="absolute top-3 right-3 p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Institution</Label>
                            <Input value={edu.institution} onChange={(e) => updateEdu(i, { institution: e.target.value })} />
                          </div>
                          <div className="space-y-2">
                            <Label>Degree</Label>
                            <Input value={edu.degree} onChange={(e) => updateEdu(i, { degree: e.target.value })} />
                          </div>
                          <div className="space-y-2">
                            <Label>Duration</Label>
                            <Input value={edu.duration} onChange={(e) => updateEdu(i, { duration: e.target.value })} placeholder="2018 – 2022" />
                          </div>
                          <div className="space-y-2">
                            <Label>GPA (optional)</Label>
                            <Input value={edu.gpa || ''} onChange={(e) => updateEdu(i, { gpa: e.target.value })} placeholder="3.8 / 4.0" />
                          </div>
                        </div>
                      </div>
                    ))}
                    <Button variant="outline" onClick={() => setEducations((p) => [...p, { ...blankEducation }])}>
                      <Plus className="h-4 w-4 mr-2" /> Add Education
                    </Button>
                  </div>
                )}

                {/* ── Step 3: Projects ──────────────────── */}
                {step === 3 && (
                  <div className="space-y-6">
                    {projects.map((proj, i) => (
                      <div key={i} className="rounded-2xl border border-border/60 bg-card/60 p-5 space-y-4 relative">
                        {projects.length > 1 && (
                          <button type="button" onClick={() => setProjects((p) => p.filter((_, idx) => idx !== i))} className="absolute top-3 right-3 p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Project Name</Label>
                            <Input value={proj.name} onChange={(e) => updateProj(i, { name: e.target.value })} />
                          </div>
                          <div className="space-y-2">
                            <Label>Technologies</Label>
                            <Input value={proj.technologies} onChange={(e) => updateProj(i, { technologies: e.target.value })} placeholder="React, Python, Docker" />
                          </div>
                        </div>
                        <div className="space-y-2">
                          <Label>Project Highlights</Label>
                          {proj.descriptions.map((d, di) => (
                            <div key={di} className="flex gap-2">
                              <Textarea
                                value={d}
                                onChange={(e) => {
                                  const updated = [...proj.descriptions];
                                  updated[di] = e.target.value;
                                  updateProj(i, { descriptions: updated });
                                }}
                                className="min-h-[80px]"
                                placeholder={`Highlight ${di + 1}`}
                              />
                              {proj.descriptions.length > 1 && (
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  onClick={() => {
                                    updateProj(i, { descriptions: proj.descriptions.filter((_, idx) => idx !== di) });
                                  }}
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              )}
                            </div>
                          ))}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateProj(i, { descriptions: [...proj.descriptions, ''] })}
                          >
                            <Plus className="h-3.5 w-3.5 mr-1" /> Add Highlight
                          </Button>
                        </div>
                      </div>
                    ))}
                    <Button variant="outline" onClick={() => setProjects((p) => [...p, { ...blankProject }])}>
                      <Plus className="h-4 w-4 mr-2" /> Add Project
                    </Button>
                  </div>
                )}

                {/* ── Step 4: Skills ────────────────────── */}
                {step === 4 && (
                  <div className="space-y-6">
                    {skillCategories.map((cat, ci) => (
                      <div key={ci} className="rounded-2xl border border-border/60 bg-card/60 p-5 space-y-4 relative">
                        {skillCategories.length > 1 && (
                          <button type="button" onClick={() => setSkillCategories((p) => p.filter((_, idx) => idx !== ci))} className="absolute top-3 right-3 p-1.5 rounded-lg text-muted-foreground hover:text-red-500 hover:bg-red-500/10 transition-colors">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        )}
                        <div className="space-y-2">
                          <Label>Category Name</Label>
                          <Input value={cat.category} onChange={(e) => {
                            const updated = [...skillCategories];
                            updated[ci] = { ...cat, category: e.target.value };
                            setSkillCategories(updated);
                          }} placeholder="e.g. Programming Languages" />
                        </div>
                        <div className="space-y-2">
                          <Label>Skills</Label>
                          {cat.skills.map((skill, si) => (
                            <div key={si} className="flex gap-2">
                              <Input value={skill} onChange={(e) => {
                                const updated = [...skillCategories];
                                const skills = [...cat.skills];
                                skills[si] = e.target.value;
                                updated[ci] = { ...cat, skills };
                                setSkillCategories(updated);
                              }} placeholder={`Skill ${si + 1}`} />
                              {cat.skills.length > 1 && (
                                <Button size="icon" variant="ghost" onClick={() => {
                                  const updated = [...skillCategories];
                                  updated[ci] = { ...cat, skills: cat.skills.filter((_, idx) => idx !== si) };
                                  setSkillCategories(updated);
                                }}><Trash2 className="h-3.5 w-3.5" /></Button>
                              )}
                            </div>
                          ))}
                          <Button variant="ghost" size="sm" onClick={() => {
                            const updated = [...skillCategories];
                            updated[ci] = { ...cat, skills: [...cat.skills, ''] };
                            setSkillCategories(updated);
                          }}>
                            <Plus className="h-3.5 w-3.5 mr-1" /> Add Skill
                          </Button>
                        </div>
                      </div>
                    ))}
                    <Button variant="outline" onClick={() => setSkillCategories((p) => [...p, { category: '', skills: [''] }])}>
                      <Plus className="h-4 w-4 mr-2" /> Add Category
                    </Button>
                  </div>
                )}

                {/* ── Step 5: Preview & Download ────────── */}
                {step === 5 && (
                  <div className="space-y-6">
                    {/* Summary */}
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-2xl border border-border/60 bg-card/60 p-4 space-y-1">
                        <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Name</p>
                        <p className="font-semibold">{name || '—'}</p>
                      </div>
                      <div className="rounded-2xl border border-border/60 bg-card/60 p-4 space-y-1">
                        <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Email</p>
                        <p className="font-semibold">{email || '—'}</p>
                      </div>
                      <div className="rounded-2xl border border-border/60 bg-card/60 p-4 space-y-1">
                        <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Location</p>
                        <p className="font-semibold">{location || '—'}</p>
                      </div>
                      <div className="rounded-2xl border border-border/60 bg-card/60 p-4 space-y-1">
                        <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Links</p>
                        <p className="text-sm text-muted-foreground truncate">{linkedin || github || '—'}</p>
                      </div>
                    </div>

                    <div className="rounded-2xl border border-border/60 bg-card/60 p-4 space-y-2">
                      <p className="text-xs uppercase tracking-[0.25em] text-muted-foreground">Sections filled</p>
                      <div className="flex flex-wrap gap-2">
                        <Badge variant="secondary">{experiences.filter((e) => e.company).length} experience(s)</Badge>
                        <Badge variant="secondary">{educations.filter((e) => e.institution).length} education(s)</Badge>
                        <Badge variant="secondary">{projects.filter((p) => p.name).length} project(s)</Badge>
                        <Badge variant="secondary">{skillCategories.filter((c) => c.category).length} skill group(s)</Badge>
                      </div>
                    </div>

                    {/* Download buttons */}
                    <div className="flex flex-wrap gap-3 pt-2">
                      <Button onClick={handleDownloadPdf} disabled={generating || !name || !email} className="gap-2">
                        {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                        Download PDF
                      </Button>
                      <Button variant="outline" onClick={handleDownloadLatex} disabled={generating || !name || !email} className="gap-2">
                        <FileText className="h-4 w-4" />
                        Download .tex source
                      </Button>
                    </div>

                    {latexAvailable === false && (
                      <p className="text-xs text-amber-600 dark:text-amber-400">
                        PDF conversion API is unavailable right now. You can still download the .tex source and compile locally.
                      </p>
                    )}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>

          {/* ── Navigation ──────────────────────────────── */}
          <div className="flex items-center justify-between">
            <Button variant="outline" onClick={() => setStep((s) => s - 1)} disabled={isFirstStep} className="gap-2">
              <ChevronLeft className="h-4 w-4" /> Previous
            </Button>
            <p className="text-xs text-muted-foreground">
              {step + 1} / {STEPS.length}
            </p>
            <Button onClick={() => setStep((s) => s + 1)} disabled={isLastStep} className="gap-2">
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}
