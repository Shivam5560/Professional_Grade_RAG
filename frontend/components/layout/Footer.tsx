export function Footer() {
  return (
    <footer className="border-t border-slate-800/50 backdrop-blur-xl bg-slate-900/80 py-4">
      <div className="flex flex-col items-center justify-center gap-3 md:flex-row max-w-7xl mx-auto px-6">
        <p className="text-center text-sm text-slate-400">
          Built with <span className="text-cyan-400 font-medium">LlamaIndex</span>, <span className="text-blue-400 font-medium">Ollama</span>, <span className="text-purple-400 font-medium">PostgreSQL</span> & <span className="text-cyan-400 font-medium">BGE-Reranker</span>
        </p>
        <p className="text-center text-xs text-slate-500">
          v1.0.0 • <span className="text-cyan-400 font-medium">Enterprise Edition</span>
        </p>
      </div>
    </footer>
  );
}
