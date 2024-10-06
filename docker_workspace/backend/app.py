from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from lib.tools.files_checker import filesChecker
from lib.middleware.middleware import LogRequestsMiddleware
from lib.instances.instance import instance
from lib.routers.get import router as get_router
from lib.routers.post import router as post_router
from lib.routers.put import router as put_router
from lib.routers.delete import router as delete_router
from contextlib import asynccontextmanager
import asyncio

@asynccontextmanager
async def lifespan(router: FastAPI):
    task = asyncio.create_task(instance.redis_tool._listenForExpirations())
    yield

    session_keys = await instance.redis_tool.getAllSessions()
    
    for key in session_keys:
        if key.startswith("session:"):
            session_id = key.split(":")[1]
            await instance.redis_tool.deleteSession(session_id)

    task.cancel()
    await task

del filesChecker

app_ip = instance.app_ip
app_port = instance.app_port

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=instance.origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(LogRequestsMiddleware)

app.include_router(get_router)
app.include_router(post_router)
app.include_router(put_router)
app.include_router(delete_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=app_ip, port=app_port, access_log=False)