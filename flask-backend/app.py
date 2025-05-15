import traceback
import sys
import os
import logging
import shutil
from pathlib import Path
import zipfile

from flask import Flask, render_template, Response, jsonify, send_from_directory
from flask_cors import CORS
from flask_caching import Cache
from flask_compress import Compress

from topas_portal.data_api.exceptions import (
    CohortDataNotLoadedError,
    DataLayerUnavailableError,
    IntensityUnitUnavailableError,
)
import db
import topas_portal.utils as utils
import topas_portal.transcripts_preprocess as transcript

import topas_portal.settings as settings
import topas_portal.prexp_preprocess as pp
import topas_portal.topas_preprocess as bp
import topas_portal.correlations_preprocess as cp

import topas_portal.fetch_data_matrix as hp
import topas_portal.differential_expression as differential_test
import topas_portal.genomics_preprocess as genomics_process


config = {
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
}
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

error_log = []

cohorts_db = db.cohorts_db

app = Flask(__name__, static_folder="../dist/static", template_folder="../dist")
app.config.from_mapping(config)
app.config["config_file"] = cohorts_db.config.get_config_path()
app.config["LOCAL_HTTTP"] = cohorts_db.config.get_local_http()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["integration_http"] = cohorts_db.config.get_integration_test_http()
cache = Cache(app)
Compress(app)

with app.app_context():
    from compartments.qc_app import qc_page
    from compartments.drug_app import drug_page

    # from compartments.drugscore_app import drugscore_page # under development
    from compartments.proteinscore_app import proteinscore_page
    from compartments.kinasescores_app import kinasescore_page
    from compartments.integration_log import integration_page
    from compartments.entityscore_app import entityscore_page
    from compartments.overview_app import overview_page
    from compartments.z_scoring_app import zscoring_page

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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/config")
# http://localhost:3832/config
def configuration():
    cohorts_db.config.reload_config()
    return jsonify(cohorts_db.config.get_config())


@app.route("/config/checkall")
# http://localhost:3832/config/checkall
def configuration_checks():
    cohorts_db.config.reload_config()
    return utils.check_all_config_file(cohorts_db.config.get_config())


@app.route("/password/<password>")
# http://localhost:3832/password/topaswp3
def password_check(password):
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


@app.route("/config/config_path")
def config_path():
    return {"path": str(cohorts_db.config.config_path)}


@app.route("/cohort_names")
# http://localhost:3832/cohort_names
def cohort_names():
    return jsonify(cohorts_db.config.get_cohort_names())


@app.route("/colnames")
# http://localhost:3832/colnames
def column_names():
    return jsonify(settings.front_end_col_names)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@cache.cached(timeout=50)
@app.route("/<cohort_index>/patient_report/<patient>/<level>/<downloadmethod>")
# http://localhost:3832/patient_report/I007-031-108742/0/protein/onfly
def get_patient_report_table(
    cohort_index, patient: str, level: str, downloadmethod: str
):
    """Returns tables from the patient reports.

    Args:
        cohort_index (int): cohort index
        patient (str): patient identifier
        level (str): see utils.DataType
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
@app.route("/<int:cohort_index>/patient_reports/<patients>")
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


# http://localhost:3832//entityscore/status
@app.route("/entityscore/status")
def entity_models_status():
    try:
        return jsonify(cohorts_db.config.config["use_entity_model"])
    except:
        return jsonify(0)


# http://localhost:3832/correlation/fpkmprotein/0
@app.route("/correlation/fpkmprotein/<cohort_index>")
def get_protein_fpkm_correlation(cohort_index):
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
@app.route("/oncokb/api/cnv/<identifier>/<cnv_type>")
def get_oncokb_cnv_annotation(identifier, cnv_type):
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
    return genomics_process.get_cnv_from_the_ONKOKB_api(identifier, cnv_type=cnv_type)


##################### Cohorts Loading and UPDATING
@app.route("/reload")
# http://localhost:3832/reload
def reload():
    cohorts_db.load_all_data()
    return Response("Uploaded!")


@app.route("/reloaddbz")
# http://localhost:3832/reloaddbz
def reload_db_zscores():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_pp_expression_z(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_fp_expression_z(cohorts_db.config)
    return Response("Uploaded to db!")


@app.route("/reloaddbi")
# http://localhost:3832/reloaddbi
def reload_db_intensity():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_pp_expression_intensity(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_fp_expression_intensity(cohorts_db.config)
    return Response("Uploaded to db!")


@app.route("/reloadmeta")
# http://localhost:3832/reloadmeta
def reload_db_metadata():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_patient_meta_data(cohorts_db.config)
    cohorts_db.provider.load_all_to_db_sample_annotation_df(cohorts_db.config)
    return Response("Uploaded meta data to db!")


@app.route("/reloadfpintensitymeta")
# http://localhost:3832/reloadfpintensity
def reload_fp_intensity():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_fp_meta_expression(cohorts_db.config)
    return Response("Uploaded meta dat for the FP to db!")


@app.route("/reloadmapping")
# http://localhost:3832/reloadmapping
def reload_mapping_protein_seq():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_protein_seq_mapping_df(cohorts_db.config)
    return Response("Uploaded meta data to db!")


@app.route("/reloadtopass")
# http://localhost:3832/reloadtopas
def reload_topass():
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_all_to_db_topas_scores(cohorts_db.config)
    return Response("Uploaded TOPAS to db!")


@app.route("/reload/transcripts")
# http://localhost:3832/reload/transcripts
def reload_transcripts():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_FPKM(cohorts_db.config.get_config())
    cohorts_db.provider._load_genomics(cohorts_db.config.get_config())
    cohorts_db.provider._load_onkoKB_annotations(cohorts_db.config.get_config())


@app.route("/reload/digest")
def reload_insilico_digest():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_insilicodigest(cohorts_db.config.get_config())
    return Response("Uploaded digesetd peptide map to db!")


@app.route("/reload/topasannotations")
# http://localhost:3832/reload/topasannotations
def reload_topas_annotations():
    cohorts_db.config.reload_config()
    cohorts_db.provider._load_topas_annotation_tables(cohorts_db.config.get_config())


@app.route("/digest/numpep")
# this function is not used at the moment; it can be used to calculate iBAQ in case needed
def get_the_insilico_peptide_digested():
    return utils.df_to_json(cohorts_db.get_digestes_peptides_maps())


# http://localhost:3832/reload/PAN_CANCER
@app.route("/reload/<cohort>")
def reload_current_cohort(cohort):
    cohorts_db.config.reload_config()
    cohorts_db.provider.load_tables(cohorts_db.config, cohort_names=[cohort])
    return Response("Updated!")


# http://localhost:3832/update/FP/INFORM/0
@app.route("/update/<key>/<cohort>/<value>")
def config_updater(key, cohort, value):
    """
    Updates the configuration settings for a given key and cohort, then checks if the provided value exists as a file or directory.

    Args:
        key (str): The configuration key to update.
        cohort (str): The cohort-specific context for the configuration update.
        value (str): The new value to be assigned to the configuration key.

    Returns:
        Response: An HTTP response indicating whether the provided value exists as a file or directory.

    Notes:
        - Calls `cohorts_db.config.update_config_values()` to update the configuration.
        - Uses `os.path.exists(value)` to check if the new value corresponds to an existing file or directory.
        - Returns a Flask `Response` object with a string representation of the existence check result.
    """
    cohorts_db.config.update_config_values(key, cohort, value)
    return Response(str(os.path.exists(value)))


# http://localhost:3832/addcohort/new_cohort
@app.route("/addcohort/<cohort>")
def add_cohort(cohort):
    cohorts_db.config.add_new_cohort_placeholder(cohort)
    cohorts_db.provider.load_single_cohort_with_empty_data(cohort)
    return {"done": True}


@app.route("/path/check/<path>")
def path_checker(path):
    if os.path.exists(path.replace("topas_slash", "/")):
        return Response("True")
    else:
        return Response("False")


#####################################################################
@app.route("/annotation/<cohort_index>/<modality>")
# http://localhost:3832/annotation/0/allpatients
# http://localhost:3832/annotation/0/allbatch
# http://localhost:3832/annotation/0/allentities
def get_all_modality_possibilities(cohort_index, modality):
    return pp.get_list_by_selected_modality_per_cohort(
        cohorts_db, cohort_index, modality
    )


@app.route("/venn/<cohort_index>/patientcompare/<pp_fp>/<patientslists>")
# http://localhost:3832/venn/0/patientcompare/fp/C3L-00032-1
def get_patients_proteins(cohort_index, pp_fp, patientslists):
    return pp.get_patients_proteins_as_json(
        cohorts_db, cohort_index, pp_fp, patientslists
    )


@app.route("/venn/<cohort_index>/batchcompare/<pp_fp>/<batchlists>")
# http://localhost:3832/venn/0/batchcompare/fp/1_2_43
def get_batches_proteins(cohort_index, pp_fp, batchlists):
    return pp.get_batches_proteins_as_json(cohorts_db, cohort_index, pp_fp, batchlists)


@app.route("/update/logs")
# http://localhost:3832/update/logs
def blog():
    log = "".join(cohorts_db.logger.get_log_messages())
    return jsonify(log)


@app.route("/error/logs")
# http://localhost:3832/error/logs
def errorlog():
    log = "".join(error_log)
    return jsonify(log)


@app.route("/patientcentric/ppintensity/<cohort_index>/<dtype>")
# http://localhost:3832/patientcentric/ppintensity/0/fp
# http://localhost:3832/patientcentric/ppintensity/0/pp
def get_sum_intensities_pp_level(cohort_index, dtype):
    if settings.DATABASE_MODE:
        return {}  # this query is too slow in the database

    return utils.df_to_json(
        pp.sum_intensities_across_all_patients(cohorts_db, cohort_index, dtype=dtype)
    )


@app.route("/patientcenteric/proteincounts/<cohort_index>/<fp_pp>")
@cache.cached(timeout=50)
# http://localhost:3832/patientcenteric/proteincounts/0/fp
def get_identifications_frequency(cohort_index, fp_pp):
    if settings.DATABASE_MODE:
        return {}  # this query is too slow in the database

    return utils.df_to_json(
        pp.identifications_across_all_patients(cohorts_db, fp_pp, cohort_index)
    )


@app.route("/topas/<cohort_index>/<topas_names>/<score_type>")
# http://localhost:3832/topas/0/ALK/topas_score
def topas(cohort_index, topas_names, score_type):
    return bp.get_topas_data(cohorts_db, cohort_index, topas_names, score_type)


@app.route("/topas/annotations")
# http://localhost:3832/topas/annotations
def topas_annotations():
    return utils.df_to_json(cohorts_db.get_topas_annotation_df())


@app.route("/topas/lolipopdata/<cohort_index>/<patient>")
# http://localhost:3832/topas/lolipopdata/0/I002-025-226610
def get_circular_barplot_data(cohort_index, patient):
    return utils.df_to_json(
        bp.get_circular_barplot_data_pathways(
            cohorts_db.get_topas_scores_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            patient,
        )
    )


@app.route("/topas/lolipopdata/<cohort_index>/<patient>/tumor_antigen")
# http://localhost:3832/topas/lolipopdata/0/I002-025-226610/tumor_antigen
def get_circular_barplot_data_tumor(cohort_index, patient):
    return utils.df_to_json(
        bp.get_circular_barplot_data_tumor_antigens(
            cohorts_db.get_protein_abundance_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            patient,
        )
    )


@app.route(
    "/topas/lolipopdata/expression/<cohort_index>/<patient>/downstream_signaling"
)
# http://localhost:3832/topas/lolipopdata/expression/0/I002-025-226610/downstream_signaling
def get_lolipopexpression_down_stream(cohort_index, patient):
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


@app.route("/<cohort_index>/<level>/list")
# http://localhost:3832/0/protein/list
def get_list_proteins(cohort_index, level):
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


@app.route("/topas/lolipopdata/expression/<cohort_index>/<patient>/rtk")
# http://localhost:3832/topas/lolipopdata/expression/0/I002-025-226610/rtk
def get_lolipopexpression_rtk(cohort_index, patient):
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


@app.route("/topas/<cohort_index>/topasids/<categories>")
# http://localhost:3832/topas/0/topasids
def topas_unique(cohort_index, categories):
    return bp.get_topas_unique(
        cohorts_db.get_topas_scores_df(cohort_index), categories
    )


@app.route("/topas/subscore/<cohort_index>/<topasname>")
# http://localhost:3832/topas/subscore/0/ABL
def topas_subtype(cohort_index, topasname):
    return bp.get_topas_subscore_data(cohorts_db, cohort_index, topasname)


@app.route("/<cohort_index>/sampleanot")
# http://localhost:3832/0/sampleanot
def sample_annotation(cohort_index):
    return utils.df_to_json(cohorts_db.get_sample_annotation_df(cohort_index))


@app.route("/<cohort_index>/patients")
@cache.cached(timeout=50)
# http://localhost:3832/0/patients
def patients(cohort_index):
    return utils.df_to_json(cohorts_db.get_patient_metadata_df(cohort_index))


@app.route("/<cohort_index>/patients/genomics_annotations/<identifier>")
@cache.cached(timeout=50)
# http://localhost:3832/0/patients/genomics_annotations/EGFR
def patients_genomics_annotations(cohort_index, identifier):
    patients_meta_df = cohorts_db.get_patient_metadata_df(cohort_index).copy()
    patients_meta_df = genomics_process._merge_data_with_genomics_alterations(
        cohorts_db, patients_meta_df, identifier, annotation_type="genomics_annotations"
    )
    patients_meta_df = genomics_process._merge_data_with_genomics_alterations(
        cohorts_db, patients_meta_df, identifier, annotation_type="oncoKB_annotations"
    )
    return utils.df_to_json(patients_meta_df)


@app.route("/<cohort_index>/metadata")
@cache.cached(timeout=50)
# http://localhost:3832/0/metadata
def patientsmetadata(cohort_index):
    sample_annotation_df = cohorts_db.get_sample_annotation_df(cohort_index)
    if "Entity" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df.drop(["Entity"], axis=1)
    patien_meta_df = cohorts_db.get_patient_metadata_df(cohort_index)
    final_df = utils.merge_with_patients_meta_df(sample_annotation_df, patien_meta_df)
    final_df = final_df.dropna()
    return utils.df_to_json(final_df)


@app.route("/<cohort_index>/metadata/fields")
# http://localhost:3832/0/metadata/fields
def patients_meta_fields(cohort_index):
    return jsonify(sorted(cohorts_db.get_patient_metadata_df(cohort_index).columns))


@app.route("/<cohort_index>/metadata/fields/<fieldname>")
# http://localhost:3832/0/metadata/fields/code_oncotree
def unique_field_intereset(cohort_index, fieldname):
    unique_items = (
        cohorts_db.get_patient_metadata_df(cohort_index)[fieldname]
        .dropna()
        .unique()
        .tolist()
    )
    unique_list = [str(x) for x in unique_items]
    return jsonify(sorted(unique_list))


@app.route("/<cohort_index>/metadata/fields/<fieldname>/patients/<field_interest>")
# http://localhost:3832/0/metadata/fields/code_oncotree/patients/UCEC
def get_patientslist_by_fieldname(cohort_index, fieldname, field_interest):
    df = cohorts_db.get_patient_metadata_df(cohort_index).copy()
    field_interest = field_interest.split(",")
    if len(field_interest) > 0:
        field_interest = [str(x) for x in field_interest]
        df[fieldname] = df[fieldname].astype(str)

    return jsonify(
        df[utils.ColumnNames.SAMPLE_NAME][df[fieldname].isin(field_interest)].tolist()
    )


@app.route("/patients/<cohort_index>/all_entities")
# http://localhost:3832/patients/0/all_entities
def get_patients_entities(cohort_index):
    return utils.df_to_json(cohorts_db.get_patients_entities_df(cohort_index))


# http://localhost:3832/genomics/EGFR
@app.route("/genomics/<identifier>")
def get_genomes(identifier):
    genomics_df = genomics_process.get_genomics_alterations_per_identifier(
        cohorts_db, identifier
    )
    genomics_df[utils.ColumnNames.SAMPLE_NAME] = genomics_df.index
    return utils.df_to_json(genomics_df)


# http://localhost:3832/oncokb/EGFR
@app.route("/oncokb/<identifier>")
def get_oncokb(identifier):
    genomics_df = genomics_process.get_genomics_alterations_per_identifier(
        cohorts_db, identifier, annotation_type="oncoKB_annotations"
    )
    genomics_df[utils.ColumnNames.SAMPLE_NAME] = genomics_df.index
    return utils.df_to_json(genomics_df)


@app.route("/density/fpkm/<identifier>/<intensity_unit>")
# http://localhost:3832/density/fpkm/EGFR/z_scored
def density_calc_fpkm(identifier, intensity_unit):
    return transcript.get_density_calc_fpkm(
        cohorts_db, identifier, utils.IntensityUnit(intensity_unit)
    )


@app.route("/<cohort_index>/density/protein/<identifier>/<intensity_unit>")
# http://localhost:3832/0/density/protein/EGFR/z_scored
def density_calc_protein(cohort_index, identifier, intensity_unit):
    return pp.get_density_calc_protein(
        cohorts_db, cohort_index, identifier, utils.IntensityUnit(intensity_unit)
    )


@app.route("/<cohort_index>/important_phospho/<identifier>")
# http://localhost:3832/0/important_phospho/EGFR
def get_important_phospho(cohort_index, identifier):
    return bp.get_topas_subscore_data_per_type(
        cohorts_db.get_report_dir(cohort_index),
        identifier,
        sub_type="important phosphorylation",
        return_json=True,
    )


@app.route("/<cohort_index>/<level>/abundance/<identifier>/<imputation>")
@cache.cached(timeout=50)
# http://localhost:3832/0/protein/abundance/EGFR/noimpute
# http://localhost:3832/0/fpkm/abundance/EGFR/noimpute
# http://localhost:3832/0/kinase/abundance/EGFR/noimpute
# http://localhost:3832/0/phospho_score/abundance/EGFR/noimpute
# http://localhost:3832/0/psite/abundance/_pYSPSQNpSPIHHIPSR_/noimpute
def abundance(cohort_index, level, identifier, imputation):
    return pp.get_abundance(
        cohorts_db,
        cohort_index,
        utils.DataType(level),
        identifier,
        utils.ImputationMode(imputation),
    )


@app.route(
    "/<cohort_index>/<level>/correlation/<level_2>/<identifier>/<intensity_unit>/<patients_list>"
)
@cache.cached(timeout=50)
# http://localhost:3832/0/topas_score/correlation/protein/EGFR/z_scored
# http://localhost:3832/0/phospho_score/correlation/protein/EGFR/intensity
# http://localhost:3832/0/fpkm/correlation/protein/EGFR/z_scored
# http://localhost:3832/0/important_phosphorylation/correlation/protein/EGFR/z_scored
def correlation(
    cohort_index, level, identifier, level_2, intensity_unit, patients_list=None
):
    patients_list = None if patients_list == "all" else patients_list.split(",")
    return cp.compute_correlation_df(
        cohorts_db,
        cohort_index,
        identifier,
        utils.DataType(level),
        utils.DataType(level_2),
        utils.IntensityUnit(intensity_unit),
        patients_list=patients_list,
    )


@app.route("/batcheffect/<level>/<cohort_index>/<identifier>/<sample_ids>/<data_type>")
# http://localhost:3832/batcheffect/expression_level/0/ABL/1,23,24/plot
# http://localhost:3832/batcheffect/phospho_level/0/ABL/1,23,24/plot
# http://localhost:3832/batcheffect/kinase_level/0/ALK/1,23,24/plot
def batch_effect(
    cohort_index: str, identifier: str, sample_ids: str, data_type: str, level: str
):
    merged_df = hp.fetch_data_matrix_with_sample_annotations(
        cohorts_db,
        cohort_index,
        identifier.split(","),
        sample_ids.split(","),
        utils.DataType(level),
    )
    return utils.merged_df_to_json(data_type, merged_df, level)


@app.route("/differential/<cohort_index>/<level>/<grp1_ind>/<grp2_ind>/<y_axis_type>")
# http://localhost:3832/differential/0/intensity/index_346_286_463/index_444_514_592
# http://localhost:3832/differential/0/phosphopeptides/index_346_286_463/index
# http://localhost:3832/differential/0/topasscores/index_346_286_463/index_444_514_592
def get_t_test_json(cohort_index, grp1_ind, grp2_ind, level, y_axis_type):
    return utils.df_to_json(
        differential_test.get_data_for_t_test(
            cohorts_db,
            cohort_index,
            grp1_ind,
            grp2_ind,
            utils.DataType(level),
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

    app.run(debug=debug, use_reloader=debug, host="0.0.0.0", port=3832)
