import pytest
from fastapi import FastAPI
from patched_put_module import PatchedPutModule
from unittest.mock import AsyncMock

# Constants to be used in tests for consistent session ID and URL
FAKE_SESSION_ID = 'session123'
FAKE_URL = "http://testserver"

@pytest.fixture(scope="function")
def fixture_test_app(patched_put_module):
    """
    Fixture that provides a FastAPI test application instance
    with the router from the patched_put_module included.
    Ensures that each test runs in isolation.
    """
    test_app = FastAPI()
    
    # Include the router from the patched module to expose its endpoints in the test app
    test_app.include_router(patched_put_module.router)

    return test_app

@pytest.fixture(scope="function")
def patched_put_module():
    """
    Fixture that provides an instance of PatchedPutModule, which mocks
    certain database and session operations. Ensures isolation across tests.
    """
    with PatchedPutModule() as patched:
        yield patched
