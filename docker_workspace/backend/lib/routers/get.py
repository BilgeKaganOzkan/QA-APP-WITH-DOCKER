from fastapi import (APIRouter, Depends, HTTPException, status)
from fastapi.responses import JSONResponse
from lib.models.get_models import ProgressResponse
from lib.models.general_models import InformationResponse
from lib.instances.instance import Instance

instance = Instance()

router = APIRouter()

@router.get(instance.start_session_end_point, response_model=InformationResponse)
async def startSession(session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Initiates a session and prompts the user to upload a file.

    This endpoint signals the start of a session, asking the user to upload a file.

    @param session The session data dependency for validation.
    @return Information message prompting for file upload.
    """
    return {"informationMessage": "Please upload a file"}

@router.get(instance.check_session_end_point, response_model=InformationResponse)
async def checkSession(session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Checks the validity of the current session.

    This endpoint verifies if the current session is valid.

    @param session The session data dependency for validation.
    @return Information message indicating the validity of the session.
    """
    return {"informationMessage": "Session is valid"}

@router.get(instance.progress_end_point, response_model=ProgressResponse)
async def getProgress(session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Retrieves the progress of the current session.

    This endpoint checks the session data for the progress value.
    If the progress is not found, it raises an HTTP 404 error.

    @param session The session data dependency for validation.
    @return JSON response containing the current progress.

    @exception HTTPException If the progress is not found.
    """
    _, session_data = session
    progress = session_data.get("progress")

    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress not found.")

    return JSONResponse(content={"progress": progress})