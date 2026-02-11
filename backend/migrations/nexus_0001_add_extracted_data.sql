-- Add extracted_data column to resume_files_nexus_rag table
-- This caches LLM-extracted resume data to reduce API calls from 3 to 2 per analysis

ALTER TABLE resume_files_nexus_rag
ADD COLUMN IF NOT EXISTS extracted_data JSONB DEFAULT NULL;

COMMENT ON COLUMN resume_files_nexus_rag.extracted_data IS 'Cached LLM-extracted resume data (personal_info, education, work_experience, keywords, etc.)';
