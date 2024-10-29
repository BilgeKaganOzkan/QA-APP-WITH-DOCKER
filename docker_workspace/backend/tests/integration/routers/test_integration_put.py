from httpx import AsyncClient, ASGITransport
from io import BytesIO
from lib.routers.put import router, instance
from lib.database.config.configuration import getAsyncDB
from sqlalchemy import text
from reportlab.pdfgen import canvas
from tests.integration.fixtures import *
import pytest, time, os, shutil

# Constants for test session and URL
FAKE_SESSION_ID = "test_session"
FAKE_URL = "http://testserver"

@pytest.mark.asyncio
async def test_upload_csv(setup_and_tear_down, event_loop):
    """
    Integration Test: Verifies CSV upload functionality by checking file upload, conversion to database tables, 
    and Redis progress updates.

    **Purpose**: Ensure that a CSV file can be uploaded, converted into a table in a temporary database, 
    and that the upload progress is correctly tracked in Redis.

    **Steps**:
    1. **Database Setup**: Ensure no pre-existing test database remains; then set up a new temporary database.
    2. **Redis Session Setup**: Initialize a Redis session with test data for progress tracking.
    3. **CSV File Preparation**: Create a sample CSV file for uploading.
    4. **File Upload**: Send a PUT request to upload the CSV file.
    5. **Progress Verification**: Check Redis to confirm progress reaches 100% upon upload completion.
    6. **Database Verification**: Verify the creation of the table in the temporary database with expected rows.
    7. **Cleanup**: Delete the temporary database and Redis session data post-test.

    **Expected Outcome**:
    - CSV file is uploaded and converted into a table in the temporary database.
    - Redis progress value reaches 100%.
    """

    # Step 1: Prepare a temporary database for testing
    async for db in getAsyncDB("postgres"):
        # Drop existing test database to avoid conflicts, then create a new one
        await db.execute(terminate_query)
        await db.execute(text(f"DROP DATABASE IF EXISTS {temp_db_name}"))

    # Step 2: Set up Redis session key for tracking progress
    session_key = f"session:{FAKE_SESSION_ID}"
    await instance.redis_tool.redis.hset(session_key, mapping={"created_at": str(time.time()), "data": "{}"})

    # Step 3: Create in-memory CSV data for testing
    csv_content = "name,age\nAlice,30\nBob,25"
    csv_file = BytesIO(csv_content.encode())
    csv_file.name = "test.csv"

    # Step 4: Send PUT request to upload CSV file
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        client.cookies.set("session_id", FAKE_SESSION_ID)
        response = await client.put(instance.upload_csv_end_point, 
                                    files={"files": ("test.csv", csv_file, "text/csv")},
                                    headers={"session-id": FAKE_SESSION_ID})

    # Step 5: Check the response and verify progress reaches 100%
    assert response.status_code == 200, "Failed to upload CSV file"
    session_data = await instance.redis_tool.redis.hgetall(session_key)
    progress = session_data.get("progress")
    assert progress == "100", "Progress did not reach 100% after CSV upload"

    # Step 6: Verify table creation in the temporary database with correct row count
    async for db in getAsyncDB(temp_db_name):
        result = await db.execute(text("SELECT * FROM test"))
        rows = result.fetchall()
        assert len(rows) == 2, "Table in temp database did not have expected row count"

    # Step 7: Clean up the temporary database and Redis session data
    async for db in getAsyncDB("postgres"):
        await db.execute(terminate_query)
        await db.execute(text(f"DROP DATABASE IF EXISTS {temp_db_name}"))

    await instance.redis_tool.redis.delete(session_key)

@pytest.mark.asyncio
async def test_upload_pdf(setup_and_tear_down, event_loop):
    """
    Integration Test: Verifies PDF upload functionality by checking file upload, vector storage creation, 
    and Redis session tracking for progress.

    **Purpose**: Ensure that a PDF file can be uploaded, processed into a vector store for RAG queries, 
    and progress is updated in Redis.

    **Steps**:
    1. **Redis Session Setup**: Create a Redis session and set up vector storage path.
    2. **PDF File Preparation**: Create a sample PDF file in memory.
    3. **File Upload**: Send a PUT request to upload the PDF file.
    4. **Progress Verification**: Check Redis to confirm progress reaches 100% after processing.
    5. **Vector Store Path Verification**: Confirm the vector store path is set in Redis and the directory exists.
    6. **Cleanup**: Remove the Redis session and vector store directory.

    **Expected Outcome**:
    - PDF file is successfully uploaded and processed, resulting in a vector store directory.
    - Redis progress value reaches 100%, and the vector store path is properly set.
    """

    # Step 1: Set up Redis session and vector store path for the test session
    vector_store_path = f'./.vector_stores/{FAKE_SESSION_ID}'
    if os.path.exists(vector_store_path):
        shutil.rmtree(vector_store_path)  # Remove any previous test directories

    session_key = f"session:{FAKE_SESSION_ID}"
    await instance.redis_tool.redis.hset(session_key, mapping={"created_at": str(time.time()), "data": "{}"})

    # Step 2: Create a sample PDF file as an in-memory byte stream
    pdf_content = BytesIO()
    c = canvas.Canvas(pdf_content)
    c.drawString(100, 750, "This is a sample PDF for testing.")
    c.save()
    pdf_content.seek(0)  # Move to the start of the file
    pdf_content.name = "test.pdf"

    # Step 3: Send PUT request to upload PDF file
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        client.cookies.set("session_id", FAKE_SESSION_ID)
        response = await client.put(instance.upload_pdf_end_point, 
                                    files={"files": ("test.pdf", pdf_content, "application/pdf")},
                                    headers={"session-id": FAKE_SESSION_ID})

    # Step 4: Check the response and verify that progress reaches 100% after processing
    assert response.status_code == 200, "Failed to upload PDF file"
    session_data = await instance.redis_tool.redis.hgetall(session_key)
    progress = session_data.get("progress")
    assert progress == "100", "Progress did not reach 100% after PDF upload"

    # Step 5: Verify that the vector store path is set in Redis and the directory exists
    redis_vector_store_path = session_data.get("vector_store_path")
    assert vector_store_path, "Vector store path not set in Redis session after PDF upload"
    assert redis_vector_store_path == vector_store_path
    assert os.path.exists(vector_store_path), "Vector store path does not exist"

    # Step 6: Clean up Redis session and remove the vector store directory
    if os.path.exists(vector_store_path):
        shutil.rmtree(vector_store_path)
    await instance.redis_tool.redis.delete(session_key)