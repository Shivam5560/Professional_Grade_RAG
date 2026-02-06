/**
 * ModeSelector — Toggle between Fast and Think RAG modes.
 * Fast: Hybrid BM25 + Vector retrieval (quick)
 * Think: PageIndex reasoning-based tree search (deeper analysis)
 */

'use client';

import { Zap, Brain } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { RAGMode } from '@/lib/types';

interface ModeSelectorProps {
  mode: RAGMode;
  onModeChange: (mode: RAGMode) => void;
  disabled?: boolean;
}

export function ModeSelector({ mode, onModeChange, disabled = false }: ModeSelectorProps) {
  return (
    <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-800/60 border border-slate-700/50 backdrop-blur-sm">
      {/* Fast Mode */}
      <button
        type="button"
        onClick={() => onModeChange('fast')}
        disabled={disabled}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer',
          mode === 'fast'
            ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-500/10'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        title="Fast Mode — Hybrid keyword + vector search with reranking. Best for quick factual lookups."
      >
        <Zap className="h-3.5 w-3.5" />
        <span>Fast</span>
      </button>

      {/* Think Mode */}
      <button
        type="button"
        onClick={() => onModeChange('think')}
        disabled={disabled}
        className={cn(
          'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 cursor-pointer',
          mode === 'think'
            ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-300 border border-purple-500/40 shadow-lg shadow-purple-500/10'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        title="Think Mode — Reasoning-based tree search using document structure. Best for complex questions that need deep analysis."
      >
        <Brain className="h-3.5 w-3.5" />
        <span>Think</span>
      </button>
    </div>
  );
}
