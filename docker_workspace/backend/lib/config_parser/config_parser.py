import yaml, sys
from pydantic import ValidationError
from lib.config_parser.yaml_model import ConfigModel

class Configuration:
    def __init__(self) -> None:
        with open('./config/config.yaml', 'r') as file:
            config= yaml.safe_load(file)
        
        try:
            self.config_data = ConfigModel(**config)
            print("YAML file is valid!")
        except ValidationError as e:
            print("YAML file validation failed:")
            print(e)
            sys.exit(-1)

    def getSessionTimeout(self) -> int:
        return int(self.config_data.session_timeout)
    
    def getDbMaxTableLimit(self) -> int:
        return int(self.config_data.db_max_table_limit)

    def getMaxFileLimit(self) -> int:
        return int(self.config_data.max_file_limit)

    def getLLMModelName(self) -> str:
        return str(self.config_data.llm_configs.sql_llm_model_name)

    def getEmbeddingLLMModelName(self) -> str:
        return str(self.config_data.llm_configs.embedding_model_name)
    
    def getLLMMaxIteration(self) -> int:
        return int(self.config_data.llm_configs.llm_max_iteration)
    
    def getSignUpEndpoint(self) -> str:
        return str(self.config_data.end_points.signup)
    
    def getLoginEndpoint(self) -> str:
        return str(self.config_data.end_points.login)

    def getStartSessionEndpoint(self) -> str:
        return str(self.config_data.end_points.start_session)
    
    def getCheckSessionEndpoint(self) -> str:
        return str(self.config_data.end_points.check_session)

    def getUploadCsvEndpoint(self) -> str:
        return str(self.config_data.end_points.upload_csv)
    
    def getUploadPdfEndpoint(self) -> str:
        return str(self.config_data.end_points.upload_pdf)
    
    def getProgressEndpoint(self) -> str:
        return str(self.config_data.end_points.progress)

    def getSqlQueryEndpoint(self) -> str:
        return str(self.config_data.end_points.sql_query)

    def getRagQueryEndpoint(self) -> str:
        return str(self.config_data.end_points.rag_query)

    def getClearSessionEndpoint(self) -> str:
        return str(self.config_data.end_points.clear_session)
    
    def getEndSessionEndpoint(self) -> str:
        return str(self.config_data.end_points.end_session)
    
    def getSyncDatabaseUrl(self) -> str:
        return str(self.config_data.server.sync_database_url)
    
    def getAsyncDatabaseUrl(self) -> str:
        return str(self.config_data.server.async_database_url)

    def getUserDatabaseName(self) -> str:
        return str(self.config_data.server.user_database_name)

    def getRedisIP(self) -> str:
        return str(self.config_data.server.redis_ip)

    def getRedisPort(self) -> int:
        return int(self.config_data.server.redis_port)

    def getAppIP(self) -> str:
        return str(self.config_data.server.app_ip)

    def getAppPort(self) -> int:
        return int(self.config_data.server.app_port)
    
    def getLogFilePath(self) -> str:
        return str(self.config_data.paths.log_file_dir)
    
    def getCheckList(self) -> list:
        return self.config_data.paths.check_list
    
    def getOriginList(self) -> list:
        return self.config_data.paths.origin_list