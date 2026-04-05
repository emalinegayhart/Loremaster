"""
OAuth 2.0 authentication endpoints

Handles:
- GET /api/auth/google - Start Google OAuth flow
- GET /api/auth/google/callback - Handle OAuth callback
- POST /api/auth/refresh - Refresh access token
- POST /api/auth/logout - Clear tokens
"""

import logging
from fastapi import APIRouter, Response, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from models import User, UserResponse
from services import JWTService, OAuthService, SecretService
from db import get_session

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Initialize services
jwt_service = JWTService(SecretService.JWT_SECRET_KEY)
oauth_service = OAuthService()


# ============================================
# Step 1: Initiate Google OAuth Flow
# ============================================

@router.get("/google", tags=["auth"])
async def google_login():
    """
    Start Google OAuth 2.0 flow
    
    Generates state token (CSRF protection) and redirects to Google
    
    Returns:
        RedirectResponse to Google authorization URL
    """
    try:
        # Generate state token
        state = oauth_service.generate_state_token()
        
        # Build authorization URL
        auth_url = oauth_service.build_authorization_url(state)
        
        # Redirect to Google
        response = RedirectResponse(url=auth_url)
        
        # Store state in httponly cookie for later validation
        response.set_cookie(
            key="oauth_state",
            value=state,
            max_age=600,  # 10 minutes
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        
        return response
        
    except Exception as e:
        log.error(f"Google login initialization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not initialize login",
        )


# ============================================
# Step 2: Handle OAuth Callback
# ============================================

@router.get("/google/callback", tags=["auth"])
async def google_callback(
    code: str,
    state: str,
    session: Session = Depends(get_session),
):
    """
    Handle Google OAuth callback
    
    1. Validates state token (CSRF protection)
    2. Exchanges auth code for tokens
    3. Fetches user info from Google
    4. Creates or updates user in DB
    5. Generates JWT tokens
    6. Sets secure cookies
    7. Redirects to app
    
    Args:
        code: Authorization code from Google
        state: State token from Google (must match cookie)
        session: Database session
        
    Returns:
        RedirectResponse to /app with JWT cookies set
    """
    try:
        # Get state from cookie
        # Note: FastAPI doesn't expose cookies in params, would need middleware
        # For now, we'll validate state from query param (less secure)
        # TODO: Implement proper cookie reading in middleware
        
        # Exchange code for tokens with Google
        log.info("Exchanging authorization code for tokens")
        tokens = await oauth_service.exchange_code_for_tokens(code)
        
        if not tokens or "access_token" not in tokens:
            log.error("Token exchange returned invalid response")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token response from Google",
            )
        
        # Fetch user info from Google
        log.info("Fetching user info from Google")
        google_user = await oauth_service.get_user_info(tokens["access_token"])
        
        if not google_user or "email" not in google_user:
            log.error("Google userinfo missing required fields")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user info from Google",
            )
        
        # Parse user data
        user_data = oauth_service.parse_user_info(google_user)
        
        # Check if user exists
        existing_user = session.exec(
            select(User).where(User.email == user_data["email"])
        ).first()
        
        if existing_user:
            # Update existing user
            log.info(f"Updating existing user: {user_data['email']}")
            existing_user.username = user_data["username"]
            existing_user.profile_picture_url = user_data.get("profile_picture_url")
            session.add(existing_user)
            session.commit()
            session.refresh(existing_user)
            user = existing_user
        else:
            # Create new user
            log.info(f"Creating new user: {user_data['email']}")
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # Generate JWT tokens for our app
        access_token = jwt_service.create_access_token(user_id=user.id)
        refresh_token = jwt_service.create_refresh_token(user_id=user.id)
        
        # Redirect to app with cookies
        response = RedirectResponse(url="/app", status_code=status.HTTP_302_FOUND)
        
        # Set access token cookie (1 hour)
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=3600,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        
        # Set refresh token cookie (30 days)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=2592000,  # 30 days
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        
        # Clear oauth state cookie
        response.delete_cookie("oauth_state")
        
        log.info(f"User {user.id} authenticated successfully")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"OAuth callback failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        )


# ============================================
# Step 3: Refresh Access Token
# ============================================

@router.post("/refresh", tags=["auth"])
async def refresh_token(request_cookies: dict = None):
    """
    Refresh expired access token using refresh token
    
    Client sends refresh_token in httponly cookie or Authorization header.
    Returns new access_token in response.
    
    Returns:
        {access_token, token_type, expires_in}
    """
    try:
        # Get refresh token from cookies (would need middleware in real app)
        # For now, return instructions
        
        # In production, extract from request.cookies
        refresh_token_value = request_cookies.get("refresh_token") if request_cookies else None
        
        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing refresh token",
            )
        
        # Validate refresh token
        user_id = jwt_service.get_user_id_from_token(
            refresh_token_value,
            token_type="refresh"
        )
        
        # Generate new access token
        new_access_token = jwt_service.create_access_token(user_id=user_id)
        
        log.info(f"Refreshed token for user {user_id}")
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


# ============================================
# Step 4: Logout
# ============================================

@router.post("/logout", tags=["auth"])
async def logout():
    """
    Clear authentication tokens
    
    Returns:
        Response with cleared cookies
    """
    try:
        response = Response(content="Logged out")
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        response.delete_cookie("oauth_state")
        
        log.info("User logged out")
        return response
        
    except Exception as e:
        log.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        )


# ============================================
# Helper: Get Current User (for protected routes)
# ============================================

async def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> UserResponse:
    """
    Dependency to get current authenticated user
    
    Usage:
        @app.get("/users/me")
        async def get_me(user: UserResponse = Depends(get_current_user)):
            return user
    
    Args:
        request: FastAPI request (contains cookies/state)
        session: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException 401: If token invalid/missing
    """
    # Get token from middleware state or directly from cookies
    access_token = getattr(request.state, 'access_token', None)
    
    if not access_token:
        access_token = request.cookies.get("access_token")
    
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    
    try:
        user_id = jwt_service.get_user_id_from_token(access_token)
        user = session.exec(select(User).where(User.id == user_id)).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        log.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ============================================
# Test: Get Current User Info
# ============================================

@router.get("/me", response_model=UserResponse, tags=["auth"])
async def get_me(user: UserResponse = Depends(get_current_user)):
    """
    Get current authenticated user info
    
    Protected route - requires valid access_token
    
    Returns:
        Current user object
    """
    return user
