/**
 * Custom React hook for managing chat state and interactions.
 */

import { useState, useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { apiClient } from '@/lib/api';
import { Message, ChatResponse, RAGMode, AskFileContent, TokenUsage, ChatMessage } from '@/lib/types';
import { useAuthStore } from '@/lib/store';

export function useChat(initialSessionId?: string) {
  const [sessionId, setSessionId] = useState<string>(initialSessionId || uuidv4());
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestTokenUsage, setLatestTokenUsage] = useState<TokenUsage | undefined>(undefined);
  const { user } = useAuthStore();
  const tokenBufferRef = useRef<Record<string, string>>({});
  const flushTimerRef = useRef<Record<string, ReturnType<typeof setTimeout> | null>>({});

  const mapChatMessagesToUiMessages = useCallback((targetSessionId: string, historyMessages: ChatMessage[]): Message[] => {
    return historyMessages.map((msg, idx) => ({
      id: `${targetSessionId}-${idx}`,
      role: msg.role,
      content: msg.content,
      timestamp: msg.created_at || new Date().toISOString(),
      confidence_score: typeof msg.confidence_score === 'number' ? msg.confidence_score : msg.confidence_score?.score,
      confidence_level: typeof msg.confidence_score === 'object' ? msg.confidence_score?.level : undefined,
      sources: msg.sources,
      reasoning: msg.reasoning,
      mode: msg.mode,
      contextFiles: msg.context_files,
      diagramXml: msg.diagram_xml,
    }));
  }, []);

  const flushBufferedTokens = useCallback((assistantMessageId: string) => {
    const buffered = tokenBufferRef.current[assistantMessageId];
    if (!buffered) return;

    setMessages((prev) => prev.map((msg) => (
      msg.id === assistantMessageId
        ? { ...msg, content: `${msg.content}${buffered}`, isTyping: true }
        : msg
    )));

    tokenBufferRef.current[assistantMessageId] = '';
  }, []);

  const scheduleFlush = useCallback((assistantMessageId: string) => {
    if (flushTimerRef.current[assistantMessageId]) return;
    flushTimerRef.current[assistantMessageId] = setTimeout(() => {
      flushBufferedTokens(assistantMessageId);
      flushTimerRef.current[assistantMessageId] = null;
    }, 80);
  }, [flushBufferedTokens]);

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
          tokenBufferRef.current[assistantMessageId] = `${tokenBufferRef.current[assistantMessageId] ?? ''}${token}`;
          scheduleFlush(assistantMessageId);
          return;
        }

        if (event === 'final') {
          const finalData = data as ChatResponse;
          if (flushTimerRef.current[assistantMessageId]) {
            clearTimeout(flushTimerRef.current[assistantMessageId]!);
            flushTimerRef.current[assistantMessageId] = null;
          }
          flushBufferedTokens(assistantMessageId);

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
                  tokenUsage: finalData.token_usage,
                  isTyping: false,
                }
              : msg
          )));
          setLatestTokenUsage(finalData.token_usage);
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
      if (flushTimerRef.current[assistantMessageId]) {
        clearTimeout(flushTimerRef.current[assistantMessageId]!);
        flushTimerRef.current[assistantMessageId] = null;
      }
      tokenBufferRef.current[assistantMessageId] = '';
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      setMessages((prev) => prev.filter((msg) => msg.id !== userMessage.id && msg.id !== assistantMessageId));
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, user]);

  const clearChat = useCallback(async () => {
    const resetLocalState = (newSessionId: string) => {
      setMessages(() => []);
      setError(() => null);
      setLatestTokenUsage(() => undefined);
      setSessionId(() => newSessionId);
    };

    try {
      // Generate a new session ID FIRST
      const newSessionId = uuidv4();
      
      // Clear backend history for old session
      await apiClient.clearHistory(sessionId);
      
      // Force state reset - use functional updates to ensure fresh state
      resetLocalState(newSessionId);
      
      return newSessionId;
    } catch (err) {
      const message = err instanceof Error ? err.message : '';
      if (message.includes('Session not found') || message.includes('HTTP 404')) {
        const newSessionId = uuidv4();
        resetLocalState(newSessionId);
        return newSessionId;
      }

      console.error('[useChat] Failed to clear chat:', err);
      // Even if backend clear fails, still reset the UI
      const newSessionId = uuidv4();
      resetLocalState(newSessionId);
      throw err;
    }
  }, [sessionId]);

  const hydrateConversation = useCallback((targetSessionId: string, historyMessages: ChatMessage[]) => {
    setSessionId(targetSessionId);
    setMessages(mapChatMessagesToUiMessages(targetSessionId, historyMessages));
    setError(null);
  }, [mapChatMessagesToUiMessages]);

  return {
    sessionId,
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
    hydrateConversation,
    latestTokenUsage,
  };
}
