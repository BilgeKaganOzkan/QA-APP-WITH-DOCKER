from unittest.mock import patch, AsyncMock, Mock
from tests.unit.routers._mock_instance import _MockInstance

class PatchedGetModule:
    """
    PatchedGetModule class is a context manager that applies patches
    for testing the 'get' router in the application.
    """

    def __init__(self):
        # Patch the Instance class in the library with a mock instance
        # _MockInstance is used as a substitute for testing purposes
        self.patcher_instance_class = patch('lib.instances.instance.Instance', new=_MockInstance, create=True)

    def __enter__(self):
        """
        Enter method to start patching when entering the context.
        """
        # Start the patcher for the instance class
        self.patcher_instance_class.start()

        # Import the necessary components to test after patching
        from lib.routers.get import instance, router
        self.instance = instance  # Mocked instance
        self.router = router      # Router to be tested

        # Return self to allow access to patched components in tests
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit method to stop patching after the context ends.
        """
        # Stop the instance patcher, restoring original behavior
        self.patcher_instance_class.stop()