import sys

from topas_portal.data_api.sql import SQLCohortDataAPI
from topas_portal.data_api.in_memory import InMemoryCohortDataAPI
import topas_portal.settings as cn
from config import get_config_path


debug = cn.DEBUG_MODE
if len(sys.argv) > 1 and sys.argv[1] == "test":
    debug = True

config_file = get_config_path()
if cn.DATABASE_MODE:
    cohorts_db = SQLCohortDataAPI(config_file)
else:
    cohorts_db = InMemoryCohortDataAPI(config_file)
