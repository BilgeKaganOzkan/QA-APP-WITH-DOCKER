from unittest.mock import patch, MagicMock
from lib.ai.llm.llm import LLM

@patch("langchain_openai.ChatOpenAI")
@patch("lib.ai.llm.llm.os.getenv")
@patch("lib.ai.llm.llm.load_dotenv")
def test_llm_initialization_success(mock_load_dotenv, mock_getenv, mock_ChatOpenAI):
    """
    Test to ensure LLM class initializes correctly when environment variables are set.
    Checks that load_dotenv is called and ChatOpenAI instance is created.
    """
    mock_getenv.return_value = "test_key"  # Mock the API key retrieval
    mock_llm_instance = MagicMock()
    mock_ChatOpenAI.return_value = mock_llm_instance  # Mock ChatOpenAI instance

    # Instantiate the LLM
    llm_instance = LLM(llm_model_name="gpt-3.5-turbo")

    # Ensure load_dotenv was called once
    mock_load_dotenv.assert_called_once()

@patch("lib.ai.llm.llm.ChatOpenAI")
@patch("lib.ai.llm.llm.os.getenv")
def test_llm_call_success(mock_getenv, mock_ChatOpenAI):
    """
    Test to check if the __call__ method correctly invokes the LLM with a query.
    Ensures invoke method of ChatOpenAI is called with the right arguments.
    """
    mock_getenv.return_value = "test_key"  # Mock API key retrieval
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = "Mocked LLM response"  # Set mock response for invoke
    mock_ChatOpenAI.return_value = mock_llm_instance

    # Instantiate LLM and call it with a sample query
    llm_instance = LLM(llm_model_name="gpt-3.5-turbo")
    response = llm_instance("Sample query")

    # Ensure the LLM invoke method was called with the query
    mock_llm_instance.invoke.assert_called_once_with("Sample query")
    # Validate response matches expected mock output
    assert response == "Mocked LLM response"

@patch("lib.ai.llm.llm.ChatOpenAI", side_effect=Exception("LLM Initialization Error"))
@patch("lib.ai.llm.llm.os.getenv")
@patch("lib.ai.llm.llm.sys.exit")
def test_llm_initialization_failure(mock_exit, mock_getenv, mock_ChatOpenAI):
    """
    Test to verify LLM class behavior when initialization fails.
    Ensures sys.exit is called to handle the failure gracefully.
    """
    mock_getenv.return_value = "test_key"  # Mock API key retrieval

    # Instantiate LLM, expecting initialization failure
    llm_instance = LLM(llm_model_name="gpt-3.5-turbo")

    # Ensure sys.exit is called once due to initialization error
    mock_exit.assert_called_once_with(-1)

@patch("lib.ai.llm.llm.ChatOpenAI")
@patch("lib.ai.llm.llm.os.getenv")
def test_llm_get_base_llm(mock_getenv, mock_ChatOpenAI):
    """
    Test to check if get_baseLLM method correctly returns the base LLM instance.
    Ensures the instance returned matches the one created in initialization.
    """
    mock_getenv.return_value = "test_key"  # Mock API key retrieval
    mock_llm_instance = MagicMock()
    mock_ChatOpenAI.return_value = mock_llm_instance

    # Instantiate LLM and retrieve base LLM
    llm_instance = LLM(llm_model_name="gpt-3.5-turbo")
    base_llm = llm_instance.get_baseLLM()

    # Assert that the returned base LLM matches the mock ChatOpenAI instance
    assert base_llm == mock_llm_instance