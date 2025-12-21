"""
Enhanced logging configuration for the RAG system.
Simplified, human-readable format with better tracking capabilities.
"""

import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from app.config import settings


class ColorFormatter(logging.Formatter):
    """Custom formatter with colors and clean output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m',       # Reset
        'BOLD': '\033[1m',        # Bold
        'DIM': '\033[2m',         # Dim
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and clean structure."""
        # Get color for log level
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        dim = self.COLORS['DIM']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S.%f')[:-3]
        
        # Extract module name (simplified)
        module = record.name.split('.')[-1] if '.' in record.name else record.name
        
        # Build base message
        base_msg = f"{dim}{timestamp}{reset} {color}[{record.levelname:8}]{reset} {module:20} │ {record.getMessage()}"
        
        # Add extra fields if present
        if hasattr(record, 'extra_data') and record.extra_data:
            extra_parts = []
            for key, value in record.extra_data.items():
                # Format value based on type
                if isinstance(value, (int, float)):
                    formatted_value = str(value)
                elif isinstance(value, bool):
                    formatted_value = str(value)
                elif isinstance(value, str) and len(value) > 100:
                    formatted_value = f"{value[:100]}..."
                elif isinstance(value, (list, dict)):
                    formatted_value = self._format_complex_type(value)
                else:
                    formatted_value = str(value)
                
                extra_parts.append(f"{key}={formatted_value}")
            
            if extra_parts:
                base_msg += f"\n    {dim}└─ {', '.join(extra_parts)}{reset}"
        
        # Add exception info if present
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg
    
    def _format_complex_type(self, value: Any, max_items: int = 3) -> str:
        """Format complex types (list, dict) in a readable way."""
        if isinstance(value, list):
            if len(value) == 0:
                return "[]"
            elif len(value) <= max_items:
                return f"[{', '.join(str(v) for v in value)}]"
            else:
                items = ', '.join(str(v) for v in value[:max_items])
                return f"[{items}, ... +{len(value) - max_items} more]"
        elif isinstance(value, dict):
            if len(value) == 0:
                return "{}"
            elif len(value) <= max_items:
                items = ', '.join(f"{k}: {v}" for k, v in value.items())
                return f"{{{items}}}"
            else:
                items = list(value.items())[:max_items]
                formatted = ', '.join(f"{k}: {v}" for k, v in items)
                return f"{{{formatted}, ... +{len(value) - max_items} more}}"
        return str(value)


class EnhancedLogger(logging.Logger):
    """Enhanced logger with simplified interface."""
    
    def debug(self, msg, *args, **kwargs):
        """Override debug to support keyword arguments."""
        extra_data = {k: v for k, v in kwargs.items() if k not in ['extra', 'exc_info', 'stack_info', 'stacklevel']}
        if extra_data:
            kwargs['extra'] = {'extra_data': extra_data}
            # Remove the extra keys from kwargs
            for k in list(extra_data.keys()):
                kwargs.pop(k, None)
        super().debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """Override info to support keyword arguments."""
        extra_data = {k: v for k, v in kwargs.items() if k not in ['extra', 'exc_info', 'stack_info', 'stacklevel']}
        if extra_data:
            kwargs['extra'] = {'extra_data': extra_data}
            # Remove the extra keys from kwargs
            for k in list(extra_data.keys()):
                kwargs.pop(k, None)
        super().info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """Override warning to support keyword arguments."""
        extra_data = {k: v for k, v in kwargs.items() if k not in ['extra', 'exc_info', 'stack_info', 'stacklevel']}
        if extra_data:
            kwargs['extra'] = {'extra_data': extra_data}
            # Remove the extra keys from kwargs
            for k in list(extra_data.keys()):
                kwargs.pop(k, None)
        super().warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """Override error to support keyword arguments."""
        extra_data = {k: v for k, v in kwargs.items() if k not in ['extra', 'exc_info', 'stack_info', 'stacklevel']}
        if extra_data:
            kwargs['extra'] = {'extra_data': extra_data}
            # Remove the extra keys from kwargs
            for k in list(extra_data.keys()):
                kwargs.pop(k, None)
        super().error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """Override critical to support keyword arguments."""
        extra_data = {k: v for k, v in kwargs.items() if k not in ['extra', 'exc_info', 'stack_info', 'stacklevel']}
        if extra_data:
            kwargs['extra'] = {'extra_data': extra_data}
            # Remove the extra keys from kwargs
            for k in list(extra_data.keys()):
                kwargs.pop(k, None)
        super().critical(msg, *args, **kwargs)
    
    def log_operation(
        self,
        operation: str,
        level: str = "INFO",
        **kwargs
    ) -> None:
        """
        Log an operation with key-value pairs.
        
        Args:
            operation: Operation description
            level: Log level (INFO, WARNING, ERROR, DEBUG)
            **kwargs: Additional context fields
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.log(log_level, operation, extra={'extra_data': kwargs})
    
    def log_request(
        self,
        method: str,
        path: str,
        status: Optional[int] = None,
        duration_ms: Optional[float] = None,
        **kwargs
    ) -> None:
        """Log HTTP request with consistent format."""
        msg = f"{method} {path}"
        data = kwargs.copy()
        if status:
            data['status'] = status
        if duration_ms:
            data['duration_ms'] = f"{duration_ms:.2f}"
        self.log(logging.INFO, msg, extra={'extra_data': data})
    
    def log_query(
        self,
        query: str,
        duration_ms: Optional[float] = None,
        results: Optional[int] = None,
        **kwargs
    ) -> None:
        """Log query operation."""
        msg = f"Query: {query[:50]}..." if len(query) > 50 else f"Query: {query}"
        data = kwargs.copy()
        if duration_ms:
            data['duration_ms'] = f"{duration_ms:.2f}"
        if results is not None:
            data['results'] = results
        self.log(logging.INFO, msg, extra={'extra_data': data})
    
    def log_document(
        self,
        operation: str,
        filename: str,
        **kwargs
    ) -> None:
        """Log document operation."""
        msg = f"{operation}: {filename}"
        self.log(logging.INFO, msg, extra={'extra_data': kwargs})
    
    def log_error(
        self,
        operation: str,
        error: Exception,
        **kwargs
    ) -> None:
        """Log error with context."""
        msg = f"❌ {operation} failed: {str(error)}"
        self.log(logging.ERROR, msg, extra={'extra_data': kwargs}, exc_info=settings.log_level == "DEBUG")


def setup_logging() -> None:
    """Configure enhanced logging for the application."""
    
    # Set custom logger class
    logging.setLoggerClass(EnhancedLogger)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler with custom formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Use color formatter
    formatter = ColorFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> EnhancedLogger:
    """
    Get an enhanced logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured enhanced logger
    """
    return logging.getLogger(name)


# Initialize logging on module import
setup_logging()
