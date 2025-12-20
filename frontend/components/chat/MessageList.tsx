/**
 * MessageList - Scrollable list of chat messages
 */

'use client';

import { useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { MessageItem } from './MessageItem';
import { Bot } from 'lucide-react';
import { TypingIndicator } from './TypingIndicator';
import type { Message, SourceReference } from '@/lib/types';

interface MessageListProps {
  messages: Message[];
  isLoading?: boolean;
  latestSources?: SourceReference[];
}

export function MessageList({ messages, isLoading, latestSources }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-center p-8">
        <div className="space-y-6 max-w-md">
          <div className="p-8 bg-gradient-to-br from-blue-600/20 to-purple-600/20 rounded-3xl w-fit mx-auto backdrop-blur-sm border border-white/10">
             <div className="text-6xl animate-pulse">✨</div>
          </div>
          <h3 className="text-3xl font-black bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
            How can I help you today?
          </h3>
          <p className="text-zinc-400 text-lg">
            I can help you analyze documents, answer questions, and provide insights from your knowledge base.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full px-4">
      <div className="flex flex-col gap-6 py-6">
        {messages.map((message, index) => {
          // Attach sources to the last assistant message
          const isLastAssistant = message.role === 'assistant' && index === messages.length - 1;
          const messageWithSources = isLastAssistant && latestSources && latestSources.length > 0
            ? { ...message, sources: latestSources }
            : message;
          
          return (
            <MessageItem
              key={index}
              message={messageWithSources}
              showConfidence={message.role === 'assistant'}
            />
          );
        })}

        {isLoading && (
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
              <Bot className="h-4 w-4" />
            </div>
            <TypingIndicator />
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
