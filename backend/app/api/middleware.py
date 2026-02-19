"""
Middleware for API request handling and optimization
"""
import time
import asyncio
from typing import Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.utils.logging_config import log_message, LG, LogLevel


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware برای تنظیم timeout روی requestها
    جلوگیری از hang کردن requestها
    """

    def __init__(self, app, timeout_seconds: int = 60):
        """
        Args:
            app: FastAPI application
            timeout_seconds: Maximum request processing time in seconds
        """
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with timeout"""
        try:
            # Skip timeout for health check and root endpoints
            if request.url.path in ["/health", "/"]:
                return await call_next(request)

            # Apply timeout for other endpoints
            try:
                response = await asyncio.wait_for(
                    call_next(request),
                    timeout=self.timeout_seconds
                )
                return response

            except asyncio.TimeoutError:
                log_message(
                    LG.API,
                    f"⏰ Request timeout after {self.timeout_seconds}s: {request.url.path}",
                    LogLevel.ERROR
                )
                raise HTTPException(
                    status_code=504,
                    detail=f"Request timeout after {self.timeout_seconds} seconds"
                )

        except Exception as e:
            log_message(LG.API, f"❌ Error in timeout middleware: {str(e)}", LogLevel.ERROR)
            raise


class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware برای لاگ کردن زمان اجرای requestها
    کمک به شناسایی bottleneckها
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request performance metrics"""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add header
        response.headers["X-Process-Time"] = str(process_time)

        # Log slow requests
        if process_time > 1.0:
            log_message(
                LG.API,
                f"⚠️ Slow request ({process_time:.2f}s): {request.method} {request.url.path}",
                LogLevel.WARNING
            )
        else:
            log_message(
                LG.API,
                f"✅ Request completed ({process_time:.2f}s): {request.method} {request.url.path}",
                LogLevel.DEBUG
            )

        return response
