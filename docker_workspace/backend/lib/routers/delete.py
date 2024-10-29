from fastapi import (APIRouter, Depends, Response)
from lib.models.general_models import InformationResponse
from lib.instances.instance import Instance
from sqlalchemy.sql import text
from lib.database.config.configuration import getAsyncDB
import os, asyncio, shutil

instance = Instance()

async def _deleteTempDatabase(session: tuple = Depends(instance.redis_tool.getSession)):   
    """
    @brief Deletes the temporary database associated with the current session.

    This function checks if a temporary database exists for the session and,
    if so, terminates any active connections and drops the database.
    
    @param session The session data dependency, containing the session ID and related data.
    @return True if the database deletion process is completed.
    """
    _, session_data = session
    temp_database_name = session_data.get("temp_database_path", "")
    
    async for db in getAsyncDB("postgres"):
        # Check if the temporary database exists
        db_check_query = f"SELECT 1 FROM pg_database WHERE datname = '{temp_database_name}';"
        result = await db.execute(text(db_check_query))
        database_exists = result.fetchone()

        if database_exists:
            # Terminate active connections to the temporary database
            terminate_connections_query = f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{temp_database_name}'
                AND pid <> pg_backend_pid();
            """
            await db.execute(text(terminate_connections_query))

            # Drop the temporary database
            drop_db_query = f"DROP DATABASE {temp_database_name};"
            await db.execute(text(drop_db_query))

    return True

async def _clearTempDatabase(session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Clears all tables from the temporary database associated with the session.

    This function fetches all tables in the temporary database and deletes each one, if any exist.

    @param session The session data dependency containing the session ID and relevant data.
    @return True if the table clearing process is completed.
    """
    _, session_data = session

    async for db in getAsyncDB(session_data.get('temp_database_path', '')):
        try:
            # Fetch all tables in the temporary database schema 'public'
            get_tables_query = """
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public';
            """
            result = await db.execute(text(get_tables_query))
            tables = result.fetchall()

            # Drop each table found in the temporary database
            if tables:
                for table in tables:
                    drop_table_query = f"DROP TABLE IF EXISTS {table[0]} CASCADE;"
                    await db.execute(text(drop_table_query))
        except:
            pass

    return True

async def _deleteVectorStore(session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Deletes the vector store associated with the session.

    This function removes the vector store path if it exists as a directory or file.
    
    @param session The session data dependency, containing session data with the vector store path.
    @return True if the deletion of the vector store is completed.
    """
    _, session_data = session
    vector_store_path = session_data.get("vector_store_path", "")
    
    if vector_store_path != '':
        try:
            # Remove vector store directory or file based on the path type
            if os.path.isdir(vector_store_path):
                await asyncio.to_thread(shutil.rmtree, path=vector_store_path, ignore_errors=True)
            else:
                await asyncio.to_thread(os.remove, vector_store_path)
        except:
            pass

    return True

router = APIRouter()

@router.post(instance.clear_session_end_point, response_model=InformationResponse)
@router.delete(instance.clear_session_end_point, response_model=InformationResponse)
async def clearSession(response: Response, session: tuple = Depends(instance.redis_tool.getSession), db_deleted: bool = Depends(_clearTempDatabase), vs_deleted: bool = Depends(_deleteVectorStore)):    
    """
    @brief Clears the session by removing related temporary data and vector stores.

    This endpoint clears the temporary data associated with the session,
    including any temporary database and vector store entries.

    @param response FastAPI response object.
    @param session The session data dependency.
    @param db_deleted Boolean indicating if the temporary database was cleared.
    @param vs_deleted Boolean indicating if the vector store was deleted.
    @return Information message indicating session clearance.
    """
    return {"informationMessage": "Session cleared."}

@router.post(instance.end_session_end_point, response_model=InformationResponse)
@router.delete(instance.end_session_end_point, response_model=InformationResponse)
async def endSession(response: Response, session: tuple = Depends(instance.redis_tool.getSession), db_deleted: bool = Depends(_deleteTempDatabase), vs_deleted: bool = Depends(_deleteVectorStore)):
    """
    @brief Ends the session by deleting session data, memory, and related resources.

    This endpoint ends the session, deleting all associated data from memory,
    Redis, and any temporary databases or vector stores.

    @param response FastAPI response object.
    @param session The session data dependency.
    @param db_deleted Boolean indicating if the temporary database was deleted.
    @param vs_deleted Boolean indicating if the vector store was deleted.
    @return Information message indicating session termination.
    """
    session_id, _ = session

    await instance.memory.deleteMemory(session_id=session_id)
    await instance.redis_tool.deleteSession(session_id=session_id)

    return {"informationMessage": "Session ended."}