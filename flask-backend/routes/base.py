from enum import Enum

class ApiBase(str, Enum):
    @property
    def path(self):
        return self.value.split("?")[0]

    @property
    def query(self):
        return self.value.split("?")[1]
