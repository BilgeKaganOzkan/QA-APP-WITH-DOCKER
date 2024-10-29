import pytest, os
from unittest.mock import patch, MagicMock
from lib.ai.llm.embedding import Embedding
from langchain_openai import OpenAIEmbeddings

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"}):
        yield

@patch("lib.ai.llm.embedding.OpenAIEmbeddings")
def test_embedding_initialization_success(mock_openai_embeddings, mock_env):
    """
    Test to check if Embedding class initializes successfully with a valid API key.
    Ensures OpenAIEmbeddings is instantiated with correct parameters.
    """
    model_name = "text-embedding-ada-002"

    # Mock OpenAIEmbeddings instance creation
    mock_openai_embeddings.return_value = MagicMock(spec=OpenAIEmbeddings)

    # Instantiate the Embedding class
    embedding_instance = Embedding(model_name=model_name)

    # Verify OpenAIEmbeddings was called with the correct arguments
    mock_openai_embeddings.assert_called_once_with(model=model_name, openai_api_key="test_api_key")
    # Ensure the instance has the expected type
    assert isinstance(embedding_instance.get_embedding(), OpenAIEmbeddings)

@patch("lib.ai.llm.embedding.OpenAIEmbeddings")
def test_embedding_initialization_missing_api_key(mock_openai_embeddings):
    """
    Test to verify Embedding class handles missing API key gracefully by exiting.
    Ensures an exception is raised if API key is not set.
    """
    model_name = "text-embedding-ada-002"
    mock_openai_embeddings.side_effect = Exception("API key missing or invalid")  # Simulate missing API key exception

    # Temporarily clear the API key environment variable and expect a SystemExit
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
        with pytest.raises(SystemExit):
            Embedding(model_name=model_name)

@patch("lib.ai.llm.embedding.OpenAIEmbeddings")
def test_embedding_get_embedding(mock_openai_embeddings, mock_env):
    """
    Test to verify get_embedding method returns the correct OpenAIEmbeddings instance.
    Ensures the returned embedding instance is of the expected type.
    """
    model_name = "text-embedding-ada-002"

    # Mock OpenAIEmbeddings instance creation
    mock_openai_embeddings.return_value = MagicMock(spec=OpenAIEmbeddings)

    # Instantiate Embedding and retrieve the embedding instance
    embedding_instance = Embedding(model_name=model_name)
    embedding = embedding_instance.get_embedding()

    # Ensure the returned instance matches the expected type
    assert isinstance(embedding, OpenAIEmbeddings)
    mock_openai_embeddings.assert_called_once()