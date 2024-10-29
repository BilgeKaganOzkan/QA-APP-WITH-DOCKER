import pytest
from unittest.mock import AsyncMock, Mock, patch
from delete_fixtures import patched_delete_module, FAKE_SESSION_ID, FAKE_DB_PATH
from lib.routers.delete import _deleteTempDatabase
from sqlalchemy import text

@pytest.mark.asyncio
async def test_delete_delete_temp_db_success_db_exist(patched_delete_module):
    """
    Test that _deleteTempDatabase successfully deletes an existing temporary database.
    - This checks the following:
      - The database existence check is performed.
      - Active connections to the database are terminated.
      - The database is dropped as expected.
    """
    # Set up the mock to return a result indicating the database exists
    mock_db_async_temp = AsyncMock()
    mock_db_async_temp.fetchone = Mock(return_value=True)
    patched_delete_module.mock_getAsyncDB.execute.return_value = mock_db_async_temp

    # Define the session with a database path
    session = (FAKE_SESSION_ID, {'temp_database_path': FAKE_DB_PATH})

    # Execute the database deletion function
    result = await _deleteTempDatabase(session=session)

    # Define SQL queries expected during this process
    db_check_query = text(f"SELECT 1 FROM pg_database WHERE datname = '{FAKE_DB_PATH}';")
    terminate_connections_query = text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{FAKE_DB_PATH}'
                AND pid <> pg_backend_pid();
            """)
    drop_db_query = text(f"DROP DATABASE {FAKE_DB_PATH};")

    # Compile expected and called queries for comparison
    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([db_check_query, terminate_connections_query, drop_db_query])
    called_queries = compile_sql([call[0][0] for call in patched_delete_module.mock_getAsyncDB.execute.call_args_list])

    # Verify the result is True and the expected queries match the called queries
    assert result == True
    assert expected_queries == called_queries

    # Ensure that the existence check was called once
    patched_delete_module.mock_getAsyncDB.execute.return_value.fetchone.assert_called_once()

@pytest.mark.asyncio
async def test_delete_delete_temp_db_success_db_no_exist(patched_delete_module):
    """
    Test that _deleteTempDatabase correctly handles a case where the temporary database does not exist.
    - This ensures:
      - The function attempts a database existence check.
      - No further actions are taken if the database does not exist.
    """
    # Set up the mock to indicate the database does not exist
    mock_db_async_temp = AsyncMock()
    mock_db_async_temp.fetchone = Mock(return_value=False)
    patched_delete_module.mock_getAsyncDB.execute.return_value = mock_db_async_temp

    # Define the session without a database path
    session = (FAKE_SESSION_ID, {'temp_database_path': ''})

    # Execute the database deletion function
    result = await _deleteTempDatabase(session=session)

    # Define only the existence check query since the database doesn't exist
    db_check_query = text("SELECT 1 FROM pg_database WHERE datname = '';")

    # Compile expected and called queries for comparison
    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([db_check_query])
    called_queries = compile_sql([call[0][0] for call in patched_delete_module.mock_getAsyncDB.execute.call_args_list])

    # Verify the result is True and the expected queries match the called queries
    assert result == True
    assert expected_queries == called_queries

    # Ensure that the existence check was called once
    patched_delete_module.mock_getAsyncDB.execute.return_value.fetchone.assert_called_once()