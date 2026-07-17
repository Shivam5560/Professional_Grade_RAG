import { cn } from "@/lib/utils";

export function NexusAperture({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn(
        "nexus-breathe relative aspect-square w-52 rounded-full border border-[hsl(var(--signal)/.3)]",
        className,
      )}
    >
      <div className="nexus-orbit absolute inset-[14%] rounded-full border border-dashed border-[hsl(var(--copper)/.38)]" />
      <div className="absolute inset-[31%] rounded-full border border-[hsl(var(--signal)/.52)]" />
      <div className="absolute inset-[46%] rounded-full bg-[hsl(var(--signal))] shadow-[0_0_32px_hsl(var(--signal)/.6)]" />
    </div>
  );
}
