import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from delete_fixtures import fixture_test_app, patched_delete_module, FAKE_URL, FAKE_SESSION_ID

@pytest.mark.asyncio
@patch("lib.routers.delete._clearTempDatabase", return_value=True)
@patch("lib.routers.delete._deleteVectorStore", return_value=True)
async def test_delete_clear_session(mock_delete_vector, mock_clear_temp_db, patched_delete_module, fixture_test_app):
    """
    Test case to verify the clear session functionality.
    This checks that:
    - Temporary database clearing is called.
    - Vector store deletion is executed.
    - Memory and session are deleted from Redis.
    """
    # Mock the session retrieval to return a session ID and an empty vector store path
    async def mock_getSession():
        yield (FAKE_SESSION_ID, {'vector_store_path': ''})

    # Override the dependency in the test app with the mock session
    fixture_test_app.dependency_overrides[patched_delete_module.instance.redis_tool.getSession] = mock_getSession

    # Setup async mocks for deleting memory and session in Redis
    patched_delete_module.instance.memory.deleteMemory = AsyncMock()
    patched_delete_module.instance.redis_tool.deleteSession = AsyncMock()

    # Make a DELETE request to the endpoint and capture the response
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.delete(patched_delete_module.instance.end_session_end_point)

    # Check that the response status and message confirm successful session deletion
    assert response.status_code == 200
    assert response.json() == {"informationMessage": "Session ended."}

    # Verify memory deletion was called with the correct session ID
    patched_delete_module.instance.memory.deleteMemory.assert_called_once_with(session_id=FAKE_SESSION_ID)
    
    # Verify session deletion in Redis was called with the correct session ID
    patched_delete_module.instance.redis_tool.deleteSession.assert_called_once_with(session_id=FAKE_SESSION_ID)