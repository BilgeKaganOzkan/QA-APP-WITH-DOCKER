from lib.routers.instance import *

router = APIRouter()

@router.delete("/clear_session", response_model=InformationResponse)
async def clearSession(response: Response, session: tuple = Depends(redis_tool.getSession)):
    session_id, session_data = session
    db_path = session_data.get("db_path", "").replace("sqlite+aiosqlite:///", "")
    
    if db_path != '':
        try:
            if os.path.isdir(db_path):
                await asyncio.to_thread(shutil.rmtree, path=db_path, ignore_errors=True)
            else:
                await asyncio.to_thread(os.remove, db_path)
        except:
            pass
        
    return {"informationMessage": "Session ended."}

@router.post(end_session_end_point, response_model=InformationResponse)
@router.delete(end_session_end_point, response_model=InformationResponse)
async def endSession(response: Response, session: tuple = Depends(redis_tool.getSession)):
    session_id, session_data = session
    db_path = session_data.get("db_path", "").replace("sqlite+aiosqlite:///", "")
    
    if db_path != '':
        await redis_tool.deleteSession(f"session:{session_id}")
        
        response.delete_cookie("session_id")

        try:
            if os.path.isdir(db_path):
                await asyncio.to_thread(shutil.rmtree, path=db_path, ignore_errors=True)
            else:
                await asyncio.to_thread(os.remove, db_path)
        finally:
            await memory.deleteMemory(session_id=session_id)
    
    try:
        active_session_list.remove(session_id)
    except:
        pass

    return {"informationMessage": "Session ended."}