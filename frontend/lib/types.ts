/**
 * TypeScript type definitions for the RAG system frontend.
 */

export interface User {
  id: number;
  email: string;
  full_name?: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface ChatSession {
  id: string;
  title?: string;
  created_at: string;
  updated_at?: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  confidence_score?: { score: number; level?: 'high' | 'medium' | 'low' };
  sources?: SourceReference[];
  reasoning?: string;
  mode?: RAGMode;
  context_files?: { id: string; filename: string }[];
  diagram_xml?: string;
}

export type RAGMode = 'fast' | 'think';

// Extended message type for UI with additional properties
export interface Message {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  confidence_score?: number;
  confidence_level?: 'high' | 'medium' | 'low';
  sources?: SourceReference[];
  isTyping?: boolean;
  contextFiles?: { id: string; filename: string }[];  // Files used as context
  reasoning?: string;   // Think mode reasoning steps
  mode?: RAGMode;       // Which mode produced this message
  diagramXml?: string;
}

export interface SourceReference {
  document: string;
  page?: number;
  chunk_id?: string;
  relevance_score: number;
  text_snippet?: string;
}

export interface ChatResponse {
  answer: string;
  confidence_score: number;
  confidence_level: 'high' | 'medium' | 'low';
  sources: SourceReference[];
  session_id: string;
  processing_time_ms?: number;
  reasoning?: string;
  mode?: RAGMode;
  diagram_xml?: string;
}

export interface ChatRequest {
  query: string;
  session_id?: string;
  user_id?: number;
  stream?: boolean;
  context_document_ids?: string[];
  mode?: RAGMode;
  context_files?: { id: string; filename: string }[];
}

export interface ChatHistory {
  session_id: string;
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    confidence_score?: number;
    confidence_level?: 'high' | 'medium' | 'low';
    sources?: SourceReference[];
    reasoning?: string;
    mode?: RAGMode;
    context_files?: { id: string; filename: string }[];
    diagram_xml?: string;
  }>;
}

export interface ApiError {
  error: string;
  message: string;
  detail?: string;
  timestamp: string;
}

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export interface ServiceStatus {
  type: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  url?: string;
  model?: string;
  host?: string;
  database?: string;
  documents?: number;
  error?: string;
  message?: string;
}

export interface PingResponse {
  status: 'healthy' | 'degraded' | 'unhealthy' | 'error';
  timestamp: string;
  services: {
    embedding?: ServiceStatus;
    reranker?: ServiceStatus;
    llm?: ServiceStatus;
    database?: ServiceStatus;
    bm25?: ServiceStatus;
  };
  summary: {
    total: number;
    healthy: number;
    unhealthy: number;
  };
  error?: string;
}

export interface DocumentInfo {
  id: string;
  filename: string;
  title?: string;
  file_type?: string;
  file_size?: number;
  vector_count: number;
  category?: string;
  upload_date: string;
}

export interface UserDocumentResponse {
  documents: DocumentInfo[];
  total: number;
}

export interface BulkDeleteRequest {
  document_ids: string[];
  user_id: number;
}

export interface BulkDeleteResponse {
  deleted_count: number;
  failed_ids: string[];
  message: string;
}

export interface TreeGenerationResponse {
  document_id: string;
  status: 'processing' | 'completed' | 'failed' | 'pending';
  node_count?: number;
  message: string;
}

export interface AuraSqlConnection {
  id: string;
  name: string;
  db_type: string;
  host: string;
  port: number;
  username: string;
  database: string;
  schema_name?: string;
  ssl_required: boolean;
}

export interface AuraSqlContext {
  id: string;
  connection_id: string;
  name: string;
  table_names: string[];
  schema_snapshot?: Record<string, unknown[]>;
}

export interface AuraSqlQueryResponse {
  sql: string;
  explanation: string;
  source_tables: string[];
  session_id?: string | null;
  confidence_score?: number | null;
  confidence_level?: 'high' | 'medium' | 'low' | null;
  validation_errors?: string[] | null;
}

export interface AuraSqlExecuteResponse {
  columns: string[];
  rows: Array<Record<string, unknown>>;
}

export interface AuraSqlHistoryItem {
  id: string;
  connection_id: string;
  session_id?: string | null;
  context_id?: string | null;
  natural_language_query?: string | null;
  generated_sql?: string | null;
  source_tables?: string[] | null;
  confidence_score?: number | null;
  confidence_level?: 'high' | 'medium' | 'low' | null;
  status: string;
  created_at: string;
  error_message?: string | null;
}

export interface AuraSqlSession {
  id: string;
  title?: string;
  connection_id?: string | null;
  context_id?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface ResumeFileInfo {
  id: string;
  resume_id: string;
  filename: string;
  status: string;
  created_at: string;
  updated_at?: string | null;
}

export interface ResumeUploadResponse {
  resume: ResumeFileInfo;
}

export interface ResumeListResponse {
  list: ResumeFileInfo[];
  total: number;
}

export interface ResumeAnalyzeRequest {
  user_id: number;
  resume_id: string;
  job_description: string;
}

export interface ResumeAnalyzeResponse {
  analysis_id: string;
  resume_id: string;
  overall_score?: number | null;
  job_description?: string | null;
  analysis: Record<string, unknown>;
  refined_recommendations?: string[] | Record<string, string> | null;
  refined_justifications?: string[] | Record<string, string> | null;
  resume_data?: Record<string, unknown> | null;
  created_at: string;
}

export interface ResumeHistoryResponse {
  list: ResumeAnalyzeResponse[];
  total: number;
}

export interface ResumeDashboardResponse {
  resume_stats: {
    total: number;
    analyzed: number;
    pending: number;
  };
  monthly_stats: Array<{ month: string; uploaded: number; analyzed: number }>;
  latest_analysis?: ResumeAnalyzeResponse | null;
}

// ── ResumeGen Types ──────────────────────────────────────
export interface ResumeGenExperience {
  company: string;
  position: string;
  duration: string;
  responsibilities: string[];
}

export interface ResumeGenEducation {
  institution: string;
  degree: string;
  duration: string;
  gpa?: string;
}

export interface ResumeGenProject {
  name: string;
  descriptions: string[];
  description?: string;
  technologies: string;
}

export interface ResumeGenData {
  name: string;
  email: string;
  location?: string;
  linkedin?: string;
  github?: string;
  experience: ResumeGenExperience[];
  education: ResumeGenEducation[];
  projects: ResumeGenProject[];
  skills: Record<string, string[]>;
}

export interface ResumeGenHealthResponse {
  latex_available: boolean;
  message: string;
}
