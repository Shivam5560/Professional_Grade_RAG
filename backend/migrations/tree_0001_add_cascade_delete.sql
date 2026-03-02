-- Migration: Add CASCADE delete to tree-related foreign keys
-- This ensures deleting a document automatically cleans up tree structures and nodes.

-- Step 1: Drop existing FK constraints on document_tree_structures_nexus_rag
ALTER TABLE document_tree_structures_nexus_rag
    DROP CONSTRAINT IF EXISTS document_tree_structures_nexus_rag_document_id_fkey;

ALTER TABLE document_tree_structures_nexus_rag
    ADD CONSTRAINT document_tree_structures_nexus_rag_document_id_fkey
    FOREIGN KEY (document_id) REFERENCES documents_nexus_rag(id) ON DELETE CASCADE;

-- Step 2: Drop existing FK constraints on tree_nodes_nexus_rag
ALTER TABLE tree_nodes_nexus_rag
    DROP CONSTRAINT IF EXISTS tree_nodes_nexus_rag_tree_id_fkey;

ALTER TABLE tree_nodes_nexus_rag
    ADD CONSTRAINT tree_nodes_nexus_rag_tree_id_fkey
    FOREIGN KEY (tree_id) REFERENCES document_tree_structures_nexus_rag(id) ON DELETE CASCADE;

ALTER TABLE tree_nodes_nexus_rag
    DROP CONSTRAINT IF EXISTS tree_nodes_nexus_rag_document_id_fkey;

ALTER TABLE tree_nodes_nexus_rag
    ADD CONSTRAINT tree_nodes_nexus_rag_document_id_fkey
    FOREIGN KEY (document_id) REFERENCES documents_nexus_rag(id) ON DELETE CASCADE;
