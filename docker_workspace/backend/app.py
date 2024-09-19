from fastapi import FastAPI
import lib.tools.files_checker 
from fastapi.middleware.cors import CORSMiddleware
from lib.middleware.middleware import LogRequestsMiddleware
from lib.routers.instance import (redis, app_ip, app_port)
from lib.routers.get import router as get_router
from lib.routers.post import router as post_router
from lib.routers.delete import router as delete_router
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(router: FastAPI):
    task = asyncio.create_task(redis._listenForExpirations())
    yield

    task.cancel()
    await task

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin", "X-API-KEY"],
)

app.add_middleware(LogRequestsMiddleware)

app.include_router(get_router)
app.include_router(post_router)
app.include_router(delete_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=app_ip, port=app_port, access_log=False)