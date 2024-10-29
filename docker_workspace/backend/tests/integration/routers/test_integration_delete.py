import pytest, os, asyncio, time
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from lib.routers.delete import instance, router
from lib.database.config.configuration import getAsyncDB
from fastapi import status
from tests.integration.fixtures import *

@pytest.mark.asyncio
async def test_clear_session(setup_and_tear_down, event_loop):
    """
    Integration Test: Verifies the `clearSession` functionality.

    **Purpose**: Ensure that calling `clearSession` deletes any temporary database tables and vector store files associated with the session.

    **Steps**:
    1. **Session Setup**: Create a Redis session with mock data for testing.
    2. **Database Preparation**: Drop any pre-existing test database, then create a new one.
    3. **Table Creation**: Create a test table within the new database.
    4. **Vector Store Directory Setup**: Create a directory for storing test vector files.
    5. **API Request**: Call the `clearSession` endpoint and verify the response.
    6. **Data Deletion Verification**: Check that the database table and vector store directory have been deleted.
    7. **Redis Cleanup**: Delete the Redis session data after test completion.

    **Expected Outcome**:
    - The database table and vector store files should be deleted.
    - The API response should confirm session clearing.
    """

    # Step 1: Set up the Redis session key with mock data
    session_key = f"session:{FAKE_SESSION_ID}"
    vector_store_path = f'./.vector_stores/{FAKE_SESSION_ID}'
    await instance.redis_tool.redis.hset(session_key, mapping={"created_at": str(time.time()), "temp_database_path": TEST_DB_NAME, "vector_store_path": vector_store_path})

    # Step 2: Ensure any previous test database is removed, then create a new database for testing
    async for db in getAsyncDB("postgres"):
        terminate_query = text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        await db.execute(terminate_query)
        await db.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await db.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))

    # Step 3: Create a test table within the newly created database
    async for db in getAsyncDB(TEST_DB_NAME):
        await db.execute(text("DROP TABLE IF EXISTS test_table"))
        await db.execute(text("CREATE TABLE test_table (id SERIAL PRIMARY KEY, name VARCHAR(50))"))
        await db.commit()

    # Step 4: Set up the vector store directory for test purposes
    os.makedirs(vector_store_path, exist_ok=True)

    # Step 5: Send request to `clearSession` endpoint and verify the response
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        client.cookies.set("session_id", FAKE_SESSION_ID)
        response = await client.delete(instance.clear_session_end_point)

    # Step 6: Verify the response status and check that it confirms session clearing
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result == {"informationMessage": "Session cleared."}

    # Step 7: Confirm deletion of temporary data (database table and vector store)
    async for db in getAsyncDB("postgres"):
        result = await db.execute(text(f"SELECT 1 FROM test_table"))
        assert not result.fetchone(), "Temporary table was not deleted."
    
    # Check that the vector store path has been deleted
    assert not os.path.exists(vector_store_path), "Vector store path was not deleted."

    # Final Cleanup: Remove the session key from Redis
    await instance.redis_tool.redis.delete(session_key)

@pytest.mark.asyncio
async def test_end_session(setup_and_tear_down, event_loop):
    """
    Integration Test: Verifies the `endSession` functionality.

    **Purpose**: Ensure that calling `endSession` removes session data from Redis, deletes the temporary database, and removes vector store files.

    **Steps**:
    1. **Session Setup**: Initialize a Redis session with mock session data.
    2. **Database Preparation**: Drop any pre-existing test database and create a new one.
    3. **Table Creation**: Create a test table within the temporary database.
    4. **Vector Store Directory Setup**: Create a directory for storing vector files.
    5. **API Request**: Call the `endSession` endpoint and verify the response.
    6. **Session Data Verification**: Confirm that session data is deleted from Redis.
    7. **Data Deletion Verification**: Check that the temporary database and vector store directory have been deleted.
    8. **Redis Cleanup**: Delete any remaining session data after test completion.

    **Expected Outcome**:
    - The Redis session data, database, and vector store files should all be deleted.
    - The API response should confirm session ending.
    """
    
    # Step 1: Set up the Redis session key with mock data for the test session
    session_key = f"session:{FAKE_SESSION_ID}"
    vector_store_path = f'./.vector_stores/{FAKE_SESSION_ID}'
    await instance.redis_tool.redis.hset(session_key, mapping={"created_at": str(time.time()), "temp_database_path": TEST_DB_NAME, "vector_store_path": vector_store_path})

    # Step 2: Drop any previous test database, then create a new one for the session
    async for db in getAsyncDB("postgres"):
        terminate_query = text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
            AND pid <> pg_backend_pid();
        """)
        await db.execute(terminate_query)
        await db.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await db.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))

    # Step 3: Create a test table within the temporary database
    async for db in getAsyncDB(TEST_DB_NAME):
        await db.execute(text("DROP TABLE IF EXISTS test_table"))
        await db.execute(text("CREATE TABLE test_table (id SERIAL PRIMARY KEY, name VARCHAR(50))"))
        await db.commit()

    # Step 4: Set up the vector store directory for test purposes
    os.makedirs(vector_store_path, exist_ok=True)

    # Step 5: Send request to `endSession` endpoint and verify the response
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        client.cookies.set("session_id", FAKE_SESSION_ID)
        response = await client.delete(instance.end_session_end_point)

    # Step 6: Verify the response status and ensure it confirms session ending
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result == {"informationMessage": "Session ended."}

    # Step 7: Confirm that the session data has been deleted from Redis
    session_data = await instance.redis_tool.redis.hgetall(session_key)
    assert session_data == {}, "Session was not deleted from Redis."

    # Step 8: Confirm deletion of the temporary database and vector store
    async for db in getAsyncDB("postgres"):
        result = await db.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'"))
        assert not result.fetchone(), "Temporary database was not deleted."
    
    # Verify that the vector store path has been deleted
    assert not os.path.exists(vector_store_path), "Vector store path was not deleted."

    # Final Cleanup: Ensure the session key is deleted from Redis
    await instance.redis_tool.redis.delete(session_key)