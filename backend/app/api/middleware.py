"""
Middleware for API: CORS, logging, error handling.
"""

import time
import traceback
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings
from app.utils.logger import get_logger
from app.models.schemas import ErrorResponse

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        request_id = str(time.time())
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.log_request(
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=process_time_ms,
                client=request.client.host if request.client else None,
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time_ms / 1000)
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            logger.log_error(
                f"Request {request.method} {request.url.path}",
                e,
                request_id=request_id,
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions and return proper error responses."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.log_error(
                f"Unhandled exception in {request.url.path}",
                e,
            )
            
            # Create error response
            error_response = ErrorResponse(
                error="internal_server_error",
                message="An unexpected error occurred",
                detail=str(e) if settings.log_level == "DEBUG" else None
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.model_dump()
            )


def setup_cors(app):
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.log_operation("cors_configured", origins=settings.cors_origins)


def setup_middleware(app):
    """Setup all middleware for the application."""
    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Add CORS
    setup_cors(app)
    
    logger.log_operation("middleware_configured")
