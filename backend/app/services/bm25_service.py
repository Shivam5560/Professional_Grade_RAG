"""
BM25 search service for keyword-based retrieval.
"""

from typing import List, Dict, Any, Optional
import pickle
import os
from rank_bm25 import BM25Okapi
from llama_index.core.schema import TextNode, NodeWithScore
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BM25Service:
    """Service for BM25 keyword search using BM25Okapi algorithm."""
    
    def __init__(self):
        """Initialize BM25 service."""
        self.index_path = os.path.join(settings.data_dir, "bm25_index.pkl")
        self.nodes: List[TextNode] = []
        self.bm25: Optional[BM25Okapi] = None
        self.tokenized_corpus: List[List[str]] = []
        
        # Try to load existing index
        self._load_index()
        
        logger.info("bm25_service_initialized", algorithm="BM25Okapi")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization (split by whitespace and lowercase).
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        return text.lower().split()
    
    def _save_index(self) -> None:
        """Save BM25 index to disk."""
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            index_data = {
                'nodes': self.nodes,
                'tokenized_corpus': self.tokenized_corpus,
            }
            
            with open(self.index_path, 'wb') as f:
                pickle.dump(index_data, f)
            
            logger.info("bm25_index_saved", num_nodes=len(self.nodes))
            
        except Exception as e:
            logger.error("failed_to_save_bm25_index", error=str(e))
    
    def _load_index(self) -> None:
        """Load BM25 index from disk."""
        if not os.path.exists(self.index_path):
            logger.info("no_existing_bm25_index")
            return
        
        try:
            with open(self.index_path, 'rb') as f:
                index_data = pickle.load(f)
            
            self.nodes = index_data.get('nodes', [])
            self.tokenized_corpus = index_data.get('tokenized_corpus', [])
            
            if self.tokenized_corpus:
                self.bm25 = BM25Okapi(self.tokenized_corpus)
            
            logger.info("bm25_index_loaded", num_nodes=len(self.nodes))
            
        except Exception as e:
            logger.error("failed_to_load_bm25_index", error=str(e))
            self.nodes = []
            self.tokenized_corpus = []
            self.bm25 = None
    
    def add_nodes(self, nodes: List[TextNode]) -> None:
        """
        Add nodes to BM25 index.
        
        Args:
            nodes: List of TextNode objects
        """
        if not nodes:
            return
        
        try:
            # Add nodes
            self.nodes.extend(nodes)
            
            # Tokenize and add to corpus
            for node in nodes:
                tokens = self._tokenize(node.get_content())
                self.tokenized_corpus.append(tokens)
            
            # Rebuild BM25 index
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            
            # Save index
            self._save_index()
            
            logger.info("nodes_added_to_bm25", num_nodes=len(nodes))
            
        except Exception as e:
            logger.error("failed_to_add_nodes_to_bm25", error=str(e))
            raise
    
    def search(self, query: str, top_k: int = 10) -> List[NodeWithScore]:
        """
        Search using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of NodeWithScore objects
        """
        if self.bm25 is None or not self.nodes:
            logger.warning("bm25_index_not_available")
            return []
        
        try:
            # Tokenize query
            query_tokens = self._tokenize(query)
            
            # Get BM25 scores
            scores = self.bm25.get_scores(query_tokens)
            
            # Get top-k indices
            top_indices = sorted(
                range(len(scores)), 
                key=lambda i: scores[i], 
                reverse=True
            )[:top_k]
            
            # Create NodeWithScore objects
            results = []
            for idx in top_indices:
                if scores[idx] > 0:  # Only include positive scores
                    results.append(
                        NodeWithScore(
                            node=self.nodes[idx],
                            score=float(scores[idx])
                        )
                    )
            
            logger.info(
                "bm25_search_complete",
                query_length=len(query),
                num_results=len(results),
                top_k=top_k,
            )
            
            return results
            
        except Exception as e:
            logger.error("bm25_search_failed", error=str(e))
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get BM25 index statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_nodes": len(self.nodes),
            "index_available": self.bm25 is not None,
        }
    
    def reset(self) -> None:
        """Reset the BM25 index."""
        self.nodes = []
        self.tokenized_corpus = []
        self.bm25 = None
        
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        
        logger.warning("bm25_index_reset")


# Global instance
_bm25_service: Optional[BM25Service] = None


def get_bm25_service() -> BM25Service:
    """Get or create the global BM25 service instance."""
    global _bm25_service
    if _bm25_service is None:
        _bm25_service = BM25Service()
    return _bm25_service
