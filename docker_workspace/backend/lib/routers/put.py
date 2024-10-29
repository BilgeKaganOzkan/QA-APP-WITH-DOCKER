from fastapi import (APIRouter, Depends, HTTPException, status, UploadFile, File)
from typing import List
from sqlalchemy import (text, create_engine)
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from lib.models.general_models import InformationResponse
from lib.instances.instance import Instance
from lib.database.config.configuration import getAsyncDB
import pandas as pd
import os, asyncio, shutil, aiofiles

instance = Instance()

router = APIRouter()

async def _createTempDatabase(session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Creates a temporary database for the session.

    This function checks if a temporary database already exists. If it does not,
    it creates one and updates the session with the database path.
    
    @param session The session data dependency for validation.
    @return Tuple containing the synchronous database URL and a list of database tables.
    """
    db_tables = []
    db_created = False
    
    session_id, _ = session
    safe_session_id = session_id.replace("-", "_")  # Replace dashes in session ID for naming

    temp_db_name = f"temporary_database_{safe_session_id}"
    sync_temp_db_url = f"{instance.sync_database_url}/{temp_db_name}"

    async for db_async_temp in getAsyncDB("postgres"):
        # Check if the temporary database already exists
        result = await db_async_temp.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{temp_db_name}'"))
        database_exists = result.fetchall()

        if not database_exists:
            # Create the temporary database if it doesn't exist
            await db_async_temp.execute(text(f"CREATE DATABASE {temp_db_name}"))
            await instance.redis_tool.updateSession(session_id=session_id, key="temp_database_path", value=temp_db_name)
            db_created = True
        else:
            db_created = False     

        if not db_created:
            # If the database already exists, fetch its tables
            async for db_async_temp in getAsyncDB(temp_db_name):
                result = await db_async_temp.execute(text("SELECT pg_tables.tablename FROM pg_tables WHERE schemaname='public';"))
                result = result.fetchall()
                db_tables = [row[0] for row in result]

        return sync_temp_db_url, db_tables

@router.put(instance.upload_csv_end_point, response_model=InformationResponse)
async def uploadCSV(files: List[UploadFile] = File(...), session: tuple = Depends(instance.redis_tool.getSession), temp_db_urls: tuple = Depends(_createTempDatabase)):
    """
    @brief Uploads CSV files and converts them to a temporary database.

    This endpoint accepts multiple CSV files, creates a temporary database if needed,
    and uploads the data to the database, tracking progress in the session.

    @param files List of uploaded CSV files.
    @param session The session data dependency for validation.
    @param temp_db_urls The URLs and tables from the temporary database.
    @return Information message indicating successful upload.

    @exception HTTPException If the maximum file limit is exceeded.
    """
    session_id, _ = session

    sync_temp_db_url, db_tables = temp_db_urls

    # Initialize progress in the session
    await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="0")

    # Check if the number of files exceeds the maximum allowed
    if len(files) > instance.db_max_table_limit - len(db_tables):
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="-1")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"You reached max file limit {instance.db_max_table_limit}")

    total_steps = len(files) + 1  # Total steps for progress tracking
    current_step = 0

    for file in files:
        # Read the CSV file into a DataFrame
        df = await asyncio.to_thread(pd.read_csv, file.file)
        table_name = os.path.splitext(file.filename)[0]  # Extract table name from filename

        # Ensure unique table name by appending a counter if necessary
        table_counter = 1
        original_table_name = table_name
        while table_name in db_tables:
            table_name = f"{original_table_name}_{table_counter}"
            table_counter += 1
        
        db_tables.append(table_name)  # Add the new table name to the list

        # Function to save DataFrame to PostgreSQL
        def run_pandas_to_postgresql(df, table_name, db_url):
            engine = create_engine(db_url)
            with engine.connect() as connection:
                df.to_sql(table_name, con=connection, index=False, if_exists="replace")

        # Save the DataFrame to the temporary database
        await asyncio.to_thread(run_pandas_to_postgresql, df=df, table_name=table_name, db_url=sync_temp_db_url)

        # Update progress after each file upload
        current_step += 1
        progress = int((current_step / total_steps) * 100)
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value=str(progress))

    # Final progress update to 100%
    await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="100")
    
    return {"informationMessage": "CSV files uploaded and converted to database successfully."}

@router.put(instance.upload_pdf_end_point, response_model=InformationResponse)
async def uploadPDF(files: List[UploadFile] = File(...), session: tuple = Depends(instance.redis_tool.getSession)):
    """
    @brief Uploads PDF files and converts them to a vector store.

    This endpoint accepts multiple PDF files, processes them, and stores the
    resulting vectors in a FAISS vector store, tracking progress in the session.

    @param files List of uploaded PDF files.
    @param session The session data dependency for validation.
    @return Information message indicating successful upload.

    @exception HTTPException If the maximum file limit is exceeded or if an error occurs during processing.
    """
    session_id, _ = session
    vector_store_path = f"./.vector_stores/{session_id}"
    documents_dir = os.path.join(vector_store_path, "documents")
    faiss_dir = os.path.join(vector_store_path, "faiss")
    
    await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="0")
    
    try:
        # Load existing FAISS vector store if it exists
        if os.path.exists(faiss_dir):
            vector_store = FAISS.load_local(
                faiss_dir, instance.embedding, allow_dangerous_deserialization=True
            )
        else:
            # Create necessary directories if not already present
            os.makedirs(vector_store_path, exist_ok=True)
            os.makedirs(documents_dir, exist_ok=True)
            vector_store = None

        # Check for existing files in the documents directory
        existing_files = [
            f for f in os.listdir(documents_dir)
            if os.path.isfile(os.path.join(documents_dir, f))
        ]
        existing_file_count = len(existing_files)

        new_file_count = len(files)

        # Validate the total number of files
        if existing_file_count + new_file_count > instance.max_file_limit:
            await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="-1")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You reached the maximum file limit of {instance.max_file_limit}."
            )

        total_steps = new_file_count * 2 + 1  # Total steps for progress tracking
        current_step = 0

        for file in files:
            parsed_file_name = os.path.splitext(file.filename)[0]
            existing_file_list = [
                os.path.splitext(f)[0] for f in os.listdir(documents_dir)
                if os.path.isfile(os.path.join(documents_dir, f))
            ]

            # Ensure unique file name by appending a counter if necessary
            file_name_counter = 1
            original_parsed_file_name = parsed_file_name

            while parsed_file_name in existing_file_list:
                parsed_file_name = f"{original_parsed_file_name}_{file_name_counter}"
                file_name_counter += 1

            parsed_file_name += ".pdf"  # Ensure the file has a .pdf extension
            file_path = os.path.join(documents_dir, parsed_file_name)

            # Save the uploaded PDF file to the documents directory
            async with aiofiles.open(file_path, "wb") as temp_file:
                await temp_file.write(await file.read())

            # Update progress after saving the file
            current_step += 1
            progress = int((current_step / total_steps) * 100)
            await instance.redis_tool.updateSession(session_id=session_id, key="progress", value=str(progress))

            # Load and process the PDF file
            pdf_loader = PyPDFLoader(file_path)
            documents = await pdf_loader.aload()

            # Add metadata to each document
            for doc in documents:
                doc.metadata['filename'] = parsed_file_name

            # Split documents into smaller chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", " "]
            )
            
            split_documents = await text_splitter.atransform_documents(documents)

            # Add documents to the vector store
            if vector_store is None:
                vector_store = await FAISS.afrom_documents(split_documents, instance.embedding)
            else:
                await vector_store.aadd_documents(split_documents)

            # Update progress after processing the documents
            current_step += 1
            progress = int((current_step / total_steps) * 100)
            await instance.redis_tool.updateSession(session_id=session_id, key="progress", value=str(progress))

        # Save the vector store locally
        vector_store.save_local(faiss_dir)
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="100")
    except HTTPException as e:
        raise e
    except Exception as e:
        # Clean up in case of an error
        shutil.rmtree(path=vector_store_path, ignore_errors=True)
        await instance.redis_tool.updateSession(session_id=session_id, key="progress", value="-1")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to convert PDF file. Error: {str(e)}"
        )

    # Update session with the vector store path
    await instance.redis_tool.updateSession(session_id=session_id, key="vector_store_path", value=vector_store_path)
    return {"informationMessage": "PDF files uploaded and converted to database successfully."}