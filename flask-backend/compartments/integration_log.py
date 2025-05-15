import tests.datavalidation as icheck
from flask import Blueprint, jsonify, current_app

import topas_portal.utils as ef


PORTAL_CONFIG_FILE = current_app.config["config_file"]
LOCAL_HTTTP = current_app.config["integration_http"]

integration_log = []
integration_page = Blueprint(
    "integration_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)


def integration_logger(message):
    print(message)
    integration_log.append(f"{ef.time_now()}{message}#####")
    integration_log.append(" topas_separator ")


#################### portal integration checkings
@integration_page.route("/check/config")
def main_config_file_checker():
    msg = icheck.check_portal_main_config_exist(PORTAL_CONFIG_FILE)
    integration_logger(msg)
    return jsonify(msg)


@integration_page.route("/check/integrability/<cohort>")
def integraion_ability(cohort):
    msg = icheck.check_integretability_cohort(cohort)
    integration_logger(msg)
    return jsonify(msg)


@integration_page.route("/check/validity_z_score/<cohort>/<protein_name>")
def z_score_validity_check(cohort, protein_name):
    print('running res')
    res = icheck.z_score_checker(PORTAL_CONFIG_FILE, LOCAL_HTTTP, cohort, protein_name)
    print(res)
    integration_logger(res)
    return ef.df_to_json(res)


@integration_page.route("/check/validity_topas_score/<cohort>/<topas_name>")
# http://localhost:3832/check/validity_topas_score/INFORM/ALK
def topas_score_validity_check(cohort, topas_name):
    res = icheck.topas_score_checker(
        PORTAL_CONFIG_FILE, LOCAL_HTTTP, cohort, topas_name
    )
    integration_logger(res)
    return ef.df_to_json(res)


@integration_page.route("/integration/logs")
# http://localhost:3832/integration/logs
def integration_logs():
    log = "".join(integration_log)
    return jsonify(log)


@integration_page.route("/integration/clearlogs")
# http://localhost:3832/integration/clearlogs
def clear_integration_logs():
    global integration_log
    integration_log = []

    return {}
