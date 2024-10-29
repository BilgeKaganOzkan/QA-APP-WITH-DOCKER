import os
import pytest
from unittest.mock import patch, MagicMock

# Fixture to create temporary directories for testing
@pytest.fixture
def tempDirs(tmp_path):
    """
    Creates temporary directories for testing.
    Returns:
        List of directory paths as strings.
    """
    dir1 = tmp_path / "dir1"
    dir2 = tmp_path / "dir2"
    return [str(dir1), str(dir2)]  # Convert to string paths for compatibility

# Patch Instance class in lib.instances.instance for isolation from other dependencies
@patch('lib.instances.instance.Instance', new=MagicMock, create=True)
def test_files_checker_success(tempDirs):
    """
    Tests FilesChecker initialization with temporary directories.
    Verifies that the directories are created successfully.
    """
    # Import and initialize FilesChecker with mocked directories
    from lib.tools.files_checker import FilesChecker
    _ = FilesChecker(tempDirs)  # Initialize FilesChecker with tempDirs

    # Check that each directory in tempDirs exists
    for dir in tempDirs:
        assert os.path.exists(dir), f"{dir} directory was not created"