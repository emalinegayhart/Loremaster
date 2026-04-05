from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import jwt
from fastapi import HTTPException, status


class JWTService:
    """JWT token generation and validation"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30    # 30 days

    def create_access_token(self, user_id: int) -> str:
        """Generate access token (short-lived, ~1 hour)"""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": str(user_id),
            "type": "access",
            "iat": now,
            "exp": expires,
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: int) -> str:
        """Generate refresh token (long-lived, ~30 days)"""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": expires,
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str, token_type: str = "access") -> Dict:
        """
        Validate token and extract claims.
        
        Args:
            token: JWT token string
            token_type: "access" or "refresh"
            
        Returns:
            Decoded payload
            
        Raises:
            HTTPException: If token invalid/expired
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}, got {payload.get('type')}",
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )

    def get_user_id_from_token(self, token: str, token_type: str = "access") -> int:
        """Extract user_id from token"""
        payload = self.validate_token(token, token_type)
        return int(payload["sub"])

    def is_token_expired(self, token: str) -> bool:
        """Check if token is expired without raising exception"""
        try:
            jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return False
        except jwt.ExpiredSignatureError:
            return True
        except jwt.InvalidTokenError:
            return True
