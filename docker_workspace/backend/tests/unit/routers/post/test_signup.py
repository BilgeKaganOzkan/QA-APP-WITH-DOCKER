import pytest
from unittest.mock import Mock
from httpx import AsyncClient, ASGITransport
from lib.database.models.user_model import User
from sqlalchemy import select
from post_fixtures import fixture_test_app, patched_post_module, FAKE_EMAIL, FAKE_PASSWORD, FAKE_URL

@pytest.mark.asyncio
async def test_post_signup_success(patched_post_module, fixture_test_app):
    """Test case for successful user signup."""
    # Setup mock for empty user retrieval (user does not exist)
    mock_scalars = Mock()
    mock_result = Mock()
    mock_scalars.first.return_value = None  # No existing user with this email
    mock_result.scalars.return_value = mock_scalars
    patched_post_module.mock_getAsyncUserDB.execute.return_value = mock_result
    patched_post_module.mock_getPasswordHash.return_value = FAKE_PASSWORD

    # Define payload for signup request
    payload = {"email": FAKE_EMAIL, "password": FAKE_PASSWORD}

    # Send POST request to signup endpoint
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.signup_end_point, json=payload)

    # Extract the user object added to the database and refreshed from the database
    added_user = patched_post_module.mock_getAsyncUserDB.add.call_args[0][0]
    refresh_db = patched_post_module.mock_getAsyncUserDB.refresh.call_args[0][0]
    payload_email = payload.get("email")
    payload_password = payload.get("password")

    # Compile SQL query for comparison with called SQL in mock
    expected_query = select(User).where(User.email == FAKE_EMAIL)
    expected_sql = str(expected_query.compile(compile_kwargs={"literal_binds": True}))
    called_query = patched_post_module.mock_getAsyncUserDB.execute.call_args[0][0]
    called_sql = str(called_query.compile(compile_kwargs={"literal_binds": True}))

    # Assertions to verify the correct flow and response
    assert response.status_code == 201
    assert response.json()["informationMessage"] == "User successfully registered"
    patched_post_module.mock_getAsyncUserDB.execute.assert_called_once()
    assert expected_sql == called_sql, f"Expected: {expected_sql}, but got: {called_sql}"
    patched_post_module.mock_getAsyncUserDB.add.assert_called_once()
    assert added_user.email == payload_email, f"Expected email {payload_email}, got {added_user.email}"
    assert added_user.hashed_password == payload_password, f"Expected hashed_password {payload_password}, got {added_user.hashed_password}"
    patched_post_module.mock_getAsyncUserDB.commit.assert_called_once()
    patched_post_module.mock_getAsyncUserDB.refresh.assert_called_once()
    assert added_user.email == payload_email, f"Expected email {payload_email}, got {refresh_db.email}"
    assert added_user.hashed_password == payload_password, f"Expected hashed_password {payload_password}, got {refresh_db.hashed_password}"

@pytest.mark.asyncio
async def test_post_signup_failure(patched_post_module, fixture_test_app):
    """Test case for user signup failure due to existing email."""
    # Setup mock for existing user retrieval (user already exists)
    mock_scalars = Mock()
    mock_result = Mock()
    mock_scalars.first.return_value = User(email=FAKE_EMAIL, hashed_password=FAKE_PASSWORD)  # Existing user found
    mock_result.scalars.return_value = mock_scalars
    patched_post_module.mock_getAsyncUserDB.execute.return_value = mock_result

    # Define payload for signup request
    payload = {"email": FAKE_EMAIL, "password": FAKE_PASSWORD}

    # Send POST request to signup endpoint
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.signup_end_point, json=payload)

    # Compile SQL query for comparison with called SQL in mock
    expected_query = select(User).where(User.email == FAKE_EMAIL)
    expected_sql = str(expected_query.compile(compile_kwargs={"literal_binds": True}))
    called_query = patched_post_module.mock_getAsyncUserDB.execute.call_args[0][0]
    called_sql = str(called_query.compile(compile_kwargs={"literal_binds": True}))

    # Assertions to verify the correct flow and error response for existing email
    assert response.status_code == 400
    assert response.json()["detail"] == "E-mail already registered"
    patched_post_module.mock_getAsyncUserDB.execute.assert_called_once()
    assert expected_sql == called_sql, f"Expected: {expected_sql}, but got: {called_sql}"
    patched_post_module.mock_getAsyncUserDB.add.assert_not_called()
    patched_post_module.mock_getAsyncUserDB.commit.assert_not_called()
    patched_post_module.mock_getAsyncUserDB.refresh.assert_not_called()