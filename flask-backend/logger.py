import topas_portal.utils as utils
from typing import List


class CohortLogger:

    def __init__(self):
        self.load_log = []

    def log_message(self, message: str) -> None:
        """Writes message to logging tab on the portal."""
        print(message)
        self.load_log.append(f"{utils.time_now()}{message}#####")
        self.load_log.append(" topas_separator ")

    def get_log_messages(self) -> List[str]:
        return self.load_log
