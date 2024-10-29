import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from post_fixtures import fixture_test_app, patched_post_module, FAKE_SESSION_ID, FAKE_DB_PATH, FAKE_URL


@pytest.mark.asyncio
async def test_post_sql_query_success(patched_post_module, fixture_test_app):
    """Test case for successful SQL query execution."""
    # Setup mocks to simulate session memory and reset session timeout behavior
    patched_post_module.instance.memory.getMemory = AsyncMock(return_value='mock_session_memory')
    patched_post_module.instance.redis_tool.resetSessionTimeout = AsyncMock()

    # Mock session generator that returns a valid database path
    async def mock_getTrueSQLSession():
        mock_getTrueSQLSession.call_count += 1
        yield (FAKE_SESSION_ID, {'temp_database_path': FAKE_DB_PATH})

    # Initialize the session call count
    mock_getTrueSQLSession.call_count = 0
    fixture_test_app.dependency_overrides[patched_post_module.instance.redis_tool.getSession] = mock_getTrueSQLSession

    # Define the payload for the SQL query request
    payload = {'humanMessage': 'Give me all users name'}

    # Send POST request to SQL query endpoint
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.sql_query_end_point, json=payload)

    # Assertions to verify response status, content, and interaction with mocks
    assert response.status_code == 200
    assert response.json()['aiMessage'] == 'Mock response'
    assert mock_getTrueSQLSession.call_count == 1, f"mock_getSession was called {mock_getTrueSQLSession.call_count} times"
    patched_post_module.instance.memory.getMemory.assert_called_once_with(session_id=FAKE_SESSION_ID)

    # Ensure SQL query agent is initialized and executed correctly
    patched_post_module.mock_SqlQueryAgent.assert_called_once_with(
        llm=patched_post_module.instance.llm,
        memory=patched_post_module.instance.memory.getMemory.return_value,
        temp_database_path=FAKE_DB_PATH,
        max_iteration=patched_post_module.instance.llm_max_iteration
    )
    patched_post_module.mock_SqlQueryAgent.return_value.execute.assert_called_once_with('Give me all users name')
    patched_post_module.instance.redis_tool.resetSessionTimeout.assert_called_once_with(session_id=FAKE_SESSION_ID)


@pytest.mark.asyncio
async def test_post_sql_query_failure_no_database(patched_post_module, fixture_test_app):
    """Test case for SQL query failure due to missing database path in session."""
    # Setup mocks for session memory retrieval and session timeout reset
    patched_post_module.instance.memory.getMemory = AsyncMock(return_value=[])
    patched_post_module.instance.redis_tool.resetSessionTimeout = AsyncMock()

    # Mock session generator that returns an empty database path
    async def mock_getFalseSQLSession():
        mock_getFalseSQLSession.call_count += 1
        yield (FAKE_SESSION_ID, {'temp_database_path': ''})

    # Initialize the session call count
    mock_getFalseSQLSession.call_count = 0
    fixture_test_app.dependency_overrides[patched_post_module.instance.redis_tool.getSession] = mock_getFalseSQLSession

    # Define the payload for the SQL query request
    payload = {'humanMessage': 'Give me all users name'}

    # Send POST request to SQL query endpoint
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.sql_query_end_point, json=payload)

    # Assertions to verify error response status, content, and interaction with mocks
    assert response.status_code == 400
    assert response.json()["detail"] == 'No database associated with the session.'
    assert mock_getFalseSQLSession.call_count == 1, f"mock_getSession was called {mock_getFalseSQLSession.call_count} times"

    # Verify no further interactions occurred with the query agent or memory retrieval
    patched_post_module.instance.memory.getMemory.assert_not_called()
    patched_post_module.mock_SqlQueryAgent.assert_not_called()
    patched_post_module.mock_SqlQueryAgent.return_value.execute.assert_not_called()
    patched_post_module.instance.redis_tool.resetSessionTimeout.assert_not_called()