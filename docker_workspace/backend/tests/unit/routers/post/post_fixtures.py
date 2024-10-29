import pytest
from fastapi import FastAPI
from patched_post_module import PatchedPostModule

# Constants for test data
FAKE_SESSION_ID = 'session123'
FAKE_DB_PATH = 'mock_db_path'
FAKE_VECTOR_STORE_PATH = 'mock_vector_store_path'
FAKE_EMAIL = "test@example.com"
FAKE_PASSWORD = "hashed_password"
FAKE_URL = "http://testserver"

@pytest.fixture
def fixture_test_app(patched_post_module):
    """
    Fixture to set up and return a test instance of the FastAPI application with patched dependencies.
    Includes the router from PatchedPostModule and overrides the async user DB with a mock.
    """
    # Create a FastAPI instance
    test_app = FastAPI()
    # Include the router from the patched module
    test_app.include_router(patched_post_module.router)

    async def override_getAsyncUserDB():
        """
        Override function to yield a mocked async user database connection.
        Used to replace real database connections with a controlled mock during testing.
        """
        yield patched_post_module.mock_getAsyncUserDB

    # Override getAsyncUserDB dependency with the mock for controlled testing
    from lib.database.config.configuration import getAsyncUserDB
    test_app.dependency_overrides[getAsyncUserDB] = override_getAsyncUserDB

    return test_app  # Return the configured test app for use in test cases

@pytest.fixture
def patched_post_module():
    """
    Fixture to initialize and yield a patched version of PatchedPostModule.
    This includes mocked agents, user DB, and password verification utilities for isolated testing.
    """
    # Initialize the patched module and yield it for testing
    with PatchedPostModule() as patched:
        yield patched