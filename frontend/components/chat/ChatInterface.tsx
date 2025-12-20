/**
 * ChatInterface - Main chat interface component
 */

'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, X, CheckCircle, XCircle, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { DocumentUpload } from '../upload/DocumentUpload';
import { apiClient } from '@/lib/api';
import type { SourceReference, PingResponse, Message, ChatResponse } from '@/lib/types';

interface ChatInterfaceProps {
  sessionId: string;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (query: string) => Promise<ChatResponse | undefined>;
}

export function ChatInterface({ 
  sessionId, 
  messages, 
  isLoading, 
  error, 
  sendMessage 
}: ChatInterfaceProps) {
  const [latestSources, setLatestSources] = useState<SourceReference[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [servicesHealthy, setServicesHealthy] = useState(true);
  const [showServiceError, setShowServiceError] = useState(false);
  const [lastPingStatus, setLastPingStatus] = useState<PingResponse | null>(null);

  // Check service health periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await apiClient.checkHealth();
        const isHealthy = health.status === 'healthy' || health.status === 'degraded';
        setServicesHealthy(isHealthy);
        
        if (!isHealthy && !showServiceError) {
          setShowServiceError(true);
          setTimeout(() => setShowServiceError(false), 5000);
        }
      } catch (err) {
        console.error('[ChatInterface] Health check failed:', err);
        setServicesHealthy(false);
        if (!showServiceError) {
          setShowServiceError(true);
          setTimeout(() => setShowServiceError(false), 5000);
        }
      }
    };

    // Check immediately on mount
    checkHealth();

    // Check every 30 seconds
    const healthInterval = setInterval(checkHealth, 30000);

    return () => clearInterval(healthInterval);
  }, [showServiceError]);

  // Keep-alive: Ping services every 2 minutes to prevent idle timeout
  useEffect(() => {
    const pingInterval = setInterval(async () => {
      try {
        const pingResult = await apiClient.pingServices();
        setLastPingStatus(pingResult);
        
        const isHealthy = pingResult.status === 'healthy' || pingResult.status === 'degraded';
        setServicesHealthy(isHealthy);
        
        console.log('[ChatInterface] Services pinged:', {
          status: pingResult.status,
          healthy: pingResult.summary.healthy,
          unhealthy: pingResult.summary.unhealthy,
          services: Object.keys(pingResult.services)
        });
      } catch (err) {
        console.warn('[ChatInterface] Failed to ping services:', err);
        setServicesHealthy(false);
        setLastPingStatus(null);
      }
    }, 2 * 60 * 1000); // 2 minutes

    // Initial ping on mount
    apiClient.pingServices()
      .then(pingResult => {
        setLastPingStatus(pingResult);
        const isHealthy = pingResult.status === 'healthy' || pingResult.status === 'degraded';
        setServicesHealthy(isHealthy);
      })
      .catch(err => {
        console.warn('[ChatInterface] Initial ping failed:', err);
        setServicesHealthy(false);
      });

    return () => clearInterval(pingInterval);
  }, []);

  // Debug: Log when messages or sessionId changes
  useEffect(() => {
    console.log('[ChatInterface] State updated:', {
      sessionId,
      messageCount: messages.length,
      messages: messages.map(m => ({ role: m.role, contentPreview: m.content.slice(0, 50) }))
    });
  }, [sessionId, messages]);

  const handleSend = async (message: string) => {
    try {
      const response = await sendMessage(message);
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

      {showServiceError && !servicesHealthy && (
        <Alert variant="destructive" className="m-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Backend services are currently unavailable. Please check your connection and try again.
          </AlertDescription>
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

      <div className="relative p-4 bg-muted/10 border-t">
        {/* Individual Service Status Badges - Like cellular signal */}
        {lastPingStatus && (
          <div className="mb-3 flex items-center gap-2 flex-wrap">
            <span className="text-xs text-slate-400 font-medium mr-1">Services:</span>
            {/* Embedding Service */}
            {lastPingStatus.services.embedding && (
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${
                lastPingStatus.services.embedding.status === 'healthy' 
                  ? 'bg-green-500/10 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/10 text-red-400 border border-red-500/30'
              }`}>
                <div className={`h-1.5 w-1.5 rounded-full ${
                  lastPingStatus.services.embedding.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                }`} />
                <span>Embed</span>
              </div>
            )}
            {/* Reranker Service */}
            {lastPingStatus.services.reranker && (
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${
                lastPingStatus.services.reranker.status === 'healthy' 
                  ? 'bg-green-500/10 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/10 text-red-400 border border-red-500/30'
              }`}>
                <div className={`h-1.5 w-1.5 rounded-full ${
                  lastPingStatus.services.reranker.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                }`} />
                <span>Rerank</span>
              </div>
            )}
            {/* LLM Service */}
            {lastPingStatus.services.llm && (
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${
                lastPingStatus.services.llm.status === 'healthy' 
                  ? 'bg-green-500/10 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/10 text-red-400 border border-red-500/30'
              }`}>
                <div className={`h-1.5 w-1.5 rounded-full ${
                  lastPingStatus.services.llm.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                }`} />
                <span>LLM</span>
              </div>
            )}
            {/* Database Service */}
            {lastPingStatus.services.database && (
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${
                lastPingStatus.services.database.status === 'healthy' 
                  ? 'bg-green-500/10 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/10 text-red-400 border border-red-500/30'
              }`}>
                <div className={`h-1.5 w-1.5 rounded-full ${
                  lastPingStatus.services.database.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                }`} />
                <span>Database</span>
              </div>
            )}
            {/* BM25 Service */}
            {lastPingStatus.services.bm25 && (
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium ${
                lastPingStatus.services.bm25.status === 'healthy' 
                  ? 'bg-green-500/10 text-green-400 border border-green-500/30' 
                  : 'bg-red-500/10 text-red-400 border border-red-500/30'
              }`}>
                <div className={`h-1.5 w-1.5 rounded-full ${
                  lastPingStatus.services.bm25.status === 'healthy' ? 'bg-green-400' : 'bg-red-400'
                }`} />
                <span>BM25</span>
              </div>
            )}
          </div>
        )}
        
        {/* Service unavailable warning above input */}
        {!servicesHealthy && lastPingStatus && (
          <div className="mb-3 space-y-2">
            <div className="px-3 py-2 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-2 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span className="font-medium">Services unavailable - messages cannot be sent</span>
            </div>
            {/* Show unhealthy services */}
            {lastPingStatus.summary.unhealthy > 0 && (
              <div className="px-3 py-2 bg-muted/50 border rounded-lg text-xs space-y-1">
                <div className="font-medium text-muted-foreground mb-1">
                  Failed services ({lastPingStatus.summary.unhealthy}/{lastPingStatus.summary.total}):
                </div>
                {Object.entries(lastPingStatus.services).map(([name, service]) => 
                  service.status === 'unhealthy' && (
                    <div key={name} className="flex items-center gap-2 text-destructive">
                      <XCircle className="h-3 w-3" />
                      <span className="capitalize">{name}</span>
                      <span className="text-muted-foreground">({service.type})</span>
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        )}
        
        {/* Upload Overlay - Appears from bottom */}
        {showUpload && (
          <div className="absolute bottom-full left-0 right-0 bg-background border-t shadow-2xl animate-in slide-in-from-bottom duration-300 max-h-[500px] overflow-y-auto z-20">
            <div className="p-6 relative">
              <Button 
                variant="ghost" 
                size="icon" 
                className="absolute right-4 top-4 z-20"
                onClick={() => setShowUpload(false)}
              >
                <X className="h-4 w-4" />
              </Button>
              <DocumentUpload onUploadComplete={() => setShowUpload(false)} />
            </div>
          </div>
        )}
        
        <MessageInput
          onSend={handleSend}
          disabled={isLoading || !servicesHealthy}
          placeholder="Ask a question about your documents..."
          onUploadClick={() => setShowUpload(true)}
        />
      </div>
    </Card>
  );
}
