export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-5 py-4 backdrop-blur-xl bg-card/80 border border-border/70 rounded-2xl rounded-tl-none w-fit shadow-lg">
      <div className="w-2 h-2 bg-foreground rounded-full animate-bounce [animation-delay:-0.3s]" />
      <div className="w-2 h-2 bg-foreground rounded-full animate-bounce [animation-delay:-0.15s]" />
      <div className="w-2 h-2 bg-foreground rounded-full animate-bounce" />
    </div>
  );
}
