from fastapi import (APIRouter, Depends, HTTPException, status, Response, UploadFile, File)
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession)
from sqlalchemy import (text, create_engine)
from sqlalchemy.orm import sessionmaker
from typing import List
from lib.config_parser.config_parser import Configuration
from lib.tools.redis import RedisTool
from lib.ai.agents.agents import SqlQueryAgent, RagQueryAgent
from lib.ai.memory.memory import CustomMemoryDict
from lib.ai.llm.llm import LLM
from lib.ai.llm.embedding import Embedding
from lib.models.post_models import (HumanRequest, InformationResponse, AIResponse)
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
import pandas as pd, os, asyncio, shutil

config = Configuration()

llm_model_name = config.getLLMModelName()
embedding_model_name = config.getEmbeddingLLMModelName()
llm_max_iteration = config.getLLMMaxIteration()
start_session_end_point = config.getStartSessionEndpoint()
upload_csv_end_point = config.getUploadCsvEndpoint()
upload_pdf_end_point = config.getUploadPdfEndpoint()
sql_query_end_point = config.getSqlQueryEndpoint()
rag_query_end_point = config.getRagQueryEndpoint()
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
embedding = Embedding(model_name=embedding_model_name).get_embedding()
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

@router.post(upload_pdf_end_point, response_model=InformationResponse)
async def uploadPDF(files: List[UploadFile] = File(...), session: tuple = Depends(redis.getSession)):
    session_id, _ = session
    first_iteration = True
    
    temp_db_path = f"./.vector_stores/{session_id}"
    
    if os.path.exists(temp_db_path):
        first_iteration = False
        vector_store = FAISS.load_local(temp_db_path + "/faiss", embedding, allow_dangerous_deserialization=True)
    else:
        os.makedirs(temp_db_path, exist_ok=True)
        os.makedirs(temp_db_path + "/documents", exist_ok=True)
        os.makedirs(temp_db_path + "/faiss", exist_ok=True)
        vector_store = FAISS(embedding_function=embedding, docstore= InMemoryDocstore(), index_to_docstore_id={}, index=0)

    try:
        for file in files:
            temp_file_name = file.filename
            file_path = temp_db_path + "/documents/" + temp_file_name
            with open(file_path, "wb") as temp_file:
                temp_file.write(await file.read())
            
            pdf_loader = PyPDFLoader(file_path)
            documents = pdf_loader.load()

            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separator="\n")
            
            split_texts = []
            for doc in documents:
                split_texts.extend(text_splitter.split_text(doc.page_content))
                
            if first_iteration == True:
                first_iteration = False
                vector_store = await FAISS.afrom_texts(split_texts, embedding)
            else:
                await vector_store.aadd_texts(split_texts)
            
        vector_store.save_local(temp_db_path + "/faiss")
    except Exception as e:
        shutil.rmtree(path=temp_db_path, ignore_errors=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to convert PDF file. Please check the PDF file and try again.")
            
    await redis.updateSession(session_id=session_id, key="db_path", value=temp_db_path)

    return {"informationMessage": "PDF files uploaded and converted to database successfully."}


@router.post(sql_query_end_point, response_model=AIResponse)
async def sqlQuery(request: HumanRequest, session: tuple = Depends(redis.getSession)):
    data = request.model_dump()
    session_id, session_data = session
    
    temp_db_path = session_data.get("db_path")
    if not temp_db_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    session_memory = await memory.getMemory(session_id=session_id)
    sql_query_agent = SqlQueryAgent(llm=llm, memory=session_memory, db_path=temp_db_path, max_iteration=llm_max_iteration)
    
    response = await sql_query_agent.execute(data["humanMessage"])

    await redis.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}

@router.post(rag_query_end_point, response_model=AIResponse)
async def ragQuery(request: HumanRequest, session: tuple = Depends(redis.getSession)):
    data = request.model_dump()
    session_id, session_data = session
    
    temp_db_path = session_data.get("db_path")
    if not temp_db_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    session_memory = await memory.getMemory(session_id=session_id)
    rag_query_agent = RagQueryAgent(llm=llm, memory=session_memory, db_path=temp_db_path, embeddings=embedding)
    
    response = await rag_query_agent.execute(data["humanMessage"])

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
            if os.path.isdir(db_path):
                await asyncio.to_thread(shutil.rmtree, path=db_path, ignore_errors=True)
            else:
                await asyncio.to_thread(os.remove, db_path)
        finally:
            await memory.deleteMemory(session_id=session_id)
        
    return {"informationMessage": "Session ended."}