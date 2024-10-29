from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from lib.tools.files_checker import filesChecker
from lib.middleware.middleware import LogRequestsMiddleware
from lib.instances.instance import Instance
from lib.routers.get import router as get_router
from lib.routers.post import router as post_router
from lib.routers.put import router as put_router
from lib.routers.delete import router as delete_router
from contextlib import asynccontextmanager
import asyncio

# Create an instance of the application configuration
instance = Instance()

@asynccontextmanager
async def lifespan(router: FastAPI):
    """
    @brief Manages the lifespan of the FastAPI application.

    This context manager listens for Redis session expirations and ensures that
    all active sessions are cleared upon application shutdown.

    @param router (FastAPI): The FastAPI application instance.
    """
    task = asyncio.create_task(instance.redis_tool._listenForExpirations())  # Start listening for session expirations
    yield

    # Retrieve and delete all active sessions upon shutdown
    session_keys = await instance.redis_tool.getAllSessions()
    for key in session_keys:
        if key.startswith("session:"):
            session_id = key.split(":")[1]  # Extract session ID
            await instance.redis_tool.deleteSession(session_id)

    task.cancel()
    await task

del filesChecker  # Delete the filesChecker instance

app_ip = instance.app_ip
app_port = instance.app_port

# Create the FastAPI application instance with lifespan management
app = FastAPI(lifespan=lifespan)

# Configure CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=instance.origin_list,  # Specify allowed origins
    allow_credentials=True,  # Allow credentials in CORS requests
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specify allowed HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Add custom logging middleware
app.add_middleware(LogRequestsMiddleware)

# Include routers for handling different HTTP methods
app.include_router(get_router)
app.include_router(post_router)
app.include_router(put_router)
app.include_router(delete_router)

# Run the application using Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=app_ip, port=app_port, access_log=False)  # Start the server with specified IP and port