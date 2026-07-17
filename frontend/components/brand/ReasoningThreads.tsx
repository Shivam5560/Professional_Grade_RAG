import { cn } from "@/lib/utils";

export function ReasoningThreads({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden
      className={cn("h-full w-full", className)}
      viewBox="0 0 640 260"
      fill="none"
    >
      <defs>
        <linearGradient
          id="thread-mint"
          x1="40"
          y1="210"
          x2="310"
          y2="60"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="hsl(var(--signal))" />
          <stop offset="1" stopColor="hsl(var(--data))" />
        </linearGradient>
        <linearGradient
          id="thread-copper"
          x1="310"
          y1="60"
          x2="590"
          y2="190"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor="hsl(var(--data))" />
          <stop offset="1" stopColor="hsl(var(--copper))" />
        </linearGradient>
      </defs>
      <path
        d="M48 208C142 194 190 86 310 62"
        stroke="url(#thread-mint)"
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
      <path
        d="M310 62C398 60 470 180 590 190"
        stroke="url(#thread-copper)"
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
      <path
        d="M48 208C220 242 420 232 590 190"
        stroke="hsl(var(--foreground)/.16)"
        vectorEffect="non-scaling-stroke"
      />
      {[
        [48, 208],
        [310, 62],
        [455, 145],
        [590, 190],
      ].map(([cx, cy], index) => (
        <circle
          key={index}
          cx={cx}
          cy={cy}
          r="5"
          fill={
            index === 3 ? "hsl(var(--copper))" : "hsl(var(--signal))"
          }
        />
      ))}
    </svg>
  );
}
