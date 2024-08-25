from pydantic import (BaseModel, Field)

ip_pattern = r"^(localhost|(\d{1,3}\.){3}\d{1,3})$"

class EndPointsModel(BaseModel):
    start_session: str
    upload_csv: str
    query: str
    end_session: str

class ServerModel(BaseModel):
    redis_ip: str = Field(..., pattern=ip_pattern)
    redis_port: int = Field(..., ge=1, le=65535)
    app_ip: str = Field(..., pattern=ip_pattern)
    app_port: int = Field(..., ge=1, le=65535)

class LLMConfigs(BaseModel):
    llm_model_name: str
    llm_max_iteration: int = Field(..., ge=1, le=65535)

class ConfigModel(BaseModel):
    session_timeout: int = Field(..., ge=1)
    db_max_table_limit: int = Field(..., ge=1, le=65535)
    llm_configs: LLMConfigs
    end_points: EndPointsModel
    server: ServerModel
