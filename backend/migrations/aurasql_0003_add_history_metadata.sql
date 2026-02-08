ALTER TABLE aurasql_query_history_nexus_rag
ADD COLUMN source_tables JSON NULL,
ADD COLUMN confidence_score DOUBLE PRECISION NULL,
ADD COLUMN confidence_level VARCHAR NULL;