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
import { ModeSelector } from './ModeSelector';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, ListPlus, Sparkles, ShieldCheck } from 'lucide-react';
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
import type { SourceReference, Message, ChatResponse, DocumentInfo, RAGMode } from '@/lib/types';
import { apiClient } from '@/lib/api';

interface ChatInterfaceProps {
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (
    query: string, 
    contextDocumentIds?: string[],
    contextFiles?: { id: string; filename: string }[],
    mode?: RAGMode,
  ) => Promise<ChatResponse | undefined>;
}

export function ChatInterface({ 
  sessionId, 
  messages, 
  isLoading, 
  error, 
  sendMessage 
}: ChatInterfaceProps) {
  const [latestSources, setLatestSources] = useState<SourceReference[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<DocumentInfo[]>([]);
  const [mode, setMode] = useState<RAGMode>('fast');
  const modeTouchedRef = useRef(false);
  const [inputValue, setInputValue] = useState('');
  const [promptSuggestions, setPromptSuggestions] = useState<Array<{ title: string; prompt: string }>>([]);
  const [servicesHealthy, setServicesHealthy] = useState(true);
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
    setSelectedFiles(prev => {
      const exists = prev.find(f => f.id === file.id);
      if (exists) {
        return prev.filter(f => f.id !== file.id);
      } else {
        return [...prev, file];
      }
    });
  };

  const handleClearAll = () => {
    setSelectedFiles([]);
  };

  const handleSend = async (message: string) => {
    try {
      // Pass selected file IDs as context
      const contextIds = selectedFiles.length > 0 
        ? selectedFiles.map(f => f.id) 
        : undefined;
      
      // Pass context files for display in message
      const contextFilesInfo = selectedFiles.length > 0
        ? selectedFiles.map(f => ({ id: f.id, filename: f.filename }))
        : undefined;
      
      const response = await sendMessage(message, contextIds, contextFilesInfo, mode);
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

  return (
    <Card className="relative flex h-full flex-col overflow-hidden border-none bg-transparent shadow-none">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(520px_circle_at_12%_-8%,hsl(var(--chart-1)/0.18),transparent_60%),radial-gradient(560px_circle_at_88%_110%,hsl(var(--chart-2)/0.16),transparent_62%)]" />

      <div className="relative z-10 flex flex-wrap items-center justify-between gap-3 px-4 pt-4">
        <div className="flex items-center gap-2">
          <Badge className="rounded-full bg-foreground text-background px-3 py-1 text-[10px] uppercase tracking-[0.24em]">
            RAG Chat
          </Badge>
          <Badge
            variant="outline"
            className="rounded-full border-border/70 bg-card/70 px-3 py-1 text-[10px] uppercase tracking-[0.2em]"
          >
            <ShieldCheck className="mr-1.5 h-3 w-3" />
            Retrieval + Reasoning
          </Badge>
        </div>
        <div className="text-xs text-muted-foreground">
          {selectedFiles.length > 0
            ? `${selectedFiles.length} context file${selectedFiles.length !== 1 ? 's' : ''} active`
            : 'No context files selected'}
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
            {/* Quick File Selector - Shows last 5 files, upload, and query options */}
            <QuickFileSelector
              selectedFiles={selectedFiles}
              onFileToggle={handleFileToggle}
              onClearAll={handleClearAll}
            />
            
            <div className="flex items-end gap-3">
              <ModeSelector
                mode={mode}
                onModeChange={(nextMode) => {
                  modeTouchedRef.current = true;
                  setMode(nextMode);
                }}
                disabled={isLoading}
              />
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
              <div className="flex-1">
                <MessageInput
                  onSend={handleSend}
                  disabled={isLoading || !servicesHealthy}
                  value={inputValue}
                  onChange={setInputValue}
                  placeholder={
                    mode === 'think'
                      ? selectedFiles.length > 0
                        ? `Think deeply about ${selectedFiles.length} file${selectedFiles.length !== 1 ? 's' : ''}...`
                        : "Ask a complex question (Think mode)..."
                      : selectedFiles.length > 0
                        ? `Ask about ${selectedFiles.length} selected file${selectedFiles.length !== 1 ? 's' : ''}...`
                        : "Ask a question about your documents..."
                  }
                />
              </div>
            </div>
            <div className="flex items-center justify-between px-1 pt-1 text-[11px] text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <Sparkles className="h-3 w-3" />
                Prompt library available anytime from the `+` button.
              </span>
              <span>Shift+Enter for newline</span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
