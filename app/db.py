from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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

SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
