import pytest
from fastapi import FastAPI
from patched_delete_module import PatchedDeleteModule
from unittest.mock import AsyncMock

# Constants for test data
FAKE_SESSION_ID = 'session123'
FAKE_DB_PATH = 'mock_db_path'
FAKE_VECTOR_STORE_PATH = 'mock_vector_store_path'
FAKE_URL = "http://testserver"

@pytest.fixture(scope="function")
def fixture_test_app(patched_delete_module):
    """
    Fixture to set up a FastAPI test application that includes the delete router.
    This application will be used to test delete operations.
    """
    # Create a new FastAPI instance for testing.
    test_app = FastAPI()
    
    # Include the delete module's router to make its endpoints available in the test app.
    test_app.include_router(patched_delete_module.router)

    # Return the configured test application for use in tests.
    return test_app

@pytest.fixture(scope="function")
def patched_delete_module():
    """
    Fixture to set up a patched version of the delete module, 
    replacing actual dependencies with mock objects to isolate tests.
    """
    # Use the patched delete module, which has mocked dependencies, 
    # ensuring that real database or external calls are not made during tests.
    with PatchedDeleteModule() as patched:
        yield patched