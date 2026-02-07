export function Footer() {
  return (
    <footer className="border-t border-border/60 backdrop-blur-xl bg-background/80 py-4">
      <div className="flex flex-col items-center justify-center gap-3 md:flex-row max-w-7xl mx-auto px-6">
        <p className="text-center text-sm text-muted-foreground">
          Built with <span className="text-foreground font-semibold">LlamaIndex</span>, <span className="text-foreground font-semibold">Ollama</span>, <span className="text-foreground font-semibold">PostgreSQL</span>, <span className="text-foreground font-semibold">Groq</span> & <span className="text-foreground font-semibold">Mxbai Reranker</span>
        </p>
        <p className="text-center text-xs text-muted-foreground">
          v1.0.0 • <span className="text-foreground font-semibold">Enterprise Edition</span>
        </p>
      </div>
    </footer>
  );
}
