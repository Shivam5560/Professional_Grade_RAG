# NexusMind MCP Server

MCP server for invoking NexusMind backend tools (chat + health + docs) from MCP-capable clients.

This server is intended to be deployed as a central maintainer-controlled MCP service.

## Features
- `health_check`: Ping backend health endpoint
- `chat_query`: Send chat query in `fast`, `think`, or `ask` mode
- `list_user_documents`: List user documents by `userId`
- `list_tools_catalog`: View all MCP tools with icon hints and usage notes

## Setup
```bash
cd mcp-server
npm install
npm run build
```

## Environment
- `NEXUS_API_BASE` (default: `http://localhost:8000/api/v1`)
- `NEXUS_MAINTAINER_TOKEN` (required; maintainer-only token)
- `NEXUS_BEARER_TOKEN` (legacy fallback if maintainer token is not set)
- `NEXUS_DEVELOPER_USER_ID` (optional but recommended, locks all user-scoped tools to one developer user)

## Access control
- This MCP server is standalone over `stdio` (no public HTTP exposure by default).
- It requires `NEXUS_MAINTAINER_TOKEN` (or legacy `NEXUS_BEARER_TOKEN`) to start.
- If `NEXUS_DEVELOPER_USER_ID` is set, user-scoped tools are restricted to that single developer account.

## Tool governance
- Tool definitions are maintained in source code and deployed centrally.
- Only the project maintainer should update tool registrations and redeploy the MCP server.

## Run
```bash
npm start
```

Use the executable output with your MCP client configuration (stdio transport).
