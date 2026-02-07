'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Upload, X, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAuthStore } from '@/lib/store';
import { useToast } from '@/hooks/useToast';

// Configuration constants
const MAX_FILE_SIZE_MB = 200;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const ALLOWED_EXTENSIONS = ['.txt', '.md', '.pdf', '.docx'];

interface UploadedFile {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  message?: string;
  documentId?: string;
  chunksCreated?: number;
}

interface DocumentUploadProps {
  onUploadComplete?: () => void;
}

export function DocumentUpload({ onUploadComplete }: DocumentUploadProps) {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user } = useAuthStore();
  const { toast } = useToast();

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Check file size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
      return {
        valid: false,
        error: `File too large (${sizeMB} MB). Maximum allowed: ${MAX_FILE_SIZE_MB} MB`
      };
    }

    // Check file extension
    const hasValidExtension = ALLOWED_EXTENSIONS.some(ext => 
      file.name.toLowerCase().endsWith(ext)
    );
    
    if (!hasValidExtension) {
      return {
        valid: false,
        error: `Unsupported file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`
      };
    }

    return { valid: true };
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    
    // Validate all files first
    const validatedFiles: UploadedFile[] = selectedFiles.map(file => {
      const validation = validateFile(file);
      
      if (!validation.valid) {
        return {
          file,
          status: 'error' as const,
          message: validation.error
        };
      }
      
      return {
        file,
        status: 'pending' as const
      };
    });
    
    setFiles(prev => [...prev, ...validatedFiles]);
    
    // Auto-upload only valid files
    const filesToUpload = validatedFiles.filter(f => f.status === 'pending');
    if (filesToUpload.length > 0) {
      await uploadFiles(filesToUpload);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async (filesToUpload: UploadedFile[]) => {
    if (filesToUpload.length === 0) return;
    
    // Check if user is logged in
    if (!user) {
      setFiles(prev => prev.map(f => ({
        ...f,
        status: 'error',
        message: 'Please log in to upload documents'
      })));
      toast({
        title: 'Upload failed',
        description: 'Please log in to upload documents.',
        variant: 'destructive',
      });
      setIsUploading(false);
      return;
    }

    setIsUploading(true);
    let successCount = 0;

    for (let i = 0; i < filesToUpload.length; i++) {
      const currentFile = filesToUpload[i];
      
      // Update status to uploading
      setFiles(prev => prev.map(f => 
        f.file === currentFile.file ? { ...f, status: 'uploading' } : f
      ));

      try {
        const formData = new FormData();
        formData.append('file', currentFile.file);
        formData.append('user_id', user.id.toString());
        formData.append('title', currentFile.file.name);

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/documents/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Upload failed');
        }

        const result = await response.json();
        successCount++;

        // Update status to success
        setFiles(prev => prev.map(f => 
          f.file === currentFile.file ? { 
            ...f, 
            status: 'success',
            documentId: result.document_id,
            chunksCreated: result.chunks_created,
            message: `Uploaded successfully! ${result.chunks_created} chunks created.`
          } : f
        ));

        toast({
          title: 'Document ready',
          description: `${currentFile.file.name} uploaded and indexed (${result.chunks_created} chunks).`,
        });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Upload failed';
        // Update status to error
        setFiles(prev => prev.map(f => 
          f.file === currentFile.file ? { 
            ...f, 
            status: 'error',
            message: message
          } : f
        ));

        toast({
          title: 'Upload failed',
          description: `${currentFile.file.name}: ${message}`,
          variant: 'destructive',
        });
      }
    }

    setIsUploading(false);
    
    // If all files uploaded successfully and callback exists, close after delay
    if (successCount === filesToUpload.length && onUploadComplete) {
      setTimeout(() => {
        onUploadComplete();
      }, 1500);
    }
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status === 'pending' || f.status === 'uploading'));
  };

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const formatFileSize = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    if (mb >= 1) {
      return `${mb.toFixed(2)} MB`;
    }
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  const hasCompleted = files.some(f => f.status === 'success' || f.status === 'error');

  return (
    <Card className="w-full backdrop-blur-xl bg-zinc-900/80 border-white/10 shadow-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-zinc-200">
          <Upload className="h-5 w-5 text-blue-400" />
          Upload Documents
        </CardTitle>
        <CardDescription className="text-zinc-400">
          Upload documents to add them to the knowledge base. 
          <br />
          <span className="text-xs mt-1 block">
            Supported formats: {ALLOWED_EXTENSIONS.join(', ')} • Max size: {MAX_FILE_SIZE_MB} MB per file
          </span>
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* File Input */}
        <div className="flex gap-2">
          <Input
            ref={fileInputRef}
            type="file"
            onChange={handleFileSelect}
            multiple
            accept={ALLOWED_EXTENSIONS.join(',')}
            className="flex-1 bg-zinc-800/60 border-white/20 text-white focus:ring-blue-500/60 rounded-xl"
          />
        </div>

        {/* Upload Status */}
        {isUploading && (
          <div className="flex items-center justify-center p-4 backdrop-blur-xl bg-zinc-800/60 rounded-xl border border-white/10">
            <Loader2 className="h-6 w-6 animate-spin text-blue-400 mr-2" />
            <span className="text-sm font-medium text-zinc-200">Uploading documents...</span>
          </div>
        )}

        {/* Success Alert */}
        {hasCompleted && (
          <Alert className="backdrop-blur-xl bg-zinc-800/60 border-green-500/30 text-zinc-200">
            <CheckCircle className="h-4 w-4 text-green-400" />
            <AlertTitle className="text-zinc-200">Upload Complete</AlertTitle>
            <AlertDescription className="text-zinc-400">
              {files.filter(f => f.status === 'success').length} file(s) uploaded successfully.
              The documents are now available in the knowledge base.
            </AlertDescription>
          </Alert>
        )}

        {/* File List */}
        {files.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium text-zinc-200">Files ({files.length})</h4>
              {hasCompleted && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearCompleted}
                  className="hover:bg-white/10 text-zinc-400"
                >
                  Clear Completed
                </Button>
              )}
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {files.map((fileItem, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 p-3 border border-white/10 rounded-xl backdrop-blur-xl bg-zinc-800/40 hover:bg-zinc-800/60 transition-colors"
                >
                  <div className="mt-0.5">
                    {getStatusIcon(fileItem.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate text-zinc-200">
                      {fileItem.file.name}
                    </p>
                    <p className="text-xs text-zinc-400">
                      {formatFileSize(fileItem.file.size)}
                    </p>
                    {fileItem.message && (
                      <p className={`text-xs mt-1 ${
                        fileItem.status === 'error' ? 'text-red-400' : 'text-green-400'
                      }`}>
                        {fileItem.message}
                      </p>
                    )}
                  </div>
                  {fileItem.status === 'pending' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(index)}
                      className="h-8 w-8 p-0 hover:bg-white/10 text-zinc-400"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info */}
        <div className="text-xs text-zinc-500 space-y-1">
          <p>• Supported formats: TXT, PDF, DOC, DOCX, MD</p>
          <p>• Files are chunked and embedded for semantic search</p>
          <p>• You can only query documents you&apos;ve uploaded</p>
          <p>• Manage your documents in the Knowledge Base section</p>
        </div>
      </CardContent>
    </Card>
  );
}
