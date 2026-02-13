export function TypingIndicator() {
  return (
    <div className="flex w-fit items-center gap-1.5 rounded-2xl rounded-tl-none border border-border/70 bg-card/80 px-5 py-4 shadow-lg backdrop-blur-xl">
      <div className="h-2 w-2 animate-bounce rounded-full bg-[hsl(var(--chart-2))] [animation-delay:-0.3s]" />
      <div className="h-2 w-2 animate-bounce rounded-full bg-[hsl(var(--chart-1))] [animation-delay:-0.15s]" />
      <div className="h-2 w-2 animate-bounce rounded-full bg-[hsl(var(--chart-3))]" />
    </div>
  );
}
