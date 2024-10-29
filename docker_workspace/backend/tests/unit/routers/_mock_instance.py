from unittest.mock import Mock

class _MockInstance:
    _instance = None

    # Ensure the class behaves as a singleton, allowing only one instance
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(_MockInstance, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re-initialization if the instance already exists
        if getattr(self, '_initialized', False):
            return

        # Set up mock configuration attributes
        self.config = Mock()
        self.llm_model_name = 'mock_llm_model_name'
        self.embedding_model_name = 'mock_embedding_model_name'
        self.llm_max_iteration = 5

        # Define API endpoint paths
        self.signup_end_point = '/signup'
        self.login_end_point = '/login'
        self.start_session_end_point = '/start_session'
        self.check_session_end_point = '/check_session'
        self.upload_csv_end_point = '/upload_csv'
        self.upload_pdf_end_point = '/upload_pdf'
        self.progress_end_point = '/progress'
        self.sql_query_end_point = '/sql_query'
        self.rag_query_end_point = '/rag_query'
        self.clear_session_end_point = '/clear_session'
        self.end_session_end_point = '/end_session'

        # Define other configuration settings
        self.session_timeout = 3600  # session timeout in seconds
        self.db_max_table_limit = 100  # maximum number of tables allowed in DB
        self.max_file_limit = 5  # maximum number of files allowed for upload
        self.sync_database_url = 'sqlite:///:memory:'  # synchronous DB URL for testing
        self.async_database_url = 'sqlite+aiosqlite:///:memory:'  # asynchronous DB URL
        self.user_database_name = 'user_db'  # name of the user database

        # Define mock server and logging configuration
        self.redis_ip = 'localhost'  # Redis server IP for session management
        self.redis_port = 6379  # Redis server port
        self.app_ip = 'localhost'  # application IP
        self.app_port = 8000  # application port
        self.log_file_path = '/var/log/app.log'  # log file path

        # Additional attributes for tracking in tests
        self.check_list = []
        self.origin_list = []

        # Create mock objects for components like memory, LLM, embedding, and Redis tools
        self.memory = Mock()
        self.llm = Mock()
        self.embedding = Mock()
        self.redis_tool = Mock()

        # Mark the instance as initialized to prevent re-initialization
        self._initialized = True