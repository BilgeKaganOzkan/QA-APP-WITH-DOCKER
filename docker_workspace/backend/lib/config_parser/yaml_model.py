from pydantic import (BaseModel, Field)
from typing import List

ip_pattern = r"^(localhost|(\d{1,3}\.){3}\d{1,3})$"
sync_database_url_pattern = r"^postgresql\+psycopg2:\/\/(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)"
async_database_url_pattern = r"^postgresql\+asyncpg:\/\/(?P<username>[^:]+):(?P<password>[^@]+)@(?P<host>[^:]+):(?P<port>\d+)"

class EndPointsModel(BaseModel):
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
    sync_database_url: str = Field(..., pattern=sync_database_url_pattern)
    async_database_url: str = Field(..., pattern=async_database_url_pattern)
    user_database_name: str
    redis_ip: str = Field(..., pattern=ip_pattern)
    redis_port: int = Field(..., ge=1, le=65535)
    app_ip: str = Field(..., pattern=ip_pattern)
    app_port: int = Field(..., ge=1, le=65535)

class LLMConfigs(BaseModel):
    sql_llm_model_name: str
    embedding_model_name: str
    llm_max_iteration: int = Field(..., ge=1, le=65535)

class PathsModel(BaseModel):
    log_file_dir: str
    check_list: List[str]
    origin_list: List[str]

class ConfigModel(BaseModel):
    session_timeout: int = Field(..., ge=1)
    db_max_table_limit: int = Field(..., ge=1, le=65535)
    max_file_limit: int = Field(..., ge=1, le=65535)
    llm_configs: LLMConfigs
    end_points: EndPointsModel
    server: ServerModel
    paths: PathsModel