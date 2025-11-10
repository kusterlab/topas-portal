from enum import Enum

class ApiBase(str, Enum):
    def path(self):
        return self.value.split("?")[0]

    def query(self):
        return self.value.split("?")[1]
