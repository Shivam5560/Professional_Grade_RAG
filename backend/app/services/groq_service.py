"""
Groq service for LLM inference.
Wraps Groq API calls using LlamaIndex for the RAG system.
"""

import time
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
            logger.log_operation("⚠️  GROQ_API_KEY not set", level="WARNING")
            raise ValueError("GROQ_API_KEY must be set in environment variables")
        
        # Initialize Groq LLM with LlamaIndex
        self.llm = Groq(
            model=self.model,
            api_key=self.api_key,
            temperature=0.1,  # Lower temperature for more deterministic responses
            max_tokens=settings.max_tokens,
        )

        self._aurasql_llm = Groq(
            model=self.model,
            api_key=self.api_key,
            temperature=0.1,
            max_tokens=settings.aurasql_max_tokens,
        )
        
        # Health check caching to prevent excessive API calls
        self._last_health_check: Optional[float] = None
        self._last_health_status: bool = True
        self._health_check_cache_duration: int = 60  # Cache for 60 seconds
        
        logger.log_operation("🤖 Groq LLM initialized", model=self.model)
    
    def get_llm(self) -> Groq:
        """
        Get the Groq LLM instance.
        
        Returns:
            Groq LLM instance
        """
        return self.llm

    def get_aurasql_llm(self) -> Groq:
        """Get Groq LLM tuned for AuraSQL token budgets."""
        return self._aurasql_llm
    
    async def check_health(self) -> bool:
        """
        Check if Groq service is available.
        Uses caching to prevent excessive API calls during health checks.
        
        Returns:
            True if service is healthy
        """
        # Check if we have a recent cached result
        current_time = time.time()
        if (self._last_health_check is not None and 
            (current_time - self._last_health_check) < self._health_check_cache_duration):
            logger.debug(
                "groq_health_check_cached",
                cached_status=self._last_health_status,
                seconds_since_check=int(current_time - self._last_health_check)
            )
            return self._last_health_status
        
        # Perform actual health check
        try:
            # Try a minimal completion to verify API key and service availability
            response = await self.llm.acomplete("Hello")
            is_healthy = bool(response.text)
            
            # Update cache
            self._last_health_check = current_time
            self._last_health_status = is_healthy
            
            return is_healthy
        except Exception as e:
            logger.log_error("Groq health check", e)
            
            # Update cache with failure
            self._last_health_check = current_time
            self._last_health_status = False
            
            return False


# Global instance
_groq_service: Optional[GroqService] = None


def get_groq_service() -> GroqService:
    """Get or create the global Groq service instance."""
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service
