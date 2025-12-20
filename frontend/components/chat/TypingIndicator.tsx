import { cn } from '@/lib/utils';

export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-5 py-4 backdrop-blur-xl bg-slate-900/80 border border-slate-800/50 rounded-2xl rounded-tl-none w-fit shadow-lg">
      <div className="w-2 h-2 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
      <div className="w-2 h-2 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
      <div className="w-2 h-2 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full animate-bounce" />
    </div>
  );
}
