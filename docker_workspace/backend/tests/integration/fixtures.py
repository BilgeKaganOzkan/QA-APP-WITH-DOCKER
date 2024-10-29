import pytest, asyncio
from lib.routers.post import instance
from sqlalchemy import text

# Constants for test user and session details
FAKE_USER_EMAIL = "testuser@example.com"
FAKE_USER_PASSWORD = "securepassword123"
FAKE_SESSION_ID = "test_session"
FAKE_URL = "http://testserver"

TEST_USER_EMAIL = "test_user@qaapp.com"
TEST_USER_PASSWORD = "test_password"
TEST_USER_WRONG_PASSWORD = "test_wrong_password"
TEST_DB_NAME = f"temporary_database_{FAKE_SESSION_ID}"

temp_db_name = f"temporary_database_{FAKE_SESSION_ID}"
terminate_query = text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{temp_db_name}'
            AND pid <> pg_backend_pid();
        """)
terminate_user_query = text(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = 'test_user_db'
            AND pid <> pg_backend_pid();
        """)

@pytest.fixture(scope="session")
def event_loop():
    """Creates a new event loop specifically for running async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_and_tear_down():
    await instance.redis_tool.redis.initialize()
    yield
    await instance.redis_tool.redis.close()