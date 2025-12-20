"""
Main RAG engine orchestrating retrieval and generation.
"""

import time
import uuid
from typing import Optional, Dict, Any, List
from llama_index.core.schema import NodeWithScore
from app.core.retriever import get_hybrid_retriever
from app.core.reranker import get_reranker
from app.core.confidence_scorer import get_confidence_scorer
from app.core.context_manager import get_context_manager
from app.services.groq_service import get_groq_service
from app.models.prompts import PROFESSIONAL_SYSTEM_PROMPT
from app.models.schemas import SourceReference
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RAGEngine:
    """
    Main RAG engine that orchestrates the entire pipeline:
    1. Context-aware query reformulation
    2. Hybrid retrieval (BM25 + Vector)
    3. Reranking
    4. Response generation with Groq
    5. Confidence scoring
    """
    
    def __init__(self):
        """Initialize RAG engine with all components."""
        # Get services
        self.groq_service = get_groq_service()
        self.context_manager = get_context_manager()
        self.confidence_scorer = get_confidence_scorer()
        
        # Don't initialize retriever yet - will be lazy loaded
        self.hybrid_retriever = None
        self.reranker = get_reranker()
        
        # Get LLM from Groq service
        self.llm = self.groq_service.get_llm()
        
        logger.info("rag_engine_initialized")
    
    def _ensure_retriever(self):
        """Lazy load the retriever if not already initialized."""
        if self.hybrid_retriever is None:
            self.hybrid_retriever = get_hybrid_retriever()
        return self.hybrid_retriever
    
    def _extract_sources(self, nodes: List[NodeWithScore]) -> List[SourceReference]:
        """
        Extract source references from retrieved nodes.
        
        Args:
            nodes: Retrieved and reranked nodes
            
        Returns:
            List of source references
        """
        sources = []
        
        for node in nodes:
            metadata = node.node.metadata or {}
            
            source = SourceReference(
                document=metadata.get("filename", "Unknown"),
                page=metadata.get("page"),
                chunk_id=metadata.get("chunk_id"),
                relevance_score=node.score or 0.0,
                text_snippet=node.node.get_content()[:200] + "..." if len(node.node.get_content()) > 200 else node.node.get_content()
            )
            sources.append(source)
        
        return sources
    
    async def query(
        self,
        query: str,
        session_id: Optional[str] = None,
        use_context: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a RAG query.
        
        Args:
            query: User query
            session_id: Session identifier for context
            use_context: Whether to use conversation context
            
        Returns:
            Dictionary with answer, confidence, and sources
        """
        start_time = time.time()
        
        try:
            # Generate session ID if not provided
            if session_id is None:
                session_id = str(uuid.uuid4())
            
            # Add user message to context
            self.context_manager.add_message(session_id, "user", query)
            
            # Reformulate query with context if enabled
            if use_context:
                reformulated_query = self.context_manager.reformulate_query(session_id, query)
            else:
                reformulated_query = query
            
            logger.info(
                "query_received",
                session_id=session_id,
                query_length=len(query),
                reformulated_length=len(reformulated_query),
            )
            
            # Lazy load the retriever (will check DB for existing documents)
            retriever = self._ensure_retriever()
            
            # Check if retriever is available (documents exist in DB)
            if retriever is None:
                logger.warning("no_documents_available", query=query)
                answer = "I don't have any documents in my knowledge base yet. Please upload some documents first before asking questions."
                confidence_result = {
                    "confidence_score": 0.0,
                    "confidence_level": "low",
                    "breakdown": {}
                }
                sources = []
            else:
                # Step 1: Hybrid Retrieval
                from llama_index.core.schema import QueryBundle
                query_bundle = QueryBundle(query_str=reformulated_query)
                retrieved_nodes = retriever.retrieve(query_bundle)
            
                if not retrieved_nodes:
                    logger.warning("no_nodes_retrieved", query=query)
                    answer = "I don't have sufficient information in my knowledge base to answer this question accurately."
                    confidence_result = {
                        "confidence_score": 0.0,
                        "confidence_level": "low",
                        "breakdown": {}
                    }
                    sources = []
                else:
                    # Step 2: Reranking with LlamaIndex's SentenceTransformerRerank
                    # This uses BGE reranker (cross-encoder) for better relevance scoring
                    reranked_nodes = self.reranker._postprocess_nodes(
                        retrieved_nodes,
                        query_str=reformulated_query
                    )
                    
                    # Step 3: Build context from nodes
                    context_str = "\n\n".join([
                        f"[Source: {node.node.metadata.get('filename', 'Unknown')}]\n{node.node.get_content()}"
                        for node in reranked_nodes
                    ])
                    
                    # Step 4: Get conversation history
                    chat_history = self.context_manager.get_chat_messages(session_id)
                    
                    # Step 5: Generate response with system prompt
                    prompt = f"""{PROFESSIONAL_SYSTEM_PROMPT}

Context from knowledge base:
{context_str}

User Question: {query}

Provide a comprehensive answer based on the context above."""
                    
                    # Generate answer
                    response = await self.llm.acomplete(prompt)
                    answer = response.text.strip()
                    
                    # Extract LLM's self-assessment confidence from the answer
                    llm_confidence = self._extract_llm_confidence(answer)
                    # Remove the CONFIDENCE: XX line from the answer for cleaner display
                    answer = self._clean_answer(answer)
                    
                    # Step 6: Extract sources
                    sources = self._extract_sources(reranked_nodes)
                    
                    # Step 7: Calculate confidence
                    confidence_result = self.confidence_scorer.calculate_confidence(
                        query=query,
                        nodes=reranked_nodes,
                        answer=answer,
                        llm_assessment=llm_confidence  # Pass LLM's self-assessment
                    )
            
            # Add assistant message to context
            self.context_manager.add_message(
                session_id,
                "assistant",
                answer,
                confidence_score=confidence_result["confidence_score"]
            )
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000  # milliseconds
            
            result = {
                "answer": answer,
                "confidence_score": confidence_result["confidence_score"],
                "confidence_level": confidence_result["confidence_level"],
                "sources": sources,
                "session_id": session_id,
                "processing_time_ms": round(processing_time, 2),
            }
            
            logger.info(
                "query_completed",
                session_id=session_id,
                confidence_score=confidence_result["confidence_score"],
                num_sources=len(sources),
                processing_time_ms=processing_time,
            )
            
            return result
            
        except Exception as e:
            logger.error("query_failed", error=str(e), query=query)
            raise
    
    async def stream_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        use_context: bool = True
    ):
        """
        Execute a RAG query with streaming response.
        
        Args:
            query: User query
            session_id: Session identifier
            use_context: Whether to use conversation context
            
        Yields:
            Response chunks
        """
        # This would implement streaming using async generators
        # For now, we'll keep it simple with the regular query
        result = await self.query(query, session_id, use_context)
        
        # Yield the complete result
        # In a real streaming implementation, we'd yield tokens as they're generated
        yield result
    
    def _extract_llm_confidence(self, answer: str) -> Optional[float]:
        """
        Extract LLM's self-assessed confidence score from the answer.
        
        Looks for pattern: CONFIDENCE: XX where XX is a number between 0-100.
        
        Args:
            answer: The LLM's response text
            
        Returns:
            Confidence score as a float 0-1, or None if not found
        """
        import re
        
        # Look for CONFIDENCE: XX pattern (case insensitive)
        pattern = r'CONFIDENCE:\s*(\d+)'
        match = re.search(pattern, answer, re.IGNORECASE)
        
        if match:
            confidence_value = int(match.group(1))
            # Normalize from 0-100 to 0-1
            normalized = min(max(confidence_value / 100.0, 0.0), 1.0)
            logger.info(
                "llm_confidence_extracted",
                raw_value=confidence_value,
                normalized=normalized
            )
            return normalized
        
        logger.warning("llm_confidence_not_found", answer_preview=answer[:200])
        return None
    
    def _clean_answer(self, answer: str) -> str:
        """
        Remove the CONFIDENCE: XX line from the answer for cleaner display.
        
        Args:
            answer: The LLM's response text
            
        Returns:
            Cleaned answer without the confidence line
        """
        import re
        
        # Remove CONFIDENCE: XX line (and surrounding whitespace/newlines)
        pattern = r'\n*CONFIDENCE:\s*\d+\s*\n*'
        cleaned = re.sub(pattern, '', answer, flags=re.IGNORECASE)
        
        # Clean up any trailing/leading whitespace
        cleaned = cleaned.strip()
        
        return cleaned


# Global instance
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get or create the global RAG engine instance."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
