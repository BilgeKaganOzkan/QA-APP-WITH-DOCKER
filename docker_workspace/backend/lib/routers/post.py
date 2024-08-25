from fastapi import (APIRouter, Depends, HTTPException, status, Response, UploadFile, File)
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession)
from sqlalchemy import (text, create_engine)
from sqlalchemy.orm import sessionmaker
from typing import List
from lib.config_parser.config_parser import Configuration
from lib.tools.redis import RedisTool
from lib.ai.agents.agents import QueryAgent
from lib.ai.memory.memory import CustomMemoryDict
from lib.ai.llm.llm import LLM
from lib.models.post_models import (HumanRequest, InformationResponse, AIResponse)
import pandas as pd, os, asyncio

config = Configuration()

llm_model_name = config.getLLMModelName()
llm_max_iteration = config.getLLMMaxIteration()
start_session_end_point = config.getStartSessionEndpoint()
upload_csv_end_point = config.getUploadCsvEndpoint()
query_end_point = config.getQueryEndpoint()
end_session_end_point = config.getEndSessionEndpoint()
session_timeout = config.getSessionTimeout()
db_max_table_limit = config.getDbMaxTableLimit()
redis_ip = config.getRedisIP()
redis_port = config.getRedisPort()
app_ip = config.getAppIP()
app_port = config.getAppPort()

del config

router = APIRouter()
memory = CustomMemoryDict()
llm = LLM(llm_model_name=llm_model_name)
redis = RedisTool(memory=memory, session_timeout=session_timeout, redis_ip=redis_ip, redis_port=redis_port)


@router.get(start_session_end_point, response_model=InformationResponse)
async def startSession(response: Response):
    session_id = await redis.createSession()
    await memory.createMemory(session_id=session_id)
    response.set_cookie(key="session_id", value=session_id)
    
    return {"informationMessage": "Session started."}


@router.post(upload_csv_end_point, response_model=InformationResponse)
async def uploadCSV(files: List[UploadFile] = File(...), session: tuple = Depends(redis.getSession)):
    session_id, _ = session

    temp_db_path = f"sqlite+aiosqlite:///./.temp_databases/temporary_database_{session_id}.db"
    async_db_engine = create_async_engine(temp_db_path, echo=False)
    
    db_tables = []

    async_session = sessionmaker(async_db_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        async with session.begin():
            try:
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                result = result.fetchall()
                db_tables = [row[0] for row in result]
            except Exception as e:
                print(f"Failed to retrieve tables: {e}")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to convert CSV file. Please check the CSV file and try again.")

    if len(files) > db_max_table_limit - len(db_tables):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"You reached max file limit {db_max_table_limit}")

    for file in files:
        df = await asyncio.to_thread(pd.read_csv, file.file)
        table_name = os.path.splitext(file.filename)[0]

        table_counter = 1
        original_table_name = table_name

        while table_name in db_tables:
            table_name = f"{original_table_name}_{table_counter}"
            table_counter += 1

        del async_db_engine

        def run_pandas_to_sql(df, table_name, db_path):
            engine = create_engine(db_path)
            with engine.connect() as connection:
                df.to_sql(table_name, con=connection, index=False, if_exists="replace")

        await asyncio.to_thread(run_pandas_to_sql, df=df, table_name=table_name, db_path=f"sqlite:///./.temp_databases/temporary_database_{session_id}.db")

    await redis.updateSession(session_id=session_id, key="db_path", value=temp_db_path)
    
    return {"informationMessage": "CSV files uploaded and converted to database successfully."}


@router.post(query_end_point, response_model=AIResponse)
async def query(request: HumanRequest, session: tuple = Depends(redis.getSession)):
    data = request.model_dump()
    session_id, session_data = session
    
    temp_db_path = session_data.get("db_path")
    if not temp_db_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    session_memory = await memory.getMemory(session_id=session_id)
    query_agent = QueryAgent(llm=llm, memory=session_memory, db_path=temp_db_path, max_iteration=llm_max_iteration)
    
    response = await query_agent.execute(data["humanMessage"])

    await redis.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}


@router.delete(end_session_end_point, response_model=InformationResponse)
async def endSession(response: Response, session: tuple = Depends(redis.getSession)):
    session_id, session_data = session
    db_path = session_data.get("db_path", "").replace("sqlite+aiosqlite:///", "")
    
    if db_path != '':
        await redis.deleteSession(f"session:{session_id}")
        
        response.delete_cookie("session_id")

        try:
            await asyncio.to_thread(os.remove, db_path)
        except Exception as e:
            print(f"Failed to delete database file: {e}")

        await memory.deleteMemory(session_id=session_id)
        
    return {"informationMessage": "Session ended."}