/**
 * MessageList - Scrollable list of chat messages
 */

'use client';

import { useEffect, useMemo, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageItem } from './MessageItem';
import { Bot } from 'lucide-react';
import { TypingIndicator } from './TypingIndicator';
import { AnimatePresence, motion } from 'framer-motion';
import { useAuthStore } from '@/lib/store';
import type { Message, SourceReference } from '@/lib/types';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  latestSources?: SourceReference[];
  promptSuggestions?: Array<{ title: string; prompt: string }>;
  onPromptSelect?: (prompt: string) => void;
}

export function MessageList({
  messages,
  isLoading,
  latestSources,
  promptSuggestions = [],
  onPromptSelect,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const { user } = useAuthStore();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: isLoading ? 'auto' : 'smooth' });
  }, [messages.length, isLoading]);

  const greeting = useMemo(() => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  }, []);

  const displayName = useMemo(() => {
    if (user?.full_name) return user.full_name;
    if (user?.email) {
      const localPart = user.email.split('@')[0] || '';
      const cleaned = localPart.replace(/[._-]+/g, ' ').trim();
      if (!cleaned) return 'there';
      return cleaned
        .split(' ')
        .filter(Boolean)
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
    }
    return 'there';
  }, [user?.full_name, user?.email]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="relative h-full overflow-y-auto">
        <div className="relative z-10 flex min-h-full items-center justify-center p-6 md:p-10">
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="w-full max-w-3xl"
          >
            <div className="space-y-8">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, ease: 'easeOut' }}
                className="text-center"
              >
                <div className="text-2xl font-semibold text-foreground md:text-3xl">
                  {greeting}, {displayName}
                </div>
                <div className="mt-2 text-sm text-muted-foreground md:text-base">
                  What would you like to understand from your evidence?
                </div>
              </motion.div>

              {promptSuggestions.length > 0 && (
                <div className="grid gap-2 sm:grid-cols-2">
                    {promptSuggestions.slice(0, 4).map((chip, index) => (
                    <motion.button
                      key={chip.title}
                      type="button"
                      onClick={() => onPromptSelect?.(chip.prompt)}
                      initial={{ opacity: 0, y: 14, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ duration: 0.45, ease: 'easeOut', delay: index * 0.04 }}
                      whileHover={{ y: -2 }}
                      className="min-h-14 rounded-md border border-border/70 bg-workspace-raised px-4 py-3 text-left text-sm font-medium text-foreground transition-colors hover:bg-workspace-inset"
                    >
                      {chip.title}
                    </motion.button>
                    ))}
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea data-scroll-owner="messages" data-testid="knowledge-message-scroll" className="h-full px-4">
      <div className="flex flex-col gap-6 py-6">
        <AnimatePresence initial={false}>
          {messages.map((message, index) => {
            // Attach sources to the last assistant message
            const isLastAssistant = message.role === 'assistant' && index === messages.length - 1;
            const messageWithSources = isLastAssistant && latestSources && latestSources.length > 0
              ? { ...message, sources: message.sources || latestSources }
              : message;
            
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 8, scale: 0.98 }}
                transition={{ duration: 0.24, ease: 'easeOut' }}
              >
                <MessageItem
                  message={messageWithSources}
                  showConfidence={message.role === 'assistant'}
                />
              </motion.div>
            );
          })}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            className="flex items-center gap-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
              <Bot className="h-4 w-4" />
            </div>
            <TypingIndicator />
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
