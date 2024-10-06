from fastapi import (HTTPException, status, Cookie)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
from lib.ai.memory.memory import CustomMemoryDict
from lib.config_parser.config_parser import Configuration
import os, asyncio, shutil, uuid, time

class RedisTool:
    def __init__(self, memory: CustomMemoryDict, session_timeout: int, redis_ip: str, redis_port: int) -> None:
        self.redis = Redis(host=redis_ip, port=redis_port, decode_responses=True, db=0)
        self.memory = memory
        self.session_timeout = session_timeout

        config = Configuration()
        self.async_database_url = config.getAsyncDatabaseUrl()

    async def createSession(self) -> str:
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        while await self.redis.exists(session_key):
            session_id = str(uuid.uuid4())
            session_key = f"session:{session_id}"
            
        await self.redis.hset(session_key, mapping={"created_at": str(time.time()), "data": "{}"})
        await self.resetSessionTimeout(session_id=session_id)
        return session_id

    async def getSession(self, session_id: str = Cookie(None)) -> tuple:
        session_key = f"session:{session_id}"
        session_data = await self.redis.hgetall(session_key)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. Invalid session.",
                headers={"WWW-Authenticate": "Bearer"})
        
        return session_id, session_data
    
    async def getAllSessions(self) -> list:
        session_keys = await self.redis.keys('session:*')
        return session_keys

    async def updateSession(self, session_id: str, key: str, value: str) -> None:
        session_key = f"session:{session_id}"
        await self.redis.hset(session_key, key, value)
        await self.resetSessionTimeout(session_id=session_id)
    
    async def deleteSession(self, session_id: str) -> None:
        session_key = f"session:{session_id}"
        await self.redis.delete(session_key)
    
    async def resetSessionTimeout(self, session_id: str) -> None:
        session_key = f"session:{session_id}"
        await self.redis.expire(session_key, self.session_timeout)
    

    async def _listenForExpirations(self) -> None:
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("__keyevent@0__:expired")

        try:
            async for message in pubsub.listen():
                if message["type"] == "pmessage":
                    session_key = message["data"]
                    if session_key.startswith("session:"):
                        session_id = session_key.split(":")[1]
                        session_data = await self.redis.hgetall(session_key)
                        await self._deleteTempDatabase(session_data)
                        await self._deleteVectorStore(session_data)
        except asyncio.CancelledError:
            pubsub = self.redis.pubsub()
            await pubsub.psubscribe("__keyevent@0__:expired")

        

    async def _deleteTempDatabase(self, session_data: str):
        db_url = self.async_database_url + "/postgres"
        
        temp_database_name = session_data.get("temp_database_path", "")
        
        async_temp_database_engine = create_async_engine(db_url, echo=False, isolation_level="AUTOCOMMIT")
        
        async with async_temp_database_engine.connect() as connection:
            db_check_query = f"SELECT 1 FROM pg_database WHERE datname = '{temp_database_name}';"
            result = await connection.execute(text(db_check_query))
            database_exists = result.fetchone()

            if database_exists:
                terminate_connections_query = f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{temp_database_name}'
                    AND pid <> pg_backend_pid();
                """
                await connection.execute(text(terminate_connections_query))

                drop_db_query = f"DROP DATABASE {temp_database_name};"
                await connection.execute(text(drop_db_query))

        return True

    async def _deleteVectorStore(self, session_data: str):        
        vector_store_path = session_data.get("vector_store_path", "")
        
        if vector_store_path != '':
            try:
                if os.path.isdir(vector_store_path):
                    await asyncio.to_thread(shutil.rmtree, path=vector_store_path, ignore_errors=True)
                else:
                    await asyncio.to_thread(os.remove, vector_store_path)
            except:
                pass

        return True