from fastapi import (HTTPException, status, Cookie)
from redis.asyncio import Redis
from lib.ai.memory.memory import CustomMemoryDict
import uuid, time, os, asyncio

class RedisTool:
    def __init__(self, memory: CustomMemoryDict, session_timeout: int, redis_ip: str, redis_port: int) -> None:
        self.redis = Redis(host=redis_ip, port=redis_port, decode_responses=True)
        self.memory = memory
        self.session_timeout = session_timeout

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session.")
        
        return session_id, session_data

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

        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                session_key = message["data"]
                if session_key.startswith("session:"):
                    session_id = session_key.split(":")[1]
                    await self._onSessionExpired(session_id)
    
    async def _onSessionExpired(self, session_id: str) -> None:
        temp_db_path = f".temp_databases/temporary_database_{session_id}.db"

        try:
            await asyncio.to_thread(os.remove, temp_db_path)
        except:
            pass

        await self.memory.deleteMemory(session_id=session_id)