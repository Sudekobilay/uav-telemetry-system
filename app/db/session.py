from typing import AsyncGenerator
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


async def ensure_database_exists():
    """
    MySQL'e doğrudan bağlanıp veritabanı yoksa otomatik oluşturur.
    """
    conn = await aiomysql.connect(
        host=settings.MYSQL_SERVER,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD if settings.MYSQL_PASSWORD else None
    )
    async with conn.cursor() as cur:
        await cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{settings.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
    conn.close()


engine = create_async_engine(
    settings.ASYNC_DATABASE_URI,
    echo=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()