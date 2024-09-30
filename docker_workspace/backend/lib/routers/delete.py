from fastapi import (APIRouter, Depends, Response)
from lib.models.general_models import InformationResponse
from lib.routers.instance import instance
import os, asyncio, shutil
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

async def deleteTempDatabase(session: tuple = Depends(instance.redis_tool.getSession)):
    db_url = instance.async_database_url + "/postgres"
    
    session_id, session_data = session
    temp_database_name = session_data.get("temp_database_path", "")
    
    async_temp_database_engine = create_async_engine(db_url, echo=False, isolation_level="AUTOCOMMIT")
    
    async with async_temp_database_engine.connect() as connection:
        db_check_query = f"SELECT 1 FROM pg_database WHERE datname = '{temp_database_name}';"
        result = await connection.execute(text(db_check_query))
        database_exists = result.fetchone()

        if database_exists:
            terminate_connections_query = f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{temp_database_name}'
                AND pid <> pg_backend_pid();
            """
            await connection.execute(text(terminate_connections_query))

            drop_db_query = f"DROP DATABASE {temp_database_name};"
            await connection.execute(text(drop_db_query))

    return True

async def clearTempDatabase(session: tuple = Depends(instance.redis_tool.getSession)):
    session_id, session_data = session
    db_url = instance.async_database_url + f"/{session_data.get('temp_database_path', '')}"
    
    async_temp_database_engine = create_async_engine(db_url, echo=False, isolation_level="AUTOCOMMIT")
    
    async with async_temp_database_engine.connect() as connection:
        get_tables_query = """
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public';
        """
        result = await connection.execute(text(get_tables_query))
        tables = result.fetchall()

        if tables:
            for table in tables:
                drop_table_query = f"DROP TABLE IF EXISTS {table[0]} CASCADE;"
                await connection.execute(text(drop_table_query))

    return True

async def deleteVectorStore(session: tuple = Depends(instance.redis_tool.getSession)):
    session_id, session_data = session
    
    vector_store_path = session_data.get("vector_store_path", "")
    
    if vector_store_path != '':
        try:
            if os.path.isdir(vector_store_path):
                await asyncio.to_thread(shutil.rmtree, path=vector_store_path, ignore_errors=True)
            else:
                await asyncio.to_thread(os.remove, vector_store_path)
        except:
            pass

    return True

router = APIRouter()

@router.delete(instance.clear_session_end_point, response_model=InformationResponse)
async def clearSession(response: Response, session: tuple = Depends(instance.redis_tool.getSession), db_deleted: bool = Depends(clearTempDatabase), vs_deleted: bool = Depends(deleteVectorStore)):    
    return {"informationMessage": "Session cleared."}

@router.post(instance.end_session_end_point, response_model=InformationResponse)
@router.delete(instance.end_session_end_point, response_model=InformationResponse)
async def endSession(response: Response, session: tuple = Depends(instance.redis_tool.getSession), db_deleted: bool = Depends(deleteTempDatabase), vs_deleted: bool = Depends(deleteVectorStore)):
    session_id, session_data = session

    await instance.memory.deleteMemory(session_id=session_id)

    if session_id in instance.active_session_list:
        instance.active_session_list.remove(session_id)

    return {"informationMessage": "Session ended."}