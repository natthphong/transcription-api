from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

try:
    from sqlalchemy.ext.asyncio import async_sessionmaker
except ImportError:  # SQLAlchemy 1.4 compatibility
    async_sessionmaker = None

from app.config import load_settings

settings = load_settings()
database_url = settings.database_url()
if not database_url:
    raise RuntimeError("Database configuration missing. Set DBConfig or DATABASE_URL.")

engine = create_async_engine(
    database_url,
    pool_size=settings.DBConfig.MaxOpenConn if settings.DBConfig else 4,
    pool_recycle=settings.DBConfig.MaxConnLifeTime if settings.DBConfig else 300,
    pool_pre_ping=True,
)

if async_sessionmaker is not None:
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
else:
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
