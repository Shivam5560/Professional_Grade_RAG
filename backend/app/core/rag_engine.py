"""
Main RAG engine orchestrating retrieval and generation.
"""

import time
import uuid
from typing import Optional, Dict, Any, List, AsyncGenerator
from llama_index.core.schema import NodeWithScore, QueryBundle
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
        
        logger.log_operation("🔧 RAG engine initialized")
    
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

        def _build_prompt(self, context_str: str, history_str: str, query: str) -> str:
            """Build the final prompt with context and short-term memory."""
            history_block = ""
            if history_str:
                history_block = f"\n\nConversation context:\n{history_str}"

            return f"""{PROFESSIONAL_SYSTEM_PROMPT}

    Context from knowledge base:
    {context_str}
    {history_block}

    User Question: {query}

    Provide a comprehensive answer based on the context above."""
    
    async def query(
        self,
        query: str,
        session_id: Optional[str] = None,
        use_context: bool = True,
        user_id: Optional[int] = None,
        context_document_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a RAG query.
        
        Args:
            query: User query
            session_id: Session identifier for context
            use_context: Whether to use conversation context
            user_id: User ID to filter documents (user can only query their own documents)
            context_document_ids: Specific document IDs to use as context (if provided, only these will be searched)
            
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
            
            # Log search start
            search_context = {
                'user_id': user_id,
                'has_filters': context_document_ids is not None and len(context_document_ids) > 0
            }
            if context_document_ids:
                search_context['num_docs'] = len(context_document_ids)
            
            logger.log_query(
                query=query,
                **search_context
            )
            
            # Step 1: Hybrid Retrieval (BM25 + Vector) with user_id and document_ids filter
            from app.services.vector_store import get_vector_store_service
            from app.services.bm25_service import get_bm25_service
            
            vector_store = get_vector_store_service()
            bm25_service = get_bm25_service()
            
            # Get results from both retrievers
            vector_nodes = vector_store.retrieve(
                query=reformulated_query,
                top_k=settings.top_k_retrieval,
                similarity_threshold=settings.similarity_threshold,
                user_id=user_id,
                document_ids=context_document_ids
            )
            
            bm25_nodes = bm25_service.search(
                query=reformulated_query,
                top_k=settings.top_k_retrieval,
                user_id=user_id,
                document_ids=context_document_ids
            )
            
            logger.log_operation(
                "🔍 Hybrid search complete",
                vector_results=len(vector_nodes),
                bm25_results=len(bm25_nodes)
            )
            
            # Merge results using simple score-based fusion
            # Combine and deduplicate by node ID
            node_dict = {}
            for node in vector_nodes:
                node_id = node.node.node_id
                node_dict[node_id] = node
            
            for node in bm25_nodes:
                node_id = node.node.node_id
                if node_id in node_dict:
                    # Average scores if node appears in both
                    node_dict[node_id].score = (node_dict[node_id].score + node.score) / 2
                else:
                    node_dict[node_id] = node
            
            # Sort by combined score and take top_k
            all_merged = sorted(
                node_dict.values(),
                key=lambda x: x.score or 0.0,
                reverse=True
            )
            retrieved_nodes = all_merged[:settings.top_k_retrieval]
            
            # Log merged results
            if retrieved_nodes:
                logger.log_operation(
                    "📦 Merged results",
                    total_unique=len(all_merged),
                    kept=len(retrieved_nodes)
                )
        
            if not retrieved_nodes:
                context_msg = ""
                if context_document_ids and len(context_document_ids) > 0:
                    context_msg = " in the selected documents"
                logger.log_operation(
                    "⚠️  No relevant documents found",
                    level="WARNING"
                )
                answer = f"I don't have sufficient information{context_msg} to answer this question accurately."
                confidence_result = {
                    "confidence_score": 0.0,
                    "confidence_level": "low",
                    "breakdown": {}
                }
                sources = []
            else:
                # Step 2: Reranking with LlamaIndex's SentenceTransformerRerank
                # This uses BGE reranker (cross-encoder) for better relevance scoring
                logger.log_operation(
                    "🎯 Reranking nodes",
                    nodes=len(retrieved_nodes),
                    target=settings.top_k_rerank
                )
                
                reranked_nodes = self.reranker.postprocess_nodes(
                    retrieved_nodes,
                    QueryBundle(query_str=reformulated_query)
                )
                
                logger.log_operation(
                    "✅ Reranking complete",
                    reranked=len(reranked_nodes)
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
            
            logger.log_operation(
                "✅ Query completed",
                confidence=f"{confidence_result['confidence_score']:.2f}",
                sources=len(sources),
                duration_ms=f"{processing_time:.0f}"
            )
            
            return result
            
        except Exception as e:
            logger.log_error("Query execution", e, query=query[:50])
            raise
    
    async def stream_query(
        self,
        query: str,
        session_id: Optional[str] = None,
        use_context: bool = True,
        user_id: Optional[int] = None,
        context_document_ids: Optional[List[str]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a RAG query response token-by-token.

        Yields:
            Dict events with "type" and "data" keys.
        """
        start_time = time.time()

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

        # Step 1: Hybrid Retrieval (BM25 + Vector)
        from app.services.vector_store import get_vector_store_service
        from app.services.bm25_service import get_bm25_service

        vector_store = get_vector_store_service()
        bm25_service = get_bm25_service()

        vector_nodes = vector_store.retrieve(
            query=reformulated_query,
            top_k=settings.top_k_retrieval,
            similarity_threshold=settings.similarity_threshold,
            user_id=user_id,
            document_ids=context_document_ids,
        )

        bm25_nodes = bm25_service.search(
            query=reformulated_query,
            top_k=settings.top_k_retrieval,
            user_id=user_id,
            document_ids=context_document_ids,
        )

        # Merge results using simple score-based fusion
        node_dict = {}
        for node in vector_nodes:
            node_id = node.node.node_id
            node_dict[node_id] = node

        for node in bm25_nodes:
            node_id = node.node.node_id
            if node_id in node_dict:
                node_dict[node_id].score = (node_dict[node_id].score + node.score) / 2
            else:
                node_dict[node_id] = node

        all_merged = sorted(
            node_dict.values(),
            key=lambda x: x.score or 0.0,
            reverse=True,
        )
        retrieved_nodes = all_merged[:settings.top_k_retrieval]

        if not retrieved_nodes:
            context_msg = ""
            if context_document_ids and len(context_document_ids) > 0:
                context_msg = " in the selected documents"
            answer = f"I don't have sufficient information{context_msg} to answer this question accurately."
            confidence_result = {
                "confidence_score": 0.0,
                "confidence_level": "low",
                "breakdown": {},
            }
            sources = []
        else:
            # Rerank nodes
            reranked_nodes = self.reranker.postprocess_nodes(
                retrieved_nodes,
                QueryBundle(query_str=reformulated_query),
            )

            context_str = "\n\n".join([
                f"[Source: {node.node.metadata.get('filename', 'Unknown')}]\n{node.node.get_content()}"
                for node in reranked_nodes
            ])

            history_str = self.context_manager.get_context_string(session_id, max_messages=4)
            prompt = self._build_prompt(context_str, history_str, query)

            answer_parts: List[str] = []
            async for chunk in self.llm.astream_complete(prompt):
                token = getattr(chunk, "delta", None) or getattr(chunk, "text", None) or ""
                if token:
                    answer_parts.append(token)
                    yield {"type": "token", "data": token}

            answer = "".join(answer_parts).strip()

            llm_confidence = self._extract_llm_confidence(answer)
            answer = self._clean_answer(answer)
            sources = self._extract_sources(reranked_nodes)
            confidence_result = self.confidence_scorer.calculate_confidence(
                query=query,
                nodes=reranked_nodes,
                answer=answer,
                llm_assessment=llm_confidence,
            )

        # Add assistant response to context
        self.context_manager.add_message(
            session_id, "assistant", answer, confidence_result["confidence_score"]
        )

        processing_time = (time.time() - start_time) * 1000
        yield {
            "type": "final",
            "data": {
                "answer": answer,
                "confidence_score": confidence_result["confidence_score"],
                "confidence_level": confidence_result["confidence_level"],
                "sources": sources,
                "session_id": session_id,
                "processing_time_ms": round(processing_time, 2),
                "reasoning": None,
                "mode": "fast",
            },
        }

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
