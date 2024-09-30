from fastapi import (APIRouter, Depends, HTTPException, status)
from fastapi.responses import JSONResponse
from lib.models.get_models import ProgressResponse
from lib.models.general_models import InformationResponse
from lib.routers.instance import instance

router = APIRouter()

@router.get(instance.start_session_end_point, response_model=InformationResponse)
async def getProgress(session: tuple = Depends(instance.redis_tool.getSession)):
    return {"informationMessage": "Please upload a file"}

@router.get(instance.check_session_end_point, response_model=InformationResponse)
async def checkSession(session: tuple = Depends(instance.redis_tool.getSession)):
    session_id, _ = session 
    if session_id in instance.active_session_list:
        return {"informationMessage": "Session is valid"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed. Invalid session.",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.get(instance.progress_end_point, response_model=ProgressResponse)
async def getProgress(session: tuple = Depends(instance.redis_tool.getSession)):
    session_id, session_data = session
    progress = session_data.get("progress")

    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found.")

    return JSONResponse(content={"progress": progress})