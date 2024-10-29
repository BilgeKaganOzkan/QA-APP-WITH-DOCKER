import pytest
from fastapi import FastAPI
from patched_get_module import PatchedGetModule
from unittest.mock import AsyncMock

# Constants to use in tests
FAKE_SESSION_ID = 'session123'
FAKE_URL = "http://testserver"

@pytest.fixture(scope="function")
def fixture_test_app(patched_get_module):
    """
    Fixture to create and configure a FastAPI test application, including the router
    from the patched GET module.
    - scope="function" ensures a fresh instance for each test function.
    """
    # Create a FastAPI test app and include the router from the patched GET module
    test_app = FastAPI()
    test_app.include_router(patched_get_module.router)
    return test_app

@pytest.fixture(scope="function")
def patched_get_module():
    """
    Fixture for creating and providing an instance of PatchedGetModule with
    the necessary patches applied.
    - scope="function" provides a fresh, isolated instance for each test function.
    """
    with PatchedGetModule() as patched:
        # Yield the patched module instance, allowing tests to access it directly
        yield patched