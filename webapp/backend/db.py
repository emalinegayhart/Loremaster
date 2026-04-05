from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session
from services.secret_service import SecretService

# Initialize secrets first
SecretService.load()

# Create engine
engine = create_engine(
    SecretService.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Test connections before using them
)

# Session factory
SessionLocal = sessionmaker(
    engine,
    class_=Session,
    expire_on_commit=False,
)


def get_session():
    """Dependency for FastAPI to get DB session"""
    with SessionLocal() as session:
        yield session


def init_db():
    """Create all tables"""
    SQLModel.metadata.create_all(engine)
    print("✅ Database initialized")


def drop_all_tables():
    """⚠️ Drop all tables (dev only)"""
    SQLModel.metadata.drop_all(engine)
    print("⚠️ All tables dropped")
