import logging
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DatabaseError
from sqlmodel import SQLModel, Session
from services.secret_service import SecretService

log = logging.getLogger(__name__)

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


def init_db(retries=3, delay=2):
    """Create all tables with retry logic"""
    for attempt in range(retries):
        try:
            SQLModel.metadata.create_all(engine)
            print("✅ Database initialized")
            return
        except (OperationalError, DatabaseError) as e:
            if attempt < retries - 1:
                log.warning(f"Database unavailable (attempt {attempt+1}/{retries}), retrying in {delay}s: {e}")
                time.sleep(delay)
            else:
                log.warning(f"Database unavailable after {retries} attempts: {e}")
                raise


def drop_all_tables():
    """⚠️ Drop all tables (dev only)"""
    SQLModel.metadata.drop_all(engine)
    print("⚠️ All tables dropped")
