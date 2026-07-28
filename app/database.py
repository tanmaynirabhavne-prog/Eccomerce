from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os


# Load .env file
load_dotenv()


# PostgreSQL URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")


# Fallback for testing
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./ecommerce.db"


# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )


# Database Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for models
Base = declarative_base()



# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()