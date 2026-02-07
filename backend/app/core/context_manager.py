"""
Chat context manager for handling conversation history.
"""

from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.memory import ChatMemoryBuffer
from app.config import settings
from app.models.schemas import Message
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ContextManager:
    """
    Manages chat context and conversation history for sessions.
    """
    
    def __init__(self):
        """Initialize context manager."""
        self.max_history = settings.max_chat_history
        self.max_tokens = settings.max_tokens
        
        # In-memory storage: session_id -> LlamaIndex ChatMemoryBuffer
        # In production, use Redis or database-backed ChatStore
        self.sessions: Dict[str, ChatMemoryBuffer] = defaultdict(
            lambda: ChatMemoryBuffer.from_defaults(token_limit=self.max_tokens)
        )
        
        logger.info(
            "context_manager_initialized",
            max_history=self.max_history,
            max_tokens=self.max_tokens,
        )
    
    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        confidence_score: Optional[float] = None
    ) -> None:
        """
        Add a message to the session history.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant)
            content: Message content
            confidence_score: Optional confidence score for assistant messages
        """
        message = ChatMessage(
            role=MessageRole.USER if role == "user" else MessageRole.ASSISTANT,
            content=content,
        )

        memory = self.sessions[session_id]
        memory.put(message)
        
        logger.info(
            "message_added_to_context",
            session_id=session_id,
            role=role,
            content_length=len(content),
            total_messages=len(memory.get())
        )
    
    def get_history(self, session_id: str) -> List[Message]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of messages
        """
        memory = self.sessions.get(session_id)
        if memory is None:
            return []

        history: List[Message] = []
        for msg in memory.get()[-self.max_history:]:
            history.append(
                Message(
                    role="user" if msg.role == MessageRole.USER else "assistant",
                    content=msg.content,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )
        return history
    
    def get_chat_messages(self, session_id: str) -> List[ChatMessage]:
        """
        Get history formatted as LlamaIndex ChatMessage objects.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of ChatMessage objects
        """
        memory = self.sessions.get(session_id)
        if memory is None:
            return []

        return memory.get()[-self.max_history:]
    
    def get_context_string(self, session_id: str, max_messages: Optional[int] = None) -> str:
        """
        Get conversation history as a formatted string.
        
        Args:
            session_id: Session identifier
            max_messages: Maximum number of recent messages to include
            
        Returns:
            Formatted conversation history
        """
        memory = self.sessions.get(session_id)
        if memory is None:
            return ""

        history = memory.get()
        if max_messages:
            history = history[-max_messages:]

        if not history:
            return ""

        context_parts = []
        for msg in history:
            prefix = "User" if msg.role == MessageRole.USER else "Assistant"
            context_parts.append(f"{prefix}: {msg.content}")

        return "\n".join(context_parts)
    
    def reformulate_query(self, session_id: str, query: str) -> str:
        """
        Reformulate query with conversation context.
        
        Args:
            session_id: Session identifier
            query: Current user query
            
        Returns:
            Reformulated query with context
        """
        memory = self.sessions.get(session_id)

        if memory is None:
            return query

        history = memory.get()

        # If no history or query is already detailed, return as-is
        if not history or len(query.split()) > 10:
            return query

        # Get last few messages for context
        recent_history = history[-3:] if len(history) >= 3 else history

        # Build context-aware query
        context_parts = []
        for msg in recent_history:
            if msg.role == MessageRole.USER:
                context_parts.append(f"Previous question: {msg.content}")
            # We can include assistant responses if needed, but keeping it simple
        
        if context_parts:
            reformulated = f"{' '.join(context_parts)}. Current question: {query}"
            
            logger.info(
                "query_reformulated",
                session_id=session_id,
                original_length=len(query),
                reformulated_length=len(reformulated),
            )
            
            return reformulated
        
        return query
    
    def clear_session(self, session_id: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info("session_cleared", session_id=session_id)
    
    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)


# Global instance
_context_manager: Optional[ContextManager] = None


def get_context_manager() -> ContextManager:
    """Get or create the global context manager instance."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
