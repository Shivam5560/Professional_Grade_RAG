'use client';

import { useEffect, useState, useRef, useCallback, type RefObject } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { X, Plus, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { AskFileContent, DocumentInfo, RAGMode } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import { useToast } from '@/hooks/useToast';

interface QuickFileSelectorProps {
  mode: RAGMode;
  selectedFiles?: DocumentInfo[];
  onFileToggle?: (file: DocumentInfo) => void;
  onClearAll?: () => void;
  askFiles?: AskFileContent[];
  selectedAskFileIds?: string[];
  onAskFileToggle?: (fileId: string) => void;
  onAskUpload?: (file: File) => Promise<void>;
  isAskUploading?: boolean;
  showUploadButton?: boolean;
  fileInputRef?: RefObject<HTMLInputElement>;
  onUploadingChange?: (uploading: boolean) => void;
}

export function QuickFileSelector({
  mode,
  selectedFiles = [],
  onFileToggle,
  onClearAll,
  askFiles = [],
  selectedAskFileIds = [],
  onAskFileToggle,
  onAskUpload,
  isAskUploading = false,
  showUploadButton = true,
  fileInputRef: fileInputRefProp,
  onUploadingChange,
}: QuickFileSelectorProps) {
  const { user } = useAuthStore();
  const [recentFiles, setRecentFiles] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const internalFileInputRef = useRef<HTMLInputElement>(null);
  const resolvedFileInputRef = fileInputRefProp ?? internalFileInputRef;
  const { toast } = useToast();

  const loadRecentFiles = useCallback(async () => {
    if (!user || mode === 'ask') return;
    
    setLoading(true);
    try {
      const response = await apiClient.getUserDocuments(user.id);
      const scoped = response.documents.filter((doc) => doc.category === `chat-${mode}`);
      // Get last 5 files sorted by upload date
      const recent = scoped
        .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())
        .slice(0, 5);
      setRecentFiles(recent);
    } catch (error) {
      console.error('Failed to load recent files:', error);
    } finally {
      setLoading(false);
    }
  }, [user, mode]);

  useEffect(() => {
    if (user) {
      loadRecentFiles();
    }
  }, [user, loadRecentFiles]);

  const handleUploadClick = () => {
    resolvedFileInputRef.current?.click();
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (mode === 'ask') {
      if (!onAskUpload) return;
      await onAskUpload(file);
      if (resolvedFileInputRef.current) {
        resolvedFileInputRef.current.value = '';
      }
      return;
    }

    if (!user || !onFileToggle) return;

    setUploading(true);
    onUploadingChange?.(true);

    try {
      const result = await apiClient.uploadDocument(file, user.id, { title: file.name, category: `chat-${mode}` });
      
      // Reload recent files
      await loadRecentFiles();

      // Auto-select the newly uploaded file
      const newFile: DocumentInfo = {
        id: result.document_id as string,
        filename: file.name,
        file_size: file.size,
        file_type: file.type,
        upload_date: new Date().toISOString(),
        vector_count: result.chunks_created as number,
      };
      onFileToggle(newFile);

      // Reset file input
      if (resolvedFileInputRef.current) {
        resolvedFileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Upload failed:', error);
      toast({
        title: 'Upload failed',
        description: error instanceof Error ? error.message : 'Failed to upload file',
        variant: 'destructive',
      });
    } finally {
      setUploading(false);
      onUploadingChange?.(false);
    }
  };

  const isFileSelected = (fileId: string) => {
    return selectedFiles.some(f => f.id === fileId);
  };

  const isAskFileSelected = (fileId: string) => selectedAskFileIds.includes(fileId);

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>Loading files...</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
        {mode === 'fast' ? 'Fast mode files' : mode === 'think' ? 'Think mode files' : 'Ask mode files'}
      </div>
      {/* File badges */}
      <div className="flex flex-wrap items-center gap-2">
        {mode === 'ask' ? (
          askFiles.length > 0 ? (
            askFiles.map((file) => {
              const selected = isAskFileSelected(file.id);
              return (
                <Badge
                  key={file.id}
                  variant={selected ? 'default' : 'outline'}
                  className={`
                    cursor-pointer rounded-full py-1 px-3 transition-all hover:scale-105
                    ${selected
                      ? 'border-transparent bg-gradient-to-r from-[hsl(var(--chart-5))] to-[hsl(var(--chart-4))] text-white hover:brightness-105'
                      : 'bg-card/80 text-muted-foreground border-border/70 hover:bg-muted/60'
                    }
                  `}
                  onClick={() => onAskFileToggle?.(file.id)}
                >
                  <span className="truncate max-w-[150px]">{file.filename}</span>
                  {selected && (
                    <X
                      className="ml-1 h-3 w-3"
                      onClick={(e) => {
                        e.stopPropagation();
                        onAskFileToggle?.(file.id);
                      }}
                    />
                  )}
                </Badge>
              );
            })
          ) : (
            <span className="text-sm text-muted-foreground">No files uploaded yet</span>
          )
        ) : recentFiles.length > 0 ? (
          <>
            {recentFiles.map((file) => {
              const selected = isFileSelected(file.id);
              return (
                <Badge
                  key={file.id}
                  variant={selected ? 'default' : 'outline'}
                  className={`
                    cursor-pointer rounded-full py-1 px-3 transition-all hover:scale-105
                    ${selected 
                      ? 'border-transparent bg-gradient-to-r from-[hsl(var(--chart-2))] to-[hsl(var(--chart-1))] text-white hover:brightness-105' 
                      : 'bg-card/80 text-muted-foreground border-border/70 hover:bg-muted/60'
                    }
                  `}
                  onClick={() => onFileToggle?.(file)}
                >
                  <span className="truncate max-w-[150px]">{file.filename}</span>
                  {selected && (
                    <X
                      className="ml-1 h-3 w-3"
                      onClick={(e) => {
                        e.stopPropagation();
                        onFileToggle?.(file);
                      }}
                    />
                  )}
                </Badge>
              );
            })}
          </>
        ) : (
          <span className="text-sm text-muted-foreground">No files uploaded yet</span>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-1">
          {(mode === 'ask' ? selectedAskFileIds.length > 0 : selectedFiles.length > 0) && (
          <Button
            size="sm"
            variant="ghost"
            onClick={mode === 'ask' ? () => selectedAskFileIds.forEach((id) => onAskFileToggle?.(id)) : onClearAll}
            className="h-7 px-2 text-xs text-muted-foreground hover:bg-muted/60 hover:text-foreground"
          >
            Clear all
          </Button>
          )}

          {showUploadButton && (
            <Button
              size="sm"
              variant="outline"
              onClick={handleUploadClick}
              disabled={mode === 'ask' ? isAskUploading : uploading}
              className="h-10 w-10 rounded-xl border-border/70 bg-muted/70 p-0 text-foreground hover:bg-background/90"
              title={mode === 'ask' ? 'Add ask file' : 'Upload file'}
              aria-label={mode === 'ask' ? 'Add ask file' : 'Upload file'}
            >
              {(mode === 'ask' ? isAskUploading : uploading) ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Plus className="h-3.5 w-3.5" />
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={resolvedFileInputRef}
        type="file"
        accept=".txt,.md,.pdf,.docx"
        className="hidden"
        onChange={handleFileSelect}
      />

      {/* Selected count indicator */}
      {(mode === 'ask' ? selectedAskFileIds.length > 0 : selectedFiles.length > 0) && (
        <div className="text-xs text-muted-foreground">
          {mode === 'ask' ? selectedAskFileIds.length : selectedFiles.length} file{(mode === 'ask' ? selectedAskFileIds.length : selectedFiles.length) !== 1 ? 's' : ''} selected as context
        </div>
      )}
    </div>
  );
}
