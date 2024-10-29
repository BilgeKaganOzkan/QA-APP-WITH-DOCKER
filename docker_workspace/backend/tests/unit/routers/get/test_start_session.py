import pytest
from httpx import AsyncClient, ASGITransport
from get_fixtures import fixture_test_app, patched_get_module, FAKE_URL, FAKE_SESSION_ID
from fastapi import status

@pytest.mark.asyncio
async def test_get_start_session(patched_get_module, fixture_test_app):
    """
    Test for verifying the 'start_session' endpoint.
    This test checks that the endpoint responds correctly when starting a new session.
    """

    # Override the getSession dependency to yield a mock session ID.
    async def override_getSession():
        yield FAKE_SESSION_ID, {}

    # Apply the dependency override to replace the actual session retrieval with the mock function.
    fixture_test_app.dependency_overrides[patched_get_module.instance.redis_tool.getSession] = override_getSession

    # Send a GET request to the 'start_session' endpoint to simulate session start.
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.get(patched_get_module.instance.start_session_end_point)

    # Assert that the response status is 200 OK, indicating a successful session start.
    assert response.status_code == status.HTTP_200_OK

    # Verify that the response JSON contains the correct message, prompting the user to upload a file.
    assert response.json() == {"informationMessage": "Please upload a file"}