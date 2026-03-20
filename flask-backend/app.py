import traceback
import sys
import os
import logging
import threading
from dotenv import load_dotenv

load_dotenv()

from flask import (
    Flask,
    render_template,
    Response,
    jsonify,
    send_from_directory,
    request,
)
from flask_cors import CORS
from flask_compress import Compress
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)

import db
import routing_converters
from extensions import cache
from routes import ApiRoutes
from topas_portal.data_api.exceptions import (
    CohortDataNotLoadedError,
    DataLayerUnavailableError,
    IntensityUnitUnavailableError,
)
from topas_portal.data_api.data_api import CohortDataAPI

from topas_portal import utils
from topas_portal import transcripts_preprocess as transcript
from topas_portal import settings

from topas_portal import prexp_preprocess as pp
from topas_portal import topas_preprocess as bp
from topas_portal import correlations_preprocess as cp
from topas_portal import fetch_data_matrix as hp
from topas_portal import differential_expression as differential_test
from topas_portal import genomics_preprocess as genomics_process
from topas_portal import plotly_preprocess as plotlyprepare

debug = settings.DEBUG_MODE
if len(sys.argv) > 1 and sys.argv[1] == "test":
    debug = True

config = {
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
}
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# global variables
error_log = []
cohorts_db: CohortDataAPI = db.cohorts_db

app = Flask(__name__, static_folder="../dist/static", template_folder="../dist")

app.config.from_mapping(config)
app.config["config_file"] = cohorts_db.config.get_config_path()
app.config["LOCAL_HTTTP"] = cohorts_db.config.get_local_http()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["integration_http"] = cohorts_db.config.get_integration_test_http()
app.config["JWT_SECRET_KEY"] = settings.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = settings.JWT_ACCESS_TOKEN_EXPIRES

app.url_map.converters["data_type"] = routing_converters.DataTypeConverter
app.url_map.converters["intensity_unit"] = routing_converters.IntensityUnitConverter
app.url_map.converters["include_ref"] = routing_converters.IncludeRefConverter

cache.init_app(app)
jwt = JWTManager(app)
Compress(app)


def start_background_loader():
    thread = threading.Thread(target=cohorts_db.load_all_data)
    thread.daemon = True  # Allows thread to exit when the main program exits
    thread.start()


with app.app_context():
    from compartments.config import config_page
    from compartments.qc_app import qc_page
    from compartments.drug_app import drug_page

    # from compartments.drugscore_app import drugscore_page # under development
    from compartments.kinasescores_app import kinasescore_page
    from compartments.integration_log import integration_page
    from compartments.entityscore_app import entityscore_page
    from compartments.overview_app import overview_page
    from compartments.z_scoring_app import zscoring_page
    from compartments.ptmnavigator_app import ptmnavigator_page
    from compartments.patient_report.patient_report_app import patient_report_page

    if cohorts_db.config.do_load_data_on_startup() and (
        os.getenv("WERKZEUG_RUN_MAIN") == "true" or not debug
    ):
        start_background_loader()

app.register_blueprint(config_page)
app.register_blueprint(qc_page)
# app.register_blueprint(drugscore_page) # under development
app.register_blueprint(kinasescore_page)
app.register_blueprint(drug_page)
app.register_blueprint(integration_page)
app.register_blueprint(entityscore_page)
app.register_blueprint(overview_page)
app.register_blueprint(zscoring_page)
app.register_blueprint(ptmnavigator_page)
app.register_blueprint(patient_report_page)

CORS(app)

logging.basicConfig(filename=settings.PORTAL_LOG_FILE, level=logging.ERROR)


@app.route(ApiRoutes.INDEX)
def index():
    return render_template("index.html")


@app.route(ApiRoutes.FAVICON)
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route(ApiRoutes.AUTH_LOGIN, methods=["POST"])
# http://localhost:3832/auth/login
def auth_login():
    """
    Validates the provided password against the predefined system password.

    Body:
        password (str): The input password to be checked.

    Returns:
        pass: string
        access_token: string
    """
    data = request.get_json()
    password = data.get("password")

    if str(password) == settings.PASSWORD:
        token = create_access_token(identity="admin")
        return {"pass": "valid", "access_token": token}
    else:
        return {"pass": "invalid"}


@app.route(ApiRoutes.AUTH_ME, methods=["GET"])
@jwt_required()
# http://localhost:3832/auth/me
def auth_me():
    """
    Validates the jwt token and returns the user info.

    Returns:
        username: user name
        vallid: bool
    """
    return jsonify(username=get_jwt_identity(), valid=True)


@app.route(ApiRoutes.COHORT_NAMES)
# http://localhost:3832/cohort_names
def cohort_names():
    return jsonify(cohorts_db.config.get_cohort_names())


@app.route(ApiRoutes.COLUMN_NAMES)
# http://localhost:3832/colnames
def column_names():
    return jsonify(settings.front_end_col_names)


# http://localhost:3832/entityscore/status
@app.route(ApiRoutes.ENTITY_STATUS)
def entity_models_status():
    try:
        return jsonify(cohorts_db.config.config["use_entity_model"])
    except:
        return jsonify(0)


# http://localhost:3832/correlation/fpkmprotein/0
@app.route(ApiRoutes.CORRELATION_FPKM_PROTEIN)
def get_protein_fpkm_correlation(cohort_index: int):
    """
    Computes the correlation between protein abundance and transcript expression (FPKM) for a given cohort.

    Args:
        cohort_index (int): The index of the cohort for which the correlation is computed.

    Returns:
        str: A JSON-formatted string containing the correlation data between protein abundance
             and transcript expression across patients.

    Notes:
        - Retrieves transcript expression (FPKM) data.
        - Fetches protein abundance data for the specified cohort.
        - Computes the correlation across patients.
        - Converts the resulting correlation DataFrame to JSON format before returning.
    """
    transcript_df = cohorts_db.get_fpkm_df(intensity_unit=utils.IntensityUnit.INTENSITY)
    protein_intensity_df = cohorts_db.get_protein_abundance_df(
        cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
    )
    correlation_df = cp.get_correlation_across_patients(
        protein_intensity_df, transcript_df
    )
    return utils.df_to_json(correlation_df)


# http://localhost:3832/oncokb/api/cnv/EGFR/AMPLIFICATION
@app.route(ApiRoutes.ONCOKB_CNV)
def get_oncokb_cnv_annotation(identifier: str, cnv_type: str):
    """
    Retrieves Copy Number Variation (CNV) annotation for a given identifier from the OncoKB API.

    Args:
        identifier (str): The gene or variant identifier for which CNV annotation is requested.
        cnv_type (str): The type of CNV (e.g., amplification, deletion) to be queried.

    Returns:
        dict: A dictionary containing the CNV annotation data retrieved from the OncoKB API.

    Notes:
        - This function queries the OncoKB API for CNV annotations based on the provided identifier.
        - The `cnv_type` parameter specifies the type of copy number variation.
        - The returned data structure is dependent on the OncoKB API response format.
    """
    oncokb_api_token = cohorts_db.config.get_oncokb_api_token()
    return genomics_process.get_cnv_from_the_ONKOKB_api(
        identifier, cnv_type=cnv_type, oncokb_api_token=oncokb_api_token
    )


##################### Cohorts Loading and UPDATING
@app.route(ApiRoutes.RELOAD)
@jwt_required()
# http://localhost:3832/reload
def reload():
    cohorts_db.load_all_data()
    return Response("Uploaded!")


@app.route(ApiRoutes.RELOAD_DB_ZSCORES)
@jwt_required()
# http://localhost:3832/reloaddbz
def reload_db_zscores():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_pp_expression_z(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_fp_expression_z(cohorts_db.config)
    return Response("Uploaded to db!")


@app.route(ApiRoutes.RELOAD_DB_INTENSITY)
@jwt_required()
# http://localhost:3832/reloaddbi
def reload_db_intensity():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_pp_expression_intensity(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_fp_expression_intensity(cohorts_db.config)
    return Response("Uploaded to db!")


@app.route(ApiRoutes.RELOAD_METADATA)
@jwt_required()
# http://localhost:3832/reloadmeta
def reload_db_metadata():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_patient_meta_data(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_sample_annotation_df(cohorts_db.config)
    return Response("Uploaded meta data to db!")


@app.route(ApiRoutes.RELOAD_FP_INTENSITY_META)
@jwt_required()
# http://localhost:3832/reloadfpintensity
def reload_fp_intensity():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_fp_meta_expression(cohorts_db.config)
    return Response("Uploaded meta dat for the FP to db!")


@app.route(ApiRoutes.RELOAD_MAPPING_PROTEIN_SEQ)
@jwt_required()
# http://localhost:3832/reloadmapping
def reload_mapping_protein_seq():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_protein_seq_mapping_df(cohorts_db.config)
    return Response("Uploaded meta data to db!")


@app.route(ApiRoutes.RELOAD_TOPAS)
@jwt_required()
# http://localhost:3832/reloadtopas
def reload_topass():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_topas_scores(cohorts_db.config)
    return Response("Uploaded TOPAS to db!")


@app.route(ApiRoutes.RELOAD_TRANSCRIPTS)
@jwt_required()
# http://localhost:3832/reload/transcripts
def reload_transcripts():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_FPKM(cohorts_db.config.get_config())
    cohorts_db.provider._load_genomics(cohorts_db.config.get_config())
    cohorts_db.provider._load_onkoKB_annotations(cohorts_db.config.get_config())


@app.route(ApiRoutes.RELOAD_TOPAS_ANNOTATIONS)
@jwt_required()
# http://localhost:3832/reload/topasannotations
def reload_topas_annotations():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_topas_annotation_tables(cohorts_db.config.get_config())


@app.route(ApiRoutes.RELOAD_COHORT)
@jwt_required()
# http://localhost:3832/reload/PAN_CANCER
def reload_current_cohort(cohort: str):
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_tables(cohorts_db.config, cohort_names=[cohort])
    return Response("Updated!")


@app.route(ApiRoutes.PATH_CHECK)
@jwt_required()
def path_checker(path: str):
    if os.path.exists(path.replace("topas_slash", "/")):
        return Response("True")
    else:
        return Response("False")


#####################################################################
@app.route(ApiRoutes.ANNOTATION_MODALITY)
# http://localhost:3832/annotation/0/allpatients
# http://localhost:3832/annotation/0/allbatch
# http://localhost:3832/annotation/0/allentities
def get_all_modality_possibilities(cohort_index: int, modality: str):
    return pp.get_list_by_selected_modality_per_cohort(
        cohorts_db, cohort_index, modality
    )


@app.route(ApiRoutes.VENN_PATIENT_COMPARE)
# http://localhost:3832/venn/0/patientcompare/fp/C3L-00032-1
def get_patients_proteins(cohort_index: int, level: utils.DataType, patients: str):
    return pp.get_patients_proteins_as_json(cohorts_db, cohort_index, level, patients)


@app.route(ApiRoutes.VENN_BATCH_COMPARE)
# http://localhost:3832/venn/0/batchcompare/fp/1_2_43
def get_batches_proteins(cohort_index: int, level: utils.DataType, batchlists: str):
    return pp.get_batches_proteins_as_json(cohorts_db, cohort_index, level, batchlists)


@app.route(ApiRoutes.UPDATE_LOG)
# http://localhost:3832/update/logs
def update_log():
    log = "".join(cohorts_db.logger.get_log_messages())
    return jsonify(log)


@app.route(ApiRoutes.ERROR_LOG)
# http://localhost:3832/error/logs
def get_error_log():
    log = "".join(error_log)
    return jsonify(log)


@app.route(ApiRoutes.PATIENT_CENTRIC_SUMMED_INTENSITY)
# http://localhost:3832/patientcentric/summed_intensity/0/fp
# http://localhost:3832/patientcentric/summed_intensity/0/pp
def get_sum_intensities_pp_level(
    cohort_index: int,
    level: utils.DataType,
    include_ref: utils.IncludeRef,
):
    if settings.DATABASE_MODE:
        return {}  # this query is not implemented yet in the database

    return utils.df_to_json(
        pp.summed_intensities_per_patient(cohorts_db, cohort_index, level)
    )


@app.route(ApiRoutes.PATIENT_CENTRIC_COUNTS)
@cache.cached(timeout=50)
# http://localhost:3832/patientcentric/counts/0/fp
def get_identifications_frequency(
    cohort_index: int,
    level: utils.DataType,
    include_ref: utils.IncludeRef,
):
    if settings.DATABASE_MODE:
        return {}  # this query is not implemented yet in the database

    return utils.df_to_json(
        pp.num_identifications_per_patient(cohorts_db, cohort_index, level)
    )


@app.route(ApiRoutes.TOPAS_ANNOTATIONS)
# http://localhost:3832/topas/annotations
def topas_annotations():
    return utils.df_to_json(cohorts_db.get_topas_annotation_df())


@app.route(ApiRoutes.ANALYTES_ANNOTATION_TABLE)
@cache.cached(timeout=3600)
# http://localhost:3832/0/protein/annotations
def get_annotation_table(cohort_index: int, level: utils.DataType):
    return utils.df_to_json(
        pp.get_annotation_df(cohorts_db, cohort_index, level).reset_index()
    )


@app.route(ApiRoutes.PROTEIN_LIST)
@cache.cached(timeout=3600)
# http://localhost:3832/0/protein/list
def get_list_proteins(cohort_index: int, level: str):
    return jsonify(
        sorted(
            hp.fetch_data_matrix(
                cohorts_db,
                cohort_index,
                utils.get_selection_list_data_type(level),
                identifiers=None,
                intensity_unit=None,
            ).index
        )
    )


@app.route(ApiRoutes.TOPAS_IDS)
# http://localhost:3832/topas/0/topasids
def topas_unique(cohort_index: int):
    return bp.get_topas_unique(cohorts_db.get_topas_rtk_scores_df(cohort_index))


@app.route(ApiRoutes.TOPAS_SUBSCORE)
# http://localhost:3832/topas/subscore/0/ABL
def topas_subtype(cohort_index: int, topasname: str):
    return bp.get_topas_subscore_data(cohorts_db, cohort_index, topasname)


@app.route(ApiRoutes.SAMPLE_ANNOTATION)
# http://localhost:3832/0/sampleanot
def sample_annotation(cohort_index: int):
    return utils.df_to_json(cohorts_db.get_sample_annotation_df(cohort_index))


@app.route(ApiRoutes.PATIENTS)
@cache.cached(timeout=50)
# http://localhost:3832/0/patients
def patients(cohort_index: int):
    return utils.df_to_json(cohorts_db.get_patient_metadata_df(cohort_index))


@app.route(ApiRoutes.PATIENTS_GENOMICS_ANNOTATIONS)
@cache.cached(timeout=50)
# http://localhost:3832/0/patients/genomics_annotations/EGFR
def patients_genomics_annotations(cohort_index: int, identifier: str):
    patients_meta_df = cohorts_db.get_patient_metadata_df(cohort_index).copy()
    patients_meta_df = genomics_process.merge_data_with_genomics_alterations(
        cohorts_db, patients_meta_df, identifier, annotation_type="genomics_annotations"
    )
    patients_meta_df = genomics_process.merge_data_with_genomics_alterations(
        cohorts_db, patients_meta_df, identifier, annotation_type="oncoKB_annotations"
    )
    return utils.df_to_json(patients_meta_df)


@app.route(ApiRoutes.PATIENTS_METADATA)
@cache.cached(timeout=50)
# http://localhost:3832/0/metadata
def patientsmetadata(cohort_index: int, include_ref: utils.IncludeRef):
    sample_annotation_df = cohorts_db.get_sample_annotation_df(
        cohort_index, include_ref
    )
    if "Entity" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df.drop(["Entity"], axis=1)
    patient_metadata_df = cohorts_db.get_patient_metadata_df(cohort_index)
    final_df = utils.merge_with_patients_meta_df(
        sample_annotation_df, patient_metadata_df
    )
    return utils.df_to_json(final_df)


@app.route(ApiRoutes.PATIENTS_METADATA_FIELDS)
# http://localhost:3832/0/metadata/fields
def patients_meta_fields(cohort_index: int):
    return jsonify(sorted(cohorts_db.get_patient_metadata_df(cohort_index).columns))


@app.route(ApiRoutes.PATIENTS_METADATA_FIELD_VALUES)
# http://localhost:3832/0/metadata/fields/code_oncotree
def unique_field_intereset(cohort_index: int, fieldname: str):
    unique_items = (
        cohorts_db.get_patient_metadata_df(cohort_index)[fieldname]
        .dropna()
        .unique()
        .tolist()
    )
    unique_list = [str(x) for x in unique_items]
    return jsonify(sorted(unique_list))


@app.route(ApiRoutes.PATIENTS_BY_FIELD_INTEREST)
# http://localhost:3832/0/metadata/fields/code_oncotree/patients/UCEC
def get_patientslist_by_fieldname(
    cohort_index: int, fieldname: str, field_interest: str
):
    df = cohorts_db.get_patient_metadata_df(cohort_index).copy()
    field_interest = field_interest.split(",")
    if len(field_interest) > 0:
        field_interest = [str(x) for x in field_interest]
        df[fieldname] = df[fieldname].astype(str)

    return jsonify(
        df[utils.ColumnNames.SAMPLE_NAME][df[fieldname].isin(field_interest)].tolist()
    )


@app.route(ApiRoutes.PATIENTS_ALL_ENTITIES)
# http://localhost:3832/patients/0/all_entities
def get_patients_entities(cohort_index: int):
    return utils.df_to_json(cohorts_db.get_patients_entities_df(cohort_index))


# http://localhost:3832/genomics/EGFR
@app.route(ApiRoutes.GENOMICS_IDENTIFIER)
def get_genomes(identifier: str):
    genomics_df = genomics_process.get_genomics_alterations_per_identifier(
        cohorts_db, identifier
    )
    genomics_df[utils.ColumnNames.SAMPLE_NAME] = genomics_df.index
    return utils.df_to_json(genomics_df)


@app.route(ApiRoutes.DENSITY_FPKM)
# http://localhost:3832/density/fpkm/EGFR/z_scored
def density_calc_fpkm(identifier: str, intensity_unit: utils.IntensityUnit):
    return transcript.get_density_calc_fpkm(cohorts_db, identifier, intensity_unit)


@app.route(ApiRoutes.DENSITY_PROTEIN)
# http://localhost:3832/0/density/protein/EGFR/z_scored
def density_calc_protein(
    cohort_index: int, identifier: str, intensity_unit: utils.IntensityUnit
):
    return pp.get_density_calc_protein(
        cohorts_db, cohort_index, identifier, intensity_unit
    )


@app.route(ApiRoutes.ABUNDANCE)
@cache.cached(timeout=50)
# http://localhost:3832/0/protein/abundance/EGFR/noimpute
# http://localhost:3832/0/fpkm/abundance/EGFR/noimpute
# http://localhost:3832/0/kinase/abundance/EGFR/noimpute
# http://localhost:3832/0/phospho_score/abundance/EGFR/noimpute
# http://localhost:3832/0/psite/abundance/_pYSPSQNpSPIHHIPSR_/noimpute
def abundance(
    cohort_index: int,
    level: utils.DataType,
    identifier: str,
    imputation: str,
    include_ref: utils.IncludeRef,
):
    return pp.get_abundance_with_annotations(
        cohorts_db,
        cohort_index,
        level,
        identifier,
        utils.ImputationMode(imputation),
        include_ref,
    )


@app.route(ApiRoutes.CORRELATION)
@cache.cached(timeout=50)
# http://localhost:3832/0/topas_score/correlation/protein/EGFR/z_scored
# http://localhost:3832/0/phospho_score/correlation/protein/EGFR/intensity
# http://localhost:3832/0/fpkm/correlation/protein/EGFR/z_scored
def correlation(
    cohort_index: int,
    level: utils.DataType,
    identifier: str,
    level_2: utils.DataType,
    intensity_unit: utils.IntensityUnit,
    patients_list: str = None,
):
    patients_list = None if patients_list == "all" else patients_list.split(",")
    return cp.compute_correlation_df(
        cohorts_db,
        cohort_index,
        identifier,
        level,
        level_2,
        intensity_unit,
        patients_list=patients_list,
    )


@app.route(ApiRoutes.HEATMAP)
def heatmap(
    cohort_index: int,
    level: utils.DataType,
    identifier: str,
    patients: str,
    output_format: str,
):
    merged_df = hp.fetch_data_matrix_with_sample_annotations(
        cohorts_db,
        cohort_index,
        level,
        identifier.split(","),
        patients.split(","),
        include_ref=utils.IncludeRef.INCLUDE_REF,
    )
    if output_format == "plot":
        merged_df.index = merged_df["Sample name"]
        sample_annot_cols = merged_df.columns.intersection(
            settings.SAMPLE_ANNOTATION.values()
        )
        plot_df = merged_df.drop(sample_annot_cols, axis=1)
        return plotlyprepare.get_simple_heatmap(plot_df, level.value)
    elif output_format == "table":
        return utils.df_to_json(merged_df)
    else:
        raise ValueError(f"Unknown output format {output_format}")


@app.route(ApiRoutes.DIFFERENTIAL)
# http://localhost:3832/differential/0/intensity/index_346_286_463/index_444_514_592
# http://localhost:3832/differential/0/phosphopeptides/index_346_286_463/index
# http://localhost:3832/differential/0/topasscores/index_346_286_463/index_444_514_592
def get_t_test_json(
    cohort_index: int,
    grp1_ind: str,
    grp2_ind: str,
    level: utils.DataType,
    y_axis_type: str,
):
    return utils.df_to_json(
        differential_test.get_data_for_t_test(
            cohorts_db,
            cohort_index,
            grp1_ind,
            grp2_ind,
            level,
            y_axis_type,
        )
    )


@app.errorhandler(DataLayerUnavailableError)
@app.errorhandler(CohortDataNotLoadedError)
@app.errorhandler(IntensityUnitUnavailableError)
def handle_cohort_data_not_loaded_error(err):
    portal_logger(f"{type(err).__name__}: {err}", log_list=error_log)
    portal_logger(traceback.format_exc(), log_list=error_log)
    return "", f"400 {type(err).__name__}: {err}"


@app.errorhandler(Exception)
def handle_exception(err):
    portal_logger(f"{type(err).__name__}: {err}", log_list=error_log)
    portal_logger(traceback.format_exc(), log_list=error_log)
    return Response(f"{type(err).__name__}: {err}"), 500


def portal_logger(message, log_list: list = error_log):
    print(message)
    log_list.append(f"{utils.time_now()}{message}#####")
    log_list.append(" topas_separator ")


if __name__ == "__main__":
    if os.path.exists("record.log"):
        utils.log_delete("record.log")

    app.run(
        debug=debug, use_reloader=debug, host="0.0.0.0", port=settings.CI_BACKEND_PORT
    )
