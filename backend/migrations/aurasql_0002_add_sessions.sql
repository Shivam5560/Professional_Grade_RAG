CREATE TABLE IF NOT EXISTS aurasql_chat_sessions_nexus_rag (
  id VARCHAR PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users_nexus_rag(id),
  title VARCHAR,
  connection_id VARCHAR REFERENCES aurasql_connections_nexus_rag(id),
  context_id VARCHAR REFERENCES aurasql_contexts_nexus_rag(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ
);

ALTER TABLE aurasql_query_history_nexus_rag
  ADD COLUMN IF NOT EXISTS session_id VARCHAR REFERENCES aurasql_chat_sessions_nexus_rag(id);

CREATE INDEX IF NOT EXISTS idx_aurasql_query_history_session_id
  ON aurasql_query_history_nexus_rag(session_id);
