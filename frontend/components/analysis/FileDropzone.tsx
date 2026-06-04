'use client';
import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileSpreadsheet, X, CheckCircle2 } from 'lucide-react';

interface FileDropzoneProps {
  onFileSelect: (file: File | null) => void;
  selectedFile?: File | null;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileExtension(name: string): string {
  return name.split('.').pop()?.toUpperCase() || 'FILE';
}

export function FileDropzone({ onFileSelect, selectedFile }: FileDropzoneProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) onFileSelect(acceptedFiles[0]);
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    maxSize: 100 * 1024 * 1024,
  });

  if (selectedFile) {
    return (
      <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-500/10">
            <FileSpreadsheet className="h-5 w-5 text-emerald-500" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{selectedFile.name}</p>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-muted-foreground">
              <span className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 text-[10px] font-semibold uppercase">
                {getFileExtension(selectedFile.name)}
              </span>
              <span>{formatFileSize(selectedFile.size)}</span>
              <span className="flex items-center gap-1 text-emerald-600">
                <CheckCircle2 className="h-3 w-3" /> Ready
              </span>
            </div>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); onFileSelect(null); }}
            className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            title="Remove file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`group cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-all ${
        isDragActive
          ? 'border-primary bg-primary/5 shadow-[0_0_0_4px_hsl(var(--primary)/0.1)]'
          : 'border-border hover:border-primary/50 hover:bg-muted/30'
      }`}
    >
      <input {...getInputProps()} />
      <div className={`mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full transition-colors ${
        isDragActive ? 'bg-primary/10' : 'bg-muted group-hover:bg-primary/10'
      }`}>
        <Upload className={`h-5 w-5 transition-colors ${isDragActive ? 'text-primary' : 'text-muted-foreground group-hover:text-primary'}`} />
      </div>
      <p className="text-sm font-medium">
        {isDragActive ? 'Drop your file here' : 'Drag & drop your data file'}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        CSV or Excel • Up to 100 MB
      </p>
    </div>
  );
}
