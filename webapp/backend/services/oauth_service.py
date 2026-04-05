import logging
import secrets
from typing import Optional, Dict
import httpx

from services.secret_service import SecretService

log = logging.getLogger(__name__)


class OAuthService:
    """Google OAuth 2.0 integration"""
    
    GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def __init__(self):
        self.client_id = SecretService.GOOGLE_CLIENT_ID
        self.client_secret = SecretService.GOOGLE_CLIENT_SECRET
        self.redirect_uri = SecretService.GOOGLE_REDIRECT_URI
    
    def generate_state_token(self) -> str:
        """Generate random CSRF protection token"""
        return secrets.token_urlsafe(32)
    
    def build_authorization_url(self, state: str) -> str:
        """
        Build Google OAuth authorization URL
        
        Args:
            state: CSRF protection token
            
        Returns:
            Full authorization URL to redirect user to
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "include_granted_scopes": "true",
            "state": state,
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.GOOGLE_AUTHORIZE_URL}?{query_string}"
    
    def validate_state_token(self, state_from_cookie: str, state_from_request: str) -> bool:
        """
        Validate CSRF token from callback
        
        Args:
            state_from_cookie: State stored in secure httponly cookie
            state_from_request: State from callback query param
            
        Returns:
            True if valid, False otherwise
        """
        if not state_from_cookie or not state_from_request:
            return False
        
        # Constant-time comparison to prevent timing attacks
        return secrets.compare_digest(state_from_cookie, state_from_request)
    
    async def exchange_code_for_tokens(self, code: str) -> Dict:
        """
        Exchange authorization code for access + refresh tokens
        
        Args:
            code: Authorization code from Google callback
            
        Returns:
            {access_token, refresh_token, expires_in, ...}
            
        Raises:
            Exception: If exchange fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.GOOGLE_TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": self.redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    timeout=10.0,
                )
                
                if response.status_code != 200:
                    log.error(f"Token exchange failed: {response.status_code} {response.text}")
                    raise Exception(f"Google token exchange failed: {response.status_code}")
                
                return response.json()
                
            except httpx.TimeoutException:
                log.error("Token exchange timeout")
                raise Exception("Google token exchange timeout")
            except Exception as e:
                log.error(f"Token exchange error: {str(e)}")
                raise
    
    async def get_user_info(self, access_token: str) -> Dict:
        """
        Fetch user info from Google using access token
        
        Args:
            access_token: Google access token
            
        Returns:
            {id, email, name, picture, ...}
            
        Raises:
            Exception: If request fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                
                if response.status_code != 200:
                    log.error(f"User info fetch failed: {response.status_code} {response.text}")
                    raise Exception(f"Google userinfo failed: {response.status_code}")
                
                user_info = response.json()
                
                # Validate required fields
                required_fields = ["id", "email"]
                missing = [f for f in required_fields if f not in user_info]
                if missing:
                    raise Exception(f"Missing required fields from Google: {missing}")
                
                return user_info
                
            except httpx.TimeoutException:
                log.error("User info fetch timeout")
                raise Exception("Google userinfo timeout")
            except Exception as e:
                log.error(f"User info fetch error: {str(e)}")
                raise
    
    def parse_user_info(self, google_user: Dict) -> Dict:
        """
        Parse Google user info into our format
        
        Args:
            google_user: Raw response from Google userinfo endpoint
            
        Returns:
            {oauth_id, email, username, profile_picture_url}
        """
        return {
            "oauth_id": google_user.get("id"),
            "email": google_user.get("email"),
            "username": google_user.get("name", google_user.get("email", "").split("@")[0]),
            "profile_picture_url": google_user.get("picture"),
            "oauth_provider": "google",
        }
