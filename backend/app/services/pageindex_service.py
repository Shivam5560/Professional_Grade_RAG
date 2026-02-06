"""
PageIndex Service — manages tree generation, storage, and retrieval.
Orchestrates the full lifecycle of PageIndex trees per document.
"""

import json
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from app.core.pageindex_utils import (
    generate_tree_from_pdf,
    flatten_tree_nodes,
    get_tree_without_text,
    build_node_map,
    _count_nodes,
)
from app.db.models import Document, DocumentTreeStructure, TreeNode
from app.services.groq_service import GroqService
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PageIndexService:
    """
    Manages PageIndex tree structures:
    - Generate tree from PDF using Groq LLM
    - Persist tree + flat nodes to PostgreSQL
    - Retrieve tree for reasoning-based RAG
    """

    def __init__(self, groq_service: GroqService):
        self.groq_service = groq_service

    # ------------------------------------------------------------------
    # Tree Generation
    # ------------------------------------------------------------------

    async def generate_tree(self, pdf_path: str) -> Dict[str, Any]:
        """
        Generate a PageIndex tree structure from a PDF.

        Returns:
            Dict with doc_name, doc_description, structure
        """
        logger.log_operation("🌲 PageIndex: generating tree", pdf=pdf_path)
        tree = await generate_tree_from_pdf(pdf_path, self.groq_service)
        return tree

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def store_tree(
        self,
        db: Session,
        document_id: str,
        tree: Dict[str, Any],
    ) -> DocumentTreeStructure:
        """
        Persist a generated tree (and its flattened nodes) to the database.
        Replaces any existing tree for the same document.
        """
        # Remove old tree if it exists
        existing = (
            db.query(DocumentTreeStructure)
            .filter(DocumentTreeStructure.document_id == document_id)
            .first()
        )
        if existing:
            db.delete(existing)
            db.flush()

        structure = tree.get("structure", [])
        node_count = _count_nodes(structure)

        db_tree = DocumentTreeStructure(
            document_id=document_id,
            tree_json=tree,
            doc_description=tree.get("doc_description", ""),
            node_count=node_count,
            status="completed",
        )
        db.add(db_tree)
        db.flush()  # get db_tree.id

        # Flatten and store individual nodes
        flat_nodes = flatten_tree_nodes(structure)
        for fn in flat_nodes:
            db_node = TreeNode(
                tree_id=db_tree.id,
                document_id=document_id,
                node_id=fn["node_id"],
                title=fn["title"],
                summary=fn.get("summary", ""),
                text_content=fn.get("text_content", ""),
                start_page=fn.get("start_page"),
                end_page=fn.get("end_page"),
                parent_node_id=fn.get("parent_node_id"),
                depth=fn.get("depth", 0),
            )
            db.add(db_node)

        db.commit()
        db.refresh(db_tree)

        logger.log_operation(
            "✅ Tree stored",
            document_id=document_id,
            nodes=node_count,
        )
        return db_tree

    def mark_tree_status(
        self,
        db: Session,
        document_id: str,
        status: str,
        error_message: Optional[str] = None,
    ):
        """Update tree generation status (processing / failed)."""
        existing = (
            db.query(DocumentTreeStructure)
            .filter(DocumentTreeStructure.document_id == document_id)
            .first()
        )
        if existing:
            existing.status = status
            existing.error_message = error_message
            db.commit()
        else:
            db_tree = DocumentTreeStructure(
                document_id=document_id,
                tree_json={},
                status=status,
                error_message=error_message,
            )
            db.add(db_tree)
            db.commit()

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_tree(self, db: Session, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the full tree JSON for a document.
        Returns None if no tree exists or generation hasn't completed.
        """
        db_tree = (
            db.query(DocumentTreeStructure)
            .filter(
                DocumentTreeStructure.document_id == document_id,
                DocumentTreeStructure.status == "completed",
            )
            .first()
        )
        if db_tree and db_tree.tree_json:
            return db_tree.tree_json
        return None

    def get_tree_status(self, db: Session, document_id: str) -> Optional[str]:
        """Get tree generation status for a document."""
        db_tree = (
            db.query(DocumentTreeStructure)
            .filter(DocumentTreeStructure.document_id == document_id)
            .first()
        )
        return db_tree.status if db_tree else None

    def get_node_texts(
        self,
        db: Session,
        document_id: str,
        node_ids: List[str],
    ) -> Dict[str, str]:
        """
        Retrieve text content for specific tree nodes by node_id.
        Returns dict of node_id -> text_content.
        """
        nodes = (
            db.query(TreeNode)
            .filter(
                TreeNode.document_id == document_id,
                TreeNode.node_id.in_(node_ids),
            )
            .all()
        )
        return {n.node_id: n.text_content or "" for n in nodes}

    def has_tree(self, db: Session, document_id: str) -> bool:
        """Check if a completed tree exists for a document."""
        return self.get_tree_status(db, document_id) == "completed"

    def get_documents_with_trees(
        self, db: Session, document_ids: List[str]
    ) -> List[str]:
        """Filter document_ids to only those that have completed trees."""
        results = (
            db.query(DocumentTreeStructure.document_id)
            .filter(
                DocumentTreeStructure.document_id.in_(document_ids),
                DocumentTreeStructure.status == "completed",
            )
            .all()
        )
        return [r[0] for r in results]


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

_pageindex_service: Optional[PageIndexService] = None


def get_pageindex_service() -> PageIndexService:
    """Get or create the global PageIndexService."""
    global _pageindex_service
    if _pageindex_service is None:
        from app.services.groq_service import get_groq_service
        _pageindex_service = PageIndexService(get_groq_service())
    return _pageindex_service
