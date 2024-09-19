from lib.routers.instance import *

router = APIRouter()

@router.get(start_session_end_point, response_model=InformationResponse)
async def startSession(response: Response):
    session_id = await redis.createSession()
    await memory.createMemory(session_id=session_id)
    response.set_cookie(key="session_id", value=session_id)
    
    return {"informationMessage": "Session started."}