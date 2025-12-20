/**
 * MessageInput - Chat input component with send button and file upload
 * Features ChatGPT-style file attachments shown above the input
 */

'use client';

import { useState, KeyboardEvent, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Send, Paperclip, X, FileText, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  onUploadClick?: () => void;
}

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  message?: string;
  documentId?: string;
  chunksCreated?: number;
}

export function MessageInput({
  onSend,
  disabled = false,
  placeholder = 'Ask a question...',
  onUploadClick,
}: MessageInputProps) {
  const [input, setInput] = useState('');
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
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

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    const newFiles: UploadedFile[] = selectedFiles.map(file => ({
      file,
      status: 'pending'
    }));
    
    // Add files to state immediately
    setFiles(prev => [...prev, ...newFiles]);
    
    // Auto-upload files
    await uploadFiles(newFiles);
    
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const uploadFiles = async (filesToUpload: UploadedFile[]) => {
    if (filesToUpload.length === 0 || isUploading) return;

    setIsUploading(true);

    for (let i = 0; i < filesToUpload.length; i++) {
      if (filesToUpload[i].status !== 'pending') continue;

      // Update status to uploading
      setFiles(prev => prev.map((f) => 
        f.file === filesToUpload[i].file ? { ...f, status: 'uploading' } : f
      ));

      try {
        const formData = new FormData();
        formData.append('file', filesToUpload[i].file);
        formData.append('title', filesToUpload[i].file.name);

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/documents/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();

        // Update status to success
        setFiles(prev => prev.map((f) => 
          f.file === filesToUpload[i].file ? { 
            ...f, 
            status: 'success',
            documentId: result.document_id,
            chunksCreated: result.chunks_created,
            message: `${result.chunks_created} chunks`
          } : f
        ));

        // Auto-remove successful uploads after 5 seconds
        setTimeout(() => {
          setFiles(prev => prev.filter(f => f.file !== filesToUpload[i].file));
        }, 5000);
      } catch (error) {
        // Update status to error
        setFiles(prev => prev.map((f) => 
          f.file === filesToUpload[i].file ? { 
            ...f, 
            status: 'error',
            message: error instanceof Error ? error.message : 'Upload failed'
          } : f
        ));
      }
    }

    setIsUploading(false);
  };

  const removeFile = (file: File) => {
    setFiles(prev => prev.filter(f => f.file !== file));
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getFileExtension = (filename: string) => {
    return filename.split('.').pop()?.toUpperCase() || 'FILE';
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div className="relative">
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileSelect}
        multiple
        accept=".txt,.pdf,.doc,.docx,.md"
        className="hidden"
      />

      {/* ChatGPT-style File Attachments - Shown Above Input */}
      {files.length > 0 && (
        <div className="mb-3 px-4">
          <div className="flex flex-wrap gap-2">
            {files.map((fileItem, index) => (
              <div
                key={index}
                className={cn(
                  "group relative flex items-center gap-2 px-3 py-2 rounded-lg border transition-all",
                  fileItem.status === 'success' && "bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800",
                  fileItem.status === 'error' && "bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800",
                  fileItem.status === 'uploading' && "bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800 animate-pulse",
                  fileItem.status === 'pending' && "bg-muted/50 border-border"
                )}
              >
                {/* File Icon with Status */}
                <div className="flex-shrink-0">
                  {getStatusIcon(fileItem.status)}
                </div>

                {/* File Info */}
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium truncate max-w-[150px]">
                      {fileItem.file.name}
                    </span>
                    <span className="text-[10px] text-muted-foreground px-1.5 py-0.5 bg-muted/50 rounded">
                      {getFileExtension(fileItem.file.name)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                    <span>{formatFileSize(fileItem.file.size)}</span>
                    {fileItem.message && (
                      <>
                        <span>•</span>
                        <span className={cn(
                          fileItem.status === 'error' && "text-destructive",
                          fileItem.status === 'success' && "text-green-600 dark:text-green-400"
                        )}>
                          {fileItem.message}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => removeFile(fileItem.file)}
                  className={cn(
                    "flex-shrink-0 p-1 rounded hover:bg-background/80 transition-opacity",
                    fileItem.status === 'uploading' ? "opacity-50 cursor-not-allowed" : "opacity-60 hover:opacity-100"
                  )}
                  disabled={fileItem.status === 'uploading'}
                  title="Remove file"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-end gap-3">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
            setInput(e.target.value);
            // Auto-resize textarea
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className="flex-1 min-h-[56px] max-h-[200px] resize-none bg-slate-800/40 border-slate-700/50 text-white placeholder:text-slate-500 focus:ring-2 focus:ring-cyan-500/50 focus:border-cyan-500/50 transition-all rounded-2xl px-5 py-4"
          rows={1}
        />
        <div className="flex gap-2 pb-1">
          <Button
            onClick={() => onUploadClick ? onUploadClick() : fileInputRef.current?.click()}
            disabled={disabled || isUploading}
            size="icon"
            variant="ghost"
            title="Upload documents"
            className="h-12 w-12 text-slate-400 hover:text-cyan-400 hover:bg-slate-800/30 transition-all rounded-xl"
          >
            <Paperclip className="h-5 w-5" />
          </Button>
          <Button
            onClick={handleSend}
            disabled={!input.trim() || disabled}
            size="icon"
            className="h-12 w-12 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/30 transition-all rounded-xl disabled:opacity-50"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}

