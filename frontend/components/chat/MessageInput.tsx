/**
 * MessageInput - Chat input component with send button and file upload
 * Features ChatGPT-style file attachments shown above the input
 */

'use client';

import { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Send } from 'lucide-react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  isSending?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export function MessageInput({
  onSend,
  disabled = false,
  isSending = false,
  placeholder = 'Ask a question...',
  value,
  onChange,
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const hasValueProp = typeof value === 'string';
  if (process.env.NODE_ENV !== 'production' && hasValueProp && typeof onChange !== 'function') {
    console.warn(
      '[MessageInput] A controlled value was provided without an onChange handler. The component will operate as uncontrolled.'
    );
  }
  const isControlled = hasValueProp && typeof onChange === 'function';
  const currentValue = isControlled ? value : input;

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = 'auto';
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 320)}px`;
  }, [currentValue]);

  const handleSend = () => {
    if (currentValue.trim() && !disabled && !isSending) {
      onSend(currentValue.trim());
      if (isControlled) {
        onChange?.('');
      } else {
        setInput('');
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="relative">
      {/* Input Area */}
      <div className="flex items-end gap-3">
        <Textarea
          ref={textareaRef}
          value={currentValue}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
            const nextValue = e.target.value;
            if (isControlled) {
              onChange?.(nextValue);
            } else {
              setInput(nextValue);
            }
            // Auto-resize textarea
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 320) + 'px';
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isSending}
          aria-label="Message"
          enterKeyHint="send"
          className="flex-1 min-h-[56px] max-h-[320px] resize-none rounded-2xl border-border/70 bg-muted/70 px-5 py-4 text-foreground placeholder:text-muted-foreground transition-all focus:border-foreground/30 focus:ring-2 focus:ring-foreground/20"
          rows={1}
        />
        <Button
          type="button"
          onClick={handleSend}
          disabled={!currentValue.trim() || disabled || isSending}
          size="icon"
          className="h-12 w-12 rounded-xl bg-gradient-to-br from-[hsl(var(--chart-1))] to-[hsl(var(--chart-2))] text-white shadow-lg shadow-black/20 transition-all hover:brightness-105 disabled:opacity-50"
          title={isSending ? 'Sending…' : 'Send message'}
          aria-label={isSending ? 'Sending' : 'Send message'}
        >
          {isSending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
        </Button>
      </div>
    </div>
  );
}
