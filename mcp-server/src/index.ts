import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const API_BASE = process.env.NEXUS_API_BASE ?? "http://localhost:8000/api/v1";
const TOKEN = process.env.NEXUS_MAINTAINER_TOKEN ?? process.env.NEXUS_BEARER_TOKEN;
const DEVELOPER_USER_ID = process.env.NEXUS_DEVELOPER_USER_ID
  ? Number(process.env.NEXUS_DEVELOPER_USER_ID)
  : undefined;

if (!TOKEN) {
  throw new Error("NEXUS_MAINTAINER_TOKEN is required (or legacy NEXUS_BEARER_TOKEN). Use a maintainer-only token.");
}

if (DEVELOPER_USER_ID !== undefined && Number.isNaN(DEVELOPER_USER_ID)) {
  throw new Error("NEXUS_DEVELOPER_USER_ID must be a valid number when provided.");
}

function authHeaders(): Record<string, string> {
  return TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {};
}

function enforceDeveloperUser(userId?: number): number | undefined {
  if (DEVELOPER_USER_ID === undefined) {
    return userId;
  }
  if (userId !== undefined && userId !== DEVELOPER_USER_ID) {
    throw new Error("This MCP server is locked to the configured developer user.");
  }
  return DEVELOPER_USER_ID;
}

async function backendFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = (data as { detail?: string; message?: string }).detail
      || (data as { detail?: string; message?: string }).message
      || `HTTP ${response.status}`;
    throw new Error(message);
  }
  return data;
}

const server = new McpServer({
  name: "nexusmind-mcp",
  version: "0.1.0",
});

server.registerTool(
  "health_check",
  {
    title: "Nexus Health Check",
    description: "Check backend and dependency health",
    inputSchema: {},
  },
  async () => {
    const result = await backendFetch("/health/ping");
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }
);

server.registerTool(
  "chat_query",
  {
    title: "Chat Query",
    description: "Run chat query using fast/think/ask modes",
    inputSchema: {
      query: z.string().min(1),
      mode: z.enum(["fast", "think", "ask"]).default("fast"),
      sessionId: z.string().optional(),
      userId: z.number().optional(),
      askFiles: z.array(z.object({
        id: z.string(),
        filename: z.string(),
        content: z.string(),
      })).optional(),
    },
  },
  async ({ query, mode, sessionId, userId, askFiles }) => {
    const effectiveUserId = enforceDeveloperUser(userId);
    const result = await backendFetch("/chat/query", {
      method: "POST",
      body: JSON.stringify({
        query,
        mode,
        session_id: sessionId,
        user_id: effectiveUserId,
        ask_files: askFiles,
      }),
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }
);

server.registerTool(
  "list_user_documents",
  {
    title: "List User Documents",
    description: "List uploaded documents for a user",
    inputSchema: {
      userId: z.number(),
    },
  },
  async ({ userId }) => {
    const effectiveUserId = enforceDeveloperUser(userId);
    if (effectiveUserId === undefined) {
      throw new Error("userId is required when NEXUS_DEVELOPER_USER_ID is not set.");
    }
    const result = await backendFetch(`/documents/my-documents/${effectiveUserId}`);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }
);

server.registerTool(
  "list_tools_catalog",
  {
    title: "List MCP Tools",
    description: "Show available MCP tools with icon hints and brief usage notes",
    inputSchema: {},
  },
  async () => {
    const tools = [
      {
        icon: "🩺",
        name: "health_check",
        description: "Check backend and dependency health",
      },
      {
        icon: "💬",
        name: "chat_query",
        description: "Run chat query in fast/think/ask mode",
      },
      {
        icon: "📚",
        name: "list_user_documents",
        description: "List uploaded documents for developer user",
      },
      {
        icon: "🧭",
        name: "list_tools_catalog",
        description: "Return MCP tool catalog",
      },
    ];

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            server: "nexusmind-mcp",
            developer_only: true,
            tools,
          }, null, 2),
        },
      ],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
