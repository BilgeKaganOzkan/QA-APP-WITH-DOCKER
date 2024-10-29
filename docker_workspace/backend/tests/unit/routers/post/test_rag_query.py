import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from post_fixtures import fixture_test_app, patched_post_module, FAKE_SESSION_ID, FAKE_VECTOR_STORE_PATH, FAKE_URL

@pytest.mark.asyncio
async def test_post_rag_query_success(patched_post_module, fixture_test_app):
    """Test case for a successful RAG query with valid session and vector store path."""
    # Mock memory retrieval and session timeout reset
    patched_post_module.instance.memory.getMemory = AsyncMock(return_value=[])
    patched_post_module.instance.redis_tool.resetSessionTimeout = AsyncMock()

    # Mock session retrieval with a valid vector store path
    async def mock_getTrueRAGSession():
        mock_getTrueRAGSession.call_count += 1
        yield (FAKE_SESSION_ID, {'vector_store_path': FAKE_VECTOR_STORE_PATH})

    mock_getTrueRAGSession.call_count = 0
    fixture_test_app.dependency_overrides[patched_post_module.instance.redis_tool.getSession] = mock_getTrueRAGSession

    # Define payload for RAG query
    payload = {'humanMessage': 'Give me all file names'}

    # Send request to RAG query endpoint
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.rag_query_end_point, json=payload)

    # Assertions to verify successful query response and correct calls to mocks
    assert response.status_code == 200
    assert response.json()['aiMessage'] == 'Mock response'
    assert mock_getTrueRAGSession.call_count == 1, f"mock_getSession was called {mock_getTrueRAGSession.call_count} times"
    patched_post_module.instance.memory.getMemory.assert_called_once_with(session_id=FAKE_SESSION_ID)
    patched_post_module.mock_RagQueryAgent.assert_called_once_with(
        llm=patched_post_module.instance.llm,
        memory=patched_post_module.instance.memory.getMemory.return_value,
        vector_store_path=FAKE_VECTOR_STORE_PATH,
        embeddings=patched_post_module.instance.embedding,
        max_iteration=patched_post_module.instance.llm_max_iteration
    )
    patched_post_module.mock_RagQueryAgent.return_value.execute.assert_called_once_with('Give me all file names')
    patched_post_module.instance.redis_tool.resetSessionTimeout.assert_called_once_with(session_id=FAKE_SESSION_ID)

@pytest.mark.asyncio
async def test_post_rag_query_failure_no_database(patched_post_module, fixture_test_app):
    """Test case for RAG query failure when there is no database associated with the session."""
    # Mock memory retrieval and session timeout reset
    patched_post_module.instance.memory.getMemory = AsyncMock(return_value='mock_session_memory')
    patched_post_module.instance.redis_tool.resetSessionTimeout = AsyncMock()

    # Mock session retrieval with an empty vector store path
    async def mock_getFalseRAGSession():
        mock_getFalseRAGSession.call_count += 1
        yield (FAKE_SESSION_ID, {'vector_store_path': ''})

    mock_getFalseRAGSession.call_count = 0
    fixture_test_app.dependency_overrides[patched_post_module.instance.redis_tool.getSession] = mock_getFalseRAGSession

    # Define payload for RAG query
    payload = {'humanMessage': 'Give me all the file names'}

    # Send request to RAG query endpoint
    async with AsyncClient(transport=ASGITransport(app=fixture_test_app), base_url=FAKE_URL) as client:
        response = await client.post(patched_post_module.instance.rag_query_end_point, json=payload)

    # Assertions to verify failure response due to missing database and no calls to RAG query agent
    assert response.status_code == 400
    assert response.json()["detail"] == 'No database associated with the session.'
    assert mock_getFalseRAGSession.call_count == 1, f"mock_getSession was called {mock_getFalseRAGSession.call_count} times"
    patched_post_module.instance.memory.getMemory.assert_not_called()
    patched_post_module.mock_RagQueryAgent.assert_not_called()
    patched_post_module.mock_RagQueryAgent.return_value.execute.assert_not_called()
    patched_post_module.instance.redis_tool.resetSessionTimeout.assert_not_called()