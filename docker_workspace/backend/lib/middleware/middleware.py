from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status
from logging.handlers import RotatingFileHandler
from lib.routers.instance import instance
import logging

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(instance.log_file_path, maxBytes=10485760, backupCount=100),
    ]
)

class LogRequestsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logging.error(f"Error processing request {request.method} {request.url}: {str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected internal server error")