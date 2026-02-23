# apps/core/session.py
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from apps.core.settings import settings

# ==========================================
# ASYNC ENGINE (для основного приложения)
# ==========================================
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# ==========================================
# SYNC ENGINE (для SQLAdmin)
# ==========================================
# Конвертируем async URL в sync для SQLAdmin
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2") \
    .replace("+aiosqlite", "+sqlite") \
    .replace("+aiomysql", "+pymysql")

sync_engine: create_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    expire_on_commit=False,
    class_=Session,
)

# ==========================================
# EXPORT
# ==========================================
__all__ = ["engine", "sync_engine", "AsyncSessionLocal", "SyncSessionLocal"]