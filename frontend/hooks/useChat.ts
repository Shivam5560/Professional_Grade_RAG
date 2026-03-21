/**
 * Custom React hook for managing chat state and interactions.
 */

import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { apiClient } from '@/lib/api';
import { Message, ChatResponse, RAGMode, AskFileContent } from '@/lib/types';
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
    mode?: RAGMode,
    askFiles?: AskFileContent[],
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
    const assistantMessageId = uuidv4();
    const assistantPlaceholder: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
      mode: mode,
      isTyping: true,
    };
    setMessages(prev => [...prev, userMessage, assistantPlaceholder]);

    try {
      const response: ChatResponse = await apiClient.queryStream({
        query,
        session_id: sessionId,
        user_id: user?.id,
        context_document_ids: contextDocumentIds,
        context_files: contextFiles,
        ask_files: askFiles,
        mode: mode,
        stream: true,
      }, (event, data) => {
        if (event === 'token') {
          const token = (data as { token?: string })?.token ?? '';
          if (!token) return;
          setMessages((prev) => prev.map((msg) => (
            msg.id === assistantMessageId
              ? { ...msg, content: `${msg.content}${token}`, isTyping: true }
              : msg
          )));
          return;
        }

        if (event === 'final') {
          const finalData = data as ChatResponse;
          setMessages((prev) => prev.map((msg) => (
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: finalData.answer,
                  confidence_score: finalData.confidence_score,
                  reasoning: finalData.reasoning,
                  sources: finalData.sources,
                  mode: finalData.mode,
                  diagramXml: finalData.diagram_xml,
                  isTyping: false,
                }
              : msg
          )));
        }
      });

      if (user?.id) {
        window.dispatchEvent(
          new CustomEvent('chat-history-updated', {
            detail: { userId: user.id, sessionId: response.session_id },
          })
        );
      }
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id && msg.id !== assistantMessageId));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, user]);

  const clearChat = useCallback(async () => {
    try {
      // Generate a new session ID FIRST
      const newSessionId = uuidv4();
      
      // Clear backend history for old session
      await apiClient.clearHistory(sessionId);
      
      // Force state reset - use functional updates to ensure fresh state
      setMessages(() => []);
      setError(() => null);
      setSessionId(() => newSessionId);
      
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
