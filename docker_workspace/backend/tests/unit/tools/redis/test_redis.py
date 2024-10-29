import pytest
from unittest.mock import AsyncMock, patch, Mock
from lib.tools.redis import RedisTool
from fastapi import status
from sqlalchemy.sql import text

# Constants for the test setup
FAKE_TIMEOUT = 3600
FAKE_IP_ADDR = "localhost"
FAKE_PORT = 6379
FAKE_ASYNC_DB_URL = "fake_async_db_url"
DB_SUFFIX = "/postgres"

# Fixture to provide a mock memory dictionary
@pytest.fixture
def mock_memory():
    return {}

# Fixture to set up RedisTool instance with mocked Redis
@pytest.fixture
def redis_tool(mock_memory):
    with patch('redis.asyncio.Redis', new_callable=AsyncMock) as mock_redis:
        # Initialize RedisTool with mocked parameters
        redis_tool = RedisTool(memory=mock_memory, session_timeout=FAKE_TIMEOUT, redis_ip=FAKE_IP_ADDR, redis_port=6379, async_database_url=FAKE_ASYNC_DB_URL)
        redis_tool.redis = mock_redis
        yield redis_tool

@pytest.mark.asyncio
@patch("time.time", new_callable=Mock)
async def test_redis_create_session_success(mock_time, redis_tool):
    """
    Test to verify Redis session creation functionality.
    Ensures session data is set with correct attributes and calls to helper methods are accurate.
    """
    _call_count = 3
    mock_time.return_value = 12345678
    redis_tool.redis.exists = AsyncMock(side_effect=[*[(True,)] * _call_count, False])  # Mock for session existence check
    redis_tool.resetSessionTimeout = AsyncMock()
    redis_tool.redis.hset = AsyncMock()

    session_id = await redis_tool.createSession()
    session_key = f"session:{session_id}"

    # Assert checks
    assert isinstance(session_id, str)
    redis_tool.redis.hset.assert_called_once_with(session_key, mapping={"created_at": str(mock_time.return_value), "data": "{}"})
    redis_tool.resetSessionTimeout.assert_called_once_with(session_id=session_id)
    assert redis_tool.redis.exists.call_count == _call_count + 1

@pytest.mark.asyncio
async def test_redis_get_session_data_success(redis_tool):
    """
    Test to verify successful retrieval of session data from Redis.
    Ensures data consistency with expected session attributes.
    """
    session_id = '12345'
    session_data = {"created_at": "1698245632.0", "data": "{}"}
    redis_tool.redis.hgetall = AsyncMock(return_value=session_data)

    # Fetch session data and assert results
    returned_session_id, returned_session_data = await redis_tool.getSession(session_id=session_id)
    assert returned_session_id == session_id
    assert returned_session_data == session_data

@pytest.mark.asyncio
async def test_redis_get_session_data_failure_invalid_data(redis_tool):
    """
    Test to verify error handling for invalid session retrieval.
    Ensures correct exception is raised with expected status code and error details.
    """
    session_id = "invalid_id"
    redis_tool.redis.hgetall = AsyncMock(return_value={})

    with pytest.raises(Exception) as exc_info:
        await redis_tool.getSession(session_id=session_id)
    
    # Asserts for raised exception details
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Authentication failed. Invalid session."
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

@pytest.mark.asyncio
async def test_redis_get_all_session_success(redis_tool):
    """
    Test to verify retrieval of all active sessions from Redis.
    Ensures all session keys are returned accurately.
    """
    expected_sessions = ["session1", "session2", "session3"]
    redis_tool.redis.keys = AsyncMock(return_value=expected_sessions)
    called_sessions = await redis_tool.getAllSessions()
    assert called_sessions == expected_sessions

@pytest.mark.asyncio
async def test_redis_update_session_success(redis_tool):
    """
    Test to verify updating of specific session data in Redis.
    Ensures correct key-value pair update and session timeout reset.
    """
    session_id = '12345'
    key = 'some_key'
    value = 'some_value'
    redis_tool.redis.hset = AsyncMock()
    redis_tool.resetSessionTimeout = AsyncMock()
    
    # Update session and verify actions
    await redis_tool.updateSession(session_id, key, value)
    redis_tool.redis.hset.assert_called_with(f'session:{session_id}', key, value)
    redis_tool.resetSessionTimeout.assert_called_once_with(session_id=session_id)

@pytest.mark.asyncio
async def test_redis_delete_session_success(redis_tool):
    """
    Test to verify Redis session deletion functionality.
    Ensures session key is deleted as expected.
    """
    session_id = '12345'
    redis_tool.redis.delete = AsyncMock()
    await redis_tool.deleteSession(session_id)
    redis_tool.redis.delete.assert_called_with(f'session:{session_id}')

@pytest.mark.asyncio
async def test_redis_reset_session_timeout_success(redis_tool):
    """
    Test to verify resetting the session timeout in Redis.
    Ensures session expiration timeout is updated correctly.
    """
    session_id = '12345'
    session_key = f"session:{session_id}"
    redis_tool.redis.expire = AsyncMock()
    await redis_tool.resetSessionTimeout(session_id)
    redis_tool.redis.expire.assert_called_with(session_key, FAKE_TIMEOUT)

@pytest.mark.asyncio
@patch('lib.tools.redis.create_async_engine')
async def test_redis_delete_temp_database_success_database_exist(mock_create_async_engine, redis_tool):
    """
    Test to verify deletion of a temporary database when it exists.
    Ensures database existence check, connection termination, and deletion queries are executed as expected.
    """
    db_url = FAKE_ASYNC_DB_URL + DB_SUFFIX
    temp_database_name = "test_db"
    
    # Queries for DB check, connection termination, and DB drop
    db_check_query = text(f"SELECT 1 FROM pg_database WHERE datname = '{temp_database_name}';")
    terminate_connections_query = text(f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{temp_database_name}'
                    AND pid <> pg_backend_pid();
                """)
    drop_db_query = text(f"DROP DATABASE {temp_database_name};")
    
    # Set up mocks and expected results
    mock_connection = AsyncMock()
    mock_connection.execute.return_value.fetchone = Mock(return_value=(1,))
    mock_create_async_engine.return_value.connect.return_value.__aenter__.return_value = mock_connection
    session_data = {'temp_database_path': temp_database_name}

    await redis_tool._deleteTempDatabase(session_data)
    
    # Verify SQL queries executed
    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([db_check_query, terminate_connections_query, drop_db_query])
    called_queries = compile_sql([call[0][0] for call in mock_connection.execute.call_args_list])

    mock_create_async_engine.assert_called_once_with(db_url, echo=False, isolation_level="AUTOCOMMIT")
    assert mock_connection.execute.call_count == 3
    assert expected_queries == called_queries

@pytest.mark.asyncio
@patch('lib.tools.redis.create_async_engine')
async def test_redis_delete_temp_database_success_database_not_exist(mock_create_async_engine, redis_tool):
    """
    Test to verify handling of non-existent temporary database deletion.
    Ensures only the existence check query is executed, and no errors occur.
    """
    db_url = FAKE_ASYNC_DB_URL + DB_SUFFIX
    temp_database_name = "test_db"
    db_check_query = text(f"SELECT 1 FROM pg_database WHERE datname = '{temp_database_name}';")

    mock_connection = AsyncMock()
    mock_connection.execute.return_value.fetchone = Mock(return_value=None)
    mock_create_async_engine.return_value.connect.return_value.__aenter__.return_value = mock_connection
    session_data = {'temp_database_path': temp_database_name}

    await redis_tool._deleteTempDatabase(session_data)

    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([db_check_query])
    called_queries = compile_sql([call[0][0] for call in mock_connection.execute.call_args_list])

    mock_create_async_engine.assert_called_once_with(db_url, echo=False, isolation_level="AUTOCOMMIT")
    assert mock_connection.execute.call_count == 1
    assert expected_queries == called_queries