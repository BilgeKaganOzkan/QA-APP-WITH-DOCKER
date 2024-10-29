from fastapi import (HTTPException, status, Cookie)
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text
from lib.ai.memory.memory import CustomMemoryDict
import os, asyncio, shutil, uuid, time

class RedisTool:
    """
    @brief A tool for managing session storage and handling expiration events in Redis.

    RedisTool provides functions to create, retrieve, update, delete, and monitor sessions.
    It also manages temporary databases and vector stores linked to session data.
    
    @param memory An instance of CustomMemoryDict for handling memory-related operations.
    @param session_timeout Session expiration time in seconds.
    @param redis_ip IP address of the Redis server.
    @param redis_port Port number of the Redis server.
    @param async_database_url URL for the asynchronous database connection.
    """

    def __init__(self, memory: CustomMemoryDict, session_timeout: int, redis_ip: str, redis_port: int, async_database_url) -> None:
        self.redis = Redis(host=redis_ip, port=redis_port, decode_responses=True, db=0)
        self.memory = memory
        self.session_timeout = session_timeout
        self.async_database_url = async_database_url
        self.db_suffix = "/postgres"

    async def createSession(self) -> str:
        """
        @brief Creates a new session with a unique session ID.
        
        Generates a new session ID and stores it in Redis with a default timeout.
        
        @return The newly generated session ID.
        """
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"
        while await self.redis.exists(session_key):
            session_id = str(uuid.uuid4())
            session_key = f"session:{session_id}"

        await self.redis.hset(session_key, mapping={"created_at": str(time.time()), "data": "{}"})
        await self.resetSessionTimeout(session_id=session_id)
        return session_id

    async def getSession(self, session_id: str = Cookie(None)) -> tuple:
        """
        @brief Retrieves session data for the provided session ID.
        
        @param session_id The ID of the session to retrieve.
        @return Tuple of session ID and session data.
        
        @exception HTTPException If the session is invalid or does not exist.
        """
        session_key = f"session:{session_id}"
        session_data = await self.redis.hgetall(session_key)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed. Invalid session.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return session_id, session_data
    
    async def getAllSessions(self) -> list:
        """
        @brief Retrieves all active session keys in Redis.
        
        @return List of session keys currently stored in Redis.
        """
        session_keys = await self.redis.keys('session:*')
        return session_keys

    async def updateSession(self, session_id: str, key: str, value: str) -> None:
        """
        @brief Updates a specific key-value pair within a session and resets the timeout.
        
        @param session_id The session ID to update.
        @param key The key within the session data to update.
        @param value The new value for the specified key.
        """
        session_key = f"session:{session_id}"
        await self.redis.hset(session_key, key, value)
        await self.resetSessionTimeout(session_id=session_id)
    
    async def deleteSession(self, session_id: str) -> None:
        """
        @brief Deletes a session from Redis.
        
        @param session_id The ID of the session to delete.
        """
        session_key = f"session:{session_id}"
        await self.redis.delete(session_key)
    
    async def resetSessionTimeout(self, session_id: str) -> None:
        """
        @brief Resets the timeout for a given session to the configured session_timeout value.
        
        @param session_id The ID of the session to reset the timeout for.
        """
        session_key = f"session:{session_id}"
        await self.redis.expire(session_key, self.session_timeout)
    
    async def _listenForExpirations(self) -> None:
        """
        @brief Monitors Redis for session expiration events and handles cleanup tasks.
        
        Listens to the Redis expiration channel and triggers cleanup operations
        on session data, such as deleting temporary databases and vector stores.
        """
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
        """
        @brief Deletes a temporary database associated with session data.

        Checks if a temporary database exists and, if so, terminates any active connections 
        before dropping the database.
        
        @param session_data Session data containing the temporary database path.
        @return True if deletion was attempted, even if the database didn't exist.
        """
        db_url = self.async_database_url + self.db_suffix
        temp_database_name = session_data.get("temp_database_path", "")
        
        async_temp_database_engine = create_async_engine(db_url, echo=False, isolation_level="AUTOCOMMIT")
        
        async with async_temp_database_engine.connect() as connection:
            db_check_query = f"SELECT 1 FROM pg_database WHERE datname = '{temp_database_name}';"
            result = await connection.execute(text(db_check_query))
            database_exists = result.fetchone()

            if database_exists:
                # Terminate active connections to the temporary database before dropping it
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
        """
        @brief Deletes a vector store directory or file associated with the session.

        Removes the directory or file located at the path specified in `vector_store_path`
        within session data.
        
        @param session_data Session data containing the vector store path.
        @return True if deletion was attempted, even if the path didn't exist.
        """
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