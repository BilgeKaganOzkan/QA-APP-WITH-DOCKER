from fastapi import (APIRouter, Depends, HTTPException, status)
from fastapi.responses import JSONResponse
from lib.models.get_models import ProgressResponse
from lib.models.general_models import InformationResponse
from lib.instances.instance import instance

router = APIRouter()

@router.get(instance.start_session_end_point, response_model=InformationResponse)
async def startSession(session: tuple = Depends(instance.redis_tool.getSession)):
    return {"informationMessage": "Please upload a file"}

@router.get(instance.check_session_end_point, response_model=InformationResponse)
async def checkSession(session: tuple = Depends(instance.redis_tool.getSession)):
    return {"informationMessage": "Session is valid"}

@router.get(instance.progress_end_point, response_model=ProgressResponse)
async def getProgress(session: tuple = Depends(instance.redis_tool.getSession)):
    _, session_data = session
    progress = session_data.get("progress")

    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found.")

    return JSONResponse(content={"progress": progress})