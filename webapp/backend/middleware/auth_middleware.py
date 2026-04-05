import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from services.jwt_service import JWTService
from services.token_blacklist import get_blacklist
from services.secret_service import SecretService

log = logging.getLogger(__name__)

jwt_service = JWTService(SecretService.JWT_SECRET_KEY)
blacklist = get_blacklist()


class TokenExtractionMiddleware(BaseHTTPMiddleware):
    """Extract JWT token from request (cookie or header)."""
    
    async def dispatch(self, request: Request, call_next):
        token = request.cookies.get("access_token")
        
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        request.state.access_token = token
        
        response = await call_next(request)
        return response


class ProtectedRouteMiddleware(BaseHTTPMiddleware):
    """Validate JWT tokens on protected routes."""
    
    PROTECTED_ROUTES = [
        "/api/bots/",
        "/api/editor/",
        "/api/user/",
    ]
    
    async def dispatch(self, request: Request, call_next):
        is_protected = any(
            request.url.path.startswith(route) 
            for route in self.PROTECTED_ROUTES
        )
        
        if is_protected:
            token = getattr(request.state, 'access_token', None)
            
            if not token:
                return self._unauthorized_response("Missing authentication token")
            
            if blacklist.is_blacklisted(token):
                return self._unauthorized_response("Token has been invalidated")
            
            try:
                payload = jwt_service.validate_token(token, token_type="access")
                user_id = int(payload["sub"])
                
                request.state.user_id = user_id
                request.state.token = token
                
            except HTTPException as e:
                return self._unauthorized_response(e.detail)
            except Exception as e:
                log.warning(f"Token validation failed: {str(e)}")
                return self._unauthorized_response("Invalid token")
        
        response = await call_next(request)
        return response
    
    def _unauthorized_response(self, detail: str):
        """Return 401 Unauthorized response."""
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail},
        )


class CORSMiddleware:
    """CORS headers for frontend development."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        return response
