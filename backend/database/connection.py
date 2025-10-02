from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
# Try to load .env file if it exists, but don't fail if it doesn't
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Get database URL and ensure proper format
db_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./apsara.db")

# Create engine
engine = create_async_engine(
    db_url,
    echo=False,
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def init_db():
    """Initialize database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """Dependency for getting async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



