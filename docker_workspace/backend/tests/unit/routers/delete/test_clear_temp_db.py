import pytest
from unittest.mock import AsyncMock, Mock
from delete_fixtures import patched_delete_module, FAKE_SESSION_ID, FAKE_DB_PATH
from lib.routers.delete import _clearTempDatabase
from sqlalchemy import text

@pytest.mark.asyncio
async def test_delete_clear_temp_db_success_table_exist(patched_delete_module):
    """
    Test case for _clearTempDatabase when tables exist in the database.
    Ensures that the function correctly identifies and drops existing tables.
    """
    # Setup mock to return a table list as if one exists in the database
    mock_db_async_temp = AsyncMock()
    mock_db_async_temp.fetchall = Mock(return_value=[('table1',)])
    patched_delete_module.mock_getAsyncDB.execute.return_value = mock_db_async_temp

    # Define a session with a valid database path
    session = (FAKE_SESSION_ID, {'temp_database_path': FAKE_DB_PATH})

    # Call _clearTempDatabase to clear tables
    result = await _clearTempDatabase(session=session)

    # Define expected SQL queries for checking and dropping tables
    db_check_query = text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public';
            """)
    terminate_connections_query = text("DROP TABLE IF EXISTS table1 CASCADE;")

    # Helper function to compile SQL queries for comparison
    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([db_check_query, terminate_connections_query])
    called_queries = compile_sql([call[0][0] for call in patched_delete_module.mock_getAsyncDB.execute.call_args_list])

    # Assert that the function returns True, queries match expectations, and fetchall was called once
    assert result == True
    assert expected_queries == called_queries
    patched_delete_module.mock_getAsyncDB.execute.return_value.fetchall.assert_called_once()

@pytest.mark.asyncio
async def test_delete_clear_temp_db_success_no_table_exist(patched_delete_module):
    """
    Test case for _clearTempDatabase when no tables exist in the database.
    Ensures the function executes only the table-checking query and does not attempt to drop tables.
    """
    # Setup mock to return an empty list, simulating no tables in the database
    mock_db_async_temp = AsyncMock()
    mock_db_async_temp.fetchall = Mock(return_value=[])
    patched_delete_module.mock_getAsyncDB.execute.return_value = mock_db_async_temp

    # Define a session with a valid database path
    session = (FAKE_SESSION_ID, {'temp_database_path': FAKE_DB_PATH})

    # Call _clearTempDatabase to attempt clearing tables
    result = await _clearTempDatabase(session=session)

    # Define expected SQL query for checking tables only
    db_check_query = text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public';
            """)

    # Compile SQL queries for comparison
    compile_sql = lambda queries: [str(query.compile(compile_kwargs={"literal_binds": True})) for query in queries]
    expected_queries = compile_sql([db_check_query])
    called_queries = compile_sql([call[0][0] for call in patched_delete_module.mock_getAsyncDB.execute.call_args_list])

    # Assert that the function returns True, queries match, and fetchall was called once
    assert result == True
    assert expected_queries == called_queries
    patched_delete_module.mock_getAsyncDB.execute.return_value.fetchall.assert_called_once()

@pytest.mark.asyncio
async def test_delete_clear_temp_db_success_unexpected_error(patched_delete_module):
    """
    Test case for _clearTempDatabase when an unexpected error occurs during table clearing.
    Ensures that the function handles the exception and returns True regardless.
    """
    # Setup mock to raise an exception, simulating an error during database query
    mock_db_async_temp = AsyncMock()
    mock_db_async_temp.fetchall = Mock(side_effect=Exception('Test Error'))
    patched_delete_module.mock_getAsyncDB.execute.return_value = mock_db_async_temp

    # Define a session with a valid database path
    session = (FAKE_SESSION_ID, {'temp_database_path': FAKE_DB_PATH})

    # Call _clearTempDatabase and expect it to handle the exception gracefully
    result = await _clearTempDatabase(session=session)

    # Assert that the function returns True, even with an exception
    assert result == True