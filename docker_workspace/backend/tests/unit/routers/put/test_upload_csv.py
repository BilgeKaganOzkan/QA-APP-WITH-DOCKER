import pytest, io, pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock, call
from httpx import AsyncClient, ASGITransport
from fastapi import Depends
from put_fixture import fixture_test_app, patched_put_module, FAKE_URL

@pytest.mark.asyncio
async def test_upload_csv_success(patched_put_module, fixture_test_app):
    """
    Test to verify the successful upload and processing of CSV files.
    Ensures files are processed, converted to database tables, and session progress is updated.
    """
    fixture_test_app.dependency_overrides = {}
    session_id = "test-session-id"
    temp_db_name = "temporary_database_test_session"
    sync_temp_db_url = f"{patched_put_module.instance.sync_database_url}/{temp_db_name}"

    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Mock session dependency to return a specific session ID and vector store path
    async def override_getSession():
        return "test-session-id", {'vector_store_path': "fake_path"}

    # Mock temporary database creation
    async def override_createTempDatabase(session: tuple = Depends(override_getSession)):
        temp_db_name = "temporary_database_test_session"
        sync_temp_db_url = f"{patched_put_module.instance.sync_database_url}/{temp_db_name}"
        return sync_temp_db_url, []

    from lib.routers.put import _createTempDatabase

    fixture_test_app.dependency_overrides[_createTempDatabase] = override_createTempDatabase
    fixture_test_app.dependency_overrides[patched_put_module.instance.redis_tool.getSession] = override_getSession

    with patch('lib.routers.put.create_engine') as mock_create_engine:
        # Mock database connection and table creation process
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        # Mock reading CSV and converting it to SQL
        with patch('lib.routers.put.pd.read_csv', return_value=pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})):
            with patch.object(pd.DataFrame, 'to_sql', new=MagicMock()) as mock_to_sql:
                files = [
                    ("files", ("test1.csv", io.BytesIO(b"col1,col2\n1,3\n2,4"), "text/csv")),
                    ("files", ("test2.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                ]

                # Send the request
                async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
                    response = await client.put(patched_put_module.instance.upload_csv_end_point, files=files)

    # Assert that the response is successful and contains the expected message
    assert response.status_code == 200, response.json()
    assert response.json() == {"informationMessage": "CSV files uploaded and converted to database successfully."}

    # Verify progress updates throughout the upload process
    expected_calls = [
        call(session_id=session_id, key="progress", value="0"),
        call(session_id=session_id, key="progress", value="33"),
        call(session_id=session_id, key="progress", value="66"),
        call(session_id=session_id, key="progress", value="100"),
    ]
    assert patched_put_module.instance.redis_tool.updateSession.await_count == 4
    patched_put_module.instance.redis_tool.updateSession.assert_has_awaits(expected_calls, any_order=False)

    # Check that database engine is created and tables are created as expected
    assert mock_create_engine.call_count == 2
    mock_create_engine.assert_called_with(sync_temp_db_url)
    assert mock_to_sql.call_count == 2
    mock_to_sql.assert_any_call('test1', con=mock_connection, index=False, if_exists="replace")
    mock_to_sql.assert_any_call('test2', con=mock_connection, index=False, if_exists="replace")

@pytest.mark.asyncio
async def test_upload_csv_failure_max_file_limit_exceeded(patched_put_module, fixture_test_app):
    """
    Test to verify behavior when the number of uploaded CSV files exceeds the maximum limit.
    Ensures that an error is raised and progress is updated to reflect failure.
    """
    session_id = "test-session-id"
    db_tables = []
    max_table_limit = 5

    patched_put_module.instance.db_max_table_limit = max_table_limit
    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Mock session and database dependencies
    async def override_getSession():
        return "test-session-id", {'vector_store_path': "fake_path"}

    async def override_createTempDatabase(session: tuple = Depends(override_getSession)):
        temp_db_name = "temporary_database_test_session"
        sync_temp_db_url = f"{patched_put_module.instance.sync_database_url}/{temp_db_name}"
        return sync_temp_db_url, db_tables

    from lib.routers.put import _createTempDatabase

    fixture_test_app.dependency_overrides[_createTempDatabase] = override_createTempDatabase
    fixture_test_app.dependency_overrides[patched_put_module.instance.redis_tool.getSession] = override_getSession

    # Attempt to upload more files than the limit allows
    with patch('lib.routers.put.create_engine') as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with patch('lib.routers.put.pd.read_csv', return_value=pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})):
            with patch.object(pd.DataFrame, 'to_sql', new=MagicMock()) as mock_to_sql:
                files = [
                    ("files", ("test1.csv", io.BytesIO(b"col1,col2\n1,3\n2,4"), "text/csv")),
                    ("files", ("test2.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                    ("files", ("test3.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                    ("files", ("test4.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                    ("files", ("test5.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                    ("files", ("test6.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                ]

                async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
                    response = await client.put(patched_put_module.instance.upload_csv_end_point, files=files)

    # Assert that the response contains the expected error message
    assert response.status_code == 400
    assert response.json()['detail'] == f"You reached max file limit {max_table_limit}"

    # Verify that progress was set to reflect the failure state
    patched_put_module.instance.redis_tool.updateSession.assert_any_await(
        session_id=session_id, key="progress", value="-1"
    )

@pytest.mark.asyncio
async def test_upload_csv_failure_max_file_limit_exceeded_with_before_uploaded_file(patched_put_module, fixture_test_app):
    """
    Test to verify behavior when the number of newly uploaded files plus existing tables exceeds the max table limit.
    Ensures that an error is raised without processing the files.
    """
    session_id = "test-session-id"
    db_tables = ['table1', 'table2']
    max_table_limit = 5

    patched_put_module.instance.db_max_table_limit = max_table_limit
    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Mock session and database dependencies
    async def override_getSession():
        return "test-session-id", {'vector_store_path': "fake_path"}

    async def override_createTempDatabase(session: tuple = Depends(override_getSession)):
        temp_db_name = "temporary_database_test_session"
        sync_temp_db_url = f"{patched_put_module.instance.sync_database_url}/{temp_db_name}"
        return sync_temp_db_url, db_tables

    from lib.routers.put import _createTempDatabase

    fixture_test_app.dependency_overrides[_createTempDatabase] = override_createTempDatabase
    fixture_test_app.dependency_overrides[patched_put_module.instance.redis_tool.getSession] = override_getSession

    # Attempt to upload files such that total tables would exceed the limit
    with patch('lib.routers.put.create_engine') as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection

        with patch('lib.routers.put.pd.read_csv', return_value=pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})):
            with patch.object(pd.DataFrame, 'to_sql', new=MagicMock()) as mock_to_sql:
                files = [
                    ("files", ("test1.csv", io.BytesIO(b"col1,col2\n1,3\n2,4"), "text/csv")),
                    ("files", ("test2.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                    ("files", ("test3.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                    ("files", ("test4.csv", io.BytesIO(b"col1,col2\n5,6\n7,8"), "text/csv")),
                ]

                async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
                    response = await client.put(patched_put_module.instance.upload_csv_end_point, files=files)

    # Assert that the response contains the expected error message
    assert response.status_code == 400
    assert response.json()['detail'] == f"You reached max file limit {max_table_limit}"

    # Verify that progress was set to reflect the failure state
    patched_put_module.instance.redis_tool.updateSession.assert_any_await(
        session_id=session_id, key="progress", value="-1"
    )