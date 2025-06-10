import pandas as pd
import db

from flask import Blueprint, jsonify

from topas_portal import utils


proteinscore_page = Blueprint(
    "proteinscore_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db


def _post_process_protein_scores_df(protein_scores_single_df: pd.DataFrame):
    protein_scores_single_df.columns = ["Z-score"]
    protein_scores_single_df["Sample name"] = protein_scores_single_df.index
    protein_scores_single_df["is_replicate"] = (
        protein_scores_single_df["Sample name"].str.split("-").str[-1]
    )
    protein_scores_single_df.is_replicate[
        ~protein_scores_single_df["is_replicate"].str.contains("R")
    ] = "not_replicate"
    return protein_scores_single_df


def _get_single_protein_scores_df_per_patient_name(
    cohort_index: int, patient_name: str
) -> pd.DataFrame:
    protein_scores_df = cohorts_db.get_phosphorylation_scores_df(cohort_index)
    protein_scores_single_df = protein_scores_df[[str(patient_name) + " Z-score"]]
    protein_scores_single_df = _post_process_protein_scores_df(protein_scores_single_df)
    return protein_scores_single_df


def get_protein_scores(cohort_index: int, item_name: str):
    """Gets the protein scores for all patients for one protein name as a  json file"""
    protein_scores_single_df = _get_single_protein_scores_df_per_patient_name(
        cohort_index, item_name
    )
    protein_scores_single_df = protein_scores_single_df.dropna()
    
    protein_scores_single_df = utils.QC_channel_nan_values_fill(protein_scores_single_df)
    return utils.df_to_json(protein_scores_single_df)


@proteinscore_page.route("/proteinscore/<cohort_ind>/patient/<patient_name>")
# http://localhost:3832/proteinscore/0/patient/I007-031-108742
def get_protein_scores_per_patient(cohort_ind, patient_name):
    """The list of metadata to show in the QC coloring combobox"""
    return get_protein_scores(cohort_ind, patient_name)


@proteinscore_page.route("/proteinscore/<cohort_index>/patients_list")
# http://localhost:3832/proteinscore/0/patients_list
def get_protein_patients_list(cohort_index):
    """The list of metadata to show in the QC coloring combobox"""
    protein_scores_df = cohorts_db.get_phosphorylation_scores_df(cohort_index)
    return jsonify(sorted(protein_scores_df.columns.str.removesuffix(" Z-score")))

