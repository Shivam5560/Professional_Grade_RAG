"""
PageIndex RAG Engine — Think Mode.
Reasoning-based retrieval using hierarchical tree search,
then answer generation from the selected tree nodes.
"""

import os
import time
import json
import copy
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from app.core.pageindex_utils import (
    groq_llm_call,
    extract_json_from_response,
    get_tree_without_text,
    build_node_map,
)
from app.services.pageindex_service import PageIndexService
from app.services.groq_service import GroqService
from app.models.schemas import SourceReference
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Prompts for think-mode reasoning
# ---------------------------------------------------------------------------

TREE_SEARCH_PROMPT = """You are an expert at navigating hierarchical document structures to find the most relevant sections for answering a question.

Below is the tree structure of a document. Each node has a title, summary, node_id, and page range. You need to identify which nodes contain information most relevant to the user's question.

Document: {doc_name}
Description: {doc_description}

Tree Structure (without full text — only titles and summaries):
{tree_structure}

User Question: {query}

Analyze the tree structure and select the most relevant nodes. Think step-by-step:
1. What is the user asking about?
2. Which top-level sections are likely to contain the answer?
3. Which sub-sections are most specific to the question?

Return your analysis as JSON in this exact format:
{{
    "reasoning": "Your step-by-step reasoning about which sections are relevant and why",
    "selected_node_ids": ["0001", "0003", "0005"],
    "confidence": "high|medium|low"
}}

Select between 1 and 5 nodes. Prefer more specific (deeper) nodes over broad parent nodes when possible. Only select nodes whose summaries suggest they contain relevant information."""


THINK_MODE_ANSWER_PROMPT = """You are an expert AI assistant using a reasoning-based retrieval system. You navigated a document's hierarchical structure to find the most relevant sections for the user's question.

**Retrieval Reasoning:**
{reasoning}

**Retrieved Sections:**
{context}

**User Question:** {query}

Provide a comprehensive answer based on the retrieved sections above.

**Instructions:**
- Use ALL relevant information from the retrieved sections
- Cite sections using [Section: Title] format
- Structure your response with clear headings and formatting
- Be thorough but concise
- If the retrieved sections don't fully answer the question, say so honestly

**Format your response with proper Markdown.**

End your response with: `CONFIDENCE: XX` (0-100) based on how well the retrieved sections answer the question."""


MULTI_DOC_SELECT_PROMPT = """You are deciding which documents are most likely to contain the answer to a question.

Available documents:
{doc_list}

Question: {query}

Return a JSON array of the document IDs most likely to contain the answer (select 1-3):
{{
    "selected_doc_ids": ["id1", "id2"]
}}
"""


class PageIndexRAGEngine:
    """
    Think-mode RAG engine that uses PageIndex tree structures
    for reasoning-based retrieval and answer generation.
    """

    def __init__(
        self,
        groq_service: GroqService,
        pageindex_service: PageIndexService,
    ):
        self.groq_service = groq_service
        self.pageindex_service = pageindex_service

    # ------------------------------------------------------------------
    # Main Query
    # ------------------------------------------------------------------

    async def query(
        self,
        query: str,
        db: Session,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        context_document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a think-mode query using PageIndex tree reasoning.

        Steps:
        1. Identify which documents have trees
        2. For each document, use LLM to search the tree structure
        3. Retrieve full text of selected nodes
        4. Generate answer from gathered context

        Returns:
            Dict with answer, confidence, sources, reasoning, mode
        """
        start_time = time.time()

        logger.log_operation(
            "🧠 Think mode query started",
            query=query[:80],
            user_id=user_id,
        )

        # Step 1: Get documents that have tree structures
        if context_document_ids:
            # Get ALL user docs in the context list
            all_target_ids = context_document_ids
        else:
            # Get all user documents
            from app.db.models import Document
            user_docs = (
                db.query(Document.id)
                .filter(Document.user_id == user_id)
                .all()
            )
            all_target_ids = [d[0] for d in user_docs]

        if not all_target_ids:
            processing_time = (time.time() - start_time) * 1000
            return {
                "answer": "No documents found. Please upload documents first.",
                "confidence_score": 0.0,
                "confidence_level": "low",
                "sources": [],
                "session_id": session_id or "",
                "processing_time_ms": round(processing_time, 2),
                "reasoning": "No documents found for this user.",
                "mode": "think",
            }

        # Check which docs already have trees
        doc_ids_with_trees = self.pageindex_service.get_documents_with_trees(
            db, all_target_ids
        )

        # Auto-generate trees for docs that don't have one yet
        docs_needing_trees = [
            did for did in all_target_ids if did not in doc_ids_with_trees
        ]

        if docs_needing_trees:
            from app.db.models import Document as DocModel

            newly_generated = await self._auto_generate_trees(
                db, docs_needing_trees
            )
            if newly_generated:
                doc_ids_with_trees.extend(newly_generated)
                logger.log_operation(
                    "🌲 Auto-generated trees for think mode",
                    count=len(newly_generated),
                )

        if not doc_ids_with_trees:
            processing_time = (time.time() - start_time) * 1000
            return {
                "answer": "Tree generation failed for all documents. Only PDF documents support Think mode. Please try Fast mode or upload a PDF.",
                "confidence_score": 0.0,
                "confidence_level": "low",
                "sources": [],
                "session_id": session_id or "",
                "processing_time_ms": round(processing_time, 2),
                "reasoning": "Attempted to auto-generate trees but failed. Documents may not be PDFs or PDFs are missing from disk.",
                "mode": "think",
            }

        # Step 2: Search trees across all relevant documents
        all_reasoning_parts: List[str] = []
        all_context_sections: List[Dict[str, Any]] = []
        all_sources: List[SourceReference] = []

        for doc_id in doc_ids_with_trees:
            tree_data = self.pageindex_service.get_tree(db, doc_id)
            if not tree_data:
                continue

            doc_name = tree_data.get("doc_name", "Unknown")
            doc_description = tree_data.get("doc_description", "")
            structure = tree_data.get("structure", [])

            if not structure:
                continue

            # Get tree without text for search prompt
            tree_no_text = get_tree_without_text(structure)

            # LLM searches the tree
            search_prompt = TREE_SEARCH_PROMPT.format(
                doc_name=doc_name,
                doc_description=doc_description,
                tree_structure=json.dumps(tree_no_text, indent=2)[:12000],
                query=query,
            )

            try:
                search_response = await groq_llm_call(search_prompt, self.groq_service)
                search_result = extract_json_from_response(search_response)
            except Exception as e:
                logger.log_error("Tree search failed", e, doc_id=doc_id)
                continue

            reasoning = search_result.get("reasoning", "")
            selected_ids = search_result.get("selected_node_ids", [])
            search_confidence = search_result.get("confidence", "medium")

            if reasoning:
                all_reasoning_parts.append(
                    f"**{doc_name}**: {reasoning}"
                )

            if not selected_ids:
                continue

            # Step 3: Retrieve full text of selected nodes
            node_map = build_node_map(structure)
            for nid in selected_ids:
                node = node_map.get(nid)
                if node:
                    section_text = node.get("text", "")
                    section_title = node.get("title", "Untitled")
                    start_page = node.get("start_index")
                    end_page = node.get("end_index")

                    all_context_sections.append({
                        "doc_name": doc_name,
                        "title": section_title,
                        "text": section_text,
                        "start_page": start_page,
                        "end_page": end_page,
                        "node_id": nid,
                    })

                    all_sources.append(
                        SourceReference(
                            document=doc_name,
                            page=start_page,
                            chunk_id=f"node_{nid}",
                            relevance_score=1.0 if search_confidence == "high" else 0.8 if search_confidence == "medium" else 0.5,
                            text_snippet=(node.get("summary", "") or section_text[:200]) + "..."
                            if len(node.get("summary", "") or section_text) > 200
                            else (node.get("summary", "") or section_text[:200]),
                        )
                    )

        # Step 4: Generate answer from gathered context
        combined_reasoning = "\n\n".join(all_reasoning_parts) if all_reasoning_parts else "No specific reasoning available."

        if not all_context_sections:
            processing_time = (time.time() - start_time) * 1000
            return {
                "answer": "I searched the document structure but couldn't find sections relevant to your question. Try rephrasing your question or switching to Fast mode for keyword-based retrieval.",
                "confidence_score": 10.0,
                "confidence_level": "low",
                "sources": [],
                "session_id": session_id or "",
                "processing_time_ms": round(processing_time, 2),
                "reasoning": combined_reasoning,
                "mode": "think",
            }

        # Build context string
        context_str = ""
        for section in all_context_sections:
            context_str += f"\n\n---\n**[{section['doc_name']} — {section['title']}]** (Pages {section['start_page']}-{section['end_page']})\n\n"
            context_str += section["text"][:8000]  # Limit per section

        # Truncate total context if needed
        if len(context_str) > 30000:
            context_str = context_str[:30000] + "\n\n[Context truncated for length]"

        answer_prompt = THINK_MODE_ANSWER_PROMPT.format(
            reasoning=combined_reasoning,
            context=context_str,
            query=query,
        )

        try:
            response = await groq_llm_call(answer_prompt, self.groq_service)
        except Exception as e:
            logger.log_error("Think mode answer generation failed", e)
            processing_time = (time.time() - start_time) * 1000
            return {
                "answer": "Failed to generate an answer. Please try again.",
                "confidence_score": 0.0,
                "confidence_level": "low",
                "sources": all_sources,
                "session_id": session_id or "",
                "processing_time_ms": round(processing_time, 2),
                "reasoning": combined_reasoning,
                "mode": "think",
            }

        # Extract confidence from the answer
        answer = response
        confidence_score = self._extract_confidence(answer)
        answer = self._clean_confidence_line(answer)

        if confidence_score is None:
            confidence_score = 65.0

        confidence_level = (
            "high" if confidence_score >= 75
            else "medium" if confidence_score >= 40
            else "low"
        )

        processing_time = (time.time() - start_time) * 1000

        result = {
            "answer": answer,
            "confidence_score": confidence_score,
            "confidence_level": confidence_level,
            "sources": all_sources,
            "session_id": session_id or "",
            "processing_time_ms": round(processing_time, 2),
            "reasoning": combined_reasoning,
            "mode": "think",
        }

        logger.log_operation(
            "✅ Think mode query completed",
            confidence=f"{confidence_score:.1f}",
            sources=len(all_sources),
            sections=len(all_context_sections),
            duration_ms=f"{processing_time:.0f}",
        )

        return result

    # ------------------------------------------------------------------
    # Auto-generate trees for Think mode
    # ------------------------------------------------------------------

    async def _auto_generate_trees(
        self,
        db: Session,
        document_ids: List[str],
    ) -> List[str]:
        """
        Automatically generate PageIndex trees for documents that lack them.
        Called inline (awaited) so the think-mode query can proceed immediately.

        Only processes PDF documents whose files exist on disk.

        Returns:
            List of document IDs for which trees were successfully generated.
        """
        from app.db.models import Document as DocModel

        successfully_generated: List[str] = []

        for doc_id in document_ids:
            doc = db.query(DocModel).filter(DocModel.id == doc_id).first()
            if not doc:
                continue

            # Only PDFs support tree generation
            if doc.file_type and doc.file_type.lower() not in [".pdf"]:
                logger.info(
                    "skip_tree_gen_non_pdf",
                    document_id=doc_id,
                    file_type=doc.file_type,
                )
                continue

            # Locate PDF file on disk - stored as {document_id}.pdf
            pdf_path = os.path.join(
                settings.data_dir, "documents", f"{doc_id}.pdf"
            )
            
            if not os.path.exists(pdf_path):
                logger.warning(
                    "pdf_not_found_for_tree_gen",
                    document_id=doc_id,
                    expected_path=pdf_path,
                )
                continue

            try:
                logger.log_operation(
                    "🌲 Auto-generating tree (inline)",
                    document_id=doc_id,
                    filename=doc.filename,
                )
                self.pageindex_service.mark_tree_status(db, doc_id, "processing")

                tree = await self.pageindex_service.generate_tree(pdf_path)
                self.pageindex_service.store_tree(db, doc_id, tree)

                successfully_generated.append(doc_id)
                logger.log_operation(
                    "✅ Auto-generated tree complete",
                    document_id=doc_id,
                )
            except Exception as e:
                logger.log_error(
                    "Auto tree generation failed",
                    e,
                    document_id=doc_id,
                )
                self.pageindex_service.mark_tree_status(
                    db, doc_id, "failed", error_message=str(e)
                )

        return successfully_generated

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_confidence(text: str) -> Optional[float]:
        """Extract CONFIDENCE: XX from LLM response."""
        import re
        match = re.search(r"CONFIDENCE:\s*(\d+)", text, re.IGNORECASE)
        if match:
            return min(max(float(match.group(1)), 0.0), 100.0)
        return None

    @staticmethod
    def _clean_confidence_line(text: str) -> str:
        """Remove CONFIDENCE: XX line from answer."""
        import re
        cleaned = re.sub(r"\n*CONFIDENCE:\s*\d+\s*\n*", "", text, flags=re.IGNORECASE)
        return cleaned.strip()


# ---------------------------------------------------------------------------
# Global instance
# ---------------------------------------------------------------------------

_pageindex_rag_engine: Optional[PageIndexRAGEngine] = None


def get_pageindex_rag_engine() -> PageIndexRAGEngine:
    """Get or create the global PageIndexRAGEngine."""
    global _pageindex_rag_engine
    if _pageindex_rag_engine is None:
        from app.services.groq_service import get_groq_service
        from app.services.pageindex_service import get_pageindex_service
        _pageindex_rag_engine = PageIndexRAGEngine(
            groq_service=get_groq_service(),
            pageindex_service=get_pageindex_service(),
        )
    return _pageindex_rag_engine
