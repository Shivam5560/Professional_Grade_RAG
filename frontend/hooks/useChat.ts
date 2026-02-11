/**
 * Custom React hook for managing chat state and interactions.
 */

import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { apiClient } from '@/lib/api';
import { Message, ChatResponse, RAGMode } from '@/lib/types';
import { useAuthStore } from '@/lib/store';

export function useChat(initialSessionId?: string) {
  const [sessionId, setSessionId] = useState<string>(initialSessionId || uuidv4());
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuthStore();

  const sendMessage = useCallback(async (
    query: string, 
    contextDocumentIds?: string[],
    contextFiles?: { id: string; filename: string }[],
    mode?: RAGMode
  ) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message immediately with context files
    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
      contextFiles: contextFiles,
      mode: mode,
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const assistantId = uuidv4();
      setMessages(prev => [
        ...prev,
        {
          id: assistantId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          isTyping: true,
          mode: mode,
        },
      ]);

      let finalResponse: ChatResponse | undefined;
      let streamError: Error | null = null;

      await apiClient.queryStream(
        {
          query,
          session_id: sessionId,
          user_id: user?.id,
          context_document_ids: contextDocumentIds,
          context_files: contextFiles,
          mode: mode,
          stream: true,
        },
        (event, data) => {
          if (event === 'token') {
            const token = (data as { token?: string })?.token ?? '';
            if (!token) return;
            setMessages(prev => prev.map(msg => (
              msg.id === assistantId
                ? { ...msg, content: msg.content + token }
                : msg
            )));
          }

          if (event === 'final') {
            const payload = data as ChatResponse & { diagram_xml?: string };
            finalResponse = payload;
            setMessages(prev => prev.map(msg => (
              msg.id === assistantId
                ? {
                    ...msg,
                    content: payload.answer,
                    confidence_score: payload.confidence_score,
                    sources: payload.sources,
                    reasoning: payload.reasoning,
                    mode: payload.mode,
                    diagramXml: payload.diagram_xml,
                    isTyping: false,
                  }
                : msg
            )));
          }

          if (event === 'error') {
            const message = (data as { message?: string })?.message || 'Streaming failed';
            streamError = new Error(message);
          }
        }
      );

      if (streamError) {
        throw streamError;
      }

      if (finalResponse) {
        if (user?.id) {
          window.dispatchEvent(
            new CustomEvent('chat-history-updated', {
              detail: { userId: user.id, sessionId: finalResponse.session_id },
            })
          );
        }
        return finalResponse;
      }

      return undefined;

    } catch (err) {
      try {
        // Remove the streaming placeholder if it exists
        setMessages(prev => prev.filter(msg => !msg.isTyping));

        const response: ChatResponse = await apiClient.query({
          query,
          session_id: sessionId,
          user_id: user?.id,
          context_document_ids: contextDocumentIds,
          context_files: contextFiles,
          mode: mode,
          stream: false,
        });

        const assistantMessage: Message = {
          id: uuidv4(),
          role: 'assistant',
          content: response.answer,
          timestamp: new Date().toISOString(),
          confidence_score: response.confidence_score,
          reasoning: response.reasoning,
          sources: response.sources,
          mode: response.mode,
          diagramXml: response.diagram_xml,
        };

        setMessages(prev => [...prev, assistantMessage]);
        if (user?.id) {
          window.dispatchEvent(
            new CustomEvent('chat-history-updated', {
              detail: { userId: user.id, sessionId: response.session_id },
            })
          );
        }
        return response;
      } catch (fallbackErr) {
        const errorMessage = fallbackErr instanceof Error ? fallbackErr.message : 'Failed to send message';
        setError(errorMessage);

        // Remove the user message if query failed
        setMessages(prev => prev.filter(msg => msg.role !== 'user' || msg.id !== userMessage.id));

        throw fallbackErr;
      }
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, user]);

  const clearChat = useCallback(async () => {
    try {
      console.log('[useChat] Clearing chat for session:', sessionId);
      
      // Generate a new session ID FIRST
      const newSessionId = uuidv4();
      console.log('[useChat] New session created:', newSessionId);
      
      // Clear backend history for old session
      await apiClient.clearHistory(sessionId);
      
      // Force state reset - use functional updates to ensure fresh state
      setMessages(() => []);
      setError(() => null);
      setSessionId(() => newSessionId);
      
      console.log('[useChat] State cleared successfully');
      return newSessionId;
    } catch (err) {
      console.error('[useChat] Failed to clear chat:', err);
      // Even if backend clear fails, still reset the UI
      const newSessionId = uuidv4();
      setMessages(() => []);
      setError(() => null);
      setSessionId(() => newSessionId);
      throw err;
    }
  }, [sessionId]);

  const loadHistory = useCallback(async (sessionIdToLoad?: string) => {
    try {
      const targetSessionId = sessionIdToLoad || sessionId;
      const history = await apiClient.getHistory(targetSessionId);
      
      // If loading a different session, update the session ID
      if (sessionIdToLoad && sessionIdToLoad !== sessionId) {
        setSessionId(sessionIdToLoad);
      }
      
      // Convert ChatMessage to Message format - use stable IDs based on index + sessionId
      const convertedMessages: Message[] = history.messages.map((msg, idx) => ({
        id: `${targetSessionId}-${idx}`,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || (msg as { created_at?: string }).created_at || new Date().toISOString(),
        confidence_score: msg.confidence_score,
        confidence_level: msg.confidence_level,
        sources: msg.sources,
        reasoning: msg.reasoning,
        mode: msg.mode,
        contextFiles: msg.context_files,
        diagramXml: msg.diagram_xml,
      }));
      
      setMessages(convertedMessages);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }, [sessionId]);

  return {
    sessionId,
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
    loadHistory,
  };
}
