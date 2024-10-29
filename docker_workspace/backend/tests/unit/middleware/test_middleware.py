from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

class _MockInstance:
    def __init__(self):
        self.log_file_path = 'temp_path.log'

@patch('lib.instances.instance.Instance', new=_MockInstance)
def test_middleware_success_unexpected_exception():
    """
    Test to verify LogRequestsMiddleware logs an error and raises HTTP 500 for an unexpected exception.
    Ensures logging and error response behavior is correct.
    """
    with patch("lib.middleware.middleware.logging.error") as mock_log_error:
        from lib.middleware.middleware import LogRequestsMiddleware, instance
        
        app = FastAPI()
        app.add_middleware(LogRequestsMiddleware)

        @app.get("/unexpected_error")
        async def error_route():
            # Route to trigger a generic exception
            raise Exception("This is a test error")

        client = TestClient(app)
        
        # Test the response for an unexpected error
        with pytest.raises(HTTPException) as excinfo:
            response = client.get("/unexpected_error")

        # Check that the response is an HTTP 500 error
        assert excinfo.value.status_code == 500
        assert excinfo.value.detail == "Unexpected internal server error"

        # Ensure that the error was logged once
        mock_log_error.assert_called_once()
        # Verify log file path is correctly set
        assert instance.log_file_path == 'temp_path.log'

@patch('lib.instances.instance.Instance', new=_MockInstance)
def test_middleware_success_http_exception():
    """
    Test to verify LogRequestsMiddleware correctly handles and does not log HTTPExceptions.
    Ensures the response and logging behavior align with the expected FastAPI error handling.
    """
    with patch("lib.middleware.middleware.logging.error") as mock_log_error:
        from lib.middleware.middleware import LogRequestsMiddleware
        
        app = FastAPI()
        app.add_middleware(LogRequestsMiddleware)

        @app.get("/http_error")
        async def error_route():
            # Route to trigger an HTTP 400 error
            raise HTTPException(status_code=400, detail="Test exception")

        client = TestClient(app)
        
        # Test the response for an HTTPException
        response = client.get("/http_error")

        # Verify that the response matches the HTTPException raised
        assert response.status_code == 400
        assert response.json()['detail'] == "Test exception"

        # Ensure no logging occurred for this expected error
        mock_log_error.assert_not_called()