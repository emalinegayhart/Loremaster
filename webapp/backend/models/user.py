from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    """Base User fields shared between request/response"""
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    profile_picture_url: Optional[str] = None


class User(UserBase, table=True):
    """User database model"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    oauth_provider: str = Field(default="google", index=True)
    oauth_id: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(UserBase):
    """Data received from OAuth provider"""
    oauth_id: str
    oauth_provider: str = "google"


class UserResponse(UserBase):
    """User data returned to frontend"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
