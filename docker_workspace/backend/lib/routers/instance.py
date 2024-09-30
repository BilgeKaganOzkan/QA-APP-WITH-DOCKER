from lib.config_parser.config_parser import Configuration
from lib.tools.redis import RedisTool
from lib.ai.memory.memory import CustomMemoryDict
from lib.ai.llm.llm import LLM
from lib.ai.llm.embedding import Embedding

class Instance:
    def __init__(self) -> None:
        self.config = Configuration()

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
        self.user_database_name= self.config.getUserDatabaseName()
        self.redis_ip = self.config.getRedisIP()
        self.redis_port = self.config.getRedisPort()
        self.app_ip = self.config.getAppIP()
        self.app_port = self.config.getAppPort()
        self.log_file_path = self.config.getLogFilePath()
        self.check_list = self.config.getCheckList()
        self.origin_list = self.config.getOriginList()

        self.active_session_list = []
        self.memory = CustomMemoryDict()
        self.llm = LLM(llm_model_name=self.llm_model_name)
        self.embedding = Embedding(model_name=self.embedding_model_name).get_embedding()
        self.redis_tool = RedisTool(memory=self.memory, session_timeout=self.session_timeout, redis_ip=self.redis_ip, redis_port=self.redis_port, session_list=self.active_session_list)

instance = Instance()