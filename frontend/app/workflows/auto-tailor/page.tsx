/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { ResumeFileInfo } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { ShaderAnimation } from '@/components/ui/shader-animation';
import { useToast } from '@/hooks/useToast';
import { 
  Sparkles, Loader2, ArrowLeft, CheckCircle2, 
  AlertTriangle, Download, RefreshCw, XCircle
} from 'lucide-react';

export default function AutoTailorPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { toast } = useToast();
  const [isHydrated, setIsHydrated] = useState(false);

  // Form State
  const [resumes, setResumes] = useState<ResumeFileInfo[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [targetScore, setTargetScore] = useState(85);
  const [maxIterations, setMaxIterations] = useState(3);

  // Workflow State
  const [workflowState, setWorkflowState] = useState<'setup' | 'running' | 'paused' | 'completed' | 'aborted'>('setup');
  const [analysisId, setAnalysisId] = useState('');
  const [currentIteration, setCurrentIteration] = useState(0);
  const [latestScore, setLatestScore] = useState(0);
  const [scoresBreakdown, setScoresBreakdown] = useState<any>(null);
  const [criticFeedback, setCriticFeedback] = useState('');
  const [resumeData, setResumeData] = useState<any>(null);
  
  // HITL State
  const [userFeedback, setUserFeedback] = useState('');
  const [hitlTab, setHitlTab] = useState<'critic' | 'scores' | 'preview'>('critic');
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (!isHydrated) return;
    if (!user) {
      router.push('/auth');
      return;
    }

    const loadResumes = async () => {
      try {
        const response = await apiClient.listResumes(user.id);
        setResumes(response.list || []);
        if (response.list && response.list.length > 0) {
          setSelectedResumeId(response.list[0].resume_id);
        }
      } catch (err) {
        console.error('Failed to load resumes:', err);
        toast({
          title: 'Error loading resumes',
          description: 'Unable to fetch your uploaded resumes.',
          variant: 'destructive',
        });
      }
    };

    loadResumes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isHydrated, user?.id, router]);

  const handleStartWorkflow = async () => {
    if (!selectedResumeId) {
      toast({ title: 'Resume required', description: 'Please select a master profile resume.', variant: 'destructive' });
      return;
    }
    if (!jobDescription.trim()) {
      toast({ title: 'Job Description required', description: 'Please paste the job description.', variant: 'destructive' });
      return;
    }

    setWorkflowState('running');
    setActionLoading(true);

    try {
      const data = await apiClient.startAutoTailor({
        resume_id: selectedResumeId,
        job_description: jobDescription,
        target_score: targetScore,
        max_iterations: maxIterations
      });

      setAnalysisId(data.analysis_id);
      setCurrentIteration(data.current_iteration);
      setLatestScore(data.latest_score);
      setScoresBreakdown(data.scores_breakdown);
      setCriticFeedback(data.critic_feedback);
      setResumeData(data.resume_data);
      
      if (data.status === 'completed') {
        setWorkflowState('completed');
      } else if (data.status === 'paused_for_human') {
        setWorkflowState('paused');
      } else {
        setWorkflowState('setup');
      }
    } catch (err) {
      console.error(err);
      setWorkflowState('setup');
      toast({
        title: 'Workflow failed',
        description: err instanceof Error ? err.message : 'Failed to execute Auto-Tailor workflow.',
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleHITLResponse = async (action: 'approve' | 'abort' | 'refine') => {
    if (!analysisId) return;

    if (action === 'refine' && !userFeedback.trim()) {
      toast({ title: 'Feedback required', description: 'Please enter refinement instructions for the agent.', variant: 'destructive' });
      return;
    }

    setActionLoading(true);
    if (action !== 'refine') {
      setWorkflowState('running');
    }

    try {
      const data = await apiClient.respondToAutoTailor(analysisId, {
        action,
        user_feedback: action === 'refine' ? userFeedback : undefined
      });

      if (action === 'abort') {
        setWorkflowState('aborted');
        toast({ title: 'Workflow Aborted', description: 'The tailoring loop has been stopped.' });
        return;
      }

      setCurrentIteration(data.current_iteration || currentIteration);
      setLatestScore(data.latest_score || latestScore);
      setScoresBreakdown(data.scores_breakdown || scoresBreakdown);
      setCriticFeedback(data.critic_feedback || criticFeedback);
      setResumeData(data.resume_data || resumeData);

      if (data.status === 'completed' || action === 'approve') {
        setWorkflowState('completed');
        toast({ title: 'Tailoring Complete!', description: 'Resume tailored and PDF compiled successfully.' });
      } else if (data.status === 'paused_for_human') {
        setWorkflowState('paused');
        setUserFeedback('');
        toast({ title: 'Iteration Complete', description: 'The draft has been updated. Please review.' });
      }
    } catch (err) {
      console.error(err);
      setWorkflowState('paused');
      toast({
        title: 'Action failed',
        description: err instanceof Error ? err.message : 'Failed to send input to agent.',
        variant: 'destructive',
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleDownloadPdf = async () => {
    if (!analysisId) return;
    try {
      toast({
        title: 'Downloading...',
        description: 'Downloading your tailored PDF resume.',
      });
      await apiClient.downloadAutoTailorPdf(analysisId);
    } catch (err) {
      toast({
        title: 'Download failed',
        description: err instanceof Error ? err.message : 'Could not download PDF.',
        variant: 'destructive',
      });
    }
  };

  if (!isHydrated) return null;

  return (
    <div className="min-h-screen bg-background text-foreground relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 opacity-35">
        <ShaderAnimation className="w-full h-full" speed={0.08} />
      </div>
      <div className="pointer-events-none absolute inset-0 app-aurora" />
      <div className="pointer-events-none absolute inset-0 bg-grid-soft opacity-60" />
      <div className="pointer-events-none absolute inset-0 bg-noise opacity-40" />

      <Header />

      <main className="relative z-10 px-4 md:px-8 py-6 max-w-6xl mx-auto space-y-6">
        
        {/* Back navigation */}
        <div className="flex items-center gap-3">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => router.push('/workflows')}
            className="text-muted-foreground hover:text-foreground h-9"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Workflows
          </Button>
          <span className="text-muted-foreground/40">/</span>
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Auto-Tailor Agent</span>
        </div>

        {/* ─── PHASE 1: SETUP FORM ─── */}
        {workflowState === 'setup' && (
          <div className="grid gap-6 md:grid-cols-3">
            <div className="md:col-span-2 space-y-6">
              
              {/* Form Input fields */}
              <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 space-y-6">
                <div>
                  <h2 className="text-lg font-bold text-foreground">1. Select Master Resume</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">Choose your base profile from which the RAG system will extract experiences.</p>
                  
                  {resumes.length === 0 ? (
                    <div className="mt-3 p-4 rounded-xl border border-dashed border-border text-center text-sm text-muted-foreground">
                      No uploaded resumes found. Go upload a resume in the <span className="underline cursor-pointer" onClick={() => router.push('/nexus')}>Resume Studio</span> first.
                    </div>
                  ) : (
                    <select
                      value={selectedResumeId}
                      onChange={(e) => setSelectedResumeId(e.target.value)}
                      className="mt-3 w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/45"
                    >
                      {resumes.map((r) => (
                        <option key={r.resume_id} value={r.resume_id}>
                          {r.filename} ({r.resume_id})
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                <div>
                  <h2 className="text-lg font-bold text-foreground">2. Paste Job Description (JD)</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">The AI Agent uses this target description to align your resume experiences.</p>
                  <Textarea
                    placeholder="Paste the full job description here..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    rows={10}
                    className="mt-3 resize-none rounded-xl border-border bg-background"
                  />
                </div>
              </div>
            </div>

            {/* Right configurations */}
            <div className="space-y-6">
              <div className="glass-panel sheen-border rounded-3xl p-6 space-y-6">
                <h3 className="font-bold text-foreground">Workflow Settings</h3>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-muted-foreground">Target Match Score</span>
                    <span className="text-foreground">{targetScore}%</span>
                  </div>
                  <input
                    type="range"
                    min="70"
                    max="95"
                    value={targetScore}
                    onChange={(e) => setTargetScore(Number(e.target.value))}
                    className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-foreground"
                  />
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    Workflow will auto-complete if this target overall match score is achieved.
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-muted-foreground">Max Auto Iterations</span>
                    <span className="text-foreground">{maxIterations} loops</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={maxIterations}
                    onChange={(e) => setMaxIterations(Number(e.target.value))}
                    className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-foreground"
                  />
                  <p className="text-[10px] text-muted-foreground leading-relaxed">
                    Maximum cycles the generator and critic can loop automatically before prompting you.
                  </p>
                </div>

                <Button 
                  onClick={handleStartWorkflow}
                  disabled={actionLoading || resumes.length === 0}
                  className="w-full bg-foreground text-background hover:bg-foreground/90 font-bold h-11 shadow-lg gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  Launch Tailor Loop
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* ─── PHASE 2: RUNNING / PROGRESS SCREEN ─── */}
        {workflowState === 'running' && (
          <div className="glass-panel sheen-border rounded-3xl p-10 max-w-md mx-auto text-center space-y-6 bg-accent-soft">
            <div className="relative w-16 h-16 mx-auto flex items-center justify-center rounded-full bg-foreground/5 border border-border/80">
              <Loader2 className="h-8 w-8 animate-spin text-foreground" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-bold tracking-tight text-foreground">Executing Tailoring Loop</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                The agent is optimizing your resume structure, checking keyword matching in real-time, and compiling scores.
              </p>
            </div>
            {currentIteration > 0 && (
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-foreground/5 border border-border/60 text-xs font-semibold text-muted-foreground">
                <span>Iteration {currentIteration} of {maxIterations}</span>
              </div>
            )}
          </div>
        )}

        {/* ─── PHASE 3: HUMAN-IN-THE-LOOP PANEL (PAUSED) ─── */}
        {workflowState === 'paused' && (
          <div className="grid gap-6 md:grid-cols-3">
            
            {/* Left 2 Columns: Feedback, Scores, and Preview */}
            <div className="md:col-span-2 space-y-6">
              
              {/* Tab Navigation */}
              <div className="flex border-b border-border/60 bg-card/40 backdrop-blur-xl p-1.5 rounded-2xl border">
                {[
                  { id: 'critic', label: 'Critic Gaps' },
                  { id: 'scores', label: 'ATS Scores' },
                  { id: 'preview', label: 'Resume Draft' }
                ].map((t) => (
                  <button
                    key={t.id}
                    onClick={() => setHitlTab(t.id as any)}
                    className={`flex-1 text-center py-2 text-xs uppercase tracking-wider font-semibold rounded-xl transition-all ${
                      hitlTab === t.id 
                        ? 'bg-foreground/10 text-foreground shadow-sm' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              {/* Tab 1: Critic Feedback */}
              {hitlTab === 'critic' && (
                <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 space-y-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle className="h-5 w-5 text-amber-400" />
                    <h2 className="text-lg font-bold text-foreground">Critic Agent Gap Analysis</h2>
                  </div>
                  <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap border bg-background/50 rounded-2xl p-5 border-border/70 max-h-[450px] overflow-y-auto">
                    {criticFeedback || "No criticism generated."}
                  </div>
                </div>
              )}

              {/* Tab 2: ATS Scores Breakdown */}
              {hitlTab === 'scores' && scoresBreakdown && (
                <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 space-y-6">
                  <div className="flex items-center justify-between border-b border-border/50 pb-4">
                    <h2 className="text-lg font-bold text-foreground">ATS Score Breakdown</h2>
                    <Badge variant="secondary" className="bg-primary/10 text-primary border border-primary/20 text-base font-black px-3 py-1">
                      {latestScore}% Fit
                    </Badge>
                  </div>
                  
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="border border-border/60 rounded-2xl p-5 bg-background/30">
                      <h4 className="text-xs uppercase tracking-wider text-muted-foreground font-bold mb-2">Keywords Matched</h4>
                      <div className="flex flex-wrap gap-1.5 max-h-[150px] overflow-y-auto pr-1">
                        {scoresBreakdown.ats?.matched_keywords?.map((k: string) => (
                          <Badge key={k} variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20 text-[10px]">
                            {k}
                          </Badge>
                        )) || <span className="text-xs text-muted-foreground">None</span>}
                      </div>
                    </div>

                    <div className="border border-border/60 rounded-2xl p-5 bg-background/30">
                      <h4 className="text-xs uppercase tracking-wider text-muted-foreground font-bold mb-2">Missing Keywords</h4>
                      <div className="flex flex-wrap gap-1.5 max-h-[150px] overflow-y-auto pr-1">
                        {scoresBreakdown.ats?.missing_keywords?.map((k: string) => (
                          <Badge key={k} variant="outline" className="bg-red-500/10 text-red-400 border-red-500/20 text-[10px]">
                            {k}
                          </Badge>
                        )) || <span className="text-xs text-muted-foreground">None</span>}
                      </div>
                    </div>
                  </div>

                  {scoresBreakdown.ats?.all_issues && scoresBreakdown.ats.all_issues.length > 0 && (
                    <div className="border border-border/60 rounded-2xl p-5 bg-background/30 space-y-2">
                      <h4 className="text-xs uppercase tracking-wider text-muted-foreground font-bold mb-2">ATS Formatting & Length Issues</h4>
                      <ul className="space-y-1.5 text-xs text-muted-foreground list-disc pl-4">
                        {scoresBreakdown.ats.all_issues.map((issue: string, idx: number) => (
                          <li key={idx}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Resume Preview */}
              {hitlTab === 'preview' && resumeData && (
                <div className="glass-panel sheen-border rounded-3xl p-6 md:p-8 space-y-6 max-h-[600px] overflow-y-auto pr-2">
                  <div className="text-center border-b border-border/50 pb-4">
                    <h1 className="text-2xl font-black">{resumeData.name}</h1>
                    <p className="text-xs text-muted-foreground mt-1">
                      {resumeData.email} • {resumeData.location}
                    </p>
                  </div>

                  {/* Experiences */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground border-b border-border/40 pb-1">Professional Experience</h3>
                    {resumeData.experiences?.map((exp: any, idx: number) => (
                      <div key={idx} className="space-y-1.5">
                        <div className="flex justify-between text-sm font-bold">
                          <span>{exp.title}</span>
                          <span className="font-normal text-muted-foreground">{exp.dates}</span>
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground italic">
                          <span>{exp.company}</span>
                          <span>{exp.location}</span>
                        </div>
                        <ul className="list-disc pl-4 text-xs text-muted-foreground space-y-1 leading-relaxed">
                          {exp.responsibilities?.map((bullet: string, bIdx: number) => (
                            <li key={bIdx}>{bullet}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>

                  {/* Skills */}
                  <div className="space-y-3">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground border-b border-border/40 pb-1">Skills</h3>
                    <div className="grid gap-2 text-xs text-muted-foreground">
                      {Object.entries(resumeData.skills || {}).map(([key, val]: any) => (
                        val ? (
                          <div key={key} className="flex gap-2">
                            <span className="font-semibold capitalize text-foreground w-24 shrink-0">{key}:</span>
                            <span>{val}</span>
                          </div>
                        ) : null
                      ))}
                    </div>
                  </div>
                </div>
              )}

            </div>

            {/* Right Column: HITL Responses */}
            <div className="space-y-6">
              <div className="glass-panel sheen-border rounded-3xl p-6 space-y-5 bg-card/65">
                <div className="space-y-1.5">
                  <h3 className="font-bold text-foreground">Human-in-the-loop Action</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    The latest score is **{latestScore}%**, which is below your target of **{targetScore}%**. You can refine the draft, approve it anyway, or abort.
                  </p>
                </div>

                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-foreground/5 border border-border/60 text-xs font-semibold text-muted-foreground">
                  <span>Iteration {currentIteration} of {maxIterations}</span>
                </div>

                {/* Direct refinement input */}
                <div className="space-y-2 pt-2 border-t border-border/40">
                  <label className="text-xs font-bold text-muted-foreground">Direct the next rewrite iteration</label>
                  <Textarea
                    placeholder="e.g., Emphasize my experience building FastAPI backends, and rewrite the first project bullet to focus on PostgreSQL optimization."
                    value={userFeedback}
                    onChange={(e) => setUserFeedback(e.target.value)}
                    rows={5}
                    className="resize-none text-xs rounded-xl"
                  />
                  <Button 
                    onClick={() => handleHITLResponse('refine')}
                    disabled={actionLoading || !userFeedback.trim()}
                    className="w-full bg-foreground text-background hover:bg-foreground/90 font-bold text-xs h-10 shadow-md gap-1.5"
                  >
                    <RefreshCw className={`h-3 w-3 ${actionLoading ? 'animate-spin' : ''}`} />
                    Re-Tailor Draft
                  </Button>
                </div>

                <div className="space-y-2 pt-4 border-t border-border/40">
                  <Button 
                    onClick={() => handleHITLResponse('approve')}
                    disabled={actionLoading}
                    className="w-full bg-green-600 text-white hover:bg-green-700 font-bold text-xs h-10 shadow-md gap-1.5"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Approve & Finalize PDF
                  </Button>

                  <Button 
                    onClick={() => handleHITLResponse('abort')}
                    disabled={actionLoading}
                    variant="ghost"
                    className="w-full text-red-500 hover:text-red-600 hover:bg-red-500/10 font-bold text-xs h-10 gap-1.5"
                  >
                    <XCircle className="h-4 w-4" />
                    Abort Workflow
                  </Button>
                </div>
              </div>
            </div>

          </div>
        )}

        {/* ─── PHASE 4: COMPLETE STATE ─── */}
        {workflowState === 'completed' && (
          <div className="glass-panel sheen-border rounded-3xl p-10 max-w-md mx-auto text-center space-y-6 bg-accent-soft">
            <div className="w-16 h-16 mx-auto flex items-center justify-center rounded-full bg-green-500/10 border border-green-500/30">
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-black text-foreground">Tailoring Complete!</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Your resume was successfully tailored to the Job Description in {currentIteration} iterations. 
              </p>
            </div>

            <div className="border border-border/60 rounded-2xl p-4 bg-background/40">
              <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">Final Match Score</span>
              <span className="text-4xl font-black text-foreground mt-1 block">{latestScore}%</span>
            </div>

            <div className="pt-2 flex flex-col gap-2">
              <Button 
                onClick={handleDownloadPdf}
                className="w-full bg-foreground text-background hover:bg-foreground/90 font-bold h-11 shadow-lg gap-2"
              >
                <Download className="h-4 w-4" />
                Download Tailored PDF
              </Button>
              
              <Button 
                variant="ghost"
                onClick={() => setWorkflowState('setup')}
                className="w-full text-muted-foreground hover:text-foreground hover:bg-muted/40 font-bold h-11"
              >
                Tailor Another Resume
              </Button>
            </div>
          </div>
        )}

        {/* ─── PHASE 5: ABORTED STATE ─── */}
        {workflowState === 'aborted' && (
          <div className="glass-panel sheen-border rounded-3xl p-10 max-w-md mx-auto text-center space-y-6 bg-accent-soft">
            <div className="w-16 h-16 mx-auto flex items-center justify-center rounded-full bg-red-500/10 border border-red-500/30">
              <XCircle className="h-8 w-8 text-red-500" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-black text-foreground">Workflow Aborted</h2>
              <p className="text-sm text-muted-foreground leading-relaxed">
                The tailoring loop has been aborted. No final PDF has been generated.
              </p>
            </div>

            <Button 
              onClick={() => setWorkflowState('setup')}
              className="w-full bg-foreground text-background hover:bg-foreground/90 font-bold h-11 shadow-lg"
            >
              Start Over
            </Button>
          </div>
        )}

      </main>
    </div>
  );
}
