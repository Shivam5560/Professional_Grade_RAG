'use client';

import { useEffect, useState, useRef } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { X, Upload, Database, Loader2, CheckCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { DocumentInfo } from '@/lib/types';
import { useAuthStore } from '@/lib/store';

interface QuickFileSelectorProps {
  selectedFiles: DocumentInfo[];
  onFileToggle: (file: DocumentInfo) => void;
  onClearAll: () => void;
}

export function QuickFileSelector({
  selectedFiles,
  onFileToggle,
  onClearAll,
}: QuickFileSelectorProps) {
  const { user } = useAuthStore();
  const [recentFiles, setRecentFiles] = useState<DocumentInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (user) {
      loadRecentFiles();
    }
  }, [user]);

  const loadRecentFiles = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const response = await apiClient.getUserDocuments(user.id);
      // Get last 5 files sorted by upload date
      const recent = response.documents
        .sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())
        .slice(0, 5);
      setRecentFiles(recent);
    } catch (error) {
      console.error('Failed to load recent files:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;

    setUploading(true);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', user.id.toString());
      formData.append('title', file.name);

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/documents/upload`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const result = await response.json();
      
      // Show success indicator
      setUploadSuccess(true);
      setTimeout(() => setUploadSuccess(false), 2000);

      // Reload recent files
      await loadRecentFiles();

      // Auto-select the newly uploaded file
      const newFile: DocumentInfo = {
        id: result.document_id,
        filename: file.name,
        file_size: file.size,
        file_type: file.type,
        upload_date: new Date().toISOString(),
        vector_count: result.chunks_created,
      };
      onFileToggle(newFile);

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Upload failed:', error);
      alert(error instanceof Error ? error.message : 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const isFileSelected = (fileId: string) => {
    return selectedFiles.some(f => f.id === fileId);
  };

  const handleViewAll = () => {
    window.location.href = '/knowledge-base';
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Loader2 className="h-3 w-3 animate-spin" />
        <span>Loading files...</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* File badges */}
      <div className="flex flex-wrap items-center gap-2">
        {recentFiles.length > 0 ? (
          <>
            {recentFiles.map((file) => {
              const selected = isFileSelected(file.id);
              return (
                <Badge
                  key={file.id}
                  variant={selected ? 'default' : 'outline'}
                  className={`
                    cursor-pointer transition-all hover:scale-105 py-1 px-3
                    ${selected 
                      ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50 hover:bg-cyan-500/30' 
                      : 'bg-slate-800/50 text-slate-300 border-slate-700 hover:bg-slate-700/50'
                    }
                  `}
                  onClick={() => onFileToggle(file)}
                >
                  <span className="truncate max-w-[150px]">{file.filename}</span>
                  {selected && (
                    <X
                      className="ml-1 h-3 w-3"
                      onClick={(e) => {
                        e.stopPropagation();
                        onFileToggle(file);
                      }}
                    />
                  )}
                </Badge>
              );
            })}
          </>
        ) : (
          <span className="text-sm text-slate-500">No files uploaded yet</span>
        )}

        {/* Action buttons */}
        <div className="flex items-center gap-1 ml-auto">
          {selectedFiles.length > 0 && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onClearAll}
              className="h-7 px-2 text-xs text-slate-400 hover:text-white hover:bg-slate-800/50"
            >
              Clear all
            </Button>
          )}
          
          <Button
            size="sm"
            variant="ghost"
            onClick={handleUploadClick}
            disabled={uploading}
            className="h-7 px-2 text-xs text-cyan-400 hover:text-cyan-300 hover:bg-cyan-500/10"
          >
            {uploading ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : uploadSuccess ? (
              <CheckCircle className="h-3 w-3" />
            ) : (
              <Upload className="h-3 w-3" />
            )}
            <span className="ml-1">{uploading ? 'Uploading...' : uploadSuccess ? 'Uploaded!' : 'Upload'}</span>
          </Button>

          {recentFiles.length > 0 && (
            <Button
              size="sm"
              variant="ghost"
              onClick={handleViewAll}
              className="h-7 px-2 text-xs text-slate-400 hover:text-white hover:bg-slate-800/50"
            >
              <Database className="h-3 w-3 mr-1" />
              View All
            </Button>
          )}
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.md,.pdf,.docx"
        className="hidden"
        onChange={handleFileSelect}
      />

      {/* Selected count indicator */}
      {selectedFiles.length > 0 && (
        <div className="text-xs text-slate-500">
          {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} selected as context
        </div>
      )}
    </div>
  );
}
