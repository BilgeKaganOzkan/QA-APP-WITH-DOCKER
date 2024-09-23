from lib.routers.instance import *

router = APIRouter()

@router.post(upload_csv_end_point, response_model=InformationResponse)
async def uploadCSV(files: List[UploadFile] = File(...), session: tuple = Depends(redis.getSession)):
    session_id, _ = session

    temp_db_path = f"sqlite+aiosqlite:///./.temp_databases/temporary_database_{session_id}.db"
    async_db_engine = create_async_engine(temp_db_path, echo=False)
    
    db_tables = []

    async_session = sessionmaker(async_db_engine, class_=AsyncSession, expire_on_commit=False)

    await redis.updateSession(session_id=session_id, key="progress", value="0")

    async with async_session() as session:
        async with session.begin():
            try:
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                result = result.fetchall()
                db_tables = [row[0] for row in result]
            except Exception as e:
                await redis.updateSession(session_id=session_id, key="progress", value="-1")
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to convert CSV file. Please check the CSV file and try again.")

    del async_db_engine

    if len(files) > db_max_table_limit - len(db_tables):
        await redis.updateSession(session_id=session_id, key="progress", value="-1")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"You reached max file limit {db_max_table_limit}")

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
        
        db_tables.append(original_table_name)

        def run_pandas_to_sql(df, table_name, db_path):
            engine = create_engine(db_path)
            with engine.connect() as connection:
                df.to_sql(table_name, con=connection, index=False, if_exists="replace")

        await asyncio.to_thread(run_pandas_to_sql, df=df, table_name=table_name, db_path=f"sqlite:///./.temp_databases/temporary_database_{session_id}.db")

        current_step += 1
        progress = int((current_step / total_steps) * 100)
        await redis.updateSession(session_id=session_id, key="progress", value=str(progress))

    await redis.updateSession(session_id=session_id, key="progress", value="100")
    await redis.updateSession(session_id=session_id, key="db_path", value=temp_db_path)
    
    return {"informationMessage": "CSV files uploaded and converted to database successfully."}

@router.post(upload_pdf_end_point, response_model=InformationResponse)
async def uploadPDF(files: List[UploadFile] = File(...), session: tuple = Depends(redis.getSession)):
    session_id, _ = session
    temp_db_path = f"./.vector_stores/{session_id}"
    documents_dir = os.path.join(temp_db_path, "documents")
    faiss_dir = os.path.join(temp_db_path, "faiss")
    
    await redis.updateSession(session_id=session_id, key="progress", value="0")
    
    try:
        if os.path.exists(faiss_dir):
            vector_store = FAISS.load_local(
                faiss_dir, embedding, allow_dangerous_deserialization=True
            )
        else:
            os.makedirs(temp_db_path, exist_ok=True)
            os.makedirs(documents_dir, exist_ok=True)
            vector_store = None

        existing_files = [
            f for f in os.listdir(documents_dir)
            if os.path.isfile(os.path.join(documents_dir, f))
        ]
        existing_file_count = len(existing_files)

        new_file_count = len(files)

        if existing_file_count + new_file_count > max_file_limit:
            await redis.updateSession(session_id=session_id, key="progress", value="-1")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You reached the maximum file limit of {max_file_limit}."
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
            await redis.updateSession(session_id=session_id, key="progress", value=str(progress))


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
                vector_store = await FAISS.afrom_documents(split_documents, embedding)
            else:
                await vector_store.aadd_documents(split_documents)

            current_step += 1
            progress = int((current_step / total_steps) * 100)
            await redis.updateSession(session_id=session_id, key="progress", value=str(progress))

        vector_store.save_local(faiss_dir)
        await redis.updateSession(session_id=session_id, key="progress", value="100")

    except Exception as e:
        shutil.rmtree(path=temp_db_path, ignore_errors=True)
        await redis.updateSession(session_id=session_id, key="progress", value="-1")
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