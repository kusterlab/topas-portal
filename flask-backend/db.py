import sys

from topas_portal.data_api.sql import SQLCohortDataAPI
from topas_portal.data_api.in_memory import InMemoryCohortDataAPI
from topas_portal import settings
from config import get_config_path


debug = settings.DEBUG_MODE
if len(sys.argv) > 1 and sys.argv[1] == "test":
    debug = True

config_file = get_config_path()
if settings.DATABASE_MODE:
    cohorts_db = SQLCohortDataAPI(config_file)
else:
    cohorts_db = InMemoryCohortDataAPI(config_file)
