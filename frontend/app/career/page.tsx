"use client";

import { useReducer, useState } from "react";
import { Briefcase, FileUp, ShieldCheck, Sparkles } from "lucide-react";
import { PageShell } from "@/components/layout/PageShell";
import { CareerWorkspace } from "@/components/studios/career/CareerWorkspace";
import { StudioPanel, StatusPill } from "@/components/studios/StudioPrimitives";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { careerStudioClient } from "@/lib/studios/career/client";
import { careerWorkspaceReducer, initialCareerWorkspace } from "@/lib/studios/career/reducer";
import type { CareerClaim, CareerProfile } from "@/lib/studios/career/types";
import type { CandidateEdgeInput } from "@/lib/studios/career/types";

const stages = ["sources", "requirements", "coverage", "draft", "approve"] as const;

export default function CareerStudioPage() {
  const [state, dispatch] = useReducer(careerWorkspaceReducer, initialCareerWorkspace);
  const [source, setSource] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState("");
  const [roleId, setRoleId] = useState<string | null>(null);
  const [matchId, setMatchId] = useState<string | null>(null);
  const [candidateEdges, setCandidateEdges] = useState<CandidateEdgeInput[]>([]);

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

  return <PageShell title="Career Studio" eyebrow="Truth-preserving career intelligence" description="Turn source-backed career claims into role coverage and publication-ready drafts without inventing experience." maxWidth="full">
    <div className="mb-5 rounded-xl border border-border bg-card px-5 py-4 shadow-sm"><div className="flex flex-wrap items-center gap-2">{stages.map((stage, index) => { const current = stages.indexOf(state.stage); return <div className="flex items-center gap-2" key={stage}><span className={`flex h-7 w-7 items-center justify-center rounded-full border font-mono text-[10px] ${index <= current ? "border-primary bg-primary text-primary-foreground" : "border-border bg-muted text-muted-foreground"}`}>{index + 1}</span><span className={`hidden text-xs font-medium capitalize sm:inline ${index <= current ? "text-foreground" : "text-muted-foreground"}`}>{stage}</span>{index < stages.length - 1 ? <span className="h-px w-4 bg-border md:w-8" /> : null}</div>; })}</div></div>
    <div className="mb-5 grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
      <StudioPanel title="1 · Build verified evidence" description="Upload a resume or supporting document, then review every inferred claim before it can be published." action={<StatusPill state={state.claims.length ? "verified" : "pending"} />}>
        <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-dashed border-border bg-muted/20 p-4 hover:border-primary/40"><span className="flex h-10 w-10 items-center justify-center rounded-lg bg-background"><FileUp className="h-4 w-4" /></span><span className="min-w-0 flex-1"><span className="block truncate text-sm font-medium">{source?.name ?? "Choose a structured evidence source"}</span><span className="text-xs text-muted-foreground">JSON claim bundle · exact source spans and verification status required</span></span><input className="sr-only" type="file" accept=".json,application/json" onChange={(event) => setSource(event.target.files?.[0] ?? null)} /></label>
        <Button className="mt-3 w-full" disabled={!source || state.loading} onClick={ingest}><ShieldCheck className="mr-2 h-4 w-4" />Extract evidence graph</Button>
      </StudioPanel>
      <StudioPanel title="2 · Define the target role" description="Requirements remain typed as mandatory, preferred, responsibility, seniority, education, and constraints." action={<Briefcase className="h-5 w-5 text-[hsl(var(--data))]" />}>
        <Textarea aria-label="Typed role requirements" className="min-h-28 resize-none font-mono text-xs" value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} placeholder={'{"role_id":"staff-data-lead","title":"Staff Data Lead","requirements":[...],"candidate_edges":[...]}' } />
        <p className="mt-2 text-[11px] leading-5 text-muted-foreground">Use typed requirement JSON from the role intake pipeline. Free-form extraction is intentionally unavailable until a verified parser is connected.</p>
        <div className="mt-3 flex flex-wrap gap-2"><Button disabled={jobDescription.trim().length < 10 || state.loading} onClick={analyzeRole}>Load requirements</Button><Button variant="outline" disabled={!roleId || !state.claims.some((claim) => claim.status === "verified") || state.loading} onClick={match}>Build one-to-one coverage</Button><Button variant="outline" disabled={!matchId || state.loading} onClick={draft}><Sparkles className="mr-2 h-4 w-4" />Create evidence draft</Button></div>
      </StudioPanel>
    </div>
    {state.error ? <p className="mb-5 rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{state.error}</p> : null}
    <CareerWorkspace claims={state.claims} requirements={state.requirements} matches={state.matches} gaps={state.gaps} draft={state.draft} approvals={state.approvals} />
  </PageShell>;
}

function normalizeClaimRevisions(revisions: any[]): CareerClaim[] {
  return revisions.map((revision: any) => {
    const claim = revision.claim ?? revision;
    return {
    id: claim.id,
    subject: typeof claim.subject === "string" ? claim.subject : claim.subject?.label ?? claim.subject?.id ?? "Career evidence",
    predicate: claim.predicate,
    value: typeof claim.value === "string" ? claim.value : String(claim.object?.value ?? claim.value ?? ""),
    status: claim.status ?? claim.verification_status ?? "inferred",
    confidence: claim.confidence ?? 0,
    source_label: claim.source_label ?? claim.source_spans?.[0]?.locator ?? "Source evidence",
    source_spans: claim.source_spans,
    };
  });
}

function normalizeRequirements(requirements: any[]) { return requirements.map((item) => ({ id: item.id, text: item.text ?? item.description, kind: item.kind ?? (item.priority === "required" ? "mandatory" : "preferred"), confidence: item.confidence, source_span: item.source_span?.exact_text })); }

function normalizeMatch(result: any) {
  const selected = result?.selected_matches ?? [];
  const unmatched = result?.unmatched_requirements ?? [];
  return {
    matches: selected.map((item: any) => ({ requirement_id: item.requirement_id, claim_id: item.claim_id, weight: item.score, rationale: `${item.strength} evidence match${item.uncertain ? " · uncertain" : ""}` })),
    gaps: unmatched.map((item: any) => ({ requirement_id: item.id, text: item.description, strategy: "Keep visible as an unsupported requirement; do not fabricate evidence." })),
  };
}

function normalizeDraft(draft: any, approval: any) { return { id: draft.id, revision: 1, status: approval ? "awaiting_approval" as const : "truth_review" as const, bullets: (draft.bullets ?? []).map((bullet: any, index: number) => ({ id: `${draft.id}:${index}`, text: bullet.after_text, source_claim_ids: bullet.source_claim_ids ?? [], transformation: bullet.transformation, added_keywords: (bullet.added_keywords ?? []).map((item: any) => item.keyword) })), truth_issues: [] }; }

function normalizeApproval(approval: any) { return { id: approval.id, type: "final_publication" as const, status: approval.status === "pending" ? "pending" as const : approval.status }; }

function message(reason: unknown) { return reason instanceof Error ? reason.message : "Career Studio request failed"; }
