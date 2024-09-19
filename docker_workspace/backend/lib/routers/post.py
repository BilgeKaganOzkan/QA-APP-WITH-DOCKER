from lib.routers.instance import *

router = APIRouter()

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
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to convert CSV file. Please check the CSV file and try again.")

    del async_db_engine
    
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
        
        db_tables.append(original_table_name)
        
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
    temp_db_path = f"./.vector_stores/{session_id}"

    if os.path.exists(temp_db_path + "/faiss"):
        vector_store = FAISS.load_local(
            temp_db_path + "/faiss", embedding, allow_dangerous_deserialization=True
        )

    else:
        os.makedirs(temp_db_path, exist_ok=True)
        os.makedirs(temp_db_path + "/documents", exist_ok=True)
        vector_store = None

    try:
        for file in files:
            temp_file_name = file.filename
            file_path = os.path.join(temp_db_path, "documents", temp_file_name)

            async with aiofiles.open(file_path, "wb") as temp_file:
                await temp_file.write(await file.read())

            pdf_loader = PyPDFLoader(file_path)
            documents = await pdf_loader.aload()

            for doc in documents:
                doc.metadata['filename'] = temp_file_name

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n"]
            )
            
            split_documents = await text_splitter.atransform_documents(documents)

            if vector_store is None:
                vector_store = await FAISS.afrom_documents(split_documents, embedding)
            else:
                await vector_store.aadd_documents(split_documents)

        vector_store.save_local(temp_db_path + "/faiss")
    except Exception as e:
        shutil.rmtree(path=temp_db_path, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to convert PDF file. Error: {str(e)}"
        )

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
    rag_query_agent = RagQueryAgent(llm=llm, memory=session_memory, db_path=temp_db_path, embeddings=embedding, max_iteration=llm_max_iteration)
    
    response = await rag_query_agent.execute(data["humanMessage"])

    await redis.resetSessionTimeout(session_id=session_id)
    
    return {"aiMessage": response}