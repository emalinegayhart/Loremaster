"""
Tests for OAuth 2.0 setup (PR-AUTH-1)
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "webapp" / "backend"))

# Mock environment before imports
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from services.jwt_service import JWTService
from services.oauth_service import OAuthService
from services.secret_service import SecretService
from models import User, UserCreate


class TestJWTService:
    """Test JWT token generation and validation"""
    
    @pytest.fixture
    def jwt_service(self):
        return JWTService("test-secret-key")
    
    def test_create_access_token(self, jwt_service):
        """Access token creation works"""
        token = jwt_service.create_access_token(user_id=123)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self, jwt_service):
        """Refresh token creation works"""
        token = jwt_service.create_refresh_token(user_id=123)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_validate_access_token(self, jwt_service):
        """Access token validation works"""
        user_id = 123
        token = jwt_service.create_access_token(user_id)
        
        payload = jwt_service.validate_token(token, token_type="access")
        assert payload["sub"] == "123"
        assert payload["type"] == "access"
    
    def test_validate_refresh_token(self, jwt_service):
        """Refresh token validation works"""
        user_id = 456
        token = jwt_service.create_refresh_token(user_id)
        
        payload = jwt_service.validate_token(token, token_type="refresh")
        assert payload["sub"] == "456"
        assert payload["type"] == "refresh"
    
    def test_validate_token_wrong_type_raises_error(self, jwt_service):
        """Validating token with wrong type raises HTTPException"""
        token = jwt_service.create_access_token(user_id=123)
        
        with pytest.raises(Exception):  # HTTPException
            jwt_service.validate_token(token, token_type="refresh")
    
    def test_get_user_id_from_token(self, jwt_service):
        """Extract user_id from token"""
        user_id = 789
        token = jwt_service.create_access_token(user_id)
        
        extracted_id = jwt_service.get_user_id_from_token(token)
        assert extracted_id == user_id
    
    def test_is_token_expired(self, jwt_service):
        """Check token expiration"""
        token = jwt_service.create_access_token(user_id=123)
        assert not jwt_service.is_token_expired(token)
    
    def test_invalid_token_raises_error(self, jwt_service):
        """Invalid token raises HTTPException"""
        with pytest.raises(Exception):  # HTTPException
            jwt_service.validate_token("invalid.token.string")


class TestOAuthService:
    """Test Google OAuth integration"""
    
    @pytest.fixture
    def oauth_service(self):
        SecretService.load()  # Load secrets before creating service
        return OAuthService()
    
    def test_generate_state_token(self, oauth_service):
        """State token generation works"""
        state = oauth_service.generate_state_token()
        assert isinstance(state, str)
        assert len(state) > 0
        
        # Different calls generate different tokens
        state2 = oauth_service.generate_state_token()
        assert state != state2
    
    def test_build_authorization_url(self, oauth_service):
        """Build Google authorization URL"""
        state = "test-state-token"
        url = oauth_service.build_authorization_url(state)
        
        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert "scope=openid" in url  # Check for scope parameter (spaces vs + varies)
        assert "email" in url
        assert "profile" in url
        assert f"state={state}" in url
    
    def test_validate_state_token_success(self, oauth_service):
        """State token validation succeeds for matching tokens"""
        state = "matching-state-token"
        is_valid = oauth_service.validate_state_token(state, state)
        assert is_valid is True
    
    def test_validate_state_token_failure_mismatch(self, oauth_service):
        """State token validation fails for mismatched tokens"""
        is_valid = oauth_service.validate_state_token("token1", "token2")
        assert is_valid is False
    
    def test_validate_state_token_failure_empty(self, oauth_service):
        """State token validation fails for empty tokens"""
        is_valid = oauth_service.validate_state_token("", "token")
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_parse_user_info(self, oauth_service):
        """Parse Google user info"""
        google_user = {
            "id": "123456789",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/pic.jpg",
        }
        
        parsed = oauth_service.parse_user_info(google_user)
        
        assert parsed["oauth_id"] == "123456789"
        assert parsed["email"] == "user@example.com"
        assert parsed["username"] == "Test User"
        assert parsed["profile_picture_url"] == "https://example.com/pic.jpg"
        assert parsed["oauth_provider"] == "google"


class TestSecretService:
    """Test secret loading"""
    
    def test_secrets_loaded(self):
        """Secrets are loaded from environment"""
        SecretService.load()
        
        assert SecretService.GOOGLE_CLIENT_ID == "test-client-id"
        assert SecretService.GOOGLE_CLIENT_SECRET == "test-client-secret"
        assert SecretService.JWT_SECRET_KEY == "test-jwt-secret"
    
    def test_validate_secrets(self):
        """Secret validation works"""
        SecretService.load()
        is_valid = SecretService.validate()
        assert is_valid is True


class TestUserModel:
    """Test User Sqlmodel"""
    
    def test_user_create_model(self):
        """UserCreate model works"""
        user_data = UserCreate(
            email="test@example.com",
            username="testuser",
            oauth_id="123456789",
            profile_picture_url="https://example.com/pic.jpg",
        )
        
        assert user_data.email == "test@example.com"
        assert user_data.username == "testuser"
        assert user_data.oauth_id == "123456789"
        assert user_data.oauth_provider == "google"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
