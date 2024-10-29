import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from lib.ai.agents.rag_query_agent import RagQueryAgent

@pytest.fixture
async def mock_rag_agent():
    # Set up a mock RagQueryAgent instance with mocked FAISS vector store, retriever, memory, and embeddings
    with patch("lib.ai.agents.rag_query_agent.FAISS.load_local", new_callable=MagicMock) as mock_faiss_load_local:
        mock_vector_store = MagicMock()
        mock_retriever = MagicMock()
        mock_vector_store.as_retriever.return_value = mock_retriever
        mock_faiss_load_local.return_value = mock_vector_store

        memory_mock = MagicMock()
        llm_mock = AsyncMock()
        embeddings_mock = MagicMock()

        agent = RagQueryAgent(
            llm=llm_mock,
            memory=memory_mock,
            vector_store_path="mock_vector_store",
            embeddings=embeddings_mock,
            max_iteration=5
        )
        return agent

@pytest.mark.asyncio
async def test_rag_agent_query_execution_success(mock_rag_agent):
    """
    Test for successful query execution and retrieving relevant documents.
    Ensures that LLM chain and retriever are called in sequence and return the expected result.
    """
    rag_agent_instance = await mock_rag_agent

    # Mock search responses from the retriever for different documents
    mock_retriever_search = AsyncMock()
    mock_document1 = MagicMock()
    mock_document1.page_content = "Content of file1"
    mock_document2 = MagicMock()
    mock_document2.page_content = "Content of file2"
    mock_retriever_search.side_effect = [
        [mock_document1],
        [mock_document2],
        [mock_document1],
        [mock_document2]
    ]

    # Set up LLM chain responses to simulate different iteration actions
    with patch.object(rag_agent_instance.retriever, 'ainvoke', mock_retriever_search):
        mock_llm_chain = AsyncMock()
        mock_llm_chain.ainvoke.side_effect = [
            "Filter Command: file1.txt",
            "Filter Command: file2.txt",
            "Filter Command: file1.txt",
            "Filter Command: file2.txt",
            "Here is the answer..."
        ]

        # Patch the LLM chain and run execute function
        with patch.object(rag_agent_instance, 'llm_chain', mock_llm_chain):
            user_query = "Find information about file1 and file2"
            result = await rag_agent_instance.execute(user_query)

    # Assert final response is as expected
    assert result == "Here is the answer..."
    assert mock_llm_chain.ainvoke.call_count == 5
    assert mock_retriever_search.call_count == 4

@pytest.mark.asyncio
async def test_rag_agent_execution_failure_chain(mock_rag_agent):
    """
    Test for failure case when an exception is raised in the LLM chain.
    Ensures proper handling of exceptions in query execution.
    """
    rag_agent_instance = await mock_rag_agent
    mock_llm_chain = AsyncMock()
    mock_llm_chain.ainvoke.side_effect = Exception("LLM error")

    # Expecting an exception due to LLM chain error
    with patch.object(rag_agent_instance, 'llm_chain', mock_llm_chain):
        user_query = "Find information about file1 and file2"
        with pytest.raises(Exception) as excinfo:
            await rag_agent_instance.execute(user_query)

    # Check exception details
    assert "LLM error" in str(excinfo.value)
    mock_llm_chain.ainvoke.assert_called_once()

@pytest.mark.asyncio
async def test_rag_agent_max_iteration_success(mock_rag_agent):
    """
    Test to check behavior when max iteration is reached.
    Ensures the agent stops after reaching the max iteration limit without a final answer.
    """
    rag_agent_instance = await mock_rag_agent

    # Mock retriever's response for each iteration
    mock_retriever_search = AsyncMock()
    mock_retriever_search.side_effect = [
        [MagicMock(page_content="Content of file1")],
        [MagicMock(page_content="Content of file2")],
        [MagicMock(page_content="Content of file1")],
        [MagicMock(page_content="Content of file2")],
        [MagicMock(page_content="Content of file1")]
    ]

    # Set up LLM chain response to repeat command generation without reaching final answer
    with patch.object(rag_agent_instance.retriever, 'ainvoke', mock_retriever_search):
        mock_llm_chain = AsyncMock()
        mock_llm_chain.ainvoke.side_effect = ["Filter Command: file1.txt"] * 5

        with patch.object(rag_agent_instance, 'llm_chain', mock_llm_chain):
            user_query = "Find information about file1 and file2"
            result = await rag_agent_instance.execute(user_query)

    # Validate the result matches expected response for max iteration reached
    assert result == "I couldn't generate an answer according to your question. Please change your question and try again."
    assert mock_llm_chain.ainvoke.call_count == 5
    assert mock_retriever_search.call_count == 5

@pytest.mark.asyncio
async def test_rag_agent_save_history_to_memory_success(mock_rag_agent):
    """
    Test to verify if conversation history is saved successfully to memory.
    Ensures addHistoryToMemory saves user query, command-result pairs, and final result in memory.
    """
    rag_agent_instance = await mock_rag_agent

    # Mock retriever and LLM chain responses for iteration processing
    mock_retriever_search = AsyncMock()
    mock_retriever_search.side_effect = [
        [MagicMock(page_content="Content of file1")],
        [MagicMock(page_content="Content of file2")]
    ]
    mock_llm_chain = AsyncMock()
    mock_llm_chain.ainvoke.side_effect = ["Filter Command: file1.txt", "Final answer"]

    with patch.object(rag_agent_instance.retriever, 'ainvoke', mock_retriever_search):
        with patch.object(rag_agent_instance, 'llm_chain', mock_llm_chain):
            user_query = "Find information about file1 and file2"
            result = await rag_agent_instance.execute(user_query)

    # Assert the final response is as expected and memory is updated
    assert result == "Final answer"
    mock_llm_chain.ainvoke.assert_called()
    assert mock_retriever_search.call_count > 0
    rag_agent_instance.memory.saveContext.assert_called_once()

@pytest.mark.asyncio
async def test_rag_agent_get_history_from_memory_success(mock_rag_agent):
    """
    Test for successful retrieval of conversation history from memory.
    Ensures getHistoryFromMemory returns the expected history data.
    """
    rag_agent_instance = await mock_rag_agent
    rag_agent_instance.memory.getHistory.return_value = {"Test SQL History"}

    # Retrieve history and validate it matches expected result
    result = await rag_agent_instance.getHistoryFromMemory()
    assert result == {"Test SQL History"}
    rag_agent_instance.memory.getHistory.assert_called_once_with(is_sql=True)

@pytest.mark.asyncio
async def test_rag_agent_get_available_files_success(mock_rag_agent):
    """
    Test for retrieving available file names from vector store.
    Ensures getAvailableFiles accurately lists unique file names in the vector store.
    """
    rag_agent_instance = await mock_rag_agent

    # Set up mock documents with file metadata for unique file names
    mock_document1 = MagicMock()
    mock_document1.metadata = {'filename': 'file1.txt'}
    mock_document2 = MagicMock()
    mock_document2.metadata = {'filename': 'file2.txt'}
    mock_document3 = MagicMock()
    mock_document3.metadata = {'filename': 'file1.txt'}
    
    rag_agent_instance.vector_store.docstore._dict.values.return_value = [mock_document1, mock_document2, mock_document3]

    # Retrieve available files and validate they are unique
    result = rag_agent_instance.getAvailableFiles()
    result.sort()
    
    assert result == ['file1.txt', 'file2.txt']
    rag_agent_instance.vector_store.docstore._dict.values.assert_called_once()