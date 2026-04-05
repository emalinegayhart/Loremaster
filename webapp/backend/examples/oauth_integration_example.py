"""
Example: Full OAuth 2.0 integration with Loremaster

This shows how all the components work together.
Reference for PR-AUTH-2 (OAuth endpoints).
"""

from fastapi import FastAPI, Response, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
import logging

from services import SecretService, JWTService, OAuthService
from models import User, UserCreate
from db import get_session, init_db

log = logging.getLogger(__name__)

# Initialize
SecretService.load()
init_db()

jwt_service = JWTService(SecretService.JWT_SECRET_KEY)
oauth_service = OAuthService()


async def example_oauth_flow():
    """
    Complete OAuth flow example
    """
    
    # ============================================
    # STEP 1: User clicks "Login with Google"
    # ============================================
    # Frontend sends: GET /api/auth/google
    
    # Generate state token (unique per request)
    state = oauth_service.generate_state_token()
    # Store in httponly cookie: Set-Cookie: oauth_state=<state>; HttpOnly; Secure
    
    # Build redirect URL
    auth_url = oauth_service.build_authorization_url(state)
    # auth_url = "https://accounts.google.com/o/oauth2/v2/auth?..."
    # Redirect user to this URL
    
    
    # ============================================
    # STEP 2: Google redirects back to callback
    # ============================================
    # Browser: GET /api/auth/google/callback?code=...&state=...
    
    code = "...code_from_google..."  # From query param
    state_from_url = "...state_from_query..."  # From query param
    state_from_cookie = "...state_from_cookie..."  # From httponly cookie
    
    # Validate state (CSRF protection)
    if not oauth_service.validate_state_token(state_from_cookie, state_from_url):
        raise HTTPException(status_code=400, detail="Invalid state token")
    
    # Exchange code for tokens
    try:
        tokens = await oauth_service.exchange_code_for_tokens(code)
        # tokens = {
        #   "access_token": "...",
        #   "refresh_token": "...",
        #   "expires_in": 3600,
        #   "token_type": "Bearer"
        # }
    except Exception as e:
        log.error(f"Token exchange failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")
    
    # Get user info from Google
    try:
        google_user = await oauth_service.get_user_info(tokens["access_token"])
        # google_user = {
        #   "id": "123456789",
        #   "email": "user@example.com",
        #   "name": "John Doe",
        #   "picture": "https://..."
        # }
    except Exception as e:
        log.error(f"User info fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch user info")
    
    
    # ============================================
    # STEP 3: Create or update user in DB
    # ============================================
    
    user_data = oauth_service.parse_user_info(google_user)
    # user_data = {
    #   "oauth_id": "123456789",
    #   "email": "user@example.com",
    #   "username": "John Doe",
    #   "profile_picture_url": "https://...",
    #   "oauth_provider": "google"
    # }
    
    # Try to find existing user
    session = Session()  # In real code, use Depends(get_session)
    user = session.exec(
        select(User).where(User.email == user_data["email"])
    ).first()
    
    if user:
        # Existing user: update fields
        user.username = user_data["username"]
        user.profile_picture_url = user_data["profile_picture_url"]
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        # New user: create
        new_user = User(**user_data)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        user = new_user
    
    
    # ============================================
    # STEP 4: Generate JWT tokens for user
    # ============================================
    
    access_token = jwt_service.create_access_token(user_id=user.id)
    refresh_token = jwt_service.create_refresh_token(user_id=user.id)
    
    # access_token = "eyJhbGc..." (expires in 1 hour)
    # refresh_token = "eyJhbGc..." (expires in 30 days)
    
    
    # ============================================
    # STEP 5: Set cookies + redirect to app
    # ============================================
    
    response = RedirectResponse(url="/app")
    
    # Set httponly, secure cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=3600,  # 1 hour
        httponly=True,
        secure=True,  # HTTPS only
        samesite="Lax",
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=2592000,  # 30 days
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    
    # Clear oauth_state cookie
    response.delete_cookie("oauth_state")
    
    return response


async def example_token_refresh():
    """
    Refresh access token using refresh token
    """
    
    # Frontend: POST /api/auth/refresh with refresh_token cookie
    refresh_token = "...token_from_cookie..."
    
    try:
        # Validate refresh token
        payload = jwt_service.validate_token(refresh_token, token_type="refresh")
        user_id = int(payload["sub"])
        
        # Generate new access token
        new_access_token = jwt_service.create_access_token(user_id)
        
        # Return in response (frontend stores in memory, not cookie)
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }
        
    except HTTPException as e:
        log.warning(f"Token refresh failed: {e.detail}")
        raise


async def example_protected_route(session: Session = Depends(get_session)):
    """
    Example of a protected route that requires JWT
    """
    
    # Frontend includes: Authorization: Bearer <access_token>
    access_token = "...token_from_header..."
    
    try:
        # Validate access token
        user_id = jwt_service.get_user_id_from_token(access_token)
        
        # Fetch user
        user = session.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "profile_picture_url": user.profile_picture_url,
        }
        
    except HTTPException as e:
        log.warning(f"Protected route access denied: {e.detail}")
        raise


async def example_logout():
    """
    Logout: clear tokens
    """
    
    response = Response(content="Logged out")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    response.delete_cookie("oauth_state")
    
    return response


# ============================================
# Middleware: Validate token on protected routes
# ============================================

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class TokenValidationMiddleware(BaseHTTPMiddleware):
    """
    Example middleware to validate JWT on protected routes
    """
    
    PROTECTED_ROUTES = [
        "/api/user/",
        "/api/bots/",
        "/api/editor/",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Only check protected routes
        if not any(request.url.path.startswith(route) for route in self.PROTECTED_ROUTES):
            return await call_next(request)
        
        # Get token from cookie or Authorization header
        token = request.cookies.get("access_token")
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            return HTTPException(status_code=401, detail="Missing token")
        
        # Validate token
        try:
            jwt_service.validate_token(token, token_type="access")
        except HTTPException as e:
            return e
        
        return await call_next(request)


# ============================================
# Error Handling
# ============================================

# Example error scenarios:

# 1. Missing environment variable
# ERROR: GOOGLE_CLIENT_ID not set
# → SecretService.load() raises ValueError at startup

# 2. Database error
# ERROR: Could not insert user
# → Log error, raise HTTPException 500

# 3. Google OAuth timeout
# ERROR: Token exchange timeout
# → oauth_service.exchange_code_for_tokens() raises Exception
# → Catch and raise HTTPException 500

# 4. Invalid token
# ERROR: Token signature invalid
# → jwt_service.validate_token() raises HTTPException 401

# 5. State token mismatch (CSRF attack)
# ERROR: Invalid state token
# → oauth_service.validate_state_token() returns False
# → Raise HTTPException 400

print("""
This example shows:

1. Complete OAuth 2.0 flow (code exchange → user creation → JWT generation)
2. Token refresh endpoint
3. Protected routes with token validation
4. Error handling patterns
5. Middleware for token verification

Next PR (PR-AUTH-2) will implement these as actual FastAPI endpoints.
""")
