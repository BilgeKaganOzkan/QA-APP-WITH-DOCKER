import pytest
from unittest.mock import AsyncMock, Mock, patch
from delete_fixtures import FAKE_SESSION_ID, FAKE_VECTOR_STORE_PATH
from lib.routers.delete import _deleteVectorStore

@pytest.mark.asyncio
@patch('lib.routers.delete.shutil.rmtree', new_callable=Mock)
@patch('lib.routers.delete.asyncio', new_callable=AsyncMock)
@patch('lib.routers.delete.os.path.isdir', return_value=True)
async def test_delete_delete_vector_store_success_path_is_dir(mock_os_isdir, mock_aio, mock_rmtree):
    """
    Test _deleteVectorStore when the vector store path is a directory.
    - Confirms that the function:
        - Checks the path is a directory.
        - Removes the directory asynchronously using `shutil.rmtree`.
    """
    # Set up asyncio's `to_thread` method for simulating async call to `shutil.rmtree`
    mock_aio.to_thread = AsyncMock()

    # Mock session with a vector store directory path
    session = (FAKE_SESSION_ID, {'vector_store_path': FAKE_VECTOR_STORE_PATH})

    # Execute the function
    result = await _deleteVectorStore(session=session)

    # Assertions
    assert result == True
    mock_os_isdir.assert_called_once_with(FAKE_VECTOR_STORE_PATH)
    mock_aio.to_thread.assert_called_once_with(mock_rmtree, path=FAKE_VECTOR_STORE_PATH, ignore_errors=True)

@pytest.mark.asyncio
@patch('lib.routers.delete.os.remove', new_callable=Mock)
@patch('lib.routers.delete.asyncio', new_callable=AsyncMock)
@patch('lib.routers.delete.os.path.isdir', return_value=False)
async def test_delete_delete_vector_store_success_path_is_not_dir(mock_os_isdir, mock_aio, mock_os_remove):
    """
    Test _deleteVectorStore when the vector store path is a file.
    - Confirms that the function:
        - Checks the path is not a directory.
        - Deletes the file asynchronously using `os.remove`.
    """
    # Set up asyncio's `to_thread` method for simulating async call to `os.remove`
    mock_aio.to_thread = AsyncMock()

    # Mock session with a vector store file path
    session = (FAKE_SESSION_ID, {'vector_store_path': FAKE_VECTOR_STORE_PATH})

    # Execute the function
    result = await _deleteVectorStore(session=session)

    # Assertions
    assert result == True
    mock_os_isdir.assert_called_once_with(FAKE_VECTOR_STORE_PATH)
    mock_aio.to_thread.assert_called_once_with(mock_os_remove, FAKE_VECTOR_STORE_PATH)

@pytest.mark.asyncio
async def test_delete_delete_vector_store_success_path_not_exist():
    """
    Test _deleteVectorStore when the vector store path does not exist.
    - Confirms that the function:
        - Returns True without attempting any file or directory operations.
    """
    # Mock session with an empty vector store path
    session = (FAKE_SESSION_ID, {'vector_store_path': ''})

    # Execute the function
    result = await _deleteVectorStore(session=session)

    # Assertions
    assert result == True