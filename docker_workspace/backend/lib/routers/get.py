from lib.routers.instance import *

router = APIRouter()

@router.get(start_session_end_point, response_model=InformationResponse)
async def getProgress(session: tuple = Depends(redis_tool.getSession)):
    return {"informationMessage": "Please upload a file"}

@router.get("/check_session", response_model=InformationResponse)
async def checkSession(session: tuple = Depends(redis_tool.getSession)):
    session_id, _ = session 
    if session_id in active_session_list:
        return {"informationMessage": "Session is valid"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed. Invalid session.",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.get("/get_progress")
async def getProgress(session: tuple = Depends(redis_tool.getSession)):
    session_id, session_data = session
    progress = session_data.get("progress")

    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found.")

    return JSONResponse(content={"progress": progress})