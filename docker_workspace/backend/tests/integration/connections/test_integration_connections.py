import pytest, time
from sqlalchemy.sql import text
from lib.database.config.configuration import getAsyncUserDB, getAsyncDB
from lib.instances.instance import Instance
from tests.integration.fixtures import event_loop, setup_and_tear_down

@pytest.mark.asyncio
async def test_getAsyncUserDB_success(setup_and_tear_down, event_loop):
    """
    Integration test: Verifies that `getAsyncUserDB` function connects to the correct database 
    (test_user_db) and executes a basic query successfully.

    **Test Steps**:
    1. Connect to the user database using `getAsyncUserDB`.
    2. Execute a simple query (`SELECT 1`) and verify the returned value is as expected.
    3. Confirm connection to the correct database by querying the current database name.
    
    **Expected Outcome**:
    - The database connection should be successful.
    - The `SELECT 1` query should return `1`.
    - The connected database name should match "test_user_db".
    """
    async for db in getAsyncUserDB():
        # Step 1: Execute a basic query and check if the returned value is correct
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1, "getAsyncUserDB failed: 'SELECT 1' query did not return the expected value of 1."

        # Step 2: Verify the database connection name is correct
        db_name_result = await db.execute(text("SELECT current_database()"))
        db_name = db_name_result.scalar()
        assert db_name == "test_user_db", f"getAsyncUserDB failed: Connected to '{db_name}' instead of 'test_user_db'."

@pytest.mark.asyncio
async def test_getAsyncDB_success(setup_and_tear_down, event_loop):
    """
    Integration test: Verifies that `getAsyncDB` function connects to a specified database 
    (test_database) and successfully executes a basic query.

    **Test Steps**:
    1. Connect to a specified database (test_database) using `getAsyncDB`.
    2. Execute a simple query (`SELECT 1`) to verify the database connection is functional.
    3. Check if the connected database matches the intended database name.
    
    **Expected Outcome**:
    - The database connection should be successful.
    - The `SELECT 1` query should return `1`.
    - The connected database name should match the specified "test_database".
    """
    database_name = "test_database"
    async for db in getAsyncDB(database_name):
        # Step 1: Execute a basic query to confirm functionality
        result = await db.execute(text("SELECT 1"))
        value = result.scalar()
        assert value == 1, "getAsyncDB failed: 'SELECT 1' query did not return the expected value of 1."

        # Step 2: Check if the connected database name matches the specified one
        db_name_result = await db.execute(text("SELECT current_database()"))
        db_name = db_name_result.scalar()
        assert db_name == database_name, f"getAsyncDB failed: Connected to '{db_name}' instead of '{database_name}'."

@pytest.mark.asyncio
async def test_redis_connection(setup_and_tear_down, event_loop):
    """
    Integration test: Verifies Redis connection by performing set, get, and delete operations 
    to ensure data is accurately stored and removed.

    **Test Steps**:
    1. Set a test key-value pair in Redis.
    2. Retrieve the value to verify it was stored correctly.
    3. Delete the key and confirm it no longer exists.
    
    **Expected Outcome**:
    - The value retrieved from Redis should match the value that was initially set.
    - The key should be successfully deleted, with subsequent retrieval returning `None`.
    """
    instance = Instance()

    # Step 1: Define test key and value to set in Redis
    test_key = "test_connection_key"
    test_value = str(time.time())

    # Step 2: Set the key-value pair in Redis and retrieve it
    await instance.redis_tool.redis.set(test_key, test_value)
    stored_value = await instance.redis_tool.redis.get(test_key)
    assert stored_value == test_value, "Redis connection failed: Value retrieved from Redis does not match expected value."

    # Step 3: Delete the key and ensure it no longer exists
    await instance.redis_tool.redis.delete(test_key)
    stored_value = await instance.redis_tool.redis.get(test_key)
    assert stored_value is None, "Redis connection failed: Deleted key still exists in Redis."