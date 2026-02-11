-- Clear cached embeddings for specific resume (force re-embedding with new chunk size)
-- Current resume ID from logs:
DELETE FROM nexus_resume_embeddings WHERE metadata_->>'resume_id' = 'SHIVAM-20260210-GUBM';

-- Optional: Clear ALL Nexus embeddings to force complete re-index
-- Uncomment if you want to clear everything:
-- DELETE FROM nexus_resume_embeddings;

-- Check remaining count
SELECT COUNT(*) as total_embeddings FROM nexus_resume_embeddings;
