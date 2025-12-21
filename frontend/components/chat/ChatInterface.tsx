/**
 * ChatInterface - Main chat interface component
 */

'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { QuickFileSelector } from './QuickFileSelector';
import { apiClient } from '@/lib/api';
import type { SourceReference, Message, ChatResponse, DocumentInfo } from '@/lib/types';

interface ChatInterfaceProps {
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (
    query: string, 
    contextDocumentIds?: string[],
    contextFiles?: { id: string; filename: string }[]
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
  const [servicesHealthy, setServicesHealthy] = useState(true);

  // Check service health
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await apiClient.checkHealth();
        const isHealthy = health.status === 'healthy' || health.status === 'degraded';
        setServicesHealthy(isHealthy);
      } catch (err) {
        setServicesHealthy(false);
      }
    };

    checkHealth();
    const healthInterval = setInterval(checkHealth, 30000);
    return () => clearInterval(healthInterval);
  }, []);

  // Debug: Log when messages or sessionId changes
  useEffect(() => {
    console.log('[ChatInterface] State updated:', {
      sessionId,
      messageCount: messages.length,
      messages: messages.map(m => ({ role: m.role, contentPreview: m.content.slice(0, 50) }))
    });
  }, [sessionId, messages]);

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
      
      const response = await sendMessage(message, contextIds, contextFilesInfo);
      if (response && response.sources) {
        setLatestSources(response.sources);
      }
    } catch (err) {
      console.error('Failed to send message:', err);
    }
  };

  return (
    <Card className="flex h-full flex-col overflow-hidden border-none shadow-none bg-transparent">

      {error && (
        <Alert variant="destructive" className="m-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="flex-1 overflow-hidden relative">
        <MessageList
          key={`messages-${sessionId}`}
          messages={messages}
          isLoading={isLoading}
          latestSources={latestSources}
        />
      </div>

      <div className="relative p-4 bg-muted/10 border-t space-y-3">
        {/* Quick File Selector - Shows last 5 files, upload, and query options */}
        <QuickFileSelector
          selectedFiles={selectedFiles}
          onFileToggle={handleFileToggle}
          onClearAll={handleClearAll}
        />
        
        <MessageInput
          onSend={handleSend}
          disabled={isLoading || !servicesHealthy}
          placeholder={
            selectedFiles.length > 0
              ? `Ask about ${selectedFiles.length} selected file${selectedFiles.length !== 1 ? 's' : ''}...`
              : "Ask a question about your documents..."
          }
        />
      </div>
    </Card>
  );
}
