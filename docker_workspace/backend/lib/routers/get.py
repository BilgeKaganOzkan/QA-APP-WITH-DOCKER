from lib.routers.instance import *

router = APIRouter()


@router.get("/get_progress")
async def getProgress(session: tuple = Depends(redis_tool.getSession)):
    session_id, session_data = session
    progress = session_data.get("progress")

    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found.")

    return JSONResponse(content={"progress": progress})