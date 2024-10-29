import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport
from delete_fixtures import fixture_test_app, patched_delete_module, FAKE_URL, FAKE_SESSION_ID

@pytest.mark.asyncio
@patch("lib.routers.delete._clearTempDatabase", return_value=True)
@patch("lib.routers.delete._deleteVectorStore", return_value=True)
async def test_delete_clear_session(mock_delete_vector, mock_clear_temp_db, patched_delete_module, fixture_test_app):
    """
    Test case for the DELETE /clear_session endpoint. Ensures that a session can be cleared, 
    and confirms the expected success message and status code are returned.
    """

    # Override the dependency to mock the session retrieval, simulating a session with an empty vector store path.
    async def mock_getSession():
        yield (FAKE_SESSION_ID, {'vector_store_path': ''})

    # Override the getSession dependency to use the mock version
    fixture_test_app.dependency_overrides[patched_delete_module.instance.redis_tool.getSession] = mock_getSession

    # Send the DELETE request to clear the session
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.delete(patched_delete_module.instance.clear_session_end_point)

    # Check that the response is successful with a 200 status code
    assert response.status_code == 200
    # Validate that the response message confirms the session was cleared
    assert response.json() == {"informationMessage": "Session cleared."}