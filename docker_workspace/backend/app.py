from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from lib.middleware.middleware import LogRequestsMiddleware
from lib.routers.post import (router as post_router, redis, app_ip, app_port)
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

app.include_router(post_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=app_ip, port=app_port, access_log=True)