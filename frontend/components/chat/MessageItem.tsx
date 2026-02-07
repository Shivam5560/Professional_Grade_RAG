/**
 * MessageItem - Individual message display component
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import { User, Bot, FileText, ChevronDown, ChevronUp, Brain, Zap, Copy, Check } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { formatTimestamp } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '@/lib/types';
import { DrawioDiagram } from './DrawioDiagram';

interface MessageItemProps {
  message: Message;
  showConfidence?: boolean;
}

export function MessageItem({ message, showConfidence = false }: MessageItemProps) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(false);
  const [showReasoning, setShowReasoning] = useState(false);
  const [copied, setCopied] = useState(false);

  const unwrapMarkdownFence = useCallback((value: string) => {
    const trimmed = value.trim();
    const match = trimmed.match(/^```(?:md|markdown)?\s*([\s\S]*?)\s*```$/i);
    return match ? match[1].trim() : value;
  }, []);

  const extractedContent = useMemo(() => {
    const content = message.content;

    const textParts: string[] = [];
    const xmlParts: string[] = [];
    let lastIndex = 0;
    const regex = /<mxfile[\s\S]*?<\/mxfile>/g;
    let match;

    while ((match = regex.exec(content)) !== null) {
      const textBefore = content.substring(lastIndex, match.index).trim();
      if (textBefore) {
        textParts.push(unwrapMarkdownFence(textBefore));
      }
      xmlParts.push(match[0]);
      lastIndex = regex.lastIndex;
    }

    const textAfter = content.substring(lastIndex).trim();
    if (textAfter) {
      textParts.push(unwrapMarkdownFence(textAfter));
    }

    if (textParts.length === 0) {
      textParts.push(unwrapMarkdownFence(content));
    }

    if (message.diagramXml) {
      if (xmlParts.length > 0) {
        xmlParts[0] = message.diagramXml;
      } else {
        xmlParts.push(message.diagramXml);
      }
    }

    return { text: textParts.join('\n\n'), diagrams: xmlParts };
  }, [message.content, message.diagramXml, unwrapMarkdownFence]);

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
        <div className="flex h-11 w-11 shrink-0 select-none items-center justify-center rounded-2xl logo-mark shadow-xl ring-2 ring-foreground/10 hover:shadow-2xl transition-all duration-300">
          <Bot className="h-5 w-5 text-primary-foreground" />
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
              ? "text-foreground" 
              : "text-muted-foreground"
          )}>
            {isUser ? 'You' : 'AI Assistant'}
          </span>
          <span className="text-xs text-muted-foreground">•</span>
          <span className="text-xs text-muted-foreground font-medium">
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
                className="text-xs py-0.5 px-2 bg-muted/60 text-foreground border-border/60"
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
            ? 'bubble-user text-foreground rounded-tr-sm shadow-[0_18px_40px_-30px_rgba(0,0,0,0.3)] ring-1 ring-border/60' 
            : 'bubble-bot backdrop-blur-xl border border-border/70 rounded-tl-sm text-foreground shadow-[0_20px_60px_-45px_rgba(0,0,0,0.35)] hover:shadow-[0_30px_80px_-60px_rgba(0,0,0,0.45)]',
          !isUser && 'group/msg'
        )}>
          {/* Decorative gradient overlay for assistant messages */}
          {!isUser && (
            <div className="absolute inset-0 bg-gradient-to-br from-foreground/5 via-transparent to-transparent pointer-events-none" />
          )}

          {/* Copy button for assistant messages */}
          {!isUser && (
            <button
              type="button"
              onClick={handleCopy}
              className="absolute top-2 right-2 z-20 p-1.5 rounded-lg bg-muted/70 hover:bg-muted border border-border/70 text-muted-foreground hover:text-foreground transition-all duration-200 opacity-0 group-hover/msg:opacity-100 focus:opacity-100"
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-emerald-500" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </button>
          )}
          
          <div className={cn(
            'prose prose-sm max-w-none relative z-10',
            isUser 
              ? 'text-foreground prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-code:text-foreground' 
              : 'text-foreground prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground',
            // Better table styling
            'prose-table:text-sm prose-table:border-collapse',
            'prose-th:border prose-th:border-border prose-th:bg-muted/70 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-th:font-semibold prose-th:text-foreground',
            'prose-td:border prose-td:border-border prose-td:px-3 prose-td:py-2 prose-td:text-foreground/90',
            'prose-tr:border-b prose-tr:border-border',
            // Better list styling
            'prose-ul:my-2 prose-ol:my-2 prose-li:text-foreground',
            'prose-li:my-1',
            // Better code styling
            'prose-code:text-xs prose-code:bg-muted/70 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-foreground prose-code:border prose-code:border-border',
            'prose-pre:bg-muted/80 prose-pre:border prose-pre:border-border prose-pre:text-foreground'
          )}>
            {isUser ? (
              <p className="whitespace-pre-wrap m-0 leading-relaxed font-medium tracking-wide">{message.content}</p>
            ) : (
              <>
                {extractedContent.text && (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      table: ({ ...props }) => (
                        <div className="overflow-x-auto my-4">
                          <table className="min-w-full divide-y divide-border" {...props} />
                        </div>
                      ),
                      th: ({ ...props }) => (
                        <th className="bg-muted/70 px-3 py-2 text-left text-xs font-semibold text-foreground border border-border" {...props} />
                      ),
                      td: ({ ...props }) => (
                        <td className="px-3 py-2 text-sm border border-border text-foreground/90" {...props} />
                      ),
                      h1: ({ ...props }) => (
                        <h1 className="text-2xl font-bold mt-6 mb-3 text-foreground border-b border-border/80 pb-2" {...props} />
                      ),
                      h2: ({ ...props }) => (
                        <h2 className="text-xl font-semibold mt-5 mb-2 text-foreground" {...props} />
                      ),
                      h3: ({ ...props }) => (
                        <h3 className="text-lg font-semibold mt-4 mb-2 text-foreground" {...props} />
                      ),
                      p: ({ ...props }) => (
                        <p className="mb-3 leading-relaxed text-foreground" {...props} />
                      ),
                      ul: ({ ...props }) => (
                        <ul className="list-disc list-outside ml-6 my-3 space-y-2 text-foreground marker:text-foreground" {...props} />
                      ),
                      ol: ({ ...props }) => (
                        <ol className="list-decimal list-outside ml-6 my-3 space-y-2 text-foreground marker:text-foreground marker:font-semibold" {...props} />
                      ),
                      li: ({ ...props }) => (
                        <li className="text-foreground leading-relaxed pl-1" {...props} />
                      ),
                      code: ({ inline, ...props }: React.ComponentPropsWithoutRef<'code'> & { inline?: boolean }) => 
                        inline ? (
                          <code className="bg-muted/80 px-2 py-0.5 rounded text-sm font-mono text-foreground border border-border shadow-inner" {...props} />
                        ) : (
                          <code className="block bg-muted/80 p-4 rounded-lg text-sm font-mono overflow-x-auto my-3 text-foreground border border-border shadow-lg shadow-teal-500/10" {...props} />
                        ),
                      pre: ({ ...props }) => (
                        <pre className="bg-muted/80 p-4 rounded-lg overflow-x-auto my-3 border border-border shadow-lg shadow-teal-500/10" {...props} />
                      ),
                      blockquote: ({ ...props }) => (
                        <blockquote className="border-l-4 border-teal-500 pl-4 italic my-3 text-foreground bg-teal-500/10 py-2 rounded-r backdrop-blur-sm" {...props} />
                      ),
                      hr: ({ ...props }) => (
                        <hr className="my-4 border-border" {...props} />
                      ),
                      strong: ({ ...props }) => (
                        <strong className="font-semibold text-foreground" {...props} />
                      ),
                      em: ({ ...props }) => (
                        <em className="italic text-foreground/80" {...props} />
                      ),
                      a: ({ ...props }) => (
                        <a className="text-foreground underline underline-offset-2" {...props} />
                      ),
                    }}
                  >
                    {extractedContent.text}
                  </ReactMarkdown>
                )}
                {extractedContent.diagrams.map((diagramXml, idx) => (
                  <DrawioDiagram key={idx} xml={diagramXml} title="Generated diagram" />
                ))}
              </>
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
                    ? "text-foreground bg-muted/70 border-border/60"
                    : "text-foreground bg-muted/70 border-border/60"
                )}>
                  {message.mode === 'think' ? <Brain className="h-3 w-3" /> : <Zap className="h-3 w-3" />}
                  {message.mode === 'think' ? 'Think' : 'Fast'}
                </div>
              )}

              {/* Confidence badge */}
              {showConfidence && message.confidence_score !== undefined && (
                <div className="text-xs font-semibold text-foreground bg-muted/70 px-3 py-1 rounded-full border border-border/60 shadow-lg backdrop-blur-sm">
                  Confidence: {Math.round(message.confidence_score)}%
                </div>
              )}

              {/* Reasoning badge (think mode) */}
              {message.reasoning && (
                <button
                  type="button"
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="text-xs font-semibold text-foreground bg-muted/70 px-3 py-1 rounded-full border border-border/60 shadow-lg backdrop-blur-sm hover:border-border transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
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
                  className="text-xs font-semibold text-foreground bg-muted/70 px-3 py-1 rounded-full border border-border/60 shadow-lg backdrop-blur-sm hover:border-border transition-all duration-200 flex items-center gap-1.5 cursor-pointer"
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
                <div className="bg-primary/10 border border-primary/20 rounded-lg p-4 text-xs backdrop-blur-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="h-4 w-4 text-primary" />
                    <span className="font-semibold text-primary">Reasoning Steps</span>
                  </div>
                  <div className="text-foreground/80 leading-relaxed whitespace-pre-wrap prose prose-sm max-w-none">
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
                    className="bg-card/80 border border-border/70 rounded-lg p-3 text-xs backdrop-blur-sm hover:border-secondary/40 transition-all duration-200"
                  >
                    <div className="flex items-start gap-2">
                      <FileText className="h-4 w-4 text-secondary flex-shrink-0 mt-0.5" />
                      <div className="flex-1 space-y-1">
                        <div className="font-semibold text-foreground">
                          {source.document}
                          {source.page && (
                            <span className="text-muted-foreground font-normal ml-1">
                              (Page {source.page})
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <span className="px-2 py-0.5 bg-secondary/10 border border-secondary/20 rounded text-secondary font-medium">
                            {Math.round(source.relevance_score * 100)}% relevance
                          </span>
                        </div>
                        {source.text_snippet && (
                          <div className="text-foreground/80 leading-relaxed mt-1 pt-2 border-t border-border/60">
                            &quot;{source.text_snippet}&quot;
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
        <div className="flex h-11 w-11 shrink-0 select-none items-center justify-center rounded-2xl logo-mark shadow-xl ring-2 ring-foreground/10 hover:shadow-2xl transition-all duration-300">
          <User className="h-5 w-5 text-primary-foreground" />
        </div>
      )}
    </div>
  );
}
