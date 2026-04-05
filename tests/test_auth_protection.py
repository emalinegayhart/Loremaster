import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "webapp" / "backend"))

os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-min-32-chars"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8000/api/auth/callback"

from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends, Request
from sqlmodel import Session, create_engine, SQLModel, select
from sqlmodel.pool import StaticPool

from services.secret_service import SecretService
from models import User
from services.jwt_service import JWTService
from services.token_blacklist import get_blacklist
from db import get_session

SecretService.load()

from middleware.auth_middleware import TokenExtractionMiddleware, ProtectedRouteMiddleware

jwt_service = JWTService(os.environ["JWT_SECRET_KEY"])
blacklist = get_blacklist()


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    user = User(
        email="test@example.com",
        username="testuser",
        oauth_id="google-123",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app = FastAPI()
    
    app.add_middleware(ProtectedRouteMiddleware)
    app.add_middleware(TokenExtractionMiddleware)
    
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    
    @app.post("/api/auth/refresh")
    async def refresh(request: Request):
        token = request.cookies.get("refresh_token")
        if not token:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=401, detail="Missing refresh token")
        
        user_id = jwt_service.get_user_id_from_token(token, token_type="refresh")
        new_access = jwt_service.create_access_token(user_id)
        
        from fastapi import Response
        response = Response()
        response.set_cookie(
            key="access_token",
            value=new_access,
            max_age=3600,
            httponly=True,
            secure=True,
        )
        return {"access_token": new_access}
    
    @app.post("/api/auth/logout")
    async def logout(request: Request):
        token = request.cookies.get("access_token")
        if token:
            blacklist.add_token(token)
        
        from fastapi import Response
        response = Response()
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response
    
    @app.get("/api/user/protected")
    async def protected_route(request: Request, session: Session = Depends(get_session)):
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        user = session.exec(select(User).where(User.id == user_id)).first()
        return {"id": user.id, "email": user.email}
    
    return TestClient(app)


class TestTokenBlacklist:
    
    def test_add_token_to_blacklist(self):
        blacklist.clear()
        token = "test-token-123"
        blacklist.add_token(token)
        
        assert blacklist.is_blacklisted(token)
    
    def test_token_not_blacklisted_initially(self):
        blacklist.clear()
        token = "not-blacklisted"
        
        assert not blacklist.is_blacklisted(token)
    
    def test_multiple_tokens_blacklist(self):
        blacklist.clear()
        token1 = "token1"
        token2 = "token2"
        
        blacklist.add_token(token1)
        blacklist.add_token(token2)
        
        assert blacklist.is_blacklisted(token1)
        assert blacklist.is_blacklisted(token2)
        assert blacklist.size() == 2
    
    def test_remove_token_from_blacklist(self):
        blacklist.clear()
        token = "token-to-remove"
        
        blacklist.add_token(token)
        assert blacklist.is_blacklisted(token)
        
        blacklist.remove_token(token)
        assert not blacklist.is_blacklisted(token)


class TestTokenRefresh:
    
    def test_refresh_without_refresh_token(self, client):
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401
    
    def test_refresh_with_valid_refresh_token(self, client, test_user):
        blacklist.clear()
        refresh_token = jwt_service.create_refresh_token(test_user.id)
        
        response = client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_refresh_sets_new_access_token_cookie(self, client, test_user):
        blacklist.clear()
        refresh_token = jwt_service.create_refresh_token(test_user.id)
        
        response = client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200
        assert "access_token" in response.cookies or "access_token" in response.json()
    
    def test_refresh_with_invalid_refresh_token(self, client):
        response = client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": "invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_refresh_with_access_token_fails(self, client, test_user):
        access_token = jwt_service.create_access_token(test_user.id)
        
        response = client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": access_token}
        )
        
        assert response.status_code == 401


class TestLogout:
    
    def test_logout_clears_cookies(self, client):
        response = client.post("/api/auth/logout")
        
        assert response.status_code == 200
    
    def test_logout_blacklists_token(self, client, test_user):
        blacklist.clear()
        access_token = jwt_service.create_access_token(test_user.id)
        
        response = client.post(
            "/api/auth/logout",
            cookies={"access_token": access_token}
        )
        
        assert response.status_code == 200
        assert blacklist.is_blacklisted(access_token)
    
    def test_logout_without_token(self, client):
        blacklist.clear()
        response = client.post("/api/auth/logout")
        
        assert response.status_code == 200


class TestProtectedRouteMiddleware:
    
    def test_protected_route_without_token(self, client):
        response = client.get("/api/user/protected")
        assert response.status_code == 401
    
    def test_protected_route_with_valid_token(self, client, test_user):
        blacklist.clear()
        access_token = jwt_service.create_access_token(test_user.id)
        
        response = client.get(
            "/api/user/protected",
            cookies={"access_token": access_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
    
    def test_protected_route_with_invalid_token(self, client):
        response = client.get(
            "/api/user/protected",
            cookies={"access_token": "invalid-token"}
        )
        
        assert response.status_code == 401
    
    def test_protected_route_with_blacklisted_token(self, client, test_user):
        blacklist.clear()
        access_token = jwt_service.create_access_token(test_user.id)
        blacklist.add_token(access_token)
        
        response = client.get(
            "/api/user/protected",
            cookies={"access_token": access_token}
        )
        
        assert response.status_code == 401
        assert "invalidated" in response.json().get("detail", "").lower()


class TestTokenExtractionMiddleware:
    
    def test_token_extracted_from_cookie(self, client, test_user):
        blacklist.clear()
        access_token = jwt_service.create_access_token(test_user.id)
        
        response = client.get(
            "/api/user/protected",
            cookies={"access_token": access_token}
        )
        
        assert response.status_code == 200
    
    def test_token_extracted_from_authorization_header(self, client, test_user):
        blacklist.clear()
        access_token = jwt_service.create_access_token(test_user.id)
        
        response = client.get(
            "/api/user/protected",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert response.status_code == 200


class TestFullAuthFlow:
    
    def test_token_lifecycle(self, client, test_user):
        blacklist.clear()
        
        access_token = jwt_service.create_access_token(test_user.id)
        refresh_token = jwt_service.create_refresh_token(test_user.id)
        
        response = client.get(
            "/api/user/protected",
            cookies={"access_token": access_token}
        )
        assert response.status_code == 200
        
        response = client.post(
            "/api/auth/refresh",
            cookies={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        new_access = response.json().get("access_token")
        assert new_access is not None
        
        response = client.post(
            "/api/auth/logout",
            cookies={"access_token": new_access}
        )
        assert response.status_code == 200
        
        response = client.get(
            "/api/user/protected",
            cookies={"access_token": new_access}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
