import { ArrowRight, FileCheck2, Link2, ShieldAlert } from "lucide-react";
import { EvidenceTag, EmptyStudioState, StatusPill, StudioPanel } from "../StudioPrimitives";
import type { CareerApproval, CareerClaim, CareerDraft, CareerGap, RequirementMatch, RoleRequirement } from "@/lib/studios/career/types";

interface Props { claims: CareerClaim[]; requirements: RoleRequirement[]; matches: RequirementMatch[]; gaps: CareerGap[]; draft: CareerDraft | null; approvals: CareerApproval[] }

export function CareerWorkspace({ claims, requirements, matches, gaps, draft, approvals }: Props) {
  const claimsById = new Map(claims.map((claim) => [claim.id, claim]));
  const matchesByRequirement = new Map(matches.map((match) => [match.requirement_id, match]));
  const pendingFinal = approvals.some((approval) => approval.type === "final_publication" && approval.status === "pending");
  return <div className="space-y-8">
    <div className="grid grid-cols-2 gap-x-5 gap-y-4 border-b border-border/70 pb-6"><Summary label="Verified claims" value={claims.filter((claim) => claim.status === "verified").length} /><Summary label="Needs review" value={claims.filter((claim) => claim.status === "inferred" || claim.status === "disputed").length} /><Summary label="Requirements" value={requirements.length} /><Summary label="Truth issues" value={draft?.truth_issues.length ?? 0} critical={Boolean(draft?.truth_issues.some((issue) => issue.severity === "critical"))} /></div>
    <div className="space-y-6">
      <div className="space-y-5">
        <StudioPanel title="Career evidence" description="Atomic claims tied to source spans">
          {claims.length ? <div className="space-y-2">{claims.map((claim) => <article className="rounded-lg border border-border p-3" key={claim.id}><div className="flex items-start justify-between gap-2"><EvidenceTag>{claim.id}</EvidenceTag><StatusPill state={claim.status} /></div><p className="mt-3 text-xs font-semibold">{claim.subject}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{claim.predicate}: {claim.value}</p><p className="mt-2 text-[10px] text-muted-foreground">{claim.source_label} · {Math.round(claim.confidence * 100)}%</p></article>)}</div> : <EmptyStudioState title="No career evidence" description="Upload a resume or supporting source to build a verified claim graph." />}
        </StudioPanel>
      </div>
      <div className="space-y-5">
        <StudioPanel title="Requirement coverage" description="One claim is selected for at most one requirement">
          {requirements.length ? <div className="space-y-3">{requirements.map((requirement) => { const match = matchesByRequirement.get(requirement.id); const claim = match ? claimsById.get(match.claim_id) : undefined; return <article className="rounded-lg border border-border p-4" key={requirement.id}><div className="flex items-start justify-between gap-2"><div><span className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">{requirement.kind}</span><p className="mt-1 text-xs font-semibold">{requirement.text}</p></div><StatusPill state={match ? "verified" : "uncovered"} /></div>{match ? <div className="mt-3 rounded-md bg-muted/50 p-3"><div className="flex items-center gap-2"><Link2 className="h-3.5 w-3.5 text-[hsl(var(--data))]" /><EvidenceTag>{match.claim_id}</EvidenceTag><span className="font-mono text-[10px]">{Math.round(match.weight * 100)}%</span></div><p className="mt-2 text-[11px] text-muted-foreground">{match.rationale}{claim ? ` · ${claim.subject}` : ""}</p></div> : <p className="mt-3 text-[11px] text-amber-700 dark:text-amber-300">No verified evidence selected. Keep as a truthful gap.</p>}</article>; })}</div> : <EmptyStudioState title="No target role" description="Paste a job description to extract mandatory and preferred requirements." />}
        </StudioPanel>
        {gaps.length ? <StudioPanel title="Truthful gaps"><ul className="space-y-2">{gaps.map((gap) => <li className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-xs" key={gap.requirement_id}><p className="font-medium">{gap.text}</p>{gap.strategy ? <p className="mt-1 text-muted-foreground">{gap.strategy}</p> : null}</li>)}</ul></StudioPanel> : null}
      </div>
      <div className="space-y-5">
        <StudioPanel title="Evidence-constrained draft" description={draft ? `Revision ${draft.revision} · transformations remain auditable` : "Draft only from verified evidence"} action={draft ? <StatusPill state={draft.status} /> : undefined}>
          {draft ? <div className="space-y-3">{draft.bullets.map((bullet) => <article className="rounded-lg border border-border p-4" key={bullet.id}><p className="text-sm leading-6">{bullet.text}</p><div className="mt-3 flex flex-wrap items-center gap-2"><span className="text-[10px] text-muted-foreground">{bullet.transformation}</span><ArrowRight className="h-3 w-3 text-muted-foreground" />{bullet.source_claim_ids.map((id) => <EvidenceTag key={id}>{id}</EvidenceTag>)}</div></article>)}</div> : <EmptyStudioState title="Draft not generated" description="Complete evidence review and role matching before drafting." />}
        </StudioPanel>
        {draft?.truth_issues.length ? <StudioPanel title="Truth Guardian" description="Critical issues block publication"><div className="space-y-2">{draft.truth_issues.map((issue) => <article className="rounded-lg border border-destructive/20 bg-destructive/5 p-3" key={issue.id}><div className="flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-destructive" /><StatusPill state={issue.severity} /></div><p className="mt-2 text-xs font-semibold">{issue.message}</p><p className="mt-1 font-mono text-[10px] text-muted-foreground">{issue.assertion}</p></article>)}</div></StudioPanel> : null}
        <StudioPanel title="Publication approval" description="Human approval is required before export">
          {pendingFinal ? <div className="rounded-lg border border-amber-500/25 bg-amber-500/5 p-4"><div className="flex items-center gap-2"><FileCheck2 className="h-4 w-4 text-amber-600" /><p className="text-sm font-semibold">Awaiting final approval</p></div><p className="mt-2 text-xs leading-5 text-muted-foreground">Review every assertion and its source claim before publishing this revision.</p></div> : <EmptyStudioState title="No approval pending" description="A final approval request appears after the Truth Guardian passes." />}
        </StudioPanel>
      </div>
    </div>
  </div>;
}

function Summary({ label, value, critical = false }: { label: string; value: number; critical?: boolean }) { return <div className={`border-l-2 pl-3 ${critical ? "border-destructive" : "border-border"}`}><p className="text-[10px] font-semibold uppercase text-muted-foreground">{label}</p><p className={`mt-1 text-xl font-semibold ${critical ? "text-destructive" : ""}`}>{value}</p></div>; }
