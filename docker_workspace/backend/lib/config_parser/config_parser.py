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

    def getLLMModelName(self) -> str:
        return str(self.config_data.llm_configs.llm_model_name)
    
    def getLLMMaxIteration(self) -> int:
        return int(self.config_data.llm_configs.llm_max_iteration)

    def getStartSessionEndpoint(self) -> str:
        return str(self.config_data.end_points.start_session)

    def getUploadCsvEndpoint(self) -> str:
        return str(self.config_data.end_points.upload_csv)

    def getQueryEndpoint(self) -> str:
        return str(self.config_data.end_points.query)

    def getEndSessionEndpoint(self) -> str:
        return str(self.config_data.end_points.end_session)

    def getRedisIP(self) -> str:
        return str(self.config_data.server.redis_ip)

    def getRedisPort(self) -> int:
        return int(self.config_data.server.redis_port)

    def getAppIP(self) -> str:
        return str(self.config_data.server.app_ip)

    def getAppPort(self) -> int:
        return int(self.config_data.server.app_port)