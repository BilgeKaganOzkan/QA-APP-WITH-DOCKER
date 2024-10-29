from unittest.mock import patch, AsyncMock, Mock
from tests.unit.routers._mock_instance import _MockInstance

class PatchedPostModule:
    """
    Class to patch key components for testing the 'post' module in isolation.
    This class ensures that dependencies such as database connections, authentication,
    and query agents are mocked, providing controlled responses in test cases.
    """
    def __init__(self):
        # Initialize a mock for agent execution
        mock_agent_execute = AsyncMock()
        mock_agent_execute.execute = AsyncMock(return_value='Mock response')

        # Mock SQL and RAG query agents to control their responses during tests
        self.mock_SqlQueryAgent = Mock(return_value=mock_agent_execute)
        self.mock_RagQueryAgent = Mock(return_value=mock_agent_execute)
        
        # Mock asynchronous user database and authentication functions
        self.mock_getAsyncUserDB = AsyncMock()
        self.mock_getPasswordHash = Mock()
        self.mock_verifyPassword = Mock()

        # Patches to replace actual classes and functions with the defined mocks
        self.patcher_instance_class = patch('lib.instances.instance.Instance', new=_MockInstance, create=True)
        self.patcher_sql_query_agent = patch('lib.routers.post.SqlQueryAgent', self.mock_SqlQueryAgent)
        self.patcher_rag_query_agent = patch('lib.routers.post.RagQueryAgent', self.mock_RagQueryAgent)
        self.patcher_get_async_user_db = patch('lib.routers.post.getAsyncUserDB', self.mock_getAsyncUserDB)
        self.patcher_get_password_hash = patch('lib.routers.post.getPasswordHash', self.mock_getPasswordHash)
        self.patcher_verify_password = patch('lib.routers.post.verifyPassword', self.mock_verifyPassword)

    def __enter__(self):
        # Start all patches to apply the mocked behavior
        self.patcher_instance_class.start()
        self.patcher_sql_query_agent.start()
        self.patcher_rag_query_agent.start()
        self.patcher_get_async_user_db.start()
        self.patcher_get_password_hash.start()
        self.patcher_verify_password.start()

        # Import the 'post' router and instance after patching to use them in tests
        from lib.routers.post import instance, router
        self.instance = instance
        self.router = router

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Stop all patches, restoring original behavior after tests
        self.patcher_instance_class.stop()
        self.patcher_sql_query_agent.stop()
        self.patcher_rag_query_agent.stop()
        self.patcher_get_async_user_db.stop()
        self.patcher_get_password_hash.stop()
        self.patcher_verify_password.stop()