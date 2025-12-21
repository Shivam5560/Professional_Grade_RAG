/**
 * Custom React hook for managing chat state and interactions.
 */

import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { apiClient } from '@/lib/api';
import { Message, ChatResponse } from '@/lib/types';
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
    contextFiles?: { id: string; filename: string }[]
  ) => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    // Add user message immediately with context files
    const userMessage: Message = {
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
      contextFiles: contextFiles,  // Store which files were used
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      // Send query to backend
      const response: ChatResponse = await apiClient.query({
        query,
        session_id: sessionId,
        user_id: user?.id, // Include user_id if user is logged in
        context_document_ids: contextDocumentIds,
      });

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        confidence_score: response.confidence_score,
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Store the full response for access to sources
      return response;

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Remove the user message if query failed
      setMessages(prev => prev.slice(0, -1));
      
      throw err;
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
      
      // Convert ChatMessage to Message format
      const convertedMessages: Message[] = history.messages.map(msg => ({
        ...msg,
        timestamp: msg.created_at,
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
