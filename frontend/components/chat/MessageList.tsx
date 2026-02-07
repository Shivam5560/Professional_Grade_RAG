/**
 * MessageList - Scrollable list of chat messages
 */

'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageItem } from './MessageItem';
import { Bot } from 'lucide-react';
import { TypingIndicator } from './TypingIndicator';
import { Badge } from '@/components/ui/badge';
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
  const [activeCategory, setActiveCategory] = useState<string>('All');

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

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

  const categoryMap = useMemo(() => {
    const map: Record<string, string> = {};
    promptSuggestions.forEach((item) => {
      const title = item.title.toLowerCase();
      if (title.includes('summarize') || title.includes('brief') || title.includes('recap')) {
        map[item.title] = 'Summary';
      } else if (title.includes('compare')) {
        map[item.title] = 'Comparison';
      } else if (title.includes('action') || title.includes('decision') || title.includes('timeline')) {
        map[item.title] = 'Actions';
      } else if (title.includes('risk') || title.includes('compliance') || title.includes('counterpoint')) {
        map[item.title] = 'Risk';
      } else if (title.includes('stakeholder') || title.includes('metrics')) {
        map[item.title] = 'Stakeholders';
      } else if (title.includes('faq') || title.includes('email')) {
        map[item.title] = 'Comms';
      } else {
        map[item.title] = 'Other';
      }
    });
    return map;
  }, [promptSuggestions]);

  const categories = useMemo(() => {
    const set = new Set<string>(['All']);
    promptSuggestions.forEach((item) => set.add(categoryMap[item.title] || 'Other'));
    return Array.from(set);
  }, [promptSuggestions, categoryMap]);

  const filteredPrompts = useMemo(() => {
    if (activeCategory === 'All') return promptSuggestions;
    return promptSuggestions.filter((item) => categoryMap[item.title] === activeCategory);
  }, [activeCategory, promptSuggestions, categoryMap]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="relative h-full overflow-hidden">
        <div className="pointer-events-none absolute inset-0 intro-sheen" />
        <div className="pointer-events-none absolute -top-24 left-1/4 h-72 w-72 rounded-full bg-[radial-gradient(circle_at_top,hsl(var(--chart-1)/0.45),transparent_65%)] blur-3xl float-slow" />
        <div className="pointer-events-none absolute -bottom-28 right-1/4 h-80 w-80 rounded-full bg-[radial-gradient(circle_at_top,hsl(var(--chart-2)/0.45),transparent_70%)] blur-3xl float-slower" />
        <div className="pointer-events-none absolute -top-10 right-8 h-48 w-48 rounded-full bg-[radial-gradient(circle_at_top,hsl(var(--chart-4)/0.4),transparent_70%)] blur-3xl float-slowest" />

        <div className="relative z-10 flex h-full items-center justify-center p-6 md:p-10">
          <motion.div
            initial={{ opacity: 0, y: 16, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.4, ease: 'easeOut' }}
            className="w-full max-w-4xl"
          >
            <div className="space-y-6">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45, ease: 'easeOut' }}
                className="text-center"
              >
                <div className="text-2xl md:text-3xl font-semibold text-foreground">
                  {greeting}, {displayName}
                </div>
                <div className="mt-2 text-base md:text-lg text-muted-foreground">
                  How can I help you today?
                </div>
              </motion.div>

              {categories.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                  className="flex flex-wrap items-center justify-center gap-2"
                >
                  {categories.map((category) => {
                    const isActive = category === activeCategory;
                    return (
                      <button
                        key={category}
                        type="button"
                        onClick={() => setActiveCategory(category)}
                        className="rounded-full"
                      >
                        <Badge
                          className={`px-3 py-1 text-xs uppercase tracking-[0.2em] transition-colors ${
                            isActive
                              ? 'bg-foreground text-background'
                              : 'bg-card/80 text-foreground border-border/70 hover:bg-muted/60'
                          }`}
                          variant={isActive ? 'default' : 'outline'}
                        >
                          {category}
                        </Badge>
                      </button>
                    );
                  })}
                </motion.div>
              )}

              {filteredPrompts.length > 0 && (
                <div className="max-h-[46vh] overflow-y-auto pr-1">
                  <div className="flex flex-wrap items-center justify-center gap-3">
                    {filteredPrompts.map((chip, index) => (
                    <motion.button
                      key={chip.title}
                      type="button"
                      onClick={() => onPromptSelect?.(chip.prompt)}
                      initial={{ opacity: 0, y: 14, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      transition={{ duration: 0.45, ease: 'easeOut', delay: index * 0.04 }}
                      whileHover={{ y: -3, scale: 1.04 }}
                      className="rounded-full"
                    >
                      <Badge
                        variant="outline"
                        className="px-5 py-2.5 text-sm md:text-base font-semibold bg-card/80 border-border/70 hover:bg-muted/60 hover:border-foreground/40 transition-all shadow-[0_14px_30px_-24px_rgba(0,0,0,0.5)]"
                      >
                        {chip.title}
                      </Badge>
                    </motion.button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full px-4">
      <div className="flex flex-col gap-6 py-6">
        <AnimatePresence initial={false}>
          {messages.map((message, index) => {
            // Attach sources to the last assistant message
            const isLastAssistant = message.role === 'assistant' && index === messages.length - 1;
            const messageWithSources = isLastAssistant && latestSources && latestSources.length > 0
              ? { ...message, sources: latestSources }
              : message;
            
            return (
              <motion.div
                key={index}
                layout
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
