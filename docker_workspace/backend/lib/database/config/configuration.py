from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine

Base = declarative_base()

ASYNC_USER_DATABASE_URL = "postgresql+asyncpg://qa:qa@localhost:5432/user_table"
ASYNC_TABLES_DATABASE_URL = "postgresql+asyncpg://qa:qa@localhost:5432/temp_tables"

async_user_engine = create_async_engine(ASYNC_USER_DATABASE_URL, echo=False)
async_user_session_local = sessionmaker(bind=async_user_engine, class_=AsyncSession, expire_on_commit=False)

async_tables_engine = create_async_engine(ASYNC_TABLES_DATABASE_URL, echo=False)
async_tables_session_local = sessionmaker(bind=async_tables_engine, class_=AsyncSession, expire_on_commit=False)

async def getAsyncUserDB():
    async with async_user_session_local() as db:
        try:
            yield db
        finally:
            await db.close()

async def getAsyncTablesDB():
    async with async_tables_session_local() as db:
        try:
            yield db
        finally:
            await db.close()