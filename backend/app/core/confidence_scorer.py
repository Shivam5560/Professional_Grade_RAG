"""
Confidence scoring system for RAG responses.
"""

from typing import List, Dict, Any, Optional
import math
from llama_index.core.schema import NodeWithScore
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConfidenceScorer:
    """
    Multi-factor confidence scoring for RAG responses.
    
    Confidence components:
    1. Retrieval score: Quality of retrieved documents
    2. Answer coherence: LLM self-assessment
    3. Source coverage: Number and distribution of sources
    4. Query clarity: Quality of query understanding
    """
    
    def __init__(self):
        """Initialize confidence scorer with weights from config."""
        self.weight_retrieval = settings.weight_retrieval
        self.weight_coherence = settings.weight_coherence
        self.weight_coverage = settings.weight_coverage
        self.weight_clarity = settings.weight_clarity
        
        logger.info(
            "confidence_scorer_initialized",
            weights={
                "retrieval": self.weight_retrieval,
                "coherence": self.weight_coherence,
                "coverage": self.weight_coverage,
                "clarity": self.weight_clarity,
            }
        )
    
    def calculate_retrieval_score(self, nodes: List[NodeWithScore]) -> float:
        """
        Calculate retrieval quality score.
        
        Args:
            nodes: Retrieved nodes with scores
            
        Returns:
            Normalized score between 0-1
        """
        if not nodes:
            return 0.0
        
        # Get all valid scores
        scores = [node.score for node in nodes if node.score is not None]
        if not scores:
            return 0.0
        
        # Use max score (best match) as primary indicator
        max_score = max(scores)
        min_score = min(scores)
        mean_score = sum(scores) / len(scores)
        
        # Log raw scores from nodes
        logger.info(
            "raw_node_scores",
            max_score=round(max_score, 4),
            min_score=round(min_score, 4),
            mean_score=round(mean_score, 4),
            num_nodes=len(scores),
            top_5_scores=[round(s, 4) for s in sorted(scores, reverse=True)[:5]]
        )
        
        # Calculate score variance (consistency indicator)
        if len(scores) > 1:
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance ** 0.5
        else:
            std_dev = 0.0
        
        # Reranker scores are typically between -1 and 1, need normalization
        # If scores are already between 0-1, keep them
        # If scores are between -1 and 1, normalize to 0-1
        if max_score < 0:
            # All negative scores - normalize from [-1, 0] to [0, 0.5]
            normalized_max = (max_score + 1) * 0.5
        elif max_score > 1:
            # Similarity scores can be > 1, normalize
            normalized_max = min(max_score / 2.0, 1.0)
        else:
            # Already in good range
            normalized_max = max_score
        
        # Normalize mean score same way
        if mean_score < 0:
            normalized_mean = (mean_score + 1) * 0.5
        elif mean_score > 1:
            normalized_mean = min(mean_score / 2.0, 1.0)
        else:
            normalized_mean = mean_score
        
        # Combine: prioritize max score but boost if mean is also good
        retrieval_score = (normalized_max * 0.7 + normalized_mean * 0.3)
        
        # Apply consistency boost if scores are similar (low variance)
        # Low variance means all retrieved docs are similarly relevant = high confidence
        if std_dev < 0.05 and max_score > 0.8:
            # All scores are very similar and high - boost by 15%
            retrieval_score = min(retrieval_score * 1.15, 1.0)
            logger.debug("consistency_boost_applied", std_dev=std_dev, boost=1.15)
        elif std_dev < 0.1 and max_score > 0.5:
            # Scores are somewhat similar and decent - boost by 10%
            retrieval_score = min(retrieval_score * 1.10, 1.0)
            logger.debug("consistency_boost_applied", std_dev=std_dev, boost=1.10)
        
        # Apply boost if top score is very high (strong match)
        if max_score > 0.7:
            # Boost confidence for very strong matches
            retrieval_score = min(retrieval_score * 1.15, 1.0)
        elif max_score > 0.5:
            # Boost confidence for strong matches
            retrieval_score = min(retrieval_score * 1.10, 1.0)
        
        logger.info(
            "retrieval_score_calculated",
            raw_max=round(max_score, 4),
            raw_min=round(min_score, 4),
            raw_mean=round(mean_score, 4),
            std_dev=round(std_dev, 4),
            normalized_max=round(normalized_max, 4),
            normalized_mean=round(normalized_mean, 4),
            final_score=round(retrieval_score, 4),
            boosted=max_score > 0.5,
            num_nodes=len(nodes)
        )
        
        # Ensure between 0-1
        return min(max(retrieval_score, 0.0), 1.0)
    
    def calculate_coverage_score(
        self,
        nodes: List[NodeWithScore],
        answer: str
    ) -> float:
        """
        Calculate source coverage score based on SOURCE QUALITY, not just count.
        Since we always get 3 nodes, we need to check HOW GOOD they are.
        
        Args:
            nodes: Retrieved nodes
            answer: Generated answer
            
        Returns:
            Normalized score between 0-1
        """
        if not nodes or not answer:
            return 0.0
        
        # Extract scores
        scores = [node.score for node in nodes if node.score is not None]
        if not scores:
            return 0.5  # No scores available
        
        # Factor 1: Best match quality (how good is the top result?)
        max_score = max(scores)
        if max_score > 0.9:
            best_match_score = 1.0  # Excellent match
        elif max_score > 0.7:
            best_match_score = 0.85
        elif max_score > 0.5:
            best_match_score = 0.7
        elif max_score > 0.3:
            best_match_score = 0.5
        else:
            best_match_score = 0.3  # Poor match
        
        # Factor 2: Source consistency (are all sources relevant or just one?)
        # Check if multiple sources agree (low variance = high agreement)
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
            std_dev = variance ** 0.5
            
            # Low std_dev = sources agree, high std_dev = only one good source
            if std_dev < 0.05:
                consistency_score = 1.0  # All sources highly relevant
            elif std_dev < 0.1:
                consistency_score = 0.85  # Most sources relevant
            elif std_dev < 0.2:
                consistency_score = 0.7
            elif std_dev < 0.3:
                consistency_score = 0.5
            else:
                consistency_score = 0.3  # Only one good source, others poor
        else:
            consistency_score = 0.5
        
        # Factor 3: Source diversity (are they from different documents?)
        unique_docs = set()
        for node in nodes:
            doc_id = node.node.metadata.get('filename', 'unknown')
            unique_docs.add(doc_id)
        
        num_unique_docs = len(unique_docs)
        if num_unique_docs >= 3:
            diversity_score = 1.0  # From 3 different docs
        elif num_unique_docs == 2:
            diversity_score = 0.7  # From 2 docs
        else:
            diversity_score = 0.4  # All from same doc
        
        # Factor 4: Answer substantiveness (has enough content)
        answer_length = len(answer)
        if answer_length < 50:
            substantiveness_score = answer_length / 50.0  # Too short
        elif answer_length <= 500:
            substantiveness_score = 1.0  # Ideal
        elif answer_length <= 1000:
            substantiveness_score = 0.95
        else:
            substantiveness_score = 0.85  # Very long
        
        # Combine factors with weights
        coverage_score = (
            best_match_score * 0.35 +        # 35% - top source quality
            consistency_score * 0.35 +       # 35% - all sources quality
            diversity_score * 0.15 +         # 15% - source diversity
            substantiveness_score * 0.15     # 15% - answer has content
        )
        
        logger.info(
            "coverage_score_breakdown",
            num_sources=len(nodes),
            num_unique_docs=num_unique_docs,
            max_score=round(max_score, 3),
            mean_score=round(sum(scores)/len(scores), 3),
            std_dev=round(std_dev if len(scores) > 1 else 0, 3),
            best_match_score=round(best_match_score, 3),
            consistency_score=round(consistency_score, 3),
            diversity_score=round(diversity_score, 3),
            substantiveness_score=round(substantiveness_score, 3),
            answer_length=answer_length,
            final_coverage=round(coverage_score, 3)
        )
        
        return min(max(coverage_score, 0.0), 1.0)
    
    def calculate_clarity_score(self, query: str) -> float:
        """
        Calculate query clarity score.
        
        Args:
            query: User query
            
        Returns:
            Normalized score between 0-1
        """
        if not query:
            return 0.0
        
        # Factor 1: Query length (not too short, not too long)
        words = query.split()
        word_count = len(words)
        
        if word_count < 3:
            length_score = word_count / 3.0
        elif word_count <= 15:
            length_score = 1.0
        else:
            length_score = max(0.5, 1.0 - (word_count - 15) / 50.0)
        
        # Factor 2: Question markers (helps indicate intent)
        question_words = {'what', 'why', 'how', 'when', 'where', 'who', 'which'}
        has_question_word = any(word.lower() in question_words for word in words)
        has_question_mark = '?' in query
        
        intent_score = 1.0 if (has_question_word or has_question_mark) else 0.7
        
        # Combine
        clarity_score = (length_score * 0.6 + intent_score * 0.4)
        
        return min(max(clarity_score, 0.0), 1.0)
    
    def parse_coherence_score(self, llm_assessment: Optional[float]) -> float:
        """
        Use LLM's self-assessed confidence score directly.
        
        The LLM provides a confidence score (0-1) extracted from its response.
        This is more efficient than making a separate API call.
        
        Args:
            llm_assessment: LLM's self-assessed confidence (0-1), or None if not found
            
        Returns:
            Normalized score between 0-1
        """
        if llm_assessment is not None:
            # Use the LLM's self-assessment directly
            score = min(max(llm_assessment, 0.0), 1.0)
            logger.info(
                "llm_coherence_used",
                raw_score=llm_assessment,
                normalized=score
            )
            return score
        
        # If no assessment provided, return high default
        # (LLM responses are usually coherent, especially with good prompts)
        logger.warning("no_llm_assessment_provided", using_default=0.9)
        return 0.9
    
    async def get_llm_coherence_assessment(
        self,
        query: str,
        answer: str,
        context: str
    ) -> str:
        """
        Ask the LLM to assess its own answer coherence.
        
        Args:
            query: Original user query
            answer: Generated answer
            context: Context used to generate answer
            
        Returns:
            LLM's self-assessment as a string
        """
        from app.services.groq_service import get_groq_service
        
        assessment_prompt = f"""You are evaluating the quality of an answer you just generated.

ORIGINAL QUESTION: {query}

YOUR ANSWER: {answer}

CONTEXT USED: {context[:500]}...

Assess your answer on a scale of 1-10 based on:
1. Coherence: Does the answer flow logically?
2. Relevance: Does it directly address the question?
3. Completeness: Does it provide sufficient information?
4. Accuracy: Does it correctly use the context?

Respond with ONLY a number from 1-10 (where 10 is perfect).
Example: "8.5" or "7" or "9"

Your assessment:"""

        try:
            groq_service = get_groq_service()
            llm = groq_service.get_llm()
            
            # Get LLM assessment
            response = await llm.acomplete(assessment_prompt)
            assessment = response.text.strip()
            
            logger.info(
                "llm_coherence_assessment_received",
                query_length=len(query),
                answer_length=len(answer),
                assessment=assessment
            )
            
            return assessment
            
        except Exception as e:
            logger.error("llm_coherence_assessment_failed", error=str(e))
            return "8.5"  # Default to good if assessment fails
    
    def calculate_confidence(
        self,
        query: str,
        nodes: List[NodeWithScore],
        answer: str,
        llm_assessment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate overall confidence score.
        
        Args:
            query: User query
            nodes: Retrieved nodes
            answer: Generated answer
            llm_assessment: Optional LLM self-assessment
            
        Returns:
            Dictionary with confidence score and breakdown
        """
        try:
            # Calculate individual components
            retrieval_score = self.calculate_retrieval_score(nodes)
            coverage_score = self.calculate_coverage_score(nodes, answer)
            clarity_score = self.calculate_clarity_score(query)
            coherence_score = self.parse_coherence_score(llm_assessment)
            
            # Calculate weighted overall score
            overall_score = (
                retrieval_score * self.weight_retrieval +
                coherence_score * self.weight_coherence +
                coverage_score * self.weight_coverage +
                clarity_score * self.weight_clarity
            )
            
            # Convert to percentage
            confidence_percentage = overall_score * 100.0
            
            # Determine confidence level
            if confidence_percentage >= 80:
                confidence_level = "high"
            elif confidence_percentage >= 50:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            result = {
                "confidence_score": round(confidence_percentage, 2),
                "confidence_level": confidence_level,
                "breakdown": {
                    "retrieval": round(retrieval_score * 100, 2),
                    "coherence": round(coherence_score * 100, 2),
                    "coverage": round(coverage_score * 100, 2),
                    "clarity": round(clarity_score * 100, 2),
                }
            }
            
            # Detailed logging with all components
            logger.info(
                "confidence_calculated",
                # Final results
                confidence_score=result["confidence_score"],
                confidence_level=result["confidence_level"],
                # Component scores (0-1 range)
                retrieval_score=round(retrieval_score, 3),
                coherence_score=round(coherence_score, 3),
                coverage_score=round(coverage_score, 3),
                clarity_score=round(clarity_score, 3),
                # Component scores (percentage)
                retrieval_pct=f"{retrieval_score * 100:.1f}%",
                coherence_pct=f"{coherence_score * 100:.1f}%",
                coverage_pct=f"{coverage_score * 100:.1f}%",
                clarity_pct=f"{clarity_score * 100:.1f}%",
                # Weights applied
                weights={
                    "retrieval": self.weight_retrieval,
                    "coherence": self.weight_coherence,
                    "coverage": self.weight_coverage,
                    "clarity": self.weight_clarity
                },
                # Weighted contributions to final score
                contributions={
                    "retrieval": round(retrieval_score * self.weight_retrieval * 100, 2),
                    "coherence": round(coherence_score * self.weight_coherence * 100, 2),
                    "coverage": round(coverage_score * self.weight_coverage * 100, 2),
                    "clarity": round(clarity_score * self.weight_clarity * 100, 2)
                },
                # Additional context
                num_sources=len(nodes),
                query_length=len(query),
                answer_length=len(answer)
            )
            
            return result
            
        except Exception as e:
            logger.error("confidence_calculation_failed", error=str(e))
            # Return default moderate confidence
            return {
                "confidence_score": 50.0,
                "confidence_level": "medium",
                "breakdown": {
                    "retrieval": 50.0,
                    "coherence": 50.0,
                    "coverage": 50.0,
                    "clarity": 50.0,
                }
            }


# Global instance
_confidence_scorer: Optional[ConfidenceScorer] = None


def get_confidence_scorer() -> ConfidenceScorer:
    """Get or create the global confidence scorer instance."""
    global _confidence_scorer
    if _confidence_scorer is None:
        _confidence_scorer = ConfidenceScorer()
    return _confidence_scorer
