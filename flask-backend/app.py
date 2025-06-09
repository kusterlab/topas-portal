import traceback
import sys
import os
import logging
import shutil
import threading
from pathlib import Path
import zipfile

from flask import Flask, render_template, Response, jsonify, send_from_directory
from flask_cors import CORS
from flask_caching import Cache
from flask_compress import Compress

import db
import routing_converters

from topas_portal.routes import ApiRoutes
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

app.url_map.converters["data_type"] = routing_converters.DataTypeConverter
app.url_map.converters["intensity_unit"] = routing_converters.IntensityUnitConverter
app.url_map.converters["include_ref"] = routing_converters.IncludeRefConverter

cache = Cache(app)
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
    from compartments.proteinscore_app import proteinscore_page
    from compartments.kinasescores_app import kinasescore_page
    from compartments.integration_log import integration_page
    from compartments.entityscore_app import entityscore_page
    from compartments.overview_app import overview_page
    from compartments.z_scoring_app import zscoring_page

    if cohorts_db.config.do_load_data_on_startup():
        start_background_loader()

app.register_blueprint(config_page)
app.register_blueprint(qc_page)
# app.register_blueprint(drugscore_page) # under development
app.register_blueprint(proteinscore_page)
app.register_blueprint(kinasescore_page)
app.register_blueprint(drug_page)
app.register_blueprint(integration_page)
app.register_blueprint(entityscore_page)
app.register_blueprint(overview_page)
app.register_blueprint(zscoring_page)

CORS(app)

logging.basicConfig(filename=settings.PORTAL_LOG_FILE, level=logging.ERROR)


@app.route(ApiRoutes.INDEX)
def index():
    return render_template("index.html")


@app.route(ApiRoutes.PASSWORD_CHECK)
# http://localhost:3832/password/topaswp3
def password_check(password: str):
    """
    Validates the provided password against the predefined system password.

    Args:
        password (str): The input password to be checked.

    Returns:
        dict: A dictionary with a key 'pass' and a value of 'valid' if the password matches
              the system password, otherwise 'invalid'.
    """
    if str(password) == settings.PASSWORD:
        return {"pass": "valid"}
    else:
        return {"pass": "invalid"}


@app.route(ApiRoutes.COHORT_NAMES)
# http://localhost:3832/cohort_names
def cohort_names():
    return jsonify(cohorts_db.config.get_cohort_names())


@app.route(ApiRoutes.COLUMN_NAMES)
# http://localhost:3832/colnames
def column_names():
    return jsonify(settings.front_end_col_names)


@app.route(ApiRoutes.FAVICON)
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@cache.cached(timeout=50)
@app.route(ApiRoutes.PATIENT_REPORT_TABLE)
def get_patient_report_table(
    cohort_index: int, patient: str, level: utils.DataType, downloadmethod: str
):
    """Returns tables from the patient reports.

    Example: http://localhost:3832/0/patient_report/I007-031-108742/protein/onfly

    Args:
        cohort_index (int): cohort index
        patient (str): patient identifier
        level (utils.DataType): modality (e.g. full proteome, topas, etc.) to get
            reports for, see utils.DataType.
        downloadmethod (str): "fromreport" or "onfly". Defaults to "onfly".

    Returns:
        Response: jsonified dataframe with patient report table.
    """
    return utils.df_to_json(
        pp.get_reports_per_patient(
            cohorts_db,
            cohort_index,
            patient,
            utils.DataType(level),
            download_method=downloadmethod,
        )
    )


@cache.cached(timeout=50)
@app.route(ApiRoutes.PATIENT_REPORT_TABLE_XLSX)
# http://localhost:3832/0/patient_reports/I007-031-108742
def get_patient_reports_as_attachment(cohort_index: int, patients: str):
    """Returns patient report excel files. For multiple reports, a zip file is returned.

    Args:
        cohort_index (int): cohort index
        patient (str): patient identifiers separated by semicolons

    Returns:
        Response: excel or zip file with patient report(s)
    """
    reports_dir = cohorts_db.get_report_dir(cohort_index)
    patients = patients.split(";")

    def get_patient_report_path(patient_identifier: str):
        return (
            reports_dir + "/Reports/" + patient_identifier + "_proteomics_results.xlsx"
        )

    if len(patients) == 1:
        path_to_patient_results = get_patient_report_path(patients[0])
        if not os.path.exists(path_to_patient_results):
            return f"Unable to download report for {patients[0]}", 400
        shutil.copy(path_to_patient_results, app.config["UPLOAD_FOLDER"])
        return send_from_directory(
            app.config["UPLOAD_FOLDER"],
            Path(path_to_patient_results).name,
            as_attachment=True,
        )
    elif len(patients) > 1:
        paths_to_patient_results = []
        for patient in patients:
            path_to_patient_results = get_patient_report_path(patient)
            if not os.path.exists(path_to_patient_results):
                return f"Unable to download report for {patient}", 400
            paths_to_patient_results.append(path_to_patient_results)

        output_zipfile = os.path.join(
            app.config["UPLOAD_FOLDER"], "patient_reports.zip"
        )
        with zipfile.ZipFile(output_zipfile, "w") as zipFile:
            for path_to_patient_results in paths_to_patient_results:
                zipFile.write(
                    path_to_patient_results,
                    Path(path_to_patient_results).name,
                    compress_type=zipfile.ZIP_STORED,
                )  # no compression, because Excel files are already binary
        return send_from_directory(
            app.config["UPLOAD_FOLDER"], Path(output_zipfile).name, as_attachment=True
        )


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
    protein_intensity_df = cohorts_db.get_protein_abundance_df(cohort_index).copy()
    correlation_df = cp.wrapper_get_correlation_across_patients(
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
# http://localhost:3832/reload
def reload():
    cohorts_db.load_all_data()
    return Response("Uploaded!")


@app.route(ApiRoutes.RELOAD_DB_ZSCORES)
# http://localhost:3832/reloaddbz
def reload_db_zscores():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_pp_expression_z(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_fp_expression_z(cohorts_db.config)
    return Response("Uploaded to db!")


@app.route(ApiRoutes.RELOAD_DB_INTENSITY)
# http://localhost:3832/reloaddbi
def reload_db_intensity():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_pp_expression_intensity(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_fp_expression_intensity(cohorts_db.config)
    return Response("Uploaded to db!")


@app.route(ApiRoutes.RELOAD_METADATA)
# http://localhost:3832/reloadmeta
def reload_db_metadata():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_patient_meta_data(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_sample_annotation_df(cohorts_db.config)
    return Response("Uploaded meta data to db!")


@app.route(ApiRoutes.RELOAD_FP_INTENSITY_META)
# http://localhost:3832/reloadfpintensity
def reload_fp_intensity():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_fp_meta_expression(cohorts_db.config)
    return Response("Uploaded meta dat for the FP to db!")


@app.route(ApiRoutes.RELOAD_MAPPING_PROTEIN_SEQ)
# http://localhost:3832/reloadmapping
def reload_mapping_protein_seq():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_protein_seq_mapping_df(cohorts_db.config)
    return Response("Uploaded meta data to db!")


@app.route(ApiRoutes.RELOAD_TOPAS)
# http://localhost:3832/reloadtopas
def reload_topass():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_topas_scores(cohorts_db.config)
    return Response("Uploaded TOPAS to db!")


@app.route(ApiRoutes.RELOAD_TRANSCRIPTS)
# http://localhost:3832/reload/transcripts
def reload_transcripts():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_FPKM(cohorts_db.config.get_config())
    cohorts_db.provider._load_genomics(cohorts_db.config.get_config())
    cohorts_db.provider._load_onkoKB_annotations(cohorts_db.config.get_config())


@app.route(ApiRoutes.RELOAD_DIGEST)
def reload_insilico_digest():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_insilicodigest(cohorts_db.config.get_config())
    return Response("Uploaded digesetd peptide map to db!")


@app.route(ApiRoutes.RELOAD_TOPAS_ANNOTATIONS)
# http://localhost:3832/reload/topasannotations
def reload_topas_annotations():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_topas_annotation_tables(cohorts_db.config.get_config())


@app.route(ApiRoutes.RELOAD_DIGEST)
# this function is not used at the moment; it can be used to calculate iBAQ in case needed
def get_the_insilico_peptide_digested():
    return utils.df_to_json(cohorts_db.get_digestes_peptides_maps())


# http://localhost:3832/reload/PAN_CANCER
@app.route(ApiRoutes.RELOAD_COHORT)
def reload_current_cohort(cohort: str):
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_tables(cohorts_db.config, cohort_names=[cohort])
    return Response("Updated!")


@app.route(ApiRoutes.PATH_CHECK)
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
def get_patients_proteins(cohort_index: int, pp_fp: str, patientslists: str):
    return pp.get_patients_proteins_as_json(
        cohorts_db, cohort_index, pp_fp, patientslists
    )


@app.route(ApiRoutes.VENN_BATCH_COMPARE)
# http://localhost:3832/venn/0/batchcompare/fp/1_2_43
def get_batches_proteins(cohort_index: int, pp_fp: str, batchlists: str):
    return pp.get_batches_proteins_as_json(cohorts_db, cohort_index, pp_fp, batchlists)


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


@app.route(ApiRoutes.PATIENT_CENTRIC_PP_INTENSITY)
# http://localhost:3832/patientcentric/ppintensity/0/fp
# http://localhost:3832/patientcentric/ppintensity/0/pp
def get_sum_intensities_pp_level(cohort_index: int, dtype: str):
    if settings.DATABASE_MODE:
        return {}  # this query is too slow in the database

    return utils.df_to_json(
        pp.sum_intensities_across_all_patients(cohorts_db, cohort_index, dtype=dtype)
    )


@app.route(ApiRoutes.PATIENT_CENTRIC_PROTEIN_COUNTS)
@cache.cached(timeout=50)
# http://localhost:3832/patientcenteric/proteincounts/0/fp
def get_identifications_frequency(cohort_index: int, fp_pp: str):
    if settings.DATABASE_MODE:
        return {}  # this query is too slow in the database

    return utils.df_to_json(
        pp.identifications_across_all_patients(cohorts_db, fp_pp, cohort_index)
    )


@app.route(ApiRoutes.TOPAS)
# http://localhost:3832/topas/0/ALK/topas_score
def topas(cohort_index: int, topas_names: str, score_type: str):
    return bp.get_topas_data(cohorts_db, cohort_index, topas_names, score_type)


@app.route(ApiRoutes.TOPAS_ANNOTATIONS)
# http://localhost:3832/topas/annotations
def topas_annotations():
    return utils.df_to_json(cohorts_db.get_topas_annotation_df())


@app.route(ApiRoutes.TOPAS_LOLLIPOP)
# http://localhost:3832/topas/lolipopdata/0/I002-025-226610
def get_circular_barplot_data(cohort_index: int, patient: str):
    return utils.df_to_json(
        bp.get_circular_barplot_data_pathways(
            cohorts_db.get_topas_scores_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            patient,
        )
    )


@app.route(ApiRoutes.TOPAS_LOLLIPOP_TUMOR)
# http://localhost:3832/topas/lolipopdata/0/I002-025-226610/tumor_antigen
def get_circular_barplot_data_tumor(cohort_index: int, patient: str):
    return utils.df_to_json(
        bp.get_circular_barplot_data_tumor_antigens(
            cohorts_db.get_protein_abundance_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            patient,
        )
    )


@app.route(ApiRoutes.TOPAS_EXPRESSION_DOWNSTREAM)
# http://localhost:3832/topas/lolipopdata/expression/0/I002-025-226610/downstream_signaling
def get_lolipopexpression_down_stream(cohort_index: int, patient: str):
    return utils.df_to_json(
        bp.getlolipop_expression_topas(
            cohorts_db.get_protein_abundance_df(
                cohort_index,
                intensity_unit=utils.IntensityUnit.Z_SCORE,
                patient_name=patient,
            ),
            cohorts_db.get_topas_scores_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            patient,
            type_to_filter="downstream signaling",
        )
    )


@app.route(ApiRoutes.PROTEIN_LIST)
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


@app.route(ApiRoutes.TOPAS_EXPRESSION_RTK)
# http://localhost:3832/topas/lolipopdata/expression/0/I002-025-226610/rtk
def get_lolipopexpression_rtk(cohort_index: int, patient: str):
    return utils.df_to_json(
        bp.getlolipop_expression_topas(
            cohorts_db.get_protein_abundance_df(
                cohort_index,
                intensity_unit=utils.IntensityUnit.Z_SCORE,
                patient_name=patient,
            ),
            cohorts_db.get_topas_scores_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            patient,
            type_to_filter="RTK",
        )
    )


@app.route(ApiRoutes.TOPAS_IDS)
# http://localhost:3832/topas/0/topasids
def topas_unique(cohort_index: int, categories: str):
    return bp.get_topas_unique(cohorts_db.get_topas_scores_df(cohort_index), categories)


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
    patients_meta_df = genomics_process._merge_data_with_genomics_alterations(
        cohorts_db, patients_meta_df, identifier, annotation_type="genomics_annotations"
    )
    patients_meta_df = genomics_process._merge_data_with_genomics_alterations(
        cohorts_db, patients_meta_df, identifier, annotation_type="oncoKB_annotations"
    )
    return utils.df_to_json(patients_meta_df)


@app.route(ApiRoutes.PATIENTS_METADATA)
@cache.cached(timeout=50)
# http://localhost:3832/0/metadata
def patientsmetadata(cohort_index: int):
    sample_annotation_df = cohorts_db.get_sample_annotation_df(cohort_index)
    if "Entity" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df.drop(["Entity"], axis=1)
    patien_meta_df = cohorts_db.get_patient_metadata_df(cohort_index)
    final_df = utils.merge_with_patients_meta_df(sample_annotation_df, patien_meta_df)
    final_df = final_df.dropna()
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


# http://localhost:3832/oncokb/EGFR
@app.route(ApiRoutes.ONCOKB_IDENTIFIER)
def get_oncokb(identifier: str):
    genomics_df = genomics_process.get_genomics_alterations_per_identifier(
        cohorts_db, identifier, annotation_type="oncoKB_annotations"
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


@app.route(ApiRoutes.IMPORTANT_PHOSPHO)
# http://localhost:3832/0/important_phospho/EGFR
def get_important_phospho(cohort_index: int, identifier: str):
    return bp.get_topas_subscore_data_per_type(
        cohorts_db.get_report_dir(cohort_index),
        identifier,
        sub_type="important phosphorylation",
        return_json=True,
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
    return pp.get_abundance(
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
# http://localhost:3832/0/important_phosphorylation/correlation/protein/EGFR/z_scored
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


@app.route(ApiRoutes.BATCH_EFFECT)
# http://localhost:3832/batcheffect/expression_level/0/ABL/1,23,24/plot
# http://localhost:3832/batcheffect/phospho_level/0/ABL/1,23,24/plot
# http://localhost:3832/batcheffect/kinase_level/0/ALK/1,23,24/plot
def batch_effect(
    cohort_index: str,
    identifier: str,
    sample_ids: str,
    data_type: str,
    level: utils.DataType,
):
    merged_df = hp.fetch_data_matrix_with_sample_annotations(
        cohorts_db,
        cohort_index,
        identifier.split(","),
        sample_ids.split(","),
        level,
    )
    return utils.merged_df_to_json(data_type, merged_df, level.value)


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

    debug = settings.DEBUG_MODE
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        debug = True

    app.run(
        debug=debug, use_reloader=debug, host="0.0.0.0", port=settings.CI_BACKEND_PORT
    )
