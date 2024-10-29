from lib.config_parser.config_parser import Configuration
from lib.tools.redis import RedisTool
from lib.ai.memory.memory import CustomMemoryDict
from lib.ai.llm.llm import LLM
from lib.ai.llm.embedding import Embedding

class Instance:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        @brief Creates a singleton instance of the Instance class.

        This method ensures that only one instance of the Instance class is created
        and reused throughout the application.
        """
        if cls._instance is None:
            cls._instance = super(Instance, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        @brief Initializes the instance with configuration and necessary components.

        This method loads configuration settings, initializes memory, LLM, embedding, and
        the Redis tool. It is designed to run only once, utilizing a flag to prevent
        re-initialization.
        """
        if getattr(self, '_initialized', False):
            return  # Prevent re-initialization

        # Load configuration from the specified YAML file
        self.config = Configuration(config_file_path='./config/config.yaml')

        # Initialize various attributes from the configuration
        self.llm_model_name = self.config.getLLMModelName()
        self.embedding_model_name = self.config.getEmbeddingLLMModelName()
        self.llm_max_iteration = self.config.getLLMMaxIteration()
        self.signup_end_point = self.config.getSignUpEndpoint()
        self.login_end_point = self.config.getLoginEndpoint()
        self.start_session_end_point = self.config.getStartSessionEndpoint()
        self.check_session_end_point = self.config.getCheckSessionEndpoint()
        self.upload_csv_end_point = self.config.getUploadCsvEndpoint()
        self.upload_pdf_end_point = self.config.getUploadPdfEndpoint()
        self.progress_end_point = self.config.getProgressEndpoint()
        self.sql_query_end_point = self.config.getSqlQueryEndpoint()
        self.rag_query_end_point = self.config.getRagQueryEndpoint()
        self.clear_session_end_point = self.config.getClearSessionEndpoint()
        self.end_session_end_point = self.config.getEndSessionEndpoint()
        self.session_timeout = self.config.getSessionTimeout()
        self.db_max_table_limit = self.config.getDbMaxTableLimit()
        self.max_file_limit = self.config.getMaxFileLimit()
        self.sync_database_url = self.config.getSyncDatabaseUrl()
        self.async_database_url = self.config.getAsyncDatabaseUrl()
        self.user_database_name = self.config.getUserDatabaseName()
        self.redis_ip = self.config.getRedisIP()
        self.redis_port = self.config.getRedisPort()
        self.app_ip = self.config.getAppIP()
        self.app_port = self.config.getAppPort()
        self.log_file_path = self.config.getLogFilePath()
        self.check_list = self.config.getCheckList()
        self.origin_list = self.config.getOriginList()

        # Initialize memory and AI components
        self.memory = CustomMemoryDict()  # Create an instance of custom memory
        self.llm = LLM(llm_model_name=self.llm_model_name)  # Initialize the LLM
        self.embedding = Embedding(model_name=self.embedding_model_name).get_embedding()  # Get embedding model
        self.redis_tool = RedisTool(
            memory=self.memory,
            session_timeout=self.session_timeout,
            redis_ip=self.redis_ip,
            redis_port=self.redis_port,
            async_database_url=self.async_database_url
        )  # Initialize the Redis tool with the necessary parameters

        self._initialized = True  # Set the initialized flag to True