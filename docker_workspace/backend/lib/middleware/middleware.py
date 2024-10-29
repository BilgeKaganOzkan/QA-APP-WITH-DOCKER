from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status
from logging.handlers import RotatingFileHandler
from lib.instances.instance import Instance
import logging

instance = Instance()

# Configure logging to write error messages to a log file with rotation
logging.basicConfig(
    level=logging.ERROR,  # Set logging level to ERROR
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[
        RotatingFileHandler(instance.log_file_path, maxBytes=10485760, backupCount=100),  # Rotating file handler
    ]
)

class LogRequestsMiddleware(BaseHTTPMiddleware):
    """
    @brief Middleware for logging requests and handling errors.

    This middleware logs all requests and captures any exceptions
    that occur during request processing. If an exception is raised,
    it logs the error and raises an HTTP 500 Internal Server Error.
    """

    async def dispatch(self, request: Request, call_next):
        """
        @brief Processes the request and logs errors if they occur.

        @param request The incoming request object.
        @param call_next The function to call the next middleware or route handler.
        @return The response object.

        @exception HTTPException If an error occurs while processing the request.
        """
        try:
            # Call the next middleware or route handler
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error details with the request method and URL
            logging.error(f"Error processing request {request.method} {request.url}: {str(e)}", exc_info=True)
            # Raise an HTTP 500 Internal Server Error
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected internal server error")