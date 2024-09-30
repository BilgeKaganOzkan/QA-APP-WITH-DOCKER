from lib.routers.instance import instance
import os

class FilesChecker:
    def __init__(self, dir_list) -> None:
        for dir in dir_list:
            if not os.path.exists(dir):
                os.mkdir(dir)

filesChecker = FilesChecker(instance.check_list)