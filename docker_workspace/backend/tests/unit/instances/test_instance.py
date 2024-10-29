from unittest.mock import patch
from lib.instances.instance import Instance

@patch("lib.instances.instance.Configuration")
@patch("lib.instances.instance.CustomMemoryDict")
@patch("lib.instances.instance.LLM")
@patch("lib.instances.instance.Embedding")
@patch("lib.instances.instance.RedisTool")
def test_instance_success(mock_redis_tool, mock_embedding, mock_llm, mock_memory_dict, mock_config):
    """
    Test to verify Instance class correctly initializes all attributes from Configuration and
    integrates with other components such as LLM, Embedding, and RedisTool.
    Ensures all configuration values are correctly retrieved and dependencies are initialized.
    """
    # Mock Configuration return values
    mock_config.return_value.getLLMModelName.return_value = "gpt-3"
    mock_config.return_value.getEmbeddingLLMModelName.return_value = "bert"
    mock_config.return_value.getLLMMaxIteration.return_value = 10
    mock_config.return_value.getSignUpEndpoint.return_value = "/signup"
    mock_config.return_value.getLoginEndpoint.return_value = "/login"
    mock_config.return_value.getStartSessionEndpoint.return_value = "/start_session"
    mock_config.return_value.getCheckSessionEndpoint.return_value = "/check_session"
    mock_config.return_value.getUploadCsvEndpoint.return_value = "/upload_csv"
    mock_config.return_value.getUploadPdfEndpoint.return_value = "/upload_pdf"
    mock_config.return_value.getProgressEndpoint.return_value = "/progress"
    mock_config.return_value.getSqlQueryEndpoint.return_value = "/sql_query"
    mock_config.return_value.getRagQueryEndpoint.return_value = "/rag_query"
    mock_config.return_value.getClearSessionEndpoint.return_value = "/clear_session"
    mock_config.return_value.getEndSessionEndpoint.return_value = "/end_session"
    mock_config.return_value.getSessionTimeout.return_value = 3600
    mock_config.return_value.getDbMaxTableLimit.return_value = 100
    mock_config.return_value.getMaxFileLimit.return_value = 50
    mock_config.return_value.getSyncDatabaseUrl.return_value = "postgresql+psycopg2://asd:asd@127.0.0.1:1234"
    mock_config.return_value.getAsyncDatabaseUrl.return_value = "postgresql+asyncpg://asd:asd@127.0.0.1:1234"
    mock_config.return_value.getUserDatabaseName.return_value = "user_db"
    mock_config.return_value.getRedisIP.return_value = "127.0.0.1"
    mock_config.return_value.getRedisPort.return_value = 6379
    mock_config.return_value.getAppIP.return_value = "127.0.0.1"
    mock_config.return_value.getAppPort.return_value = 8000
    mock_config.return_value.getLogFilePath.return_value = "/var/log/app.log"
    mock_config.return_value.getCheckList.return_value = ["/path/to/dir1", "/path/to/dir2"]
    mock_config.return_value.getOriginList.return_value = ["https://example.com"]
    
    # Reset the singleton instance to None to allow reinitialization
    Instance._instance = None
    instance = Instance()

    # Verify Instance attributes are correctly set
    assert instance.llm_model_name == "gpt-3"
    assert instance.embedding_model_name == "bert"
    assert instance.llm_max_iteration == 10
    assert instance.signup_end_point == "/signup"
    assert instance.login_end_point == "/login"
    assert instance.start_session_end_point == "/start_session"
    assert instance.check_session_end_point == "/check_session"
    assert instance.upload_csv_end_point == "/upload_csv"
    assert instance.upload_pdf_end_point == "/upload_pdf"
    assert instance.progress_end_point == "/progress"
    assert instance.sql_query_end_point == "/sql_query"
    assert instance.rag_query_end_point == "/rag_query"
    assert instance.clear_session_end_point == "/clear_session"
    assert instance.end_session_end_point == "/end_session"
    assert instance.session_timeout == 3600
    assert instance.db_max_table_limit == 100
    assert instance.max_file_limit == 50
    assert instance.sync_database_url == "postgresql+psycopg2://asd:asd@127.0.0.1:1234"
    assert instance.async_database_url == "postgresql+asyncpg://asd:asd@127.0.0.1:1234"
    assert instance.user_database_name == "user_db"
    assert instance.redis_ip == "127.0.0.1"
    assert instance.redis_port == 6379
    assert instance.app_ip == "127.0.0.1"
    assert instance.app_port == 8000
    assert instance.log_file_path == "/var/log/app.log"
    assert instance.check_list == ["/path/to/dir1", "/path/to/dir2"]
    assert instance.origin_list == ["https://example.com"]

    # Validate that LLM, Embedding, and RedisTool were initialized with expected arguments
    mock_llm.assert_called_with(llm_model_name="gpt-3")
    mock_embedding.assert_called_with(model_name="bert")
    mock_redis_tool.assert_called_with(
        memory=mock_memory_dict.return_value,
        session_timeout=3600,
        redis_ip="127.0.0.1",
        redis_port=6379,
        async_database_url="postgresql+asyncpg://asd:asd@127.0.0.1:1234"
    )