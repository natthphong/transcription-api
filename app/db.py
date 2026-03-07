from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import load_settings

settings = load_settings()
if not settings.DBConfig:
    raise RuntimeError("DBConfig missing in config.yaml")

engine = create_async_engine(
    settings.DBConfig.dsn_asyncpg(),
    pool_size=settings.DBConfig.MaxOpenConn,
    pool_recycle=settings.DBConfig.MaxConnLifeTime,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session