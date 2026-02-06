/**
 * MessageItem - Individual message display component
 */

'use client';

import { useState, useCallback } from 'react';
import { User, Bot, FileText, ChevronDown, ChevronUp, Brain, Zap, Copy, Check } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { formatTimestamp } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message, SourceReference } from '@/lib/types';

interface MessageItemProps {
  message: Message;
  showConfidence?: boolean;
  onShowSources?: () => void;
}

export function MessageItem({ message, showConfidence = false, onShowSources }: MessageItemProps) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [copied, setCopied] = useState(false);
  const isThinkMode = message.mode === 'think';

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  }, [message.content]);

  return (
    <div
      className={cn(
        'flex w-full gap-3 px-4',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      {/* Avatar for Assistant */}
      {!isUser && (
        <div className="flex h-11 w-11 shrink-0 select-none items-center justify-center rounded-xl bg-gradient-to-br from-cyan-500 via-cyan-400 to-blue-500 text-white shadow-xl shadow-cyan-500/40 ring-2 ring-cyan-400/20 hover:shadow-cyan-500/60 transition-all duration-300">
          <Bot className="h-5 w-5" />
        </div>
      )}

      {/* Content */}
      <div className={cn(
        "flex flex-col max-w-[80%]",
        isUser ? "items-end" : "items-start"
      )}>
        <div className="flex items-center gap-2 mb-2 px-1">
          <span className={cn(
            "text-xs font-semibold tracking-wide",
            isUser 
              ? "text-cyan-400" 
              : "bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent"
          )}>
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          <span className="text-xs text-slate-500">•</span>
          <span className="text-xs text-slate-500 font-medium">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>

        {/* Context file badges (Copilot-style) */}
        {isUser && message.contextFiles && message.contextFiles.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-2 px-1">
            {message.contextFiles.map((file) => (
              <Badge
                key={file.id}
                variant="outline"
                className="text-xs py-0.5 px-2 bg-cyan-500/10 text-cyan-300 border-cyan-500/30"
              >
                <FileText className="h-2.5 w-2.5 mr-1" />
                {file.filename}
              </Badge>
            ))}
          </div>
        )}

        {/* Message content */}
        <div className={cn(
          'rounded-2xl px-6 py-4 shadow-xl text-sm transition-all duration-300 relative overflow-hidden',
          isUser 
            ? 'bg-gradient-to-br from-cyan-500 via-cyan-600 to-blue-600 text-white rounded-tr-sm shadow-cyan-500/30 hover:shadow-cyan-500/50 ring-1 ring-white/20' 
            : 'backdrop-blur-xl bg-gradient-to-br from-slate-800/95 via-slate-850/95 to-slate-900/98 border border-slate-700/60 rounded-tl-sm text-slate-100 shadow-slate-900/60 hover:shadow-slate-900/80 hover:border-cyan-500/40 ring-1 ring-cyan-500/10',
          !isUser && 'group/msg'
        )}>
          {/* Decorative gradient overlay for assistant messages */}
          {!isUser && (
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-blue-500/5 pointer-events-none" />
          )}

          {/* Copy button for assistant messages */}
          {!isUser && (
            <button
              type="button"
              onClick={handleCopy}
              className="absolute top-2 right-2 z-20 p-1.5 rounded-lg bg-slate-700/60 hover:bg-slate-600/80 border border-slate-600/40 hover:border-cyan-500/40 text-slate-400 hover:text-cyan-300 transition-all duration-200 opacity-0 group-hover/msg:opacity-100 focus:opacity-100"
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-green-400" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          )}
          
          <div className={cn(
            'prose prose-sm max-w-none relative z-10',
            isUser 
              ? 'prose-invert text-white prose-headings:text-white prose-p:text-white prose-strong:text-white prose-code:text-cyan-100' 
              : 'text-slate-100 prose-headings:text-slate-100 prose-p:text-slate-100 prose-strong:text-white',
            // Better table styling
            'prose-table:text-sm prose-table:border-collapse',
            'prose-th:border prose-th:border-slate-600 prose-th:bg-slate-700/60 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-th:font-semibold prose-th:text-slate-200',
            'prose-td:border prose-td:border-slate-700 prose-td:px-3 prose-td:py-2 prose-td:text-slate-200',
            'prose-tr:border-b prose-tr:border-slate-700',
            // Better list styling
            'prose-ul:my-2 prose-ol:my-2 prose-li:text-slate-100',
            'prose-li:my-1',
            // Better code styling
            'prose-code:text-xs prose-code:bg-slate-900/60 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-cyan-300 prose-code:border prose-code:border-slate-700',
            'prose-pre:bg-slate-900/80 prose-pre:border prose-pre:border-slate-700 prose-pre:text-slate-200'
          )}>
            {isUser ? (
              <p className="whitespace-pre-wrap m-0 leading-relaxed font-medium tracking-wide">{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ node, ...props }) => (
                    <div className="overflow-x-auto my-4">
                      <table className="min-w-full divide-y divide-border" {...props} />
                    </div>
                  ),
                  th: ({ node, ...props }) => (
                    <th className="bg-slate-700/50 px-3 py-2 text-left text-xs font-semibold text-slate-200 border border-slate-600/50" {...props} />
                  ),
                  td: ({ node, ...props }) => (
                    <td className="px-3 py-2 text-sm border border-slate-600/30 text-slate-100" {...props} />
                  ),
                  h1: ({ node, ...props }) => (
                    <h1 className="text-2xl font-bold mt-6 mb-3 bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent border-b border-cyan-500/30 pb-2" {...props} />
                  ),
                  h2: ({ node, ...props }) => (
                    <h2 className="text-xl font-semibold mt-5 mb-2 bg-gradient-to-r from-cyan-300 to-blue-300 bg-clip-text text-transparent" {...props} />
                  ),
                  h3: ({ node, ...props }) => (
                    <h3 className="text-lg font-semibold mt-4 mb-2 text-cyan-200" {...props} />
                  ),
                  p: ({ node, ...props }) => (
                    <p className="mb-3 leading-relaxed text-slate-50" {...props} />
                  ),
                  ul: ({ node, ...props }) => (
                    <ul className="list-disc list-outside ml-6 my-3 space-y-2 text-slate-50 marker:text-cyan-400" {...props} />
                  ),
                  ol: ({ node, ...props }) => (
                    <ol className="list-decimal list-outside ml-6 my-3 space-y-2 text-slate-50 marker:text-cyan-400 marker:font-semibold" {...props} />
                  ),
                  li: ({ node, ...props }) => (
                    <li className="text-slate-50 leading-relaxed pl-1" {...props} />
                  ),
                  code: ({ node, inline, ...props }: any) => 
                    inline ? (
                      <code className="bg-slate-900/80 px-2 py-0.5 rounded text-sm font-mono text-cyan-300 border border-cyan-500/30 shadow-inner" {...props} />
                    ) : (
                      <code className="block bg-slate-950/90 p-4 rounded-lg text-sm font-mono overflow-x-auto my-3 text-cyan-100 border border-cyan-500/30 shadow-lg shadow-cyan-500/10" {...props} />
                    ),
                  pre: ({ node, ...props }) => (
                    <pre className="bg-slate-950/90 p-4 rounded-lg overflow-x-auto my-3 border border-cyan-500/30 shadow-lg shadow-cyan-500/10" {...props} />
                  ),
                  blockquote: ({ node, ...props }) => (
                    <blockquote className="border-l-4 border-cyan-500 pl-4 italic my-3 text-slate-200 bg-cyan-500/5 py-2 rounded-r backdrop-blur-sm" {...props} />
                  ),
                  hr: ({ node, ...props }) => (
                    <hr className="my-4 border-slate-600/50" {...props} />
                  ),
                  strong: ({ node, ...props }) => (
                    <strong className="font-semibold text-slate-50" {...props} />
                  ),
                  em: ({ node, ...props }) => (
                    <em className="italic text-slate-200" {...props} />
                  ),
                  a: ({ node, ...props }) => (
                    <a className="text-cyan-400 hover:text-cyan-300 underline underline-offset-2" {...props} />
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>
        </div>

        {/* Badges for assistant messages */}
        {!isUser && (showConfidence || (message.sources && message.sources.length > 0) || message.reasoning || message.mode) && (
          <div className="flex flex-col gap-2 pt-2 px-1">
            <div className="flex items-center gap-2 flex-wrap">
              {/* Mode badge */}
              {message.mode && (
                <div className={cn(
                  "text-xs font-semibold px-3 py-1 rounded-full border shadow-lg backdrop-blur-sm flex items-center gap-1.5",
                  message.mode === 'think'
                    ? "text-purple-300 bg-gradient-to-r from-purple-900/40 to-pink-900/40 border-purple-500/30 shadow-purple-500/10"
                    : "text-cyan-300 bg-gradient-to-r from-slate-800/80 to-slate-900/80 border-cyan-500/30 shadow-cyan-500/10"
                )}>
                  {message.mode === 'think' ? <Brain className="h-3 w-3" /> : <Zap className="h-3 w-3" />}
                  {message.mode === 'think' ? 'Think' : 'Fast'}
                </div>
              )}

              {/* Confidence badge */}
              {showConfidence && message.confidence_score !== undefined && (
                <div className="text-xs font-semibold text-cyan-300 bg-gradient-to-r from-slate-800/80 to-slate-900/80 px-3 py-1 rounded-full border border-cyan-500/30 shadow-lg shadow-cyan-500/10 backdrop-blur-sm">
                  Confidence: {Math.round(message.confidence_score)}%
                </div>
              )}

              {/* Reasoning badge (think mode) */}
              {message.reasoning && (
                <button
                  type="button"
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="text-xs font-semibold text-purple-300 bg-gradient-to-r from-purple-900/30 to-pink-900/30 px-3 py-1 rounded-full border border-purple-500/30 shadow-lg shadow-purple-500/10 backdrop-blur-sm hover:border-purple-400/50 hover:shadow-purple-500/20 transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
                >
                  <Brain className="h-3 w-3" />
                  <span>Reasoning</span>
                  {showReasoning ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                </button>
              )}
              
              {/* Sources badge - clickable button */}
              {message.sources && message.sources.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowSources(!showSources)}
                  className="text-xs font-semibold text-blue-300 bg-gradient-to-r from-slate-800/80 to-slate-900/80 px-3 py-1 rounded-full border border-blue-500/30 shadow-lg shadow-blue-500/10 backdrop-blur-sm hover:border-blue-400/50 hover:shadow-blue-500/20 transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
                >
                  <FileText className="h-3 w-3" />
                  <span>Sources ({message.sources.length})</span>
                  {showSources ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                </button>
              )}
            </div>

            {/* Collapsible reasoning panel */}
            {showReasoning && message.reasoning && (
              <div className="mt-2 animate-in slide-in-from-top-2 duration-200">
                <div className="bg-purple-900/20 border border-purple-500/20 rounded-lg p-4 text-xs backdrop-blur-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="h-4 w-4 text-purple-400" />
                    <span className="font-semibold text-purple-300">Reasoning Steps</span>
                  </div>
                  <div className="text-slate-300 leading-relaxed whitespace-pre-wrap prose prose-sm prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.reasoning}
                    </ReactMarkdown>
                  </div>
                </div>
              </div>
            )}
            
            {/* Collapsible sources list */}
            {showSources && message.sources && message.sources.length > 0 && (
              <div className="mt-2 space-y-2 animate-in slide-in-from-top-2 duration-200">
                {message.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-800/60 border border-slate-700/50 rounded-lg p-3 text-xs backdrop-blur-sm hover:border-cyan-500/30 transition-all duration-200"
                  >
                    <div className="flex items-start gap-2">
                      <FileText className="h-4 w-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1 space-y-1">
                        <div className="font-semibold text-cyan-300">
                          {source.document}
                          {source.page && (
                            <span className="text-slate-400 font-normal ml-1">
                              (Page {source.page})
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-slate-400">
                          <span className="px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 rounded text-cyan-400 font-medium">
                            {Math.round(source.relevance_score * 100)}% relevance
                          </span>
                        </div>
                        {source.text_snippet && (
                          <div className="text-slate-300 leading-relaxed mt-1 pt-2 border-t border-slate-700/30">
                            "{source.text_snippet}"
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Avatar for User */}
      {isUser && (
        <div className="flex h-11 w-11 shrink-0 select-none items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 via-blue-500 to-cyan-500 text-white shadow-xl shadow-blue-500/40 ring-2 ring-blue-400/20 hover:shadow-blue-500/60 transition-all duration-300">
          <User className="h-5 w-5" />
        </div>
      )}
    </div>
  );
}
