/**
 * ChatInterface - Main chat interface component
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import { Card } from '@/components/ui/card';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { ModeSelector } from './ModeSelector';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { QuickFileSelector } from './QuickFileSelector';
import { useToast } from '@/hooks/useToast';
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
  }, []);

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

  return (
    <Card className="flex h-full flex-col overflow-hidden border-none bg-transparent shadow-none">
      <div className="flex flex-wrap items-center justify-end gap-2 px-4 pt-4">
      </div>

      {error && (
        <Alert variant="destructive" className="m-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex-1 overflow-hidden relative min-h-0">
        <MessageList
          key={`messages-${sessionId}`}
          messages={messages}
          isLoading={isLoading}
          latestSources={latestSources}
          promptSuggestions={promptSuggestions}
          onPromptSelect={(prompt) => setInputValue(prompt)}
        />
      </div>

      <div className="sticky bottom-0 z-20">
        <div className="bg-gradient-to-t from-background/95 via-background/80 to-transparent px-4 pt-6 pb-4">
          <div className="mx-auto w-full max-w-4xl glass-panel rounded-3xl p-4 space-y-3">
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
          </div>
        </div>
      </div>
    </Card>
  );
}
