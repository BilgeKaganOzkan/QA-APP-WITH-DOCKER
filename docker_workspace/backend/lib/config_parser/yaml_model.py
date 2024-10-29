from pydantic import (BaseModel, Field)
from typing import List

# Define regex patterns for validating IP addresses and database URLs
ip_pattern = r"^(localhost|(\d{1,3}\.){3}\d{1,3})$"
sync_database_url_pattern = r"^postgresql\+psycopg2:\/\/(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)"
async_database_url_pattern = r"^postgresql\+asyncpg:\/\/(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)"

class EndPointsModel(BaseModel):
    """
    @brief Represents the various API endpoints used in the application.

    This model contains the endpoints for user operations and session management.

    Attributes:
    - signup (str): Endpoint for user signup.
    - login (str): Endpoint for user login.
    - start_session (str): Endpoint for starting a session.
    - check_session (str): Endpoint for checking session status.
    - upload_csv (str): Endpoint for uploading CSV files.
    - upload_pdf (str): Endpoint for uploading PDF files.
    - progress (str): Endpoint for checking progress.
    - sql_query (str): Endpoint for executing SQL queries.
    - rag_query (str): Endpoint for executing RAG queries.
    - clear_session (str): Endpoint for clearing a session.
    - end_session (str): Endpoint for ending a session.
    """
    signup: str
    login: str
    start_session: str
    check_session: str
    upload_csv: str
    upload_pdf: str
    progress: str
    sql_query: str
    rag_query: str
    clear_session: str
    end_session: str

class ServerModel(BaseModel):
    """
    @brief Represents server configuration settings.

    This model contains settings related to database connections and server parameters.

    Attributes:
    - sync_database_url (str): URL for synchronous database connection.
    - async_database_url (str): URL for asynchronous database connection.
    - user_database_name (str): Name of the user database.
    - redis_ip (str): IP address of the Redis server.
    - redis_port (int): Port number for Redis server.
    - app_ip (str): IP address for the application server.
    - app_port (int): Port number for the application server.
    """
    sync_database_url: str = Field(..., pattern=sync_database_url_pattern)
    async_database_url: str = Field(..., pattern=async_database_url_pattern)
    user_database_name: str
    redis_ip: str = Field(..., pattern=ip_pattern)
    redis_port: int = Field(..., ge=1, le=65535)  # Port must be within valid range
    app_ip: str = Field(..., pattern=ip_pattern)
    app_port: int = Field(..., ge=1, le=65535)  # Port must be within valid range

class LLMConfigs(BaseModel):
    """
    @brief Represents configuration settings for LLM (Large Language Model).

    This model contains parameters for the LLM used in the application.

    Attributes:
    - sql_llm_model_name (str): Name of the SQL LLM model.
    - embedding_model_name (str): Name of the embedding model.
    - llm_max_iteration (int): Maximum iterations for the LLM.
    """
    sql_llm_model_name: str
    embedding_model_name: str
    llm_max_iteration: int = Field(..., ge=1, le=65535)  # Must be a positive integer

class PathsModel(BaseModel):
    """
    @brief Represents file system paths used in the application.

    This model contains directories and lists relevant to file management.

    Attributes:
    - log_file_dir (str): Directory for log files.
    - check_list (List[str]): List of items for validation or processing.
    - origin_list (List[str]): List of origins for data processing.
    """
    log_file_dir: str
    check_list: List[str]
    origin_list: List[str]

class ConfigModel(BaseModel):
    """
    @brief Represents the overall application configuration.

    This model contains various configuration settings including session management,
    database limits, and endpoints.

    Attributes:
    - session_timeout (int): Timeout duration for sessions.
    - db_max_table_limit (int): Maximum number of tables allowed in the database.
    - max_file_limit (int): Maximum number of files allowed for uploads.
    - llm_configs (LLMConfigs): Configuration settings for the LLM.
    - end_points (EndPointsModel): API endpoint configurations.
    - server (ServerModel): Server configuration settings.
    - paths (PathsModel): Paths used in the application.
    """
    session_timeout: int = Field(..., ge=1)  # Must be a positive integer
    db_max_table_limit: int = Field(..., ge=1, le=65535)  # Valid range for table limits
    max_file_limit: int = Field(..., ge=1, le=65535)  # Valid range for file limits
    llm_configs: LLMConfigs
    end_points: EndPointsModel
    server: ServerModel
    paths: PathsModel