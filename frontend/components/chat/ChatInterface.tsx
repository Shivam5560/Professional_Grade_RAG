/**
 * ChatInterface - Main chat interface component
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertCircle,
  Files,
  ListPlus,
  Zap,
  Brain,
  MessageCircle,
  ChevronDown,
} from 'lucide-react';
import { QuickFileSelector } from './QuickFileSelector';
import { useToast } from '@/hooks/useToast';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { SourceReference, Message, ChatResponse, DocumentInfo, RAGMode, AskFileContent, TokenUsage } from '@/lib/types';
import { apiClient } from '@/lib/api';

interface ChatInterfaceProps {
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  tokenUsage?: TokenUsage;
  sendMessage: (
    query: string, 
    contextDocumentIds?: string[],
    contextFiles?: { id: string; filename: string }[],
    mode?: RAGMode,
    askFiles?: AskFileContent[],
  ) => Promise<ChatResponse | undefined>;
}

export function ChatInterface({ 
  sessionId, 
  messages, 
  isLoading, 
  error, 
  tokenUsage,
  sendMessage 
}: ChatInterfaceProps) {
  const [latestSources, setLatestSources] = useState<SourceReference[]>([]);
  const [selectedRagFiles, setSelectedRagFiles] = useState<DocumentInfo[]>([]);
  const [askFiles, setAskFiles] = useState<AskFileContent[]>([]);
  const [selectedAskFileIds, setSelectedAskFileIds] = useState<string[]>([]);
  const [mode, setMode] = useState<RAGMode>('fast');
  const modeTouchedRef = useRef(false);
  const [inputValue, setInputValue] = useState('');
  const [promptSuggestions, setPromptSuggestions] = useState<Array<{ title: string; prompt: string }>>([]);
  const [servicesHealthy, setServicesHealthy] = useState(true);
  const [isAskUploading, setIsAskUploading] = useState(false);
  const [, setIsRagUploading] = useState(false);
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const ping = await apiClient.pingServices();
        const unhealthy = (ping.summary?.unhealthy ?? 0) > 0;
        if (unhealthy && !modeTouchedRef.current && mode === 'fast') {
          setMode('think');
        }
        setServicesHealthy(ping.status !== 'unhealthy');
      } catch (err) {
        console.warn('[ChatInterface] Health check failed:', err);
        if (!modeTouchedRef.current && mode === 'fast') {
          setMode('think');
        }
        setServicesHealthy(false);
      }
    };

    checkHealth();
  }, [mode]);

  useEffect(() => {
    const loadPrompts = async () => {
      try {
        const response = await fetch('/prompts.md');
        if (!response.ok) {
          throw new Error('Failed to load prompts');
        }
        const text = await response.text();
        // Expected formats:
        // - Title: Prompt (colons allowed inside prompt)
        // - Single line prompt
        const parsed = text
          .split('\n')
          .map((line) => line.trim())
          .filter((line) => line.startsWith('- '))
          .map((line) => line.replace(/^\-\s*/, ''))
          .map((line) => {
            const trimmed = line.trim();
            if (!trimmed) return null;
            const splitIndex = trimmed.indexOf(':');
            if (splitIndex === -1) {
              return { title: trimmed, prompt: trimmed };
            }
            const title = trimmed.slice(0, splitIndex).trim();
            const prompt = trimmed.slice(splitIndex + 1).trim();
            if (!title || !prompt) return null;
            return { title, prompt };
          })
          .filter((item): item is { title: string; prompt: string } => Boolean(item && item.title && item.prompt));

        if (parsed.length > 0) {
          setPromptSuggestions(parsed);
        } else {
          throw new Error('No valid prompts found');
        }
      } catch (err) {
        console.warn('[ChatInterface] Using fallback prompts:', err);
        setPromptSuggestions([
          { title: 'Summarize a document', prompt: 'Summarize the key points from the attached document in 5 bullets.' },
          { title: 'Compare two files', prompt: 'Compare these two documents. Highlight differences and key overlaps.' },
          { title: 'Draft an executive brief', prompt: 'Create an executive brief with highlights, risks, and next steps.' },
        ]);
      }
    };

    loadPrompts();
  }, []);

  const handleFileToggle = (file: DocumentInfo) => {
    setSelectedRagFiles(prev => {
      const exists = prev.find(f => f.id === file.id);
      if (exists) {
        return prev.filter(f => f.id !== file.id);
      } else {
        return [...prev, file];
      }
    });
  };

  const handleClearAll = () => {
    setSelectedRagFiles([]);
  };

  const handleAskToggle = (fileId: string) => {
    setSelectedAskFileIds((prev) => (
      prev.includes(fileId) ? prev.filter((id) => id !== fileId) : [...prev, fileId]
    ));
  };

  const handleAskUploadFromSelector = async (file: File) => {
    setIsAskUploading(true);
    try {
      const extracted = await apiClient.extractFileForAskMode(file);
      setAskFiles((prev) => [extracted, ...prev.filter((item) => item.id !== extracted.id)].slice(0, 8));
      setSelectedAskFileIds((prev) => [...prev, extracted.id]);
      toast({ title: 'File ready', description: `${file.name} extracted for Ask mode.` });
    } catch (uploadErr) {
      toast({
        title: 'Ask upload failed',
        description: uploadErr instanceof Error ? uploadErr.message : 'Could not extract file text',
        variant: 'destructive',
      });
    } finally {
      setIsAskUploading(false);
    }
  };

  const handleSend = async (message: string) => {
    try {
      const contextIds = mode === 'ask'
        ? undefined
        : selectedRagFiles.length > 0
          ? selectedRagFiles.map((f) => f.id)
          : undefined;

      const contextFilesInfo = mode === 'ask'
        ? askFiles
            .filter((file) => selectedAskFileIds.includes(file.id))
            .map((file) => ({ id: file.id, filename: file.filename }))
        : selectedRagFiles.length > 0
          ? selectedRagFiles.map((f) => ({ id: f.id, filename: f.filename }))
          : undefined;

      const askFilesPayload = mode === 'ask'
        ? askFiles.filter((file) => selectedAskFileIds.includes(file.id))
        : undefined;

      const response = await sendMessage(message, contextIds, contextFilesInfo, mode, askFilesPayload);
      if (response && response.sources) {
        setLatestSources(response.sources);
        // Keep the global service indicator in sync after a successful request.
        setServicesHealthy(true);
        window.dispatchEvent(new CustomEvent('llm-health-update', { detail: { healthy: true } }));
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      toast({ title: 'Message failed', description: err instanceof Error ? err.message : 'Could not send message', variant: 'destructive' });
      // Keep the global service indicator in sync after a failed request.
      setServicesHealthy(false);
      window.dispatchEvent(new CustomEvent('llm-health-update', { detail: { healthy: false } }));
    }
  };

  const handlePromptSelect = (prompt: string) => {
    setInputValue((previous) => {
      const trimmedPrevious = previous.trim();
      if (!trimmedPrevious) {
        return prompt;
      }
      return `${trimmedPrevious}\n${prompt}`;
    });
  };

  const activeContextCount = mode === 'ask' ? selectedAskFileIds.length : selectedRagFiles.length;
  const usagePct = Math.max(0, Math.min(100, tokenUsage?.context_utilization_pct ?? 0));
  const usageDeg = usagePct * 3.6;
  const usageTier = usagePct >= 85 ? 'high' : usagePct >= 70 ? 'medium' : 'low';
  const usageColor = usageTier === 'high'
    ? 'hsl(var(--destructive))'
    : usageTier === 'medium'
      ? 'hsl(var(--chart-4))'
      : 'hsl(var(--chart-2))';
  const modeMeta = mode === 'think'
    ? {
        title: 'Think Mode',
        icon: Brain,
      }
    : mode === 'ask'
      ? {
          title: 'Ask Mode',
          icon: MessageCircle,
        }
      : {
          title: 'Fast Mode',
          icon: Zap,
        };

  const ModeIcon = modeMeta.icon;

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden bg-workspace-raised">
      {error && (
        <Alert variant="destructive" className="m-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="relative z-10 min-h-0 flex-1 overflow-hidden">
        <MessageList
          key={`messages-${sessionId}`}
          messages={messages}
          isLoading={isLoading}
          latestSources={latestSources}
          promptSuggestions={promptSuggestions}
          onPromptSelect={handlePromptSelect}
        />
      </div>

      <div data-fixed-composer="knowledge" data-testid="knowledge-composer" className="z-20 shrink-0 border-t border-border/60 bg-workspace-raised px-3 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:px-4 md:pb-3">
          <div className="mx-auto w-full max-w-4xl">
            <div className="flex items-end gap-3">
              <div className="mb-1 flex items-center gap-1.5">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      disabled={isLoading}
                      className="h-11 w-11 rounded-md border-border/70 bg-workspace-inset hover:bg-muted"
                      title="Select chat mode"
                      aria-label="Select chat mode"
                    >
                      <ModeIcon className="h-5 w-5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-56">
                    <DropdownMenuLabel>Chat Mode</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onSelect={() => {
                        modeTouchedRef.current = true;
                        setMode('fast');
                      }}
                      className="cursor-pointer"
                    >
                      <Zap className="mr-2 h-4 w-4" />
                      Fast
                      {mode === 'fast' && <ChevronDown className="ml-auto h-4 w-4 -rotate-90" />}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onSelect={() => {
                        modeTouchedRef.current = true;
                        setMode('think');
                      }}
                      className="cursor-pointer"
                    >
                      <Brain className="mr-2 h-4 w-4" />
                      Think
                      {mode === 'think' && <ChevronDown className="ml-auto h-4 w-4 -rotate-90" />}
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onSelect={() => {
                        modeTouchedRef.current = true;
                        setMode('ask');
                      }}
                      className="cursor-pointer"
                    >
                      <MessageCircle className="mr-2 h-4 w-4" />
                      Ask
                      {mode === 'ask' && <ChevronDown className="ml-auto h-4 w-4 -rotate-90" />}
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      className="relative h-11 w-11 rounded-md border-border/70 bg-workspace-inset hover:bg-muted"
                      title="Conversation files"
                      aria-label="Conversation files"
                    >
                      <Files className="h-4 w-4" />
                      {activeContextCount > 0 ? (
                        <span className="absolute -right-1 -top-1 grid h-5 min-w-5 place-items-center rounded-full bg-foreground px-1 text-[10px] text-background">
                          {activeContextCount}
                        </span>
                      ) : null}
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-[min(22rem,calc(100vw-2rem))] p-3">
                    <DropdownMenuLabel>Conversation files</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <QuickFileSelector
                      mode={mode}
                      selectedFiles={selectedRagFiles}
                      onFileToggle={handleFileToggle}
                      onClearAll={handleClearAll}
                      askFiles={askFiles}
                      selectedAskFileIds={selectedAskFileIds}
                      onAskFileToggle={handleAskToggle}
                      onAskUpload={handleAskUploadFromSelector}
                      isAskUploading={isAskUploading}
                      fileInputRef={uploadInputRef}
                      onUploadingChange={setIsRagUploading}
                    />
                  </DropdownMenuContent>
                </DropdownMenu>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      disabled={isLoading || promptSuggestions.length === 0}
                      className="h-11 w-11 rounded-md border-border/70 bg-workspace-inset hover:bg-muted"
                      title="Insert a saved prompt"
                      aria-label="Insert a saved prompt"
                    >
                      <ListPlus className="h-5 w-5" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-80 max-h-[300px] overflow-y-auto">
                    <DropdownMenuLabel>Prompt Library</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    {promptSuggestions.length > 0 ? (
                      promptSuggestions.map((item) => (
                        <DropdownMenuItem
                          key={item.title}
                          onSelect={() => handlePromptSelect(item.prompt)}
                          className="cursor-pointer"
                        >
                          {item.title}
                        </DropdownMenuItem>
                      ))
                    ) : (
                      <DropdownMenuItem disabled>No prompts available</DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="flex-1">
                <MessageInput
                  onSend={handleSend}
                  disabled={isLoading || !servicesHealthy || (mode === 'ask' && isAskUploading)}
                  isSending={isLoading}
                  value={inputValue}
                  onChange={setInputValue}
                  placeholder={
                    mode === 'think'
                      ? selectedRagFiles.length > 0
                        ? `Think deeply about ${selectedRagFiles.length} file${selectedRagFiles.length !== 1 ? 's' : ''}...`
                        : "Ask a complex question (Think mode)..."
                      : mode === 'ask'
                        ? selectedAskFileIds.length > 0
                          ? `Ask directly with ${selectedAskFileIds.length} extracted file${selectedAskFileIds.length !== 1 ? 's' : ''}...`
                          : 'Ask anything (direct mode, no retrieval)...'
                      : selectedRagFiles.length > 0
                        ? `Ask about ${selectedRagFiles.length} selected file${selectedRagFiles.length !== 1 ? 's' : ''}...`
                        : "Ask a question about your documents..."
                  }
                />
              </div>
            </div>
            <div className="flex items-center justify-end px-1 pt-2 text-[11px] text-muted-foreground">
              <span className="inline-flex items-center gap-2">
                {tokenUsage && (
                  <span className="relative inline-flex items-center group">
                    <span
                      className="inline-flex h-6 w-6 items-center justify-center rounded-full border border-border/70"
                      style={{
                        background: `conic-gradient(${usageColor} ${usageDeg}deg, hsl(var(--muted)) ${usageDeg}deg 360deg)`,
                      }}
                      aria-label="Context window usage"
                    >
                      <span className="h-3 w-3 rounded-full bg-background" />
                    </span>
                    <span className="pointer-events-none absolute bottom-8 right-0 z-30 hidden w-60 rounded-lg border border-border/70 bg-overlay p-2 text-[10px] text-foreground shadow-xl group-hover:block">
                      <div className="font-semibold">Context Window</div>
                      <div>{tokenUsage.context_tokens_used.toLocaleString()} / {tokenUsage.context_tokens_max.toLocaleString()} tokens ({usagePct.toFixed(1)}%)</div>
                      <div>
                        Status:{' '}
                        {usageTier === 'high' ? 'High usage' : usageTier === 'medium' ? 'Watch usage' : 'Healthy'}
                      </div>
                      {tokenUsage.compaction_applied && <div>Compaction: applied</div>}
                      {tokenUsage.near_limit && <div className="text-destructive">Near limit: yes</div>}
                    </span>
                  </span>
                )}
                <span>
                  {mode === 'ask' && isAskUploading
                    ? 'Extracting…'
                    : isLoading
                      ? 'Streaming…'
                      : 'Shift+Enter for newline'}
                </span>
              </span>
            </div>
          </div>
      </div>
    </div>
  );
}
