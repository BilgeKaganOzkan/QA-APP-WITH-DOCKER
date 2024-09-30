from fastapi import (APIRouter, Depends, HTTPException, status, Response, UploadFile, File)
from typing import List
from sqlalchemy.ext.asyncio import (create_async_engine, AsyncSession)
from sqlalchemy import (text, create_engine,select)
from sqlalchemy.orm import sessionmaker
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from lib.ai.agents.agents import SqlQueryAgent, RagQueryAgent
from lib.models.general_models import InformationResponse
from lib.models.post_models import (HumanRequest, AIResponse)
from lib.database.models.user_model import User
from lib.database.config.configuration import getAsyncUserDB
from lib.database.schemas.database_schema import (UserCreate, UserLogin)
from lib.database.securities.security import (getPasswordHash, verifyPassword)
from lib.routers.instance import instance
import pandas as pd
import os, asyncio, shutil, aiofiles

router = APIRouter()    
        
async def checkUserAuthentication(session: tuple = Depends(instance.redis_tool.getSession)) -> bool:
    session_id, _ = session 
    if session_id in instance.active_session_list:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed. Invalid session.",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def createTempDatabase(session: tuple = Depends(instance.redis_tool.getSession)):
    db_tables = []
    
    session_id, _ = session
    safe_session_id = session_id.replace("-", "_")

    temp_db_name = f"temporary_database_{safe_session_id}"
    sync_temp_db_url = f"{instance.sync_database_url}/{temp_db_name}"
    async_temp_db_url = f"{instance.async_database_url}/{temp_db_name}"

    db_url = instance.async_database_url + "/postgres"
    async_temp_database_engine = create_async_engine(db_url, echo=False, isolation_level="AUTOCOMMIT")

    async with async_temp_database_engine.connect() as connection:
        db_check_query = f"SELECT 1 FROM pg_database WHERE datname = '{temp_db_name}';"
        result = await connection.execute(text(db_check_query))
        database_exists = result.fetchone()

        if not database_exists:
            await connection.execute(text(f"CREATE DATABASE {temp_db_name}"))
            await instance.redis_tool.updateSession(session_id=session_id, key="temp_database_path", value=temp_db_name)
        else:
            try:
                result = await connection.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
                result = result.fetchall()
                db_tables = [row[0] for row in result]
            except Exception as e:
                await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="-1")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to retrieve existing tables from the database.")

    return sync_temp_db_url, db_tables

@router.post(instance.signup_end_point, response_model=InformationResponse, status_code=201)
async def signup(user: UserCreate, db: AsyncSession = Depends(getAsyncUserDB)):
    result = await db.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    if db_user:
        raise HTTPException(status_code=400, detail="E-mail already registered")
    hashed_password = getPasswordHash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return {"informationMessage": "User successfully registered"}

@router.post(instance.login_end_point, response_model=InformationResponse)
async def login(response: Response, form_data: UserLogin, db: AsyncSession = Depends(getAsyncUserDB)):
    result = await db.execute(select(User).where(User.email == form_data.email))
    user = result.scalars().first()
    if not user or not verifyPassword(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    session_id = await instance.redis_tool.createSession()
    await instance.memory.createMemory(session_id=session_id)
    await instance.redis_tool.updateSession(session_id=session_id, key="user_email", value=user.email)
    
    instance.active_session_list.append(session_id)
    
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="None",
        secure=True
    )
    
    return {"informationMessage": "Login successful"}

@router.post(instance.upload_csv_end_point, response_model=InformationResponse)
async def uploadCSV(files: List[UploadFile] = File(...), session: tuple = Depends(instance.redis_tool.getSession), auth: bool = Depends(checkUserAuthentication), temp_db_urls: tuple = Depends(createTempDatabase)):
    session_id, _ = session

    sync_temp_db_url, db_tables = temp_db_urls

    await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="0")

    if len(files) > instance.db_max_table_limit - len(db_tables):
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="-1")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"You reached max file limit {instance.db_max_table_limit}")

    total_steps = len(files) * 2 + 1
    current_step = 0

    for file in files:
        df = await asyncio.to_thread(pd.read_csv, file.file)
        table_name = os.path.splitext(file.filename)[0]

        table_counter = 1
        original_table_name = table_name

        while table_name in db_tables:
            table_name = f"{original_table_name}_{table_counter}"
            table_counter += 1
        
        db_tables.append(table_name)

        def run_pandas_to_postgresql(df, table_name, db_url):
            engine = create_engine(db_url)
            with engine.connect() as connection:
                df.to_sql(table_name, con=connection, index=False, if_exists="replace")

        await asyncio.to_thread(run_pandas_to_postgresql, df=df, table_name=table_name, db_url=sync_temp_db_url)

        current_step += 1
        progress = int((current_step / total_steps) * 100)
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value=str(progress))

    await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="100")
    
    return {"informationMessage": "CSV files uploaded and converted to database successfully."}


@router.post(instance.upload_pdf_end_point, response_model=InformationResponse)
async def uploadPDF(files: List[UploadFile] = File(...), session: tuple = Depends(instance.redis_tool.getSession), auth: bool = Depends(checkUserAuthentication)):
    session_id, _ = session
    vector_store_path = f"./.vector_stores/{session_id}"
    documents_dir = os.path.join(vector_store_path, "documents")
    faiss_dir = os.path.join(vector_store_path, "faiss")
    
    await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="0")
    
    try:
        if os.path.exists(faiss_dir):
            vector_store = FAISS.load_local(
                faiss_dir, instance.embedding, allow_dangerous_deserialization=True
            )
        else:
            os.makedirs(vector_store_path, exist_ok=True)
            os.makedirs(documents_dir, exist_ok=True)
            vector_store = None

        existing_files = [
            f for f in os.listdir(documents_dir)
            if os.path.isfile(os.path.join(documents_dir, f))
        ]
        existing_file_count = len(existing_files)

        new_file_count = len(files)

        if existing_file_count + new_file_count > instance.max_file_limit:
            await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="-1")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You reached the maximum file limit of {instance.max_file_limit}."
            )

        total_steps = new_file_count * 2 + 1
        current_step = 0

        for file in files:
            parsed_file_name = os.path.splitext(file.filename)[0]
            existing_file_list = [
                os.path.splitext(f)[0] for f in os.listdir(documents_dir)
                if os.path.isfile(os.path.join(documents_dir, f))
            ]

            file_name_counter = 1
            original_parsed_file_name = parsed_file_name

            while parsed_file_name in existing_file_list:
                parsed_file_name = f"{original_parsed_file_name}_{file_name_counter}"
                file_name_counter += 1

            parsed_file_name += ".pdf"
            file_path = os.path.join(documents_dir, parsed_file_name)

            async with aiofiles.open(file_path, "wb") as temp_file:
                await temp_file.write(await file.read())

            current_step += 1
            progress = int((current_step / total_steps) * 100)
            await instance.redis_tool.updateSession(session_id=session_id, key="progress", value=str(progress))


            pdf_loader = PyPDFLoader(file_path)
            documents = await pdf_loader.aload()

            for doc in documents:
                doc.metadata['filename'] = parsed_file_name

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", " "]
            )
            
            split_documents = await text_splitter.atransform_documents(documents)

            if vector_store is None:
                vector_store = await FAISS.afrom_documents(split_documents, instance.embedding)
            else:
                await vector_store.aadd_documents(split_documents)

            current_step += 1
            progress = int((current_step / total_steps) * 100)
            await instance.redis_tool.updateSession(session_id=session_id, key="progress", value=str(progress))

        vector_store.save_local(faiss_dir)
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="100")
    except Exception as e:
        shutil.rmtree(path=vector_store_path, ignore_errors=True)
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="-1")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to convert PDF file. Error: {str(e)}"
        )

    await instance.redis_tool.updateSession(session_id=session_id, key="vector_store_path", value=vector_store_path)
    return {"informationMessage": "PDF files uploaded and converted to database successfully."}

@router.post(instance.sql_query_end_point, response_model=AIResponse)
async def sqlQuery(request: HumanRequest, session: tuple = Depends(instance.redis_tool.getSession), auth: bool = Depends(checkUserAuthentication)):
    data = request.model_dump()
    session_id, session_data = session
    
    temp_database_path = session_data.get("temp_database_path")
    if not temp_database_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    session_memory = await instance.memory.getMemory(session_id=session_id)
    sql_query_agent = SqlQueryAgent(llm=instance.llm, memory=session_memory, temp_database_path=temp_database_path, max_iteration=instance.llm_max_iteration)
    
    response = await sql_query_agent.execute(data["humanMessage"])

    await instance.redis_tool.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}

@router.post(instance.rag_query_end_point, response_model=AIResponse)
async def ragQuery(request: HumanRequest, session: tuple = Depends(instance.redis_tool.getSession), auth: bool = Depends(checkUserAuthentication)):
    data = request.model_dump()
    session_id, session_data = session
    
    vector_store_path = session_data.get("vector_store_path")
    if not vector_store_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No database associated with the session.")
    
    session_memory = await instance.memory.getMemory(session_id=session_id)
    rag_query_agent = RagQueryAgent(llm=instance.llm, memory=session_memory, vector_store_path=vector_store_path, embeddings=instance.embedding, max_iteration=instance.llm_max_iteration)
    
    response = await rag_query_agent.execute(data["humanMessage"])

    await instance.redis_tool.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}
