/**
 * ChatInterface - Main chat interface component
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  AlertCircle,
  ListPlus,
  Sparkles,
  ShieldCheck,
  Zap,
  Brain,
  MessageCircle,
  Activity,
  Wrench,
  ChevronDown,
  Plus,
  Loader2,
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
  const [isRagUploading, setIsRagUploading] = useState(false);
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
        // Chat request succeeded - mark services as healthy and notify Header
        setServicesHealthy(true);
        window.dispatchEvent(new CustomEvent('llm-health-update', { detail: { healthy: true } }));
      }
    } catch (err) {
      console.error('Failed to send message:', err);
      toast({ title: 'Message failed', description: err instanceof Error ? err.message : 'Could not send message', variant: 'destructive' });
      // Chat request failed - mark services as unhealthy and notify Header
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
        subtitle: 'Deep reasoning with PageIndex traversal',
        icon: Brain,
        tone: 'from-[hsl(var(--chart-3))] to-[hsl(var(--chart-4))]',
      }
    : mode === 'ask'
      ? {
          title: 'Ask Mode',
          subtitle: 'Direct LLM responses (no retrieval)',
          icon: MessageCircle,
          tone: 'from-[hsl(var(--chart-5))] to-[hsl(var(--chart-4))]',
        }
      : {
          title: 'Fast Mode',
          subtitle: 'Hybrid retrieval with reranking',
          icon: Zap,
          tone: 'from-[hsl(var(--chart-2))] to-[hsl(var(--chart-1))]',
        };

  const ModeIcon = modeMeta.icon;

  return (
    <Card className="relative flex h-full flex-col overflow-hidden border-none bg-transparent shadow-none">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(520px_circle_at_12%_-8%,hsl(var(--chart-1)/0.18),transparent_60%),radial-gradient(560px_circle_at_88%_110%,hsl(var(--chart-2)/0.16),transparent_62%)]" />

      <div className="relative z-10 flex flex-wrap items-center justify-between gap-3 px-4 pt-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge className="rounded-full bg-foreground text-background px-3 py-1 text-[10px] uppercase tracking-[0.24em]">
            {mode === 'ask' ? 'Ask Chat' : 'RAG Chat'}
          </Badge>
          <Badge
            className={`rounded-full bg-gradient-to-r ${modeMeta.tone} text-white px-3 py-1 text-[10px] uppercase tracking-[0.2em] border-transparent`}
          >
            <ModeIcon className="mr-1.5 h-3 w-3" />
            {modeMeta.title}
          </Badge>
          <Badge
            variant="outline"
            className="rounded-full border-border/70 bg-card/70 px-3 py-1 text-[10px] uppercase tracking-[0.2em]"
          >
            <ShieldCheck className="mr-1.5 h-3 w-3" />
            {mode === 'ask' ? 'Direct LLM' : 'Retrieval + Reasoning'}
          </Badge>
        </div>
        <div className="text-xs text-muted-foreground inline-flex items-center gap-1.5">
          <Activity className={`h-3.5 w-3.5 ${servicesHealthy ? 'text-emerald-400' : 'text-red-400'}`} />
          {activeContextCount > 0
            ? `${activeContextCount} context file${activeContextCount !== 1 ? 's' : ''} active`
            : 'No context files selected'}
        </div>
      </div>

      <div className="relative z-10 px-4 pt-3">
        <div className="rounded-2xl border border-border/60 bg-card/55 px-4 py-3 backdrop-blur-sm flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-foreground">{modeMeta.title}</p>
            <p className="text-xs text-muted-foreground">{modeMeta.subtitle}</p>
          </div>
          {mode === 'ask' && (
            <Badge variant="outline" className="border-border/70 text-[10px] uppercase tracking-[0.18em]">
              In-memory files only
            </Badge>
          )}
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="m-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="relative z-10 flex-1 overflow-hidden min-h-0">
        <MessageList
          key={`messages-${sessionId}`}
          messages={messages}
          isLoading={isLoading}
          latestSources={latestSources}
          promptSuggestions={promptSuggestions}
          onPromptSelect={handlePromptSelect}
        />
      </div>

      <div className="sticky bottom-0 z-20">
        <div className="bg-gradient-to-t from-background/95 via-background/85 to-transparent px-4 pt-6 pb-4">
          <div className="mx-auto w-full max-w-4xl rounded-3xl border border-border/70 bg-card/80 p-4 shadow-[0_32px_90px_-60px_rgba(0,0,0,0.55)] backdrop-blur-xl space-y-3">
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
              showUploadButton={false}
              fileInputRef={uploadInputRef}
              onUploadingChange={setIsRagUploading}
            />
            
            <div className="space-y-2">
              <div className="flex items-center gap-2 flex-wrap">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      disabled={isLoading}
                      className="h-10 w-10 rounded-xl border-border/70 bg-muted/70 hover:bg-background/90"
                      title="Select chat mode"
                      aria-label="Select chat mode"
                    >
                      <ModeIcon className="h-4 w-4" />
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
                      className="h-10 w-10 rounded-xl border-border/70 bg-muted/70"
                      title="MCP tools"
                      aria-label="MCP tools"
                    >
                      <Wrench className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-80">
                    <DropdownMenuLabel>Developer MCP Tools</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem disabled>🩺 health_check · backend health</DropdownMenuItem>
                    <DropdownMenuItem disabled>💬 chat_query · fast/think/ask</DropdownMenuItem>
                    <DropdownMenuItem disabled>📚 list_user_documents · user docs</DropdownMenuItem>
                    <DropdownMenuItem disabled>🧭 list_tools_catalog · tool catalog</DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => uploadInputRef.current?.click()}
                  disabled={
                    isLoading ||
                    !servicesHealthy ||
                    (mode === 'ask' ? isAskUploading : isRagUploading)
                  }
                  className="h-10 w-10 rounded-xl border-border/70 bg-muted/70 hover:bg-background/90"
                  title={mode === 'ask' ? 'Add ask file' : 'Upload file'}
                  aria-label={mode === 'ask' ? 'Add ask file' : 'Upload file'}
                >
                  {mode === 'ask' ? (
                    isAskUploading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Plus className="h-4 w-4" />
                    )
                  ) : isRagUploading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4" />
                  )}
                </Button>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      disabled={isLoading || promptSuggestions.length === 0}
                      className="h-10 w-10 rounded-xl border-border/70 bg-muted/70 hover:bg-background/90"
                      title="Insert a saved prompt"
                      aria-label="Insert a saved prompt"
                    >
                      <ListPlus className="h-4 w-4" />
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

              <div className="flex items-end gap-3">
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
            </div>
            <div className="flex items-center justify-between px-1 pt-1 text-[11px] text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <Sparkles className="h-3 w-3" />
                Use the prompt button to insert saved prompts.
              </span>
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
                    <span className="pointer-events-none absolute bottom-8 right-0 z-30 hidden w-60 rounded-lg border border-border/70 bg-card/95 p-2 text-[10px] text-foreground shadow-xl group-hover:block">
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
    </Card>
  );
}
