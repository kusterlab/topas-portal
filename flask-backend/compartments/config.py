import os

from flask import Blueprint, jsonify, Response

import db
from topas_portal.routes import ApiRoutes
from topas_portal import utils


config_page = Blueprint(
    "config_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db


@config_page.route(ApiRoutes.CONFIG)
# http://localhost:3832/config
def configuration():
    cohorts_db.config.reload_config()
    return jsonify(cohorts_db.config.get_config())


@config_page.route(ApiRoutes.CONFIG_PATH)
# http://localhost:3832/config/config_path
def config_path():
    return {"path": str(cohorts_db.config.config_path)}


@config_page.route(ApiRoutes.CONFIG_CHECKALL)
# http://localhost:3832/config/checkall
def configuration_checks():
    cohorts_db.config.reload_config()
    return utils.check_all_config_file(cohorts_db.config.get_config())


@config_page.route(ApiRoutes.CONFIG_UPDATE)
# http://localhost:3832/config/update/FP/INFORM/0
def config_updater(key: str, cohort: str, value: str):
    """
    Updates the configuration settings for a given key and cohort, then checks if the provided value exists as a file or directory.

    Args:
        key (str): The configuration key to update.
        cohort (str): The cohort-specific context for the configuration update.
        value (str): The new value to be assigned to the configuration key.

    Returns:
        Response: An HTTP response indicating whether the provided value exists as a file or directory.
    """
    cohorts_db.config.update_config_values(key, cohort, value)
    return Response(str(os.path.exists(value)))


@config_page.route(ApiRoutes.ADD_COHORT)
# http://localhost:3832/config/addcohort/new_cohort
def add_cohort(cohort: str):
    cohorts_db.config.add_new_cohort_placeholder(cohort)
    cohorts_db.provider.load_single_cohort_with_empty_data(cohort)
    return {"done": True}