import io
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock, call
from httpx import AsyncClient, ASGITransport
from put_fixture import patched_put_module, fixture_test_app, FAKE_URL, FAKE_SESSION_ID


@pytest.mark.asyncio
@patch('lib.routers.put.RecursiveCharacterTextSplitter')
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('os.listdir', return_value=['test1.pdf', 'test2.pdf'])
@patch('os.path.isfile', return_value=True)
@patch('lib.routers.put.aiofiles.open', new_callable=MagicMock)
@patch('lib.routers.put.PyPDFLoader')
@patch('lib.routers.put.FAISS')
async def test_upload_pdf_success_with_existing_files(
    mock_faiss, mock_pypdf_loader, mock_aiofiles_open, mock_isfile, mock_listdir, mock_makedirs, mock_exists, mock_recursive_character_text_splitter,
    patched_put_module, fixture_test_app
):
    """
    Test to verify successful upload and processing of PDF files when some documents already exist in the target directory.
    This test checks that existing documents are handled correctly, the appropriate sessions are updated, and the documents are
    correctly processed with the PDF loader and FAISS.
    """
    vector_store_path = f"./.vector_stores/{FAKE_SESSION_ID}"
    documents_dir = os.path.join(vector_store_path, "documents")
    faiss_dir = os.path.join(vector_store_path, "faiss")

    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Mock session dependency
    async def override_getSession():
        return FAKE_SESSION_ID, {'vector_store_path': "_"}

    fixture_test_app.dependency_overrides[patched_put_module.instance.redis_tool.getSession] = override_getSession

    # Setup the async mock for file operations
    mock_file_handle = MagicMock()
    mock_file_handle.write = AsyncMock()
    mock_aiofiles_open.return_value.__aenter__.return_value = mock_file_handle
    mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

    # Setup the PDF loader mock
    mock_document = MagicMock()
    mock_document.metadata = {"filename": "test1.pdf"}
    mock_document.page_content = "Sample PDF content text"
    mock_pypdf_loader_instance = mock_pypdf_loader.return_value
    mock_pypdf_loader_instance.aload = AsyncMock(return_value=[mock_document])

    # Setup FAISS mock
    mock_vector_store = AsyncMock()
    mock_vector_store.aadd_documents = AsyncMock()
    mock_vector_store.save_local = AsyncMock()

    mock_faiss.load_local.return_value = mock_vector_store

    mock_split_documents = AsyncMock()
    mock_text_splitter = AsyncMock()
    mock_text_splitter.atransform_documents = AsyncMock(return_value = mock_split_documents)
    mock_recursive_character_text_splitter.return_value = mock_text_splitter

    # Define the PDF files to be uploaded
    files = [
        ("files", ("test1.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")),
        ("files", ("test2.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")),
    ]

    # Send the request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.put(patched_put_module.instance.upload_pdf_end_point, files=files)

    # Assertions
    assert response.status_code == 200, response.json()
    assert response.json() == {"informationMessage": "PDF files uploaded and converted to database successfully."}

    expected_calls = [
        call(session_id=FAKE_SESSION_ID, key="progress", value="0"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="20"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="40"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="60"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="80"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="100"),
        call(session_id=FAKE_SESSION_ID, key="vector_store_path", value=vector_store_path)
    ]

    assert patched_put_module.instance.redis_tool.updateSession.await_count == 7
    patched_put_module.instance.redis_tool.updateSession.assert_has_awaits(expected_calls, any_order=False)

    mock_recursive_character_text_splitter.assert_called_with(chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", ".", " "])

    # Ensure file operations were called with the correct file paths and contents
    mock_exists.called_once_with(faiss_dir)
    mock_isfile.assert_any_call(os.path.join(documents_dir, "test1.pdf"))
    mock_isfile.assert_any_call(os.path.join(documents_dir, "test2.pdf"))
    # Ensure no directory creation attempts
    mock_makedirs.assert_not_called()

    mock_listdir.assert_called_with(documents_dir)
    mock_aiofiles_open.assert_any_call(os.path.join(documents_dir, "test1_1.pdf"), "wb")
    mock_aiofiles_open.assert_any_call(os.path.join(documents_dir, "test2_1.pdf"), "wb")
    mock_file_handle.write.assert_called_with(b"%PDF-1.4")

    # Verify FAISS operations were called with expected parameters
    mock_faiss.load_local.assert_called_once_with(faiss_dir, patched_put_module.instance.embedding, allow_dangerous_deserialization=True)
    mock_vector_store.aadd_documents.call_count == 2 # Corrected to mock_vector_store

    # Check PDF loader instance call for PDF loading and splitting documents
    assert mock_pypdf_loader_instance.aload.call_count == 2
    mock_pypdf_loader.assert_any_call(os.path.join(documents_dir, "test1_1.pdf"))
    mock_pypdf_loader.assert_any_call(os.path.join(documents_dir, "test2_1.pdf"))


@pytest.mark.asyncio
@patch('lib.routers.put.RecursiveCharacterTextSplitter')
@patch('os.path.exists', return_value=False)
@patch('os.makedirs')
@patch('os.listdir', return_value=[])
@patch('os.path.isfile', return_value=True)
@patch('lib.routers.put.aiofiles.open', new_callable=MagicMock)
@patch('lib.routers.put.PyPDFLoader')
@patch('lib.routers.put.FAISS')
async def test_upload_pdf_success_with_no_existing_files(
    mock_faiss, mock_pypdf_loader, mock_aiofiles_open, mock_isfile, mock_listdir, mock_makedirs, mock_exists, mock_recursive_character_text_splitter,
    patched_put_module, fixture_test_app
):
    """
    Test to verify successful upload and processing of PDF files when no existing documents are found in the directory.
    This test ensures that new directories are created, documents are processed with the PDF loader, and FAISS handles the new embeddings.
    """
    vector_store_path = f"./.vector_stores/{FAKE_SESSION_ID}"
    documents_dir = os.path.join(vector_store_path, "documents")
    faiss_dir = os.path.join(vector_store_path, "faiss")

    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Mock session dependency
    async def override_getSession():
        return FAKE_SESSION_ID, {'vector_store_path': "_"}

    fixture_test_app.dependency_overrides[patched_put_module.instance.redis_tool.getSession] = override_getSession

    # Setup text splitter mocks
    mock_split_documents = AsyncMock()
    mock_text_splitter = AsyncMock()
    mock_text_splitter.atransform_documents = AsyncMock(return_value = mock_split_documents)
    mock_recursive_character_text_splitter.return_value = mock_text_splitter

    # Setup the async mock for file operations
    mock_file_handle = MagicMock()
    mock_file_handle.write = AsyncMock()
    mock_aiofiles_open.return_value.__aenter__.return_value = mock_file_handle
    mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

    # Setup the PDF loader mock
    mock_document = MagicMock()
    mock_document.metadata = {"filename": "test1.pdf"}
    mock_document.page_content = "Sample PDF content text"
    mock_pypdf_loader_instance = mock_pypdf_loader.return_value
    mock_pypdf_loader_instance.aload = AsyncMock(return_value=[mock_document])

    # Setup FAISS mock
    mock_faiss.afrom_documents = AsyncMock()
    mock_faiss.save_local = AsyncMock()

    # Define the PDF files to be uploaded
    files = [
        ("files", ("test1.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")),
        ("files", ("test2.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")),
    ]

    # Send the request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.put(patched_put_module.instance.upload_pdf_end_point, files=files)

    # Assertions
    assert response.status_code == 200, response.json()
    assert response.json() == {"informationMessage": "PDF files uploaded and converted to database successfully."}

    expected_calls = [
        call(session_id=FAKE_SESSION_ID, key="progress", value="0"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="20"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="40"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="60"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="80"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="100"),
        call(session_id=FAKE_SESSION_ID, key="vector_store_path", value=vector_store_path)
    ]

    mock_recursive_character_text_splitter.assert_called_with(chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", ".", " "])

    assert patched_put_module.instance.redis_tool.updateSession.await_count == 7
    patched_put_module.instance.redis_tool.updateSession.assert_has_awaits(expected_calls, any_order=False)

    mock_exists.called_once_with(faiss_dir)
    mock_isfile.assert_not_called()

    mock_listdir.assert_called_with(documents_dir)

    # Ensure important operations were called with correct parameters
    mock_makedirs.assert_any_call(vector_store_path, exist_ok=True)
    mock_makedirs.assert_any_call(documents_dir, exist_ok=True)

    # Ensure file operations were called with the correct file paths and contents
    mock_aiofiles_open.assert_any_call(os.path.join(documents_dir, "test1.pdf"), "wb")
    mock_aiofiles_open.assert_any_call(os.path.join(documents_dir, "test2.pdf"), "wb")
    mock_file_handle.write.assert_called_with(b"%PDF-1.4")

    mock_faiss.afrom_documents.assert_awaited_once_with(mock_split_documents, patched_put_module.instance.embedding)

    # Check PDF loader instance call for PDF loading and splitting documents
    assert mock_pypdf_loader_instance.aload.call_count == 2
    mock_pypdf_loader.assert_any_call(os.path.join(documents_dir, "test1.pdf"))
    mock_pypdf_loader.assert_any_call(os.path.join(documents_dir, "test2.pdf"))


@pytest.mark.asyncio
@patch('lib.routers.put.RecursiveCharacterTextSplitter')
@patch('os.path.exists', return_value=True)
@patch('os.makedirs')
@patch('os.listdir', return_value=['test1.pdf', 'test2.pdf', 'test3.pdf', 'test4.pdf', 'test5.pdf'])
@patch('os.path.isfile', return_value=True)
@patch('lib.routers.put.aiofiles.open', new_callable=MagicMock)
@patch('lib.routers.put.PyPDFLoader')
@patch('lib.routers.put.FAISS')
async def test_upload_pdf_failure_reach_max_file_limit(
    mock_faiss, mock_pypdf_loader, mock_aiofiles_open, mock_isfile, mock_listdir, mock_makedirs, mock_exists, mock_recursive_character_text_splitter,
    patched_put_module, fixture_test_app
):
    """
    Test to verify that the upload process fails when the maximum file limit is reached.
    This test ensures that no additional processing occurs and the session progress is updated accordingly.
    """
    vector_store_path = f"./.vector_stores/{FAKE_SESSION_ID}"
    documents_dir = os.path.join(vector_store_path, "documents")
    faiss_dir = os.path.join(vector_store_path, "faiss")

    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Mock session dependency
    async def override_getSession():
        return FAKE_SESSION_ID, {'vector_store_path': "_"}

    fixture_test_app.dependency_overrides[patched_put_module.instance.redis_tool.getSession] = override_getSession


    mock_split_documents = AsyncMock()
    mock_text_splitter = AsyncMock()
    mock_text_splitter.atransform_documents = AsyncMock(return_value = mock_split_documents)
    mock_recursive_character_text_splitter.return_value = mock_text_splitter

    # Setup the async mock for file operations
    mock_file_handle = MagicMock()
    mock_file_handle.write = AsyncMock()
    mock_aiofiles_open.return_value.__aenter__.return_value = mock_file_handle
    mock_aiofiles_open.return_value.__aexit__.return_value = AsyncMock()

    # Setup the PDF loader mock
    mock_document = MagicMock()
    mock_document.metadata = {"filename": "test1.pdf"}
    mock_document.page_content = "Sample PDF content text"
    mock_pypdf_loader_instance = mock_pypdf_loader.return_value
    mock_pypdf_loader_instance.aload = AsyncMock(return_value=[mock_document])

    # Setup FAISS mock
    mock_faiss.afrom_documents = AsyncMock()  # Ensure aadd_documents is an async mock method
    mock_faiss.save_local = AsyncMock()  # Mock save_local as an async function

    # Define the PDF files to be uploaded
    files = [
        ("files", ("test6.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")),
        ("files", ("test7.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf"))
    ]

    # Send the request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.put(patched_put_module.instance.upload_pdf_end_point, files=files)

    # Assertions
    assert response.status_code == 400, response.json()
    assert response.json()['detail'] == f"You reached the maximum file limit of {patched_put_module.instance.max_file_limit}."

    expected_calls = [
        call(session_id=FAKE_SESSION_ID, key="progress", value="0"),
        call(session_id=FAKE_SESSION_ID, key="progress", value="-1")
    ]

    mock_recursive_character_text_splitter.assert_not_called()

    assert patched_put_module.instance.redis_tool.updateSession.await_count == 2
    patched_put_module.instance.redis_tool.updateSession.assert_has_awaits(expected_calls, any_order=False)

    mock_exists.called_once_with(faiss_dir)
    mock_isfile.assert_any_call(os.path.join(documents_dir, "test1.pdf"))
    mock_isfile.assert_any_call(os.path.join(documents_dir, "test2.pdf"))
    mock_isfile.assert_any_call(os.path.join(documents_dir, "test3.pdf"))
    mock_isfile.assert_any_call(os.path.join(documents_dir, "test4.pdf"))
    mock_isfile.assert_any_call(os.path.join(documents_dir, "test5.pdf"))
    mock_makedirs.assert_not_called()

    mock_listdir.assert_called_with(documents_dir)

    # Ensure file operations were called with the correct file paths and contents
    mock_aiofiles_open.assert_not_called()
    mock_file_handle.write.assert_not_called()

    mock_faiss.afrom_documents.assert_not_called()

    # Check PDF loader instance call for PDF loading and splitting documents
    assert mock_pypdf_loader_instance.aload.call_count == 0
    mock_pypdf_loader.assert_not_called()

@pytest.mark.asyncio
@patch('os.path.exists')
async def test_upload_pdf_failure_unexpected_error(mock_exists, patched_put_module, fixture_test_app):
    """
    Test to verify behavior when an unexpected error occurs during the PDF upload process.
    This test ensures that the error is handled gracefully and an appropriate HTTP error response is returned.
    """
    mock_exists.side_effect = Exception('Test Error')
    patched_put_module.instance.redis_tool.updateSession = AsyncMock()

    # Mock session dependency
    async def override_getSession():
        return FAKE_SESSION_ID, {'vector_store_path': "_"}

    fixture_test_app.dependency_overrides[patched_put_module.instance.redis_tool.getSession] = override_getSession

    # Define the PDF files to be uploaded
    files = [
        ("files", ("test1.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")),
        ("files", ("test2.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf"))
    ]

    # Send the request
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.put(patched_put_module.instance.upload_pdf_end_point, files=files)

    # Assertions
    assert response.status_code == 400, response.json()
    assert response.json()['detail'] == "Failed to convert PDF file. Error: Test Error"