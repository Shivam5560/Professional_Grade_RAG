/**
 * MessageInput - Chat input component with send button and file upload
 * Features ChatGPT-style file attachments shown above the input
 */

'use client';

import { useState, KeyboardEvent, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send } from 'lucide-react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
}

export function MessageInput({
  onSend,
  disabled = false,
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

  const handleSend = () => {
    if (currentValue.trim() && !disabled) {
      onSend(currentValue.trim());
      if (isControlled) {
        onChange?.('');
      } else {
        setInput('');
      }
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
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
          disabled={disabled}
          className="flex-1 min-h-[56px] max-h-[320px] resize-none bg-muted/70 border-border/70 text-foreground placeholder:text-muted-foreground focus:ring-2 focus:ring-foreground/30 focus:border-foreground/30 transition-all rounded-2xl px-5 py-4"
          rows={1}
        />
        <Button
          onClick={handleSend}
          disabled={!currentValue.trim() || disabled}
          size="icon"
          className="h-12 w-12 bg-foreground text-background hover:bg-foreground/90 shadow-lg transition-all rounded-xl disabled:opacity-50"
        >
          <Send className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
}
