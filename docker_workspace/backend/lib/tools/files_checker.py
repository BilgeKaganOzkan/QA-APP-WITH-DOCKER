import os
from lib.instances.instance import Instance

class FilesChecker:
    """
    @brief Checks and creates directories from a provided list if they don't exist.

    FilesChecker verifies each directory in the list and creates any missing directories.

    @param dir_list List of directories to check.
    """

    def __init__(self, dir_list) -> None:
        """
        @brief Initializes the FilesChecker instance and processes the directory list.

        Iterates through each directory in `dir_list`, creating it if it doesn't already exist.

        @param dir_list List of directories to verify.
        """
        for dir in dir_list:
            if not os.path.exists(dir):
                os.mkdir(dir)

instance = Instance()
filesChecker = FilesChecker(instance.check_list)
