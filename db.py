"""
Database configuration and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from models import Base
import os
from pathlib import Path

# Ensure data directory exists
Path("data").mkdir(exist_ok=True)

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/toolbot.db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    future=True
)

# Create async session maker
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully!")

async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session() as session:
        yield session

# Dependency for handlers to get DB session
async def get_db():
    """Dependency to get database session in handlers"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()