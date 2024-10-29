import yaml
import sys
import os
from pydantic import ValidationError
from lib.config_parser.yaml_model import ConfigModel

class Configuration:
    """
    @brief Handles loading and validating configuration from a YAML file.

    This class reads a specified YAML configuration file, validates its content
    against a predefined Pydantic model, and provides methods to access various
    configuration settings.
    """
    
    def __init__(self, config_file_path: str) -> None:
        """
        @brief Initializes the Configuration object by loading the specified YAML file.

        @param config_file_path The path to the YAML configuration file.
        """
        config = None

        # Check if the configuration file exists
        if not os.path.exists(config_file_path):
            print(f"{config_file_path} path doesn't exist.")
            sys.exit(-1)

        # Load the YAML configuration file
        try:
            with open(config_file_path, 'r') as file:
                config = yaml.safe_load(file)
        except yaml.YAMLError as e:
            print("YAML parsing error occurred:")
            print(e)
            sys.exit(-1)
        
        # Check if the loaded configuration is empty
        if config is None:
            print("YAML file is empty!")
            sys.exit(-1)
        
        # Validate the loaded configuration against the ConfigModel
        try:
            self.config_data = ConfigModel(**config)
            print("YAML file is valid!")
        except ValidationError as e:
            print("YAML file validation failed:")
            print(e)
            sys.exit(-1)

    # Getter methods to access configuration settings
    def getSessionTimeout(self) -> int:
        """Returns the session timeout value."""
        return int(self.config_data.session_timeout)
    
    def getDbMaxTableLimit(self) -> int:
        """Returns the maximum number of tables allowed in the database."""
        return int(self.config_data.db_max_table_limit)

    def getMaxFileLimit(self) -> int:
        """Returns the maximum number of files allowed for uploads."""
        return int(self.config_data.max_file_limit)

    def getLLMModelName(self) -> str:
        """Returns the name of the SQL LLM model."""
        return str(self.config_data.llm_configs.sql_llm_model_name)

    def getEmbeddingLLMModelName(self) -> str:
        """Returns the name of the embedding model."""
        return str(self.config_data.llm_configs.embedding_model_name)
    
    def getLLMMaxIteration(self) -> int:
        """Returns the maximum iterations for the LLM."""
        return int(self.config_data.llm_configs.llm_max_iteration)
    
    def getSignUpEndpoint(self) -> str:
        """Returns the signup endpoint URL."""
        return str(self.config_data.end_points.signup)
    
    def getLoginEndpoint(self) -> str:
        """Returns the login endpoint URL."""
        return str(self.config_data.end_points.login)

    def getStartSessionEndpoint(self) -> str:
        """Returns the start session endpoint URL."""
        return str(self.config_data.end_points.start_session)
    
    def getCheckSessionEndpoint(self) -> str:
        """Returns the check session endpoint URL."""
        return str(self.config_data.end_points.check_session)

    def getUploadCsvEndpoint(self) -> str:
        """Returns the upload CSV endpoint URL."""
        return str(self.config_data.end_points.upload_csv)
    
    def getUploadPdfEndpoint(self) -> str:
        """Returns the upload PDF endpoint URL."""
        return str(self.config_data.end_points.upload_pdf)
    
    def getProgressEndpoint(self) -> str:
        """Returns the progress endpoint URL."""
        return str(self.config_data.end_points.progress)

    def getSqlQueryEndpoint(self) -> str:
        """Returns the SQL query endpoint URL."""
        return str(self.config_data.end_points.sql_query)

    def getRagQueryEndpoint(self) -> str:
        """Returns the RAG query endpoint URL."""
        return str(self.config_data.end_points.rag_query)

    def getClearSessionEndpoint(self) -> str:
        """Returns the clear session endpoint URL."""
        return str(self.config_data.end_points.clear_session)
    
    def getEndSessionEndpoint(self) -> str:
        """Returns the end session endpoint URL."""
        return str(self.config_data.end_points.end_session)
    
    def getSyncDatabaseUrl(self) -> str:
        """Returns the synchronous database URL."""
        return str(self.config_data.server.sync_database_url)
    
    def getAsyncDatabaseUrl(self) -> str:
        """Returns the asynchronous database URL."""
        return str(self.config_data.server.async_database_url)

    def getUserDatabaseName(self) -> str:
        """Returns the user database name."""
        return str(self.config_data.server.user_database_name)

    def getRedisIP(self) -> str:
        """Returns the IP address of the Redis server."""
        return str(self.config_data.server.redis_ip)

    def getRedisPort(self) -> int:
        """Returns the port number for the Redis server."""
        return int(self.config_data.server.redis_port)

    def getAppIP(self) -> str:
        """Returns the IP address for the application server."""
        return str(self.config_data.server.app_ip)

    def getAppPort(self) -> int:
        """Returns the port number for the application server."""
        return int(self.config_data.server.app_port)
    
    def getLogFilePath(self) -> str:
        """Returns the directory for log files."""
        return str(self.config_data.paths.log_file_dir)
    
    def getCheckList(self) -> list:
        """Returns the checklist from the configuration."""
        return self.config_data.paths.check_list
    
    def getOriginList(self) -> list:
        """Returns the list of origins from the configuration."""
        return self.config_data.paths.origin_list