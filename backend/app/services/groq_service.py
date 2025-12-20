"""
Groq service for LLM inference.
Wraps Groq API calls using LlamaIndex for the RAG system.
"""

from typing import Optional
from llama_index.llms.groq import Groq
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GroqService:
    """Service for interacting with Groq LLM."""
    
    def __init__(self):
        """Initialize Groq service with configured API key and model."""
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        
        if not self.api_key:
            logger.warning("groq_api_key_not_set", message="GROQ_API_KEY is not set in environment")
            raise ValueError("GROQ_API_KEY must be set in environment variables")
        
        # Initialize Groq LLM with LlamaIndex
        self.llm = Groq(
            model=self.model,
            api_key=self.api_key,
            temperature=0.1,  # Lower temperature for more deterministic responses
            max_tokens=4096,
        )
        
        logger.info(
            "groq_service_initialized",
            model=self.model,
        )
    
    def get_llm(self) -> Groq:
        """
        Get the Groq LLM instance.
        
        Returns:
            Groq LLM instance
        """
        return self.llm
    
    async def check_health(self) -> bool:
        """
        Check if Groq service is available by attempting a simple completion.
        
        Returns:
            True if service is healthy
        """
        try:
            # Try a minimal completion to verify API key and service availability
            response = await self.llm.acomplete("Hello")
            return bool(response.text)
        except Exception as e:
            logger.error("groq_health_check_failed", error=str(e))
            return False


# Global instance
_groq_service: Optional[GroqService] = None


def get_groq_service() -> GroqService:
    """Get or create the global Groq service instance."""
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service
