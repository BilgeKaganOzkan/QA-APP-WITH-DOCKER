import pytest
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

# Constants for test database URL and name
FAKE_DB_URL = "postgresql+asyncpg://test_user:test_password@localhost"
FAKE_DB_NAME = "test_user_db"

@pytest.mark.asyncio
class _MockInstance:
    """
    Mock Instance class to return a test async database URL and user database name.
    """
    def __init__(self):
        self.async_database_url = FAKE_DB_URL
        self.user_database_name = FAKE_DB_NAME

@pytest.mark.asyncio
@patch('lib.database.config.configuration.Instance', new=_MockInstance)
@patch('lib.database.config.configuration.create_async_engine')
@patch('lib.database.config.configuration.sessionmaker')
async def test_db_config_get_async_user_db_success(mock_sessionmaker, mock_create_async_engine):
    """
    Test for successful creation of async session with getAsyncUserDB.
    Verifies that an AsyncSession instance is created and yielded correctly.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    mock_sessionmaker.return_value = MagicMock(
        return_value=AsyncMock(
            __aenter__=AsyncMock(return_value=mock_session),
            __aexit__=AsyncMock(return_value=None)
        )
    )

    from lib.database.config.configuration import getAsyncUserDB

    # Test the yielded session type
    async for session in getAsyncUserDB():
        assert isinstance(session, AsyncSession), f"Expected AsyncSession, but got {type(session)}"

    # Ensure engine and sessionmaker were called with expected parameters
    mock_create_async_engine.assert_called_once_with(f"{FAKE_DB_URL}/{FAKE_DB_NAME}", echo=False, isolation_level="AUTOCOMMIT")
    mock_sessionmaker.assert_called_once_with(bind=mock_create_async_engine.return_value, class_=AsyncSession, expire_on_commit=False)

@pytest.mark.asyncio
@patch('lib.database.config.configuration.Instance', new=_MockInstance)
@patch('lib.database.config.configuration.create_async_engine')
@patch('lib.database.config.configuration.sessionmaker')
async def test_db_config_get_async_user_db_failure_on_create_async_engine(mock_sessionmaker, mock_create_async_engine):
    """
    Test for failure case where async engine creation fails in getAsyncUserDB.
    Ensures an exception is raised with the expected error message.
    """
    mock_create_async_engine.side_effect = Exception("Engine creation failed")
    from lib.database.config.configuration import getAsyncUserDB

    # Verify exception is raised when engine creation fails
    with pytest.raises(Exception) as exc_info:
        async for _ in getAsyncUserDB():
            pass

    assert str(exc_info.value) == "Database error: Engine creation failed"

@pytest.mark.asyncio
@patch('lib.database.config.configuration.Instance', new=_MockInstance)
@patch('lib.database.config.configuration.create_async_engine')
@patch('lib.database.config.configuration.sessionmaker')
async def test_db_config_get_async_user_db_exception_failure_when_open_async_engine(mock_sessionmaker, mock_create_async_engine):
    """
    Test for failure in async context management when opening a session in getAsyncUserDB.
    Ensures an exception is raised if __aenter__ fails.
    """
    mock_engine = Mock()
    mock_create_async_engine.return_value = mock_engine

    # Set up mock session context to fail
    mock_session_instance = AsyncMock()
    mock_session_instance.__aenter__.side_effect = Exception("Async with failed")
    mock_session_class = Mock(return_value=mock_session_instance)
    mock_sessionmaker.return_value = mock_session_class

    from lib.database.config.configuration import getAsyncUserDB

    # Expect an exception when session context fails to open
    with pytest.raises(Exception) as exc_info:
        async for _ in getAsyncUserDB():
            pass

    assert str(exc_info.value) == "Database error: Async with failed"

@pytest.mark.asyncio
@patch('lib.database.config.configuration.Instance', new=_MockInstance)
@patch('lib.database.config.configuration.create_async_engine')
async def test_db_config_get_async_db_success(mock_create_async_engine):
    """
    Test for successful database connection with getAsyncDB.
    Verifies that an async connection is created and yielded correctly.
    """
    mock_engine = MagicMock()
    mock_connection = AsyncMock()
    mock_engine.connect.return_value.__aenter__.return_value = mock_connection  # Configure mock connection
    mock_create_async_engine.return_value = mock_engine

    from lib.database.config.configuration import getAsyncDB

    # Test the yielded connection
    async for db in getAsyncDB(FAKE_DB_NAME):
        assert db is mock_connection, "Expected db to be the result of async_user_engine.connect()"

    # Ensure engine was created with the correct parameters
    mock_create_async_engine.assert_called_once_with(f"{FAKE_DB_URL}/{FAKE_DB_NAME}", echo=False, isolation_level="AUTOCOMMIT")

@pytest.mark.asyncio
@patch('lib.database.config.configuration.Instance', new=_MockInstance)
@patch('lib.database.config.configuration.create_async_engine')
async def test_db_config_get_async_db_failure_on_create_async_engine(mock_create_async_engine):
    """
    Test for failure case where async engine creation fails in getAsyncDB.
    Ensures an exception is raised with the expected error message.
    """
    mock_create_async_engine.side_effect = Exception("Engine creation failed")
    from lib.database.config.configuration import getAsyncDB

    # Verify exception is raised when engine creation fails
    with pytest.raises(Exception) as exc_info:
        async for _ in getAsyncDB(FAKE_DB_NAME):
            pass

    assert str(exc_info.value) == "Database error: Engine creation failed"

@pytest.mark.asyncio
@patch('lib.database.config.configuration.Instance', new=_MockInstance)
@patch('lib.database.config.configuration.create_async_engine')
async def test_db_config_get_async_db_exception_failure_when_open_async_engine(mock_create_async_engine):
    """
    Test for failure in async context management when opening a connection in getAsyncDB.
    Ensures an exception is raised if __aenter__ fails.
    """
    mock_engine = MagicMock()
    mock_engine.connect.return_value.__aenter__.side_effect = Exception("Test Error")
    mock_create_async_engine.return_value = mock_engine

    from lib.database.config.configuration import getAsyncDB

    # Expect an exception when connection context fails to open
    with pytest.raises(Exception) as exc_info:
        async for _ in getAsyncDB(FAKE_DB_NAME):
            pass

    assert str(exc_info.value) == "Database error: Test Error"