'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/Header';
import { Button } from '@/components/ui/button';
import { DataTable, type DataTableColumn } from '@/components/ui/data-table';
import { useAuthStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { useNexusFlowStore } from '@/lib/nexusFlowStore';
import { useToast } from '@/hooks/useToast';
import type { ResumeFileInfo } from '@/lib/types';
import AuthPage from '@/app/auth/page';

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

  const columns: DataTableColumn<ResumeFileInfo>[] = [
    { id: 'filename', header: 'File Name', accessor: 'filename' },
    { id: 'resume_id', header: 'ID', accessor: 'resume_id' },
    { id: 'status', header: 'Status', accessor: 'status', className: 'w-32' },
    {
      id: 'created_at',
      header: 'Uploaded At',
      accessor: (resume) => (resume.created_at ? new Date(resume.created_at).toLocaleString() : '—'),
      className: 'w-52 whitespace-nowrap',
    },
    {
      id: 'actions',
      header: 'Actions',
      searchable: false,
      className: 'w-48',
      cell: (resume) => (
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => handleSelectResume(resume)}>
            Select
          </Button>
          <Button size="sm" variant="destructive" onClick={() => handleDelete(resume)}>
            Delete
          </Button>
        </div>
      ),
    },
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

        <DataTable
          data={resumes}
          columns={columns}
          getRowId={(resume) => resume.id}
          loading={loading}
          searchPlaceholder="Search resumes..."
          emptyTitle="No resumes"
          emptyDescription="Upload a resume to analyze it against a job description."
          pageSize={10}
        />
      </main>
    </div>
  );
}
