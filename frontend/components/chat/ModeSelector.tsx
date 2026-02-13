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
    <div className="flex items-center gap-1 rounded-xl border border-border/70 bg-card/70 p-1 backdrop-blur-sm shadow-[0_10px_30px_-24px_rgba(0,0,0,0.5)]">
      {/* Fast Mode */}
      <button
        type="button"
        onClick={() => onModeChange('fast')}
        disabled={disabled}
        className={cn(
          'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all duration-200 cursor-pointer',
          mode === 'fast'
            ? 'bg-gradient-to-r from-[hsl(var(--chart-2))] to-[hsl(var(--chart-1))] text-white shadow-lg'
            : 'text-muted-foreground hover:text-foreground hover:bg-background/80',
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
          'flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all duration-200 cursor-pointer',
          mode === 'think'
            ? 'bg-gradient-to-r from-[hsl(var(--chart-3))] to-[hsl(var(--chart-4))] text-white shadow-lg'
            : 'text-muted-foreground hover:text-foreground hover:bg-background/80',
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
