import pytest
from httpx import AsyncClient, ASGITransport
from get_fixtures import fixture_test_app, patched_get_module, FAKE_URL, FAKE_SESSION_ID
from fastapi import status

@pytest.mark.asyncio
async def test_get_check_session(patched_get_module, fixture_test_app):
    """
    Test for verifying the 'check_session' endpoint.
    This test simulates a successful session validation.
    """

    # Override the getSession dependency to yield a mock session ID
    async def override_getSession():
        yield FAKE_SESSION_ID, {}

    # Set the dependency override to use the mock session ID instead of the actual session retrieval
    fixture_test_app.dependency_overrides[patched_get_module.instance.redis_tool.getSession] = override_getSession

    # Send a GET request to the 'check_session' endpoint
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.get(patched_get_module.instance.check_session_end_point)

    # Check that the response status is 200 OK, indicating successful session validation
    assert response.status_code == status.HTTP_200_OK

    # Verify that the response contains the expected success message
    assert response.json() == {"informationMessage": "Session is valid"}