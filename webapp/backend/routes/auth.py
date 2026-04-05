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
from services.token_blacklist import get_blacklist
from db import get_session

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

jwt_service = JWTService(SecretService.JWT_SECRET_KEY)
oauth_service = OAuthService()
blacklist = get_blacklist()

@router.get("/google", tags=["auth"])
async def google_login():
    """
    Start Google OAuth 2.0 flow.
    
    Returns:
        RedirectResponse to Google authorization URL
    """
    try:
        state = oauth_service.generate_state_token()
        auth_url = oauth_service.build_authorization_url(state)
        response = RedirectResponse(url=auth_url)
        
        response.set_cookie(
            key="oauth_state",
            value=state,
            max_age=600,
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


@router.get("/google/callback", tags=["auth"])
async def google_callback(
    code: str,
    state: str,
    session: Session = Depends(get_session),
):
    """Handle Google OAuth callback."""
    try:
        tokens = await oauth_service.exchange_code_for_tokens(code)
        
        if not tokens or "access_token" not in tokens:
            log.error("Token exchange returned invalid response")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token response from Google",
            )
        
        google_user = await oauth_service.get_user_info(tokens["access_token"])
        
        if not google_user or "email" not in google_user:
            log.error("Google userinfo missing required fields")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user info from Google",
            )
        
        user_data = oauth_service.parse_user_info(google_user)
        
        existing_user = session.exec(
            select(User).where(User.email == user_data["email"])
        ).first()
        
        if existing_user:
            log.info(f"Updating existing user: {user_data['email']}")
            existing_user.username = user_data["username"]
            existing_user.profile_picture_url = user_data.get("profile_picture_url")
            session.add(existing_user)
            session.commit()
            session.refresh(existing_user)
            user = existing_user
        else:
            log.info(f"Creating new user: {user_data['email']}")
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
        
        access_token = jwt_service.create_access_token(user_id=user.id)
        refresh_token = jwt_service.create_refresh_token(user_id=user.id)
        
        response = RedirectResponse(url="/app", status_code=status.HTTP_302_FOUND)
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            max_age=3600,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            max_age=2592000,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        
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


@router.post("/refresh", tags=["auth"])
async def refresh_token(request: Request):
    """Refresh expired access token using refresh token from cookie."""
    try:
        refresh_token_value = request.cookies.get("refresh_token")
        
        if not refresh_token_value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing refresh token",
            )
        
        user_id = jwt_service.get_user_id_from_token(
            refresh_token_value,
            token_type="refresh"
        )
        
        new_access_token = jwt_service.create_access_token(user_id=user_id)
        
        log.info(f"Refreshed token for user {user_id}")
        
        response = Response()
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            max_age=3600,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        
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


@router.post("/logout", tags=["auth"])
async def logout(request: Request):
    """Clear authentication tokens."""
    try:
        token = request.cookies.get("access_token")
        
        if token:
            blacklist.add_token(token)
        
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


async def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
) -> UserResponse:
    """Get current authenticated user from token in request."""
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


@router.get("/me", response_model=UserResponse, tags=["auth"])
async def get_me(user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user info."""
    return user
