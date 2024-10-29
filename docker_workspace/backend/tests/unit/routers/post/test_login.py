import pytest
from unittest.mock import AsyncMock, Mock
from httpx import AsyncClient, ASGITransport
from lib.database.models.user_model import User
from post_fixtures import fixture_test_app, patched_post_module, FAKE_EMAIL, FAKE_PASSWORD, FAKE_URL, FAKE_SESSION_ID

@pytest.mark.asyncio
async def test_post_login_success(patched_post_module, fixture_test_app):
    """Test case for successful login with correct email and password."""
    # Mock database result with a user matching the test email and password
    mock_scalars = Mock()
    mock_result = Mock()
    mock_scalars.first.return_value = User(email=FAKE_EMAIL, hashed_password=FAKE_PASSWORD)
    mock_result.scalars.return_value = mock_scalars

    # Mock dependencies to simulate successful login
    patched_post_module.mock_getAsyncUserDB.execute.return_value = mock_result
    patched_post_module.mock_verifyPassword.return_value = True
    patched_post_module.instance.redis_tool.create_session.return_value = FAKE_SESSION_ID
    patched_post_module.instance.memory.createMemory = AsyncMock(return_value=[])
    patched_post_module.instance.redis_tool.createSession = AsyncMock(return_value=FAKE_SESSION_ID)
    patched_post_module.instance.redis_tool.updateSession = AsyncMock()

    # Payload with correct credentials
    payload = {"email": FAKE_EMAIL, "password": FAKE_PASSWORD}
    
    # Send login request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.login_end_point, json=payload)

    # Check for successful login response and correct session handling
    assert response.status_code == 200
    assert response.json()["informationMessage"] == "Login successful"
    patched_post_module.instance.memory.createMemory.assert_called_once_with(session_id=FAKE_SESSION_ID)
    patched_post_module.instance.redis_tool.createSession.assert_called_once()
    patched_post_module.instance.redis_tool.updateSession.assert_called_once_with(session_id=FAKE_SESSION_ID, key="user_email", value=FAKE_EMAIL)
    assert response.headers.get("set-cookie") == f"session_id={FAKE_SESSION_ID}; HttpOnly; Path=/; SameSite=None; Secure"

@pytest.mark.asyncio
async def test_post_login_failure_wrong_email(patched_post_module, fixture_test_app):
    """Test case for login failure with incorrect email."""
    # Mock database result with no matching user for the provided email
    mock_scalars = Mock()
    mock_result = Mock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars

    # Mock dependencies for failed login scenario
    patched_post_module.mock_getAsyncUserDB.execute.return_value = mock_result
    patched_post_module.instance.memory.createMemory = AsyncMock(return_value=[])
    patched_post_module.instance.redis_tool.createSession = AsyncMock(return_value=FAKE_SESSION_ID)
    patched_post_module.instance.redis_tool.updateSession = AsyncMock()
    patched_post_module.mock_verifyPassword.return_value = True
    patched_post_module.instance.redis_tool.create_session.return_value = FAKE_SESSION_ID

    # Payload with incorrect email
    payload = {"email": FAKE_EMAIL, "password": FAKE_PASSWORD}

    # Send login request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.login_end_point, json=payload)
    
    # Verify response for incorrect email and absence of session setup
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
    patched_post_module.instance.memory.getMemory.assert_not_called()
    patched_post_module.instance.redis_tool.createSession.assert_not_called()
    patched_post_module.instance.redis_tool.updateSession.assert_not_called()
    assert response.headers.get("set-cookie") != f"session_id={FAKE_SESSION_ID}; HttpOnly; SameSite=None; Secure"

@pytest.mark.asyncio
async def test_post_login_failure_wrong_password(patched_post_module, fixture_test_app):
    """Test case for login failure with correct email but incorrect password."""
    # Mock database result with user having correct email
    mock_scalars = Mock()
    mock_result = Mock()
    mock_scalars.first.return_value = User(email=FAKE_EMAIL, hashed_password=FAKE_PASSWORD)
    mock_result.scalars.return_value = mock_scalars

    # Mock dependencies to simulate password mismatch scenario
    patched_post_module.mock_getAsyncUserDB.execute.return_value = mock_result
    patched_post_module.instance.memory.createMemory = AsyncMock(return_value=[])
    patched_post_module.instance.redis_tool.createSession = AsyncMock(return_value=FAKE_SESSION_ID)
    patched_post_module.instance.redis_tool.updateSession = AsyncMock()
    patched_post_module.mock_verifyPassword.return_value = False
    patched_post_module.instance.redis_tool.create_session.return_value = FAKE_SESSION_ID

    # Payload with correct email but incorrect password
    payload = {"email": FAKE_EMAIL, "password": FAKE_PASSWORD}

    # Send login request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.login_end_point, json=payload)
    
    # Verify response for incorrect password and absence of session setup
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
    patched_post_module.instance.memory.getMemory.assert_not_called()
    patched_post_module.instance.redis_tool.createSession.assert_not_called()
    patched_post_module.instance.redis_tool.updateSession.assert_not_called()
    assert response.headers.get("set-cookie") != f"session_id={FAKE_SESSION_ID}; HttpOnly; SameSite=None; Secure"

@pytest.mark.asyncio
async def test_post_login_failure_wrong_email_and_password(patched_post_module, fixture_test_app):
    """Test case for login failure with both incorrect email and password."""
    # Mock database result with no user for incorrect email
    mock_scalars = Mock()
    mock_result = Mock()
    mock_scalars.first.return_value = None
    mock_result.scalars.return_value = mock_scalars

    # Mock dependencies to simulate complete login failure scenario
    patched_post_module.mock_getAsyncUserDB.execute.return_value = mock_result
    patched_post_module.instance.memory.createMemory = AsyncMock(return_value=[])
    patched_post_module.instance.redis_tool.createSession = AsyncMock(return_value=FAKE_SESSION_ID)
    patched_post_module.instance.redis_tool.updateSession = AsyncMock()
    patched_post_module.mock_verifyPassword.return_value = False
    patched_post_module.instance.redis_tool.create_session.return_value = FAKE_SESSION_ID

    # Payload with both incorrect email and password
    payload = {"email": FAKE_EMAIL, "password": FAKE_PASSWORD}

    # Send login request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.login_end_point, json=payload)
    
    # Verify response for incorrect credentials and absence of session setup
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
    patched_post_module.instance.memory.getMemory.assert_not_called()
    patched_post_module.instance.redis_tool.createSession.assert_not_called()
    patched_post_module.instance.redis_tool.updateSession.assert_not_called()
    assert response.headers.get("set-cookie") != f"session_id={FAKE_SESSION_ID}; HttpOnly; SameSite=None; Secure"