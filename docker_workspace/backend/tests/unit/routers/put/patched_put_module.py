from unittest.mock import patch, AsyncMock
from tests.unit.routers._mock_instance import _MockInstance

class PatchedPutModule:
    """
    This class patches specific components to enable isolated and controlled testing 
    of the 'put' module in FastAPI applications. It patches the `Instance` class and 
    `getAsyncDB` function with mock objects.
    """
    def __init__(self):
        # Mock asynchronous database connection method for controlled database interactions
        self.mock_getAsyncDB = AsyncMock()

        # Patch the `Instance` class with `_MockInstance` to use a mock version in tests
        self.patcher_instance_class = patch('lib.instances.instance.Instance', new=_MockInstance, create=True)
        
        # Patch `getAsyncDB` to yield the mock async database connection
        self.patcher_put_async_user_db = patch('lib.routers.put.getAsyncDB', new=self.async_db_yielder)

    def __enter__(self):
        # Start both patches, ensuring all tests use the patched versions
        self.patcher_instance_class.start()
        self.patcher_put_async_user_db.start()

        # Import `instance` and `router` from the patched module to make them accessible in tests
        from lib.routers.put import instance, router
        self.instance = instance
        self.router = router

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Stop the patches, restoring original functionality after tests
        self.patcher_instance_class.stop()
        self.patcher_put_async_user_db.stop()

    async def async_db_yielder(self, *args, **kwargs):
        """
        Mock async generator that yields a mocked async database connection.
        Ensures compatibility with async for loops in tested code.
        """
        yield self.mock_getAsyncDB