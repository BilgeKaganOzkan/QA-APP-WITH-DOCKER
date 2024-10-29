import pytest
from unittest.mock import patch, mock_open
from lib.config_parser.config_parser import Configuration

# Valid YAML configuration for testing successful parsing and validation
CORRECT_YAML = """
session_timeout: 3600
db_max_table_limit: 100
max_file_limit: 50
llm_configs:
  sql_llm_model_name: "gpt-3"
  embedding_model_name: "bert"
  llm_max_iteration: 10
end_points:
  signup: "/signup"
  login: "/login"
  start_session: "/start_session"
  check_session: "/check_session"
  upload_csv: "/upload_csv"
  upload_pdf: "/upload_pdf"
  progress: "/progress"
  sql_query: "/sql_query"
  rag_query: "/rag_query"
  clear_session: "/clear_session"
  end_session: "/end_session"
server:
  sync_database_url: postgresql+psycopg2://asd:asd@127.0.0.1:1234
  async_database_url: postgresql+asyncpg://asd:asd@127.0.0.1:1234
  user_database_name: "user_db"
  redis_ip: "127.0.0.1"
  redis_port: 6379
  app_ip: "127.0.0.1"
  app_port: 8000
paths:
  log_file_dir: "/var/log/app.log"
  check_list:
    - "/path/to/dir1"
    - "/path/to/dir2"
  origin_list:
    - "https://example.com"
"""

# Various YAMLs with issues for testing validation failure scenarios
MISSING_FIELDS_YAML = """
session_timeout: 3600
db_max_table_limit: 100
llm_configs:
  sql_llm_model_name: "gpt-3"
  embedding_model_name: "bert"
  llm_max_iteration: 10
end_points:
  signup: "/signup"
  login: "/login"
"""

INVALID_TYPES_YAML = """
session_timeout: "3600"
db_max_table_limit: 100
max_file_limit: 50
llm_configs:
  sql_llm_model_name: "gpt-3"
  embedding_model_name: "bert"
  llm_max_iteration: 10
"""

INVALID_URL_PATTERN_YAML = """
session_timeout: 3600
db_max_table_limit: 100
max_file_limit: 50
llm_configs:
  sql_llm_model_name: "gpt-3"
  embedding_model_name: "bert"
  llm_max_iteration: 10
server:
  sync_database_url: "localhost:5432"
  async_database_url: "postgresql+asyncpg://qa:qa@172.20.0.23:5432"
"""

EMPTY_YAML = ""

PARTIAL_INVALID_YAML = """
session_timeout: 3600
db_max_table_limit: "100"
max_file_limit: 50
llm_configs:
  sql_llm_model_name: "gpt-3"
  embedding_model_name: "bert"
  llm_max_iteration: 10
"""

INVALID_YAML = """
session_timeout: 3600
db_max_table_limit: !!invalid 100
max_file_limit: 50
"""

@patch("lib.config_parser.config_parser.os.path.exists")
@patch("lib.config_parser.config_parser.open", new_callable=mock_open, read_data=CORRECT_YAML)
@patch("lib.config_parser.config_parser.sys.exit")
def test_configuration_success(mock_exit, mock_open_file, mock_exists):
    """
    Test to ensure Configuration parses and validates a correct YAML file without errors.
    Verifies all getter methods return expected values.
    """
    config = Configuration(config_file_path="")

    # Validate getter methods return expected values
    assert config.getSessionTimeout() == 3600
    assert config.getDbMaxTableLimit() == 100
    assert config.getMaxFileLimit() == 50
    assert config.getLLMModelName() == "gpt-3"
    assert config.getEmbeddingLLMModelName() == "bert"
    assert config.getLLMMaxIteration() == 10
    assert config.getSignUpEndpoint() == "/signup"
    assert config.getLoginEndpoint() == "/login"
    assert config.getStartSessionEndpoint() == "/start_session"
    assert config.getCheckSessionEndpoint() == "/check_session"
    assert config.getUploadCsvEndpoint() == "/upload_csv"
    assert config.getUploadPdfEndpoint() == "/upload_pdf"
    assert config.getProgressEndpoint() == "/progress"
    assert config.getSqlQueryEndpoint() == "/sql_query"
    assert config.getRagQueryEndpoint() == "/rag_query"
    assert config.getClearSessionEndpoint() == "/clear_session"
    assert config.getEndSessionEndpoint() == "/end_session"
    assert config.getSyncDatabaseUrl() == "postgresql+psycopg2://asd:asd@127.0.0.1:1234"
    assert config.getAsyncDatabaseUrl() == "postgresql+asyncpg://asd:asd@127.0.0.1:1234"
    assert config.getRedisIP() == "127.0.0.1"
    assert config.getRedisPort() == 6379
    assert config.getAppIP() == "127.0.0.1"
    assert config.getAppPort() == 8000
    assert config.getLogFilePath() == "/var/log/app.log"
    assert config.getCheckList() == ["/path/to/dir1", "/path/to/dir2"]
    assert config.getOriginList() == ["https://example.com"]
    mock_exit.assert_not_called()

@patch("lib.config_parser.config_parser.os.path.exists")
@patch("lib.config_parser.config_parser.open", new_callable=mock_open, read_data=MISSING_FIELDS_YAML)
def test_configuration_failure_missing_fields(mock_open_file, mock_exists):
    """
    Test to verify Configuration exits with an error if YAML has missing fields.
    """
    with pytest.raises(SystemExit) as exc_info:
        Configuration(config_file_path='')
    assert exc_info.value.code == -1

@patch("lib.config_parser.config_parser.os.path.exists")
@patch("lib.config_parser.config_parser.open", new_callable=mock_open, read_data=INVALID_TYPES_YAML)
def test_configuration_failure_invalid_types(mock_open_file, mock_exists):
    """
    Test to check Configuration exits with an error if YAML contains invalid types.
    """
    with pytest.raises(SystemExit) as exc_info:
        Configuration(config_file_path='')
    assert exc_info.value.code == -1

@patch("lib.config_parser.config_parser.os.path.exists")
@patch("lib.config_parser.config_parser.open", new_callable=mock_open, read_data=INVALID_URL_PATTERN_YAML)
def test_configuration_failure_invalid_URL_pattern(mock_open_file, mock_exists):
    """
    Test to verify Configuration exits if YAML contains an invalid URL pattern.
    """
    with pytest.raises(SystemExit) as exc_info:
        Configuration(config_file_path='')
    assert exc_info.value.code == -1

@patch("lib.config_parser.config_parser.os.path.exists")
@patch("lib.config_parser.config_parser.open", new_callable=mock_open, read_data=EMPTY_YAML)
def test_configuration_failure_empty_yaml(mock_open_file, mock_exists):
    """
    Test to check Configuration exits with an error if YAML file is empty.
    """
    with pytest.raises(SystemExit) as exc_info:
        Configuration(config_file_path='')
    assert exc_info.value.code == -1

def test_configuration_failure_invalid_file_path():
    """
    Test to verify Configuration exits if the provided file path does not exist.
    """
    with pytest.raises(SystemExit) as exc_info:
        Configuration(config_file_path='asd.yaml')
    assert exc_info.value.code == -1

@patch("lib.config_parser.config_parser.os.path.exists")
@patch("lib.config_parser.config_parser.open", new_callable=mock_open, read_data=PARTIAL_INVALID_YAML)
def test_configuration_failure_partial_invalid(mock_open_file, mock_exists):
    """
    Test to verify Configuration exits if YAML has partially invalid types or fields.
    """
    with pytest.raises(SystemExit) as exc_info:
        Configuration(config_file_path='')
    assert exc_info.value.code == -1

@patch("lib.config_parser.config_parser.os.path.exists")
@patch("lib.config_parser.config_parser.open", new_callable=mock_open, read_data=INVALID_YAML)
def test_configuration_failure_invalid_yaml_syntax(mock_open_file, mock_exists):
    """
    Test to ensure Configuration exits if YAML syntax is invalid.
    """
    with pytest.raises(SystemExit) as exc_info:
        Configuration(config_file_path='')
    assert exc_info.value.code == -1