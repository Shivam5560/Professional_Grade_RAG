import type { Capability } from "@/lib/apps/types";

export function CapabilityBadge({ capability }: { capability: Capability }) {
  return (
    <span className="rounded-full border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
      {capability}
    </span>
  );
}
