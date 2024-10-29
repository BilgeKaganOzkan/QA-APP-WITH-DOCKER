import pytest
from unittest.mock import AsyncMock, Mock
from sqlalchemy import text
from put_fixture import patched_put_module, FAKE_URL

@pytest.mark.asyncio
async def test_put_create_temp_database_success_no_db(patched_put_module):
    """
    Test to verify behavior when the temporary database does not exist.
    Ensures that a new database is created and the session is updated accordingly.
    """
    session = ("test-session-id", None)
    temp_db_name = "temporary_database_test_session_id"

    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Setup mock to simulate database not existing
    mock_db_async_temp = AsyncMock()
    mock_db_async_temp.fetchall = Mock(return_value=[])
    patched_put_module.mock_getAsyncDB.execute.return_value = mock_db_async_temp

    from lib.routers.put import _createTempDatabase

    # Call the function being tested
    result_url, result_tables = await _createTempDatabase(session=session)

    # Prepare expected SQL queries
    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([
        text(f"SELECT 1 FROM pg_database WHERE datname = '{temp_db_name}'"), 
        text(f"CREATE DATABASE {temp_db_name}")
    ])
    called_queries = compile_sql([call[0][0] for call in patched_put_module.mock_getAsyncDB.execute.call_args_list])

    # Assertions to verify function behavior
    assert result_url == f"{patched_put_module.instance.sync_database_url}/{temp_db_name}"
    assert result_tables == []
    assert called_queries == expected_queries

    # Verify that the session is updated with the new database path
    patched_put_module.instance.redis_tool.updateSession.assert_called_once_with(
        session_id="test-session-id",
        key="temp_database_path",
        value=temp_db_name
    )
    patched_put_module.mock_getAsyncDB.execute.return_value.fetchall.assert_called_once()

@pytest.mark.asyncio
async def test_put_create_temp_database_success_exist_db(patched_put_module):
    """
    Test to verify behavior when the temporary database already exists.
    Ensures that the existing database tables are returned without creating a new database or updating the session.
    """
    session = ("test-session-id", None)
    temp_db_name = "temporary_database_test_session_id"

    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Setup mock to simulate database existing with tables
    mock_db_async_temp = AsyncMock()
    mock_db_async_temp.fetchall = Mock(return_value=[("table1",)])
    patched_put_module.mock_getAsyncDB.execute.return_value = mock_db_async_temp

    from lib.routers.put import _createTempDatabase

    # Call the function being tested
    result_url, result_tables = await _createTempDatabase(session=session)

    # Prepare expected SQL queries
    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([
        text(f"SELECT 1 FROM pg_database WHERE datname = '{temp_db_name}'"), 
        text("SELECT pg_tables.tablename FROM pg_tables WHERE schemaname='public';")
    ])
    called_queries = compile_sql([call[0][0] for call in patched_put_module.mock_getAsyncDB.execute.call_args_list])

    # Assertions to verify function behavior
    assert result_url == f"{patched_put_module.instance.sync_database_url}/{temp_db_name}"
    assert result_tables == ["table1"]
    assert called_queries == expected_queries
    assert expected_queries == called_queries

    # Verify that the session is not updated since the database already exists
    patched_put_module.instance.redis_tool.updateSession.assert_not_called()
    assert patched_put_module.mock_getAsyncDB.execute.return_value.fetchall.call_count == 2