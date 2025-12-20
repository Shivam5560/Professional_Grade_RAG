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
        
        # Log request
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
            )
            
            # Add custom headers
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            logger.error(
                "request_failed",
                request_id=request_id,
                error=str(e),
                traceback=traceback.format_exc(),
            )
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling exceptions."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle exceptions and return proper error responses."""
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                "unhandled_exception",
                error=str(e),
                path=request.url.path,
                traceback=traceback.format_exc(),
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
    
    logger.info("cors_configured", origins=settings.cors_origins)


def setup_middleware(app):
    """Setup all middleware for the application."""
    # Add custom middleware
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(LoggingMiddleware)
    
    # Add CORS
    setup_cors(app)
    
    logger.info("middleware_configured")
