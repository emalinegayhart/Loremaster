import os
import logging
from typing import Optional

log = logging.getLogger(__name__)


class SecretService:
    """Load and manage secrets from environment variables"""
    
    # OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # JWT
    JWT_SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    
    # API
    API_BASE_URL: str  # http://localhost:8000 or https://example.com
    
    @classmethod
    def load(cls):
        """Load all secrets from environment"""
        cls.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        cls.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
        cls.GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/auth/google/callback")
        
        cls.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
        
        cls.DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING", "postgresql://user:password@localhost/loremaster")
        
        cls.API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        # Validate required secrets
        required = ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "JWT_SECRET_KEY"]
        missing = [key for key in required if not getattr(cls, key, None)]
        
        if missing:
            log.warning(f"Missing environment variables: {', '.join(missing)}")
            if any(key in required for key in missing):
                raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    @classmethod
    def validate(cls) -> bool:
        """Validate all secrets are loaded"""
        return all([
            cls.GOOGLE_CLIENT_ID,
            cls.GOOGLE_CLIENT_SECRET,
            cls.JWT_SECRET_KEY,
            cls.DATABASE_URL,
            cls.API_BASE_URL,
        ])
