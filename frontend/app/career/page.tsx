"use client";

import { useReducer, useState } from "react";
import { ArrowRight, Briefcase, Check, FileUp, PanelRightOpen, ShieldCheck, Sparkles } from "lucide-react";
import { PageShell } from "@/components/layout/PageShell";
import { ActionDock } from "@/components/shell/ActionDock";
import { ContextRibbon } from "@/components/shell/ContextRibbon";
import { Inspector } from "@/components/shell/Inspector";
import { CareerWorkspace } from "@/components/studios/career/CareerWorkspace";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  careerStudioClient,
  type ApprovalRequestWire,
  type CareerClaimRevisionWire,
  type CareerMatchResultWire,
  type ResumeDraftWire,
  type RoleRequirementWire,
} from "@/lib/studios/career/client";
import { careerWorkspaceReducer, initialCareerWorkspace } from "@/lib/studios/career/reducer";
import type {
  CandidateEdgeInput,
  CareerApproval,
  CareerClaim,
  CareerDraft,
  CareerGap,
  RequirementMatch,
  RoleRequirement,
} from "@/lib/studios/career/types";

const stages = ["sources", "requirements", "coverage", "draft", "approve"] as const;

export default function CareerStudioPage() {
  const [state, dispatch] = useReducer(careerWorkspaceReducer, initialCareerWorkspace);
  const [source, setSource] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [roleId, setRoleId] = useState<string | null>(null);
  const [matchId, setMatchId] = useState<string | null>(null);
  const [candidateEdges, setCandidateEdges] = useState<CandidateEdgeInput[]>([]);
  const [reviewOpen, setReviewOpen] = useState(false);

  async function ingest() {
    if (!source) return;
    dispatch({ type: "loading" });
    try {
      const document = JSON.parse(await source.text());
      const payload = Array.isArray(document) ? { claims: document } : document;
      const result = await careerStudioClient.createSource({ filename: source.name, media_type: "application/json", ingestion_mode: "structured", claims: payload.claims });
      dispatch({ type: "claims-loaded", claims: normalizeClaimRevisions(result.claims ?? []) });
    }
    catch (reason) { dispatch({ type: "failed", message: message(reason) }); }
  }

  async function analyzeRole() {
    if (jobDescription.trim().length < 10) return;
    dispatch({ type: "loading" });
    try {
      const document = JSON.parse(jobDescription);
      const result = await careerStudioClient.createRole({ role_id: document.role_id, title: document.title, requirements: document.requirements });
      setRoleId(result.id);
      setCandidateEdges(document.candidate_edges ?? []);
      dispatch({ type: "role-loaded", requirements: normalizeRequirements(result.requirements ?? []) });
    }
    catch (reason) { dispatch({ type: "failed", message: message(reason) }); }
  }

  async function match() {
    if (!roleId) return;
    dispatch({ type: "loading" });
    try { const id = `match-${Date.now()}`; const result = await careerStudioClient.createMatch({ match_id: id, role_id: roleId, candidate_edges: candidateEdges }); setMatchId(result.id); const normalized = normalizeMatch(result.result); dispatch({ type: "match-loaded", matches: normalized.matches, gaps: normalized.gaps }); }
    catch (reason) { dispatch({ type: "failed", message: message(reason) }); }
  }

  async function draft() {
    if (!matchId) return;
    dispatch({ type: "loading" });
    try { const result = await careerStudioClient.createDraft(matchId); dispatch({ type: "draft-loaded", draft: normalizeDraft(result.draft, result.approval) }); dispatch({ type: "approvals-loaded", approvals: result.approval ? [normalizeApproval(result.approval)] : [] }); }
    catch (reason) { dispatch({ type: "failed", message: message(reason) }); }
  }

  const current = stages.indexOf(state.stage);
  const activeAction = state.stage === "sources"
    ? <Button disabled={!source || state.loading} onClick={ingest}><ShieldCheck className="mr-2 h-4 w-4" />Extract evidence</Button>
    : state.stage === "requirements"
      ? <Button disabled={jobDescription.trim().length < 10 || state.loading} onClick={analyzeRole}><Briefcase className="mr-2 h-4 w-4" />Load requirements</Button>
      : state.stage === "coverage"
        ? <Button disabled={!roleId || !state.claims.some((claim) => claim.status === "verified") || state.loading} onClick={match}>Build coverage<ArrowRight className="ml-2 h-4 w-4" /></Button>
        : state.stage === "draft"
          ? <Button disabled={!matchId || state.loading} onClick={draft}><Sparkles className="mr-2 h-4 w-4" />Create draft</Button>
          : <Button disabled>Awaiting approval</Button>;

  return <PageShell title="Career Studio" eyebrow="Truth-preserving career intelligence" description="Move from verified evidence to a role-ready draft, one decision at a time." maxWidth="full">
    <ContextRibbon label="Journey">{stages.map((stage, index) => <span className={`inline-flex h-8 items-center gap-2 rounded-md px-3 text-xs font-medium capitalize ${index === current ? "bg-foreground text-background" : index < current ? "text-foreground" : "text-muted-foreground"}`} key={stage}>{index < current ? <Check className="h-3.5 w-3.5" /> : <span className="font-mono text-[10px]">0{index + 1}</span>}{stage}</span>)}</ContextRibbon>
    <main className="mx-auto flex min-h-[60svh] w-full max-w-5xl flex-col justify-center py-10 sm:py-16">
      <div className="max-w-2xl">
        <p className="text-xs font-semibold uppercase text-muted-foreground">Step {current + 1} of {stages.length}</p>
        <h2 className="mt-3 text-2xl font-semibold sm:text-3xl">{stageTitle(state.stage)}</h2>
        <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">{stageDescription(state.stage)}</p>
      </div>
      <div className="mt-8 max-w-3xl border-y border-border/70 py-6">
        {state.stage === "sources" ? <label className="group flex min-h-40 cursor-pointer items-center gap-5 border border-dashed border-border px-5 transition-colors hover:border-foreground/40"><span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-muted"><FileUp className="h-5 w-5" /></span><span className="min-w-0"><span className="block truncate text-sm font-semibold">{source?.name ?? "Choose structured evidence"}</span><span className="mt-1 block text-xs leading-5 text-muted-foreground">Upload a JSON claim bundle with exact source spans and verification status.</span></span><input className="sr-only" type="file" accept=".json,application/json" onChange={(event) => setSource(event.target.files?.[0] ?? null)} /></label> : null}
        {state.stage === "requirements" ? <Textarea aria-label="Typed role requirements" className="min-h-52 resize-none border-0 bg-muted/35 p-5 font-mono text-xs shadow-none focus-visible:ring-1" value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} placeholder={'{"role_id":"staff-data-lead","title":"Staff Data Lead","requirements":[...],"candidate_edges":[...]}' } /> : null}
        {state.stage === "coverage" ? <StageSummary value={`${state.claims.filter((claim) => claim.status === "verified").length} verified claims`} detail={`${state.requirements.length} role requirements are ready for one-to-one matching.`} /> : null}
        {state.stage === "draft" ? <StageSummary value={`${state.matches.length} supported matches`} detail={`${state.gaps.length} truthful gaps remain visible and will not be fabricated.`} /> : null}
        {state.stage === "approve" ? <StageSummary value={state.draft ? `Revision ${state.draft.revision} ready` : "Draft pending"} detail="Review every assertion and its source before publication." /> : null}
      </div>
      {state.error ? <p className="mt-5 max-w-3xl border-l-2 border-destructive py-2 pl-4 text-sm text-destructive">{state.error}</p> : null}
    </main>
    <ActionDock secondary={<Button variant="ghost" onClick={() => setReviewOpen(true)}><PanelRightOpen className="mr-2 h-4 w-4" />Review details</Button>} primary={activeAction} />
    <Inspector open={reviewOpen} onOpenChange={setReviewOpen} title="Career evidence review"><CareerWorkspace claims={state.claims} requirements={state.requirements} matches={state.matches} gaps={state.gaps} draft={state.draft} approvals={state.approvals} /></Inspector>
  </PageShell>;
}

function StageSummary({ value, detail }: { value: string; detail: string }) { return <div className="flex items-start gap-4"><span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-[hsl(var(--data))]" /><div><p className="text-lg font-semibold">{value}</p><p className="mt-1 text-sm text-muted-foreground">{detail}</p></div></div>; }
function stageTitle(stage: typeof stages[number]) { return ({ sources: "Start with evidence you can prove", requirements: "Define the role you are targeting", coverage: "Connect evidence to requirements", draft: "Build an evidence-constrained draft", approve: "Review before publication" } as const)[stage]; }
function stageDescription(stage: typeof stages[number]) { return ({ sources: "Career Studio only works from traceable claims, so every future bullet remains defensible.", requirements: "Load typed requirements and candidate edges for the exact role you want to evaluate.", coverage: "Each verified claim can support at most one requirement, keeping the match honest and readable.", draft: "Generate language only from supported matches while preserving all uncovered gaps.", approve: "The final artifact remains blocked until its assertions and sources receive human approval." } as const)[stage]; }

function normalizeClaimRevisions(revisions: CareerClaimRevisionWire[]): CareerClaim[] {
  return revisions.map((revision) => {
    const claim = revision.claim;
    return {
    id: claim.id,
    subject: claim.subject.label,
    predicate: claim.predicate,
    value: String(claim.object.value),
    status: claim.verification_status,
    confidence: claim.confidence,
    source_label: claim.source_spans[0]?.locator ?? "Source evidence",
    source_spans: claim.source_spans.map((span) => span.locator),
    };
  });
}

function normalizeRequirements(requirements: RoleRequirementWire[]): RoleRequirement[] { return requirements.map((item) => ({ id: item.id, text: item.description, kind: item.priority === "required" ? "mandatory" : "preferred", confidence: item.confidence, source_span: item.source_span.exact_text })); }

function normalizeMatch(result: CareerMatchResultWire): { matches: RequirementMatch[]; gaps: CareerGap[] } {
  const selected = result.selected_matches;
  const unmatched = result.unmatched_requirements;
  return {
    matches: selected.map((item) => ({ requirement_id: item.requirement_id, claim_id: item.claim_id, weight: item.score, rationale: `${item.strength} evidence match${item.uncertain ? " · uncertain" : ""}` })),
    gaps: unmatched.map((item) => ({ requirement_id: item.id, text: item.description, strategy: "Keep visible as an unsupported requirement; do not fabricate evidence." })),
  };
}

function normalizeDraft(draft: ResumeDraftWire, approval: ApprovalRequestWire | null): CareerDraft { return { id: draft.id, revision: 1, status: approval ? "awaiting_approval" as const : "truth_review" as const, bullets: draft.bullets.map((bullet, index) => ({ id: `${draft.id}:${index}`, text: bullet.after_text, source_claim_ids: bullet.source_claim_ids, transformation: bullet.transformation, added_keywords: bullet.added_keywords.map((item) => item.keyword) })), truth_issues: [] }; }

function normalizeApproval(approval: ApprovalRequestWire): CareerApproval { return { id: approval.id, type: "final_publication", status: approval.status }; }

function message(reason: unknown) { return reason instanceof Error ? reason.message : "Career Studio request failed"; }
