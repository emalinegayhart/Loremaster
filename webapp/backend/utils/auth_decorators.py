import logging
from functools import wraps
from fastapi import Request, HTTPException, status

log = logging.getLogger(__name__)


def require_auth(func):
    """
    Decorator to require authentication on a route.
    
    Checks that request.state.user_id exists (set by middleware).
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            for value in kwargs.values():
                if isinstance(value, Request):
                    request = value
                    break
        
        if not request:
            log.error("require_auth decorator used without Request parameter")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication check failed",
            )
        
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
            )
        
        return await func(*args, **kwargs)
    
    return wrapper
