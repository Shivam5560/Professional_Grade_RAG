'use client';

import { useState, useEffect, useCallback } from 'react';
import { Search, FileText, X, Upload } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { apiClient } from '@/lib/api';
import { DocumentInfo } from '@/lib/types';
import { useAuthStore } from '@/lib/store';
import { useRouter } from 'next/navigation';

interface FileContextSelectorProps {
  selectedFiles: DocumentInfo[];
  onFilesChange: (files: DocumentInfo[]) => void;
}

export function FileContextSelector({ selectedFiles, onFilesChange }: FileContextSelectorProps) {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const { user } = useAuthStore();
  const router = useRouter();

  const loadDocuments = useCallback(async () => {
    if (!user) return;
    
    try {
      const response = await apiClient.getUserDocuments(user.id);
      // Sort by filename ascending
      const sorted = response.documents.sort((a, b) => 
        a.filename.localeCompare(b.filename)
      );
      setDocuments(sorted);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      loadDocuments();
    }
  }, [user, loadDocuments]);

  const filteredDocuments = documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleFile = (doc: DocumentInfo) => {
    const isSelected = selectedFiles.some(f => f.id === doc.id);
    if (isSelected) {
      onFilesChange(selectedFiles.filter(f => f.id !== doc.id));
    } else {
      onFilesChange([...selectedFiles, doc]);
    }
  };

  const removeFile = (docId: string) => {
    onFilesChange(selectedFiles.filter(f => f.id !== docId));
  };

  return (
    <div className="space-y-3">
      {/* Selected Files as Badges */}
      {selectedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selectedFiles.map(file => (
            <Badge 
              key={file.id}
              variant="secondary"
              className="pl-2 pr-1 py-1 bg-cyan-500/10 border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 transition-colors"
            >
              <FileText className="h-3 w-3 mr-1" />
              <span className="text-xs font-medium">{file.filename}</span>
              <button
                onClick={() => removeFile(file.id)}
                className="ml-1 hover:bg-cyan-500/20 rounded p-0.5"
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          type="text"
          placeholder="Search your knowledge base..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9 bg-slate-800/60 border-white/10 text-white placeholder:text-slate-500 focus:ring-cyan-500/60 rounded-xl"
        />
      </div>

      {/* File List */}
      {documents.length === 0 ? (
        <div className="text-center py-8 px-4 bg-slate-800/30 rounded-xl border border-white/5">
          <FileText className="h-12 w-12 mx-auto text-slate-600 mb-3" />
          <p className="text-sm text-slate-400 mb-2">No documents in your knowledge base</p>
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push('/knowledge-base')}
            className="border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/10"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Documents
          </Button>
        </div>
      ) : (
        <ScrollArea className="h-[200px] rounded-xl border border-white/10 bg-slate-800/30">
          <div className="p-2 space-y-1">
            {filteredDocuments.length === 0 ? (
              <div className="text-center py-4 text-sm text-slate-400">
                No files match your search
              </div>
            ) : (
              filteredDocuments.map(doc => {
                const isSelected = selectedFiles.some(f => f.id === doc.id);
                return (
                  <button
                    key={doc.id}
                    onClick={() => toggleFile(doc)}
                    className={`w-full flex items-center gap-2 p-2 rounded-lg transition-all ${
                      isSelected 
                        ? 'bg-cyan-500/20 border border-cyan-500/30' 
                        : 'hover:bg-slate-700/50 border border-transparent'
                    }`}
                  >
                    <div className={`h-2 w-2 rounded-full ${
                      isSelected ? 'bg-cyan-400' : 'bg-slate-600'
                    }`} />
                    <FileText className="h-4 w-4 text-slate-400" />
                    <div className="flex-1 text-left">
                      <p className="text-sm text-white font-medium truncate">
                        {doc.filename}
                      </p>
                      <p className="text-xs text-slate-400">
                        {doc.vector_count} chunks
                      </p>
                    </div>
                    {doc.file_type && (
                      <Badge variant="outline" className="text-xs border-white/10">
                        {doc.file_type}
                      </Badge>
                    )}
                  </button>
                );
              })
            )}
          </div>
        </ScrollArea>
      )}

      {/* Info Text */}
      <p className="text-xs text-slate-500">
        Select files to provide context for your questions. Only selected files will be searched.
      </p>
    </div>
  );
}
