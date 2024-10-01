from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from lib.instances.instance import instance

database_user_database_name = instance.async_database_url + "/" + instance.user_database_name

async_user_engine = create_async_engine(database_user_database_name, echo=False)
async_user_session_local = sessionmaker(bind=async_user_engine, class_=AsyncSession, expire_on_commit=False)

async def getAsyncUserDB():
    async with async_user_session_local() as db:
        try:
            yield db
        finally:
            await db.close()