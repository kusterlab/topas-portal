import re
from enum import Enum


from enum import Enum

class ApiRoutes(str, Enum):
    INDEX = "/"
    CONFIG = "/config"
    CONFIG_CHECKALL = "/config/checkall"
    PASSWORD_CHECK = "/password/<string:password>"
    CONFIG_PATH = "/config/config_path"
    COHORT_NAMES = "/cohort_names"
    COLUMN_NAMES = "/colnames"
    FAVICON = "/favicon.ico"

    PATIENT_REPORT_TABLE = "/<int:cohort_index>/patient_reports/<string:patient>/<data_type:level>/<string:downloadmethod>"
    PATIENT_REPORT_TABLE_XLSX = "/<int:cohort_index>/patient_reports/<string:patients>"

    ENTITY_STATUS = "/entityscore/status"
    CORRELATION_FPKM_PROTEIN = "/correlation/fpkmprotein/<int:cohort_index>"
    ONCOKB_CNV = "/oncokb/api/cnv/<string:identifier>/<string:cnv_type>"

    RELOAD = "/reload"
    RELOAD_DB_ZSCORES = "/reloaddbz"
    RELOAD_DB_INTENSITY = "/reloaddbi"
    RELOAD_METADATA = "/reloadmeta"
    RELOAD_FP_INTENSITY_META = "/reloadfpintensitymeta"
    RELOAD_MAPPING_PROTEIN_SEQ = "/reloadmapping"
    RELOAD_TOPAS = "/reloadtopass"
    RELOAD_TRANSCRIPTS = "/reload/transcripts"
    RELOAD_DIGEST = "/reload/digest"
    RELOAD_TOPAS_ANNOTATIONS = "/reload/topasannotations"
    RELOAD_COHORT = "/reload/<string:cohort>"

    CONFIG_UPDATE = "/update/<string:key>/<string:cohort>/<string:value>"
    ADD_COHORT = "/addcohort/<string:cohort>"
    PATH_CHECK = "/path/check/<path:path>"

    ANNOTATION_MODALITY = "/annotation/<int:cohort_index>/<string:modality>"
    VENN_PATIENT_COMPARE = "/venn/<int:cohort_index>/patientcompare/<string:pp_fp>/<string:patientslists>"
    VENN_BATCH_COMPARE = "/venn/<int:cohort_index>/batchcompare/<string:pp_fp>/<string:batchlists>"

    UPDATE_LOG = "/update/logs"
    ERROR_LOG = "/error/logs"

    PATIENT_CENTRIC_PP_INTENSITY = "/patientcentric/ppintensity/<int:cohort_index>/<string:dtype>"
    PATIENT_CENTRIC_PROTEIN_COUNTS = "/patientcenteric/proteincounts/<int:cohort_index>/<string:fp_pp>"

    TOPAS = "/topas/<int:cohort_index>/<string:topas_names>/<string:score_type>"
    TOPAS_ANNOTATIONS = "/topas/annotations"
    TOPAS_LOLLIPOP = "/topas/lolipopdata/<int:cohort_index>/<string:patient>"
    TOPAS_LOLLIPOP_TUMOR = "/topas/lolipopdata/<int:cohort_index>/<string:patient>/tumor_antigen"
    TOPAS_EXPRESSION_DOWNSTREAM = "/topas/lolipopdata/expression/<int:cohort_index>/<string:patient>/downstream_signaling"
    TOPAS_EXPRESSION_RTK = "/topas/lolipopdata/expression/<int:cohort_index>/<string:patient>/rtk"
    TOPAS_IDS = "/topas/<int:cohort_index>/topasids/<string:categories>"
    TOPAS_SUBSCORE = "/topas/subscore/<int:cohort_index>/<string:topasname>"

    SAMPLE_ANNOTATION = "/<int:cohort_index>/sampleanot"
    PATIENTS = "/<int:cohort_index>/patients"
    PATIENTS_GENOMICS_ANNOTATIONS = "/<int:cohort_index>/patients/genomics_annotations/<string:identifier>"
    PATIENTS_METADATA = "/<int:cohort_index>/metadata"
    PATIENTS_METADATA_FIELDS = "/<int:cohort_index>/metadata/fields"
    PATIENTS_METADATA_FIELD_VALUES = "/<int:cohort_index>/metadata/fields/<string:fieldname>"
    PATIENTS_BY_FIELD_INTEREST = "/<int:cohort_index>/metadata/fields/<string:fieldname>/patients/<string:field_interest>"
    PATIENTS_ALL_ENTITIES = "/patients/<int:cohort_index>/all_entities"

    GENOMICS_IDENTIFIER = "/genomics/<string:identifier>"
    ONCOKB_IDENTIFIER = "/oncokb/<string:identifier>"

    DENSITY_FPKM = "/density/fpkm/<string:identifier>/<intensity_unit:intensity_unit>"
    DENSITY_PROTEIN = "/<int:cohort_index>/density/protein/<string:identifier>/<intensity_unit:intensity_unit>"

    IMPORTANT_PHOSPHO = "/<int:cohort_index>/important_phospho/<string:identifier>"

    ABUNDANCE = "/<int:cohort_index>/<data_type:level>/abundance/<string:identifier>/<string:imputation>"
    CORRELATION = "/<int:cohort_index>/<data_type:level>/correlation/<data_type:level_2>/<string:identifier>/<intensity_unit:intensity_unit>/<string:patients_list>"

    BATCH_EFFECT = "/batcheffect/<data_type:level>/<int:cohort_index>/<string:identifier>/<string:sample_ids>/<string:data_type>"
    DIFFERENTIAL = "/differential/<int:cohort_index>/<data_type:level>/<string:grp1_ind>/<string:grp2_ind>/<string:y_axis_type>"

    PROTEIN_LIST = "/<int:cohort_index>/<string:level>/list"



def strip_types(flask_route: str):
    """
    Convert Flask-style routes to Vue-style template: <int:id> → :id
    """
    return re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r":\1", flask_route)


def extract_params(flask_route: str):
    """
    Get parameter names from the route string.
    """
    return re.findall(r"<(?:[^:<>]+:)?([^<>]+)>", flask_route)


def generate_ts_function(name, path):
    params = extract_params(path)

    # Create parameter signature and destructuring
    if params:
        param_signature = "{" + ", ".join(params) + "}"
    else:
        param_signature = ""

    # Convert Flask route to TypeScript template literal
    ts_template = re.sub(
        r"<(?:[^:<>]+:)?([^<>]+)>", lambda m: f"${{{m.group(1)}}}", path
    )

    # Final function line
    if params:
        ts_fn = f"    {name}: ({param_signature}) => `${{API_HOST}}{ts_template}`,"
    else:
        ts_fn = f"    {name}: () => `${{API_HOST}}{ts_template}`,"

    return ts_fn


def generate_ts_file(enum_class):
    lines = [
        "// This file is automatically generated by flask-backend/routes.py, do not make changes here!!!",
        "",
        "const API_HOST = process.env.VUE_APP_API_HOST || '';",
        "",
        "export const api = {",
    ]
    for route in enum_class:
        lines.append(generate_ts_function(route.name, route.value))
    lines.append("};")
    return "\n".join(lines)


if __name__ == "__main__":
    with open("../vue-frontend/src/routes.ts", "w") as f:
        f.write(generate_ts_file(ApiRoutes))
