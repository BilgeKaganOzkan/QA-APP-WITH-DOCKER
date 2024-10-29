import pytest
from httpx import AsyncClient, ASGITransport
from get_fixtures import fixture_test_app, patched_get_module, FAKE_URL, FAKE_SESSION_ID
from fastapi import status

@pytest.mark.asyncio
async def test_get_get_progress_found(patched_get_module, fixture_test_app):
    """
    Test case for the 'get_progress' endpoint when progress is found in the session.
    This test ensures the endpoint returns the current progress value when available.
    """
    
    # Mock the session data to include a "progress" key with a value of 50.
    async def override_getSession():
        yield FAKE_SESSION_ID, {"progress": 50}

    # Apply the dependency override, replacing the real session retrieval function with the mock function.
    fixture_test_app.dependency_overrides[patched_get_module.instance.redis_tool.getSession] = override_getSession

    # Send a GET request to the 'progress' endpoint to retrieve the current progress.
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.get(patched_get_module.instance.progress_end_point)

    # Assert that the response status is 200 OK, indicating progress was successfully retrieved.
    assert response.status_code == status.HTTP_200_OK

    # Verify that the response JSON contains the correct progress value.
    assert response.json() == {"progress": 50}

@pytest.mark.asyncio
async def test_get_get_progress_not_found(patched_get_module, fixture_test_app):
    """
    Test case for the 'get_progress' endpoint when no progress value is found in the session.
    This test ensures the endpoint returns a 404 status and an appropriate error message.
    """
    
    # Mock the session data without a "progress" key to simulate progress not being set.
    async def override_getSession():
        yield FAKE_SESSION_ID, {}

    # Apply the dependency override with the mock function.
    fixture_test_app.dependency_overrides[patched_get_module.instance.redis_tool.getSession] = override_getSession

    # Send a GET request to the 'progress' endpoint to retrieve the progress.
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.get(patched_get_module.instance.progress_end_point)

    # Assert that the response status is 404 Not Found, indicating no progress was found in the session.
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Verify that the response JSON contains the correct error message.
    assert response.json() == {"detail": "Progress not found."}