/**
 * API client for the RAG backend.
 */

import {
  ChatRequest, 
  ChatResponse, 
  ChatHistory, 
  PingResponse, 
  User, 
  ChatSession, 
  ChatMessage,
  UserDocumentResponse,
  BulkDeleteRequest,
  BulkDeleteResponse,
  TreeGenerationResponse,
  AuraSqlConnection,
  AuraSqlContext,
  AuraSqlQueryResponse,
  AuraSqlExecuteResponse,
  AuraSqlHistoryItem,
  AuraSqlSession,
  ResumeUploadResponse,
  ResumeListResponse,
  ResumeAnalyzeRequest,
  ResumeAnalyzeResponse,
  ResumeHistoryResponse,
  ResumeDashboardResponse,
  ResumeGenData,
  ResumeGenHealthResponse
} from './types';
import { useAuthStore } from '@/lib/store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';
const BASE_PATH = `${API_BASE_URL}/api/${API_VERSION}`;

class ApiClient {
  private getAuthHeaders(): Record<string, string> {
    const { accessToken } = useAuthStore.getState();
    return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
  }

  private async refreshTokens(): Promise<boolean> {
    const { refreshToken, loginWithTokens, user } = useAuthStore.getState();
    if (!refreshToken || !user) return false;

    try {
      const response = await fetch(`${BASE_PATH}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;
      const data = await response.json();
      loginWithTokens(data.user, data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${BASE_PATH}${endpoint}`;

    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options?.headers,
      },
      ...options,
    });

    if (response.status === 401) {
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        const retry = await fetch(url, {
          headers: {
            'Content-Type': 'application/json',
            ...this.getAuthHeaders(),
            ...options?.headers,
          },
          ...options,
        });
        if (!retry.ok) {
          const retryError = await retry.json().catch(() => ({ message: 'An error occurred' }));
          throw new Error(retryError.message || retryError.detail?.[0]?.msg || `HTTP ${retry.status}`);
        }
        if (retry.status === 204) {
          return undefined as T;
        }
        return retry.json();
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        message: 'An error occurred',
      }));
      console.error('[API] Request failed:', response.status, error);
      throw new Error(error.message || error.detail?.[0]?.msg || `HTTP ${response.status}`);
    }

    // Handle 204 No Content - don't try to parse JSON
    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  async login(email: string, password: string): Promise<User> {
    const response = await this.request<{ user: User; access_token: string; refresh_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    useAuthStore.getState().loginWithTokens(response.user, response.access_token, response.refresh_token);
    return response.user;
  }

  async register(email: string, password: string, full_name?: string): Promise<User> {
    const response = await this.request<{ user: User; access_token: string; refresh_token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    });
    useAuthStore.getState().loginWithTokens(response.user, response.access_token, response.refresh_token);
    return response.user;
  }

  async getChatHistory(userId: number): Promise<ChatSession[]> {
    return this.request<ChatSession[]>(`/history/${userId}`);
  }

  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    return this.request<ChatMessage[]>(`/history/${sessionId}/messages`);
  }

  async deleteChatSession(sessionId: string): Promise<void> {
    await this.request(`/history/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async query(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/chat/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async queryStream(
    request: ChatRequest,
    onEvent: (event: string, data: unknown) => void
  ): Promise<void> {
    const doStream = async () => {
      const response = await fetch(`${BASE_PATH}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'text/event-stream',
          ...this.getAuthHeaders(),
        },
        body: JSON.stringify({ ...request, stream: true }),
      });
      return response;
    };

    let response = await doStream();

    if (response.status === 401) {
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        response = await doStream();
      }
    }

    if (!response.ok || !response.body) {
      const error = await response.json().catch(() => ({ message: 'Streaming failed' }));
      throw new Error(error.message || `HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        const lines = part.split('\n').filter(Boolean);
        let event = 'message';
        const dataLines: string[] = [];

        for (const line of lines) {
          if (line.startsWith('event:')) {
            event = line.replace('event:', '').trim();
          } else if (line.startsWith('data:')) {
            dataLines.push(line.replace('data:', '').trim());
          }
        }

        const rawData = dataLines.join('\n');
        let parsed: unknown = rawData;
        try {
          parsed = JSON.parse(rawData);
        } catch {
          // Keep raw string if JSON parsing fails.
        }

        onEvent(event, parsed);
      }
    }
  }

  async getHistory(sessionId: string): Promise<ChatHistory> {
    return this.request<ChatHistory>(`/chat/history/${sessionId}`);
  }

  async clearHistory(sessionId: string): Promise<void> {
    await this.request(`/chat/history/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async uploadDocument(
    file: File,
    userId: number,
    metadata?: { title?: string; category?: string }
  ): Promise<Record<string, unknown>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId.toString());
    
    if (metadata?.title) {
      formData.append('title', metadata.title);
    }
    if (metadata?.category) {
      formData.append('category', metadata.category);
    }

    const doUpload = async () => {
      const response = await fetch(`${BASE_PATH}/documents/upload`, {
        method: 'POST',
        headers: {
          ...this.getAuthHeaders(),
        },
        body: formData,
      });
      return response;
    };

    let response = await doUpload();

    if (response.status === 401) {
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        response = await doUpload();
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        message: 'Upload failed',
      }));
      throw new Error(error.message || 'Upload failed');
    }

    return response.json() as Promise<Record<string, unknown>>;
  }

  async getUserDocuments(userId: number): Promise<UserDocumentResponse> {
    return this.request<UserDocumentResponse>(`/documents/my-documents/${userId}`);
  }

  async bulkDeleteDocuments(request: BulkDeleteRequest): Promise<BulkDeleteResponse> {
    return this.request<BulkDeleteResponse>('/documents/bulk-delete', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async generateTree(documentId: string, userId: number): Promise<TreeGenerationResponse> {
    return this.request<TreeGenerationResponse>(`/documents/${documentId}/generate-tree`, {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }

  async createAuraSqlConnection(payload: {
    name: string;
    db_type: string;
    host: string;
    port: number;
    username: string;
    password: string;
    database: string;
    schema_name?: string;
    ssl_required?: boolean;
  }): Promise<AuraSqlConnection> {
    return this.request<AuraSqlConnection>('/aurasql/connections', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listAuraSqlConnections(): Promise<AuraSqlConnection[]> {
    const response = await this.request<{ connections: AuraSqlConnection[] }>('/aurasql/connections', {
      method: 'GET',
    });
    return response.connections;
  }

  async deleteAuraSqlConnection(connectionId: string): Promise<void> {
    await this.request<void>(`/aurasql/connections/${connectionId}`, {
      method: 'DELETE',
    });
  }

  async getAuraSqlConnection(connectionId: string): Promise<AuraSqlConnection> {
    return this.request<AuraSqlConnection>(`/aurasql/connections/${connectionId}`, {
      method: 'GET',
    });
  }

  async updateAuraSqlConnection(connectionId: string, payload: Partial<{ 
    name: string;
    db_type: string;
    host: string;
    port: number;
    username: string;
    password: string;
    database: string;
    schema_name?: string;
    ssl_required: boolean;
  }>): Promise<AuraSqlConnection> {
    return this.request<AuraSqlConnection>(`/aurasql/connections/${connectionId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async listAuraSqlTables(connectionId: string): Promise<string[]> {
    const response = await this.request<{ tables: string[] }>(`/aurasql/connections/${connectionId}/tables`, {
      method: 'GET',
    });
    return response.tables;
  }

  async createAuraSqlContext(payload: {
    connection_id: string;
    name: string;
    table_names: string[];
    is_temporary?: boolean;
  }): Promise<AuraSqlContext> {
    return this.request<AuraSqlContext>('/aurasql/contexts', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async listAuraSqlContexts(): Promise<AuraSqlContext[]> {
    const response = await this.request<{ contexts: AuraSqlContext[] }>('/aurasql/contexts', {
      method: 'GET',
    });
    return response.contexts;
  }

  async getAuraSqlContext(contextId: string): Promise<AuraSqlContext> {
    return this.request<AuraSqlContext>(`/aurasql/contexts/${contextId}`, {
      method: 'GET',
    });
  }

  async refreshAuraSqlContext(contextId: string): Promise<AuraSqlContext> {
    return this.request<AuraSqlContext>(`/aurasql/contexts/${contextId}/refresh`, {
      method: 'POST',
    });
  }

  async updateAuraSqlContext(contextId: string, payload: Partial<{
    name: string;
    table_names: string[];
    is_temporary: boolean;
  }>): Promise<AuraSqlContext> {
    return this.request<AuraSqlContext>(`/aurasql/contexts/${contextId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async deleteAuraSqlContext(contextId: string): Promise<void> {
    await this.request<void>(`/aurasql/contexts/${contextId}`, {
      method: 'DELETE',
    });
  }

  async getAuraSqlRecommendations(contextId: string): Promise<string[]> {
    const response = await this.request<{ recommendations: string[] }>('/aurasql/recommendations', {
      method: 'POST',
      body: JSON.stringify({ context_id: contextId }),
    });
    return response.recommendations;
  }

  async generateAuraSqlQuery(contextId: string, query: string): Promise<AuraSqlQueryResponse> {
    return this.request<AuraSqlQueryResponse>('/aurasql/query', {
      method: 'POST',
      body: JSON.stringify({ context_id: contextId, query }),
    });
  }

  async generateAuraSqlQueryWithSession(contextId: string, query: string, sessionId?: string): Promise<AuraSqlQueryResponse> {
    return this.request<AuraSqlQueryResponse>('/aurasql/query', {
      method: 'POST',
      body: JSON.stringify({ context_id: contextId, query, session_id: sessionId }),
    });
  }

  async executeAuraSql(connectionId: string, sql: string): Promise<AuraSqlExecuteResponse> {
    return this.request<AuraSqlExecuteResponse>('/aurasql/execute', {
      method: 'POST',
      body: JSON.stringify({ connection_id: connectionId, sql }),
    });
  }

  async executeAuraSqlWithSession(connectionId: string, sql: string, sessionId?: string): Promise<AuraSqlExecuteResponse> {
    return this.request<AuraSqlExecuteResponse>('/aurasql/execute', {
      method: 'POST',
      body: JSON.stringify({ connection_id: connectionId, sql, session_id: sessionId }),
    });
  }

  async listAuraSqlHistory(): Promise<AuraSqlHistoryItem[]> {
    return this.request<AuraSqlHistoryItem[]>('/aurasql/history', {
      method: 'GET',
    });
  }

  async listAuraSqlSessions(): Promise<AuraSqlSession[]> {
    return this.request<AuraSqlSession[]>('/aurasql/history/sessions', {
      method: 'GET',
    });
  }

  async uploadResume(file: File, userId: number): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', userId.toString());

    const doUpload = async () => {
      const response = await fetch(`${BASE_PATH}/nexus/resumes/upload`, {
        method: 'POST',
        headers: {
          ...this.getAuthHeaders(),
        },
        body: formData,
      });
      return response;
    };

    let response = await doUpload();

    if (response.status === 401) {
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        response = await doUpload();
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Upload failed' }));
      throw new Error(error.message || 'Upload failed');
    }

    return response.json();
  }

  async listResumes(userId: number): Promise<ResumeListResponse> {
    return this.request<ResumeListResponse>(`/nexus/resumes/${userId}`);
  }

  async analyzeResume(request: ResumeAnalyzeRequest): Promise<ResumeAnalyzeResponse> {
    return this.request<ResumeAnalyzeResponse>('/nexus/resumes/analyze', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getResumeHistory(userId: number): Promise<ResumeHistoryResponse> {
    return this.request<ResumeHistoryResponse>(`/nexus/resumes/history/${userId}`);
  }

  async getResumeDashboard(userId: number): Promise<ResumeDashboardResponse> {
    return this.request<ResumeDashboardResponse>(`/nexus/dashboard/${userId}`);
  }

  async deleteResume(userId: number, resumeId: string): Promise<{ message: string; resume_id: string }> {
    return this.request<{ message: string; resume_id: string }>(`/nexus/resumes/${userId}/${resumeId}`, {
      method: 'DELETE',
    });
  }

  async getAuraSqlSessionHistory(sessionId: string): Promise<AuraSqlHistoryItem[]> {
    return this.request<AuraSqlHistoryItem[]>(`/aurasql/history/sessions/${sessionId}`, {
      method: 'GET',
    });
  }

  async getTreeStatus(documentId: string): Promise<TreeGenerationResponse> {
    return this.request<TreeGenerationResponse>(`/documents/${documentId}/tree-status`);
  }

  async checkHealth(): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>('/health');
  }

  async pingServices(): Promise<PingResponse> {
    return this.request<PingResponse>('/health/ping');
  }

  // ── ResumeGen Methods ────────────────────────────────────
  async checkResumeGenHealth(): Promise<ResumeGenHealthResponse> {
    return this.request<ResumeGenHealthResponse>('/resumegen/health');
  }

  async generateResumePdf(data: ResumeGenData): Promise<Blob> {
    const url = `${BASE_PATH}/resumegen/generate`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify({ data, format: 'pdf' }),
    });

    if (response.status === 401) {
      const refreshed = await this.refreshTokens();
      if (refreshed) {
        const retry = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...this.getAuthHeaders(),
          },
          body: JSON.stringify({ data, format: 'pdf' }),
        });
        if (!retry.ok) {
          const err = await retry.json().catch(() => ({ detail: 'Generation failed' }));
          throw new Error(err.detail || `HTTP ${retry.status}`);
        }
        return retry.blob();
      }
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Generation failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.blob();
  }

  async generateResumeLatex(data: ResumeGenData): Promise<string> {
    const url = `${BASE_PATH}/resumegen/generate`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
      },
      body: JSON.stringify({ data, format: 'latex' }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Generation failed' }));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }
    return response.text();
  }
}

export const apiClient = new ApiClient();
