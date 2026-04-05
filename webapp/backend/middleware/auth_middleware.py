"""
Authentication middleware

Extracts JWT tokens from:
1. Secure httponly cookies (preferred)
2. Authorization header (Bearer token)

Makes token available to route handlers
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

log = logging.getLogger(__name__)


class TokenExtractionMiddleware(BaseHTTPMiddleware):
    """
    Extract JWT token from request (cookie or header)
    
    Adds to request.state.access_token for use in route handlers
    """
    
    async def dispatch(self, request: Request, call_next):
        # Try to get token from secure httponly cookie first
        token = request.cookies.get("access_token")
        
        # If not in cookie, check Authorization header
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]  # Remove "Bearer " prefix
        
        # Store in request state for route handlers
        request.state.access_token = token
        
        response = await call_next(request)
        return response


class CORSMiddleware:
    """
    CORS headers for frontend development
    
    In production, restrict to specific origins
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Development: allow all origins
        # TODO: In production, restrict to actual frontend domain
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response
