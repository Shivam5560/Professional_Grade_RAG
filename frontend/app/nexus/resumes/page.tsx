'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { useNexusFlowStore } from '@/lib/nexusFlowStore';
import { useToast } from '@/hooks/useToast';
import type { ResumeFileInfo } from '@/lib/types';
import AuthPage from '@/app/auth/page';

import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-quartz.css';
import { ColDef, ICellRendererParams } from 'ag-grid-community';

export default function NexusResumeSelectPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const { setSelectedResume, setJobDescription, setAnalysis } = useNexusFlowStore();
  const { toast, confirm } = useToast();
  const [isMounted, setIsMounted] = useState(false);
  const [resumes, setResumes] = useState<ResumeFileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const toastRef = useRef(toast);
  const userId = user?.id;

  useEffect(() => {
    toastRef.current = toast;
  }, [toast]);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const loadData = useCallback(async (userId: number) => {
    setLoading(true);
    try {
      const resumeData = await apiClient.listResumes(userId);
      setResumes(resumeData.list);
    } catch (error) {
      console.error('Failed to load resume data:', error);
      toastRef.current({
        title: 'Failed to load resumes',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isMounted || !isAuthenticated || !userId) return;
    loadData(userId);
  }, [isMounted, isAuthenticated, userId, loadData]);

  if (!isMounted) return null;
  if (!isAuthenticated) return <AuthPage />;

  const handleUpload = async () => {
    if (!fileRef.current?.files?.[0] || !user) return;
    setUploading(true);
    try {
      await apiClient.uploadResume(fileRef.current.files[0], user.id);
      fileRef.current.value = '';
      toast({ title: 'Resume uploaded', description: 'Your resume has been uploaded successfully.' });
      await loadData(user.id);
    } catch (error) {
      console.error('Upload failed:', error);
      toast({ title: 'Upload failed', description: error instanceof Error ? error.message : 'Could not upload resume', variant: 'destructive' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (resume: ResumeFileInfo) => {
    if (!user) return;
    const confirmed = await confirm({
      title: `Delete "${resume.filename}"?`,
      description: 'This will remove the resume and all its analyses.',
      confirmLabel: 'Delete',
      variant: 'destructive',
    });
    if (!confirmed) return;
    
    try {
      await apiClient.deleteResume(user.id, resume.resume_id);
      toast({ title: 'Resume deleted', description: `"${resume.filename}" has been removed.` });
      await loadData(user.id);
    } catch (error) {
      console.error('Delete failed:', error);
      toast({ title: 'Delete failed', description: error instanceof Error ? error.message : 'Could not delete resume', variant: 'destructive' });
    }
  };

  const handleSelectResume = (resume: ResumeFileInfo) => {
    setSelectedResume(resume);
    setJobDescription('');
    setAnalysis(null);
    router.push('/nexus/jd');
  };

  const ActionRenderer = (params: ICellRendererParams) => {
    return (
      <div className="flex gap-2 items-center h-full">
        <Button size="sm" variant="outline" onClick={() => handleSelectResume(params.data)}>Select</Button>
        <Button size="sm" variant="destructive" onClick={() => handleDelete(params.data)}>Delete</Button>
      </div>
    );
  };

  const colDefs: ColDef[] = [
    { field: 'filename', headerName: 'File Name', flex: 1, filter: true },
    { field: 'resume_id', headerName: 'ID', flex: 1, filter: true },
    { field: 'status', headerName: 'Status', width: 120, filter: true },
    { 
      field: 'created_at', 
      headerName: 'Uploaded At', 
      width: 200, 
      valueFormatter: p => p.value ? new Date(p.value).toLocaleString() : '—'
    },
    {
      headerName: 'Actions',
      width: 200,
      cellRenderer: ActionRenderer,
    }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <Header />

      <main className="flex-1 p-8 flex flex-col max-w-6xl mx-auto w-full">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold">Resume Management</h1>
            <p className="text-muted-foreground mt-1">Manage and select resumes to analyze against job descriptions.</p>
          </div>
          <div className="flex items-center gap-3">
            <input 
              type="file" 
              ref={fileRef} 
              accept=".pdf,.doc,.docx,.txt" 
              className="border p-2 rounded-md bg-card" 
            />
            <Button onClick={handleUpload} disabled={uploading}>
              {uploading ? 'Uploading...' : 'Add Resume'}
            </Button>
          </div>
        </div>

        <div className="flex-1 w-full ag-theme-quartz-dark" style={{ minHeight: '500px' }}>
          <AgGridReact
            rowData={resumes}
            columnDefs={colDefs}
            rowHeight={50}
            animateRows={true}
            pagination={true}
            paginationPageSize={10}
            domLayout="autoHeight"
            overlayLoadingTemplate={loading ? '<span class="ag-overlay-loading-center">Loading...</span>' : undefined}
          />
        </div>
      </main>
    </div>
  );
}
