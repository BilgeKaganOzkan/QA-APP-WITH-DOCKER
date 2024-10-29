import pytest, time, os, shutil
from httpx import AsyncClient, ASGITransport
from lib.routers.post import instance, router
from lib.database.config.configuration import getAsyncUserDB, getAsyncDB
from sqlalchemy import text
from io import BytesIO
from reportlab.pdfgen import canvas
from tests.integration.fixtures import *

@pytest.mark.asyncio
async def test_signup_no_exist_user_add(setup_and_tear_down, event_loop):
    """
    Tests the signup functionality for a new user who does not already exist in the database.
    
    **Purpose**: Ensure a new user can successfully sign up, be added to the database, and confirm their presence afterward.

    **Steps**:
    1. **Database Check**: Check if the test user already exists in the database; if they do, delete them to start with a clean state.
    2. **Signup Request**: Send a signup request with the test email and password to the signup endpoint.
    3. **Response Verification**: Confirm the response has a 201 status and a success message indicating the user was registered.
    4. **Database Verification**: Verify that the user is now present in the database.
    5. **Cleanup**: Remove the test user from the database after the test to maintain clean state for subsequent tests.

    **Expected Outcome**: 
    - Signup should succeed, returning a confirmation message in the response.
    - The user should be added to the database and confirmed to exist.
    """
    # Step 1: Check if the user already exists in the database; if so, delete them for a clean test setup
    async for db in getAsyncUserDB():
        await db.execute(terminate_user_query)
        result = await db.execute(text(f'SELECT * FROM "User" WHERE "email"=\'{FAKE_USER_EMAIL}\''))
        user = result.fetchone()
        if user:
            await db.execute(text(f'DELETE FROM "User" WHERE "email"=\'{FAKE_USER_EMAIL}\''))
            await db.commit()

    # Step 2: Send the signup request to register the new user
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        response = await client.post(
            instance.signup_end_point,
            json={"email": FAKE_USER_EMAIL, "password": FAKE_USER_PASSWORD}
        )
        # Step 3: Check that the response status is 201 and the user is registered successfully
        assert response.status_code == 201, "Signup failed when it should succeed."
        assert response.json() == {"informationMessage": "User successfully registered"}

    # Step 4: Verify the user’s presence in the database after signup
    async for db in getAsyncUserDB():
        await db.execute(terminate_user_query)
        result = await db.execute(text(f'SELECT * FROM "User" WHERE "email"=\'{FAKE_USER_EMAIL}\''))
        user = result.fetchone()
        assert user, "User was not found in the database after signup."

        # Step 5: Clean up by deleting the test user from the database
        await db.execute(text(f'DELETE FROM "User" WHERE "email"=\'{FAKE_USER_EMAIL}\''))
        await db.commit()

@pytest.mark.asyncio
async def test_signup_exist_user_add(setup_and_tear_down, event_loop):
    """
    Tests the signup functionality for a user who already exists in the database.
    
    **Purpose**: Confirm that signing up with an existing email results in an error, preventing duplicate accounts.

    **Steps**:
    1. Attempt to sign up with an email already registered in the system.
    2. Capture and confirm the error response contains the expected error message.

    **Expected Outcome**:
    - Signup should fail with a 400 status and a message stating "E-mail already registered."
    """
    try:
        # Step 1: Attempt to sign up with an email that already exists
        async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
            response = await client.post(
                instance.signup_end_point,
                json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
            )
    except Exception as e:
        # Step 2: Ensure the error message states the email is already registered
        assert e.args[0] == "Database error: 400: E-mail already registered"

@pytest.mark.asyncio
async def test_login_user_exist(setup_and_tear_down, event_loop):
    """
    Tests the login functionality for a valid user with correct credentials.
    
    **Purpose**: Ensure that a user with valid credentials can log in successfully and receive a session ID.

    **Steps**:
    1. Send a login request with the correct email and password.
    2. Verify the login succeeds with a 200 status code and a success message.
    3. Confirm a session ID is returned in the response cookies.

    **Expected Outcome**:
    - The login should succeed, and a session ID should be issued in the response.
    """
    # Step 1: Send login request with valid email and password
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        response = await client.post(
            instance.login_end_point,
            json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        )

    # Step 2: Verify response status is 200, confirming successful login
    assert response.status_code == 200, "Expected login to succeed, but it failed."
    assert response.json() == {"informationMessage": "Login successful"}

    # Step 3: Confirm session ID is present in cookies, indicating session creation
    assert "session_id" in response.cookies, "Session ID cookie not set in response."

@pytest.mark.asyncio
async def test_login_wrong_password(setup_and_tear_down, event_loop):
    """
    Tests the login functionality with an incorrect password for an existing user.
    
    **Purpose**: Ensure an error is returned when incorrect credentials are provided, preventing unauthorized access.

    **Steps**:
    1. Attempt to log in with the correct email but an incorrect password.
    2. Capture and verify the error response indicates incorrect credentials.

    **Expected Outcome**:
    - Login should fail with a 401 error.
    - The response should indicate "Incorrect email or password."
    """
    try:
        # Step 1: Send login request with valid email but incorrect password
        async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
            response = await client.post(
                instance.login_end_point,
                json={"email": TEST_USER_EMAIL, "password": TEST_USER_WRONG_PASSWORD}
            )
    except Exception as e:
        # Step 2: Confirm the error message states incorrect email or password
        assert e.args[0] == "Database error: 401: Incorrect email or password"

@pytest.mark.asyncio
async def test_sql_query(setup_and_tear_down, event_loop):
    """
    Tests SQL query functionality in a session-specific temporary database.
    
    **Purpose**: Verify SQL queries can be executed within a session-bound database, returning expected data.

    **Steps**:
    1. **Session Setup**: Create a Redis session and set the database path for the session.
    2. **Database Creation**: Set up a temporary database with sample data.
    3. **Query Execution**: Execute a SQL query and retrieve data from the database.
    4. **Validation**: Ensure the response includes the expected sample data.
    5. **Cleanup**: Delete the temporary database and session data.

    **Expected Outcome**:
    - SQL query should execute successfully and return the expected data.
    """
    # Step 1: Set up Redis session and assign temporary database path
    session_key = f"session:{FAKE_SESSION_ID}"
    await instance.redis_tool.redis.hset(session_key, mapping={"created_at": str(time.time()), "data": "{}"})
    await instance.redis_tool.updateSession(session_id=FAKE_SESSION_ID, key="temp_database_path", value=TEST_DB_NAME)

    # Step 2: Create a temporary database and insert sample data
    async for db in getAsyncDB("postgres"):
        await db.execute(terminate_query)
        await db.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
        await db.execute(text(f"CREATE DATABASE {TEST_DB_NAME}"))

    async for db in getAsyncDB(TEST_DB_NAME):
        await db.execute(text("CREATE TABLE test_table (id SERIAL PRIMARY KEY, name VARCHAR(50), age INT)"))
        await db.execute(text("INSERT INTO test_table (name, age) VALUES ('Alice', 30), ('Bob', 25)"))
        await db.commit()

    # Step 3: Execute SQL query through the API and retrieve data
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        client.cookies.set("session_id", FAKE_SESSION_ID)
        response = await client.post(
            instance.sql_query_end_point,
            json={"humanMessage": "Give me all names from the database."}
        )

    # Step 4: Validate the response contains expected data
    assert response.status_code == 200, "Expected SQL query to succeed, but it failed."
    result = response.json()
    assert "aiMessage" in result, "SQL query did not return aiMessage."
    assert "Alice" in result["aiMessage"] and "Bob" in result["aiMessage"], "Expected data not found in SQL query response."

    # Step 5: Cleanup - Delete the temporary database and Redis session
    async for db in getAsyncDB("postgres"):
        await db.execute(terminate_query)
        await db.execute(text(f"DROP DATABASE IF EXISTS {TEST_DB_NAME}"))
    await instance.redis_tool.redis.delete(f"session:{FAKE_SESSION_ID}")

@pytest.mark.asyncio
async def test_upload_pdf_and_rag_query(setup_and_tear_down, event_loop):
    """
    Tests the upload of a PDF, vector storage creation, and querying via a RAG endpoint.
    
    **Purpose**: Verify that a PDF can be uploaded, vectorized, stored, and queried with RAG functionality.

    **Steps**:
    1. **Session Setup**: Create a Redis session and set the vector storage path.
    2. **PDF Creation and Upload**: Generate a sample PDF and upload it to the server.
    3. **Progress Check**: Confirm the upload is successful, reaching 100% progress.
    4. **RAG Query**: Execute a RAG query to retrieve content from the PDF.
    5. **Response Validation**: Confirm the RAG query response meets expectations.
    6. **Cleanup**: Remove the vector storage directory and Redis session after the test.

    **Expected Outcome**:
    - The PDF upload and vectorization should complete with progress reaching 100%.
    - The RAG query should return a relevant response based on PDF content.
    """

    vector_store_path = f'./.vector_stores/{FAKE_SESSION_ID}'
    if os.path.exists(vector_store_path):
        shutil.rmtree(vector_store_path)
    
    session_key = f"session:{FAKE_SESSION_ID}"
    await instance.redis_tool.redis.hset(session_key, mapping={"created_at": str(time.time()), "data": "{}"})
    await instance.redis_tool.updateSession(session_id=FAKE_SESSION_ID, key="vector_store_path", value=vector_store_path)

    # Step 2: Generate and upload a sample PDF file
    pdf_content = BytesIO()
    c = canvas.Canvas(pdf_content)
    c.drawString(100, 750, "This file about a sample PDF for testing.")
    c.save()
    pdf_content.seek(0)
    pdf_content.name = "test.pdf"

    from lib.routers.put import router as put_router
    async with AsyncClient(transport=ASGITransport(app=put_router), base_url=FAKE_URL) as client:
        client.cookies.set("session_id", FAKE_SESSION_ID)
        response = await client.put(
            instance.upload_pdf_end_point,
            files={"files": ("test.pdf", pdf_content, "application/pdf")}
        )

    assert response.status_code == 200, "Failed to upload PDF file"
    
    # Step 3: Verify that upload progress reaches 100%
    session_data = await instance.redis_tool.redis.hgetall(session_key)
    progress = session_data.get("progress")
    assert progress == "100", "Progress did not reach 100% after PDF upload"

    redis_vector_store_path = session_data.get("vector_store_path")
    assert vector_store_path, "Vector store path not set in Redis session after PDF upload"
    assert redis_vector_store_path == vector_store_path
    assert os.path.exists(vector_store_path), "Vector store path does not exist"

    # Step 4: Execute a RAG query to retrieve PDF content
    async with AsyncClient(transport=ASGITransport(app=router), base_url=FAKE_URL) as client:
        client.cookies.set("session_id", FAKE_SESSION_ID)
        response = await client.post(
            instance.rag_query_end_point,
            json={"humanMessage": "What is in the PDF document?"}
        )

    # Step 5: Verify the response contains expected RAG query result
    assert response.status_code == 200, "RAG query failed when it should succeed."
    result = response.json()
    assert "aiMessage" in result, "RAG query did not return aiMessage."
    assert result != None

    # Step 6: Cleanup - Remove vector storage and delete Redis session
    if os.path.exists(vector_store_path):
        shutil.rmtree(vector_store_path)
    await instance.redis_tool.redis.delete(session_key)