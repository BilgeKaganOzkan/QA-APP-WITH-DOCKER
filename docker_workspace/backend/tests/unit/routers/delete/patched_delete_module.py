from unittest.mock import patch, AsyncMock, Mock
from tests.unit.routers._mock_instance import _MockInstance

class PatchedDeleteModule:
    """
    Patches the delete module's dependencies, replacing database connections and instance references
    with mock objects to ensure isolated and controlled testing.
    """

    def __init__(self):
        # Mock for async database connection to avoid real database interactions in tests.
        self.mock_getAsyncDB = AsyncMock()

        # Patch for the Instance class, replaced with a mock instance to control the instance behavior in tests.
        self.patcher_instance_class = patch('lib.instances.instance.Instance', new=_MockInstance, create=True)
        
        # Patch for getAsyncDB, yielding a mock database connection instead of a real one.
        self.patcher_get_async_db = patch('lib.routers.delete.getAsyncDB', new=self.async_db_yielder)

    def __enter__(self):
        # Start the patches for instance and getAsyncDB to apply mocks.
        self.patcher_instance_class.start()
        self.patcher_get_async_db.start()

        # Import the instance and router after patching, so they use the mock versions.
        from lib.routers.delete import instance, router
        self.instance = instance  # Mocked instance used within the delete module.
        self.router = router  # The router with endpoints that will be tested.

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Stop the patches, removing mocks to clean up after tests.
        self.patcher_instance_class.stop()
        self.patcher_get_async_db.stop()

    async def async_db_yielder(self, *args, **kwargs):
        """
        Yields the mock database async connection, compatible with async for loops.
        Ensures database operations are handled by the mock connection.
        """
        yield self.mock_getAsyncDB