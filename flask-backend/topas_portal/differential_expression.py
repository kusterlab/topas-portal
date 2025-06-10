from __future__ import annotations

import math
import numpy as np
from typing import TYPE_CHECKING

from topas_portal import utils
from topas_portal import settings
from topas_portal.signature_function import one_vs_all_t_test
import topas_portal.fetch_data_matrix as data
import topas_portal.topas_scores_meta as topas

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


def get_data_for_t_test(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    grp1_indexes: str,
    grp2_indexes: str,
    level: utils.DataType,
    y_axis_type: str,
):
    """
    Computes and prepares data for a t-test analysis between two patient groups 
    within a specified cohort.

    This function retrieves patient metadata, determines the two comparison groups, 
    prepares the input data for the t-test, and computes statistical differences. 
    It also formats the results for visualization, including color coding significant values.

    Args:
        cohorts_db (data_api.CohortDataAPI): The database interface for retrieving cohort data.
        cohort_index (str): The identifier of the cohort from which data is retrieved.
        grp1_indexes (str): Comma-separated string of patient identifiers for the first group.
        grp2_indexes (str): Comma-separated string of patient identifiers for the second group.
                            If set to "index", all other patients in the cohort are used as the second group.
        level (ef.DataType): The data level (e.g., proteome or phospho-proteome) to analyze.
        y_axis_type (str): The column name in the t-test results used for the y-axis transformation.

    Returns:
        pd.DataFrame: A dataframe containing the t-test results, including:
            - `expression1`: Difference in mean values between groups (x-axis).
            - `expression2`: -log10 transformed p-values (y-axis).
            - `sampleId`: Gene/protein identifier.
            - `ownColor`: Color-coded significance labels ("red", "blue", "grey").
            - Additional statistical values such as p-values, FDR, and means for both groups.

    Raises:
        ValueError: If cohort data retrieval or processing fails.
    
    Notes:
        - If `grp2_indexes` is "index", the first group is tested against all other patients.
        - If the analysis is on phospho-proteome data, PSP annotations are added.
        - Adjustments are made to filter out infinite values before returning results.
    """
    # patients_df['Sample_name_rep_truncated'] = patients_df['Sample name'].str.replace(r'-R[0-9]$', '', regex=True)
    patients_df = cohorts_db.get_patient_metadata_df(cohort_index)
    grp1 = grp1_indexes.split(",")
    if not grp2_indexes == "index":
        grp2 = grp2_indexes.split(",")
    else:  # this is for one vs all t_test
        grp2 = patients_df[
            "Sample name"
        ].tolist()  # the selected list of the patients vs all other patients

    grp2 = utils.setdiff(grp2, grp1)
    patients_list = [*grp1, *grp2]
    protein_list, input_df = _preparare_input_for_t_test(
        cohorts_db, cohort_index, patients_list, level
    )
    input_df["meta_data"] = "group2"
    input_df["meta_data"][input_df.index.isin(grp1)] = "group1"
    t_test_df = one_vs_all_t_test(input_df, protein_list, "group1", "meta_data")
    t_test_df.dropna(inplace=True)
    t_test_df["expression2"] = t_test_df[y_axis_type].apply(
        lambda x: _negative_log10(x)
    )  # y-axis of the plot
    t_test_df["expression1"] = (
        t_test_df["means_group1"] - t_test_df["means_group2"]
    )  # x-axis of the plot
    t_test_df["sampleId"] = t_test_df["Gene Names"]
    t_test_df["ownColor"] = "grey"
    t_test_df["ownColor"][
        (t_test_df["expression2"] >= 2) & (t_test_df["expression1"] >= 1)
    ] = "red"
    t_test_df["ownColor"][
        (t_test_df["expression2"] >= 2) & (t_test_df["expression1"] <= -1)
    ] = "blue"

    t_test_df = t_test_df.sort_values(by=["fdr", "p_values"])
    t_test_df[(t_test_df == np.inf) | (t_test_df == -np.inf)] = np.nan
    t_test_df = t_test_df.dropna()

    # adding psite_annotation for the PP data
    if level == utils.DataType.PHOSPHO_PROTEOME:
        t_test_df = _add_PSP_annotation(cohorts_db, t_test_df, cohort_index)

    return t_test_df


def _add_PSP_annotation(cohorts_db, t_test_df, cohort_index: int):
    """
    Adds PhosphoSitePlus (PSP) annotations to the t-test results dataframe.

    This function retrieves phospho-proteome site abundance data for a given cohort, 
    extracts relevant annotation columns, and merges them with the t-test results 
    based on the modified sequence.

    Args:
        cohorts_db (data_api.CohortDataAPI): The database interface for retrieving cohort data.
        t_test_df (pd.DataFrame): The t-test results dataframe to which annotations will be added.
        cohort_index (int): The identifier of the cohort for retrieving phospho-proteome data.

    Returns:
        pd.DataFrame: The t-test dataframe with additional PSP annotation columns.

    Notes:
        - Missing values in PSP annotation columns are filled with `"n.d."` (not detected).
        - The function renames `"Gene names"` to `"Genes"` for consistency.
        - The merge is performed using `"Gene Names"` (from `t_test_df`) and `"Modified sequence"` 
          (from `psite_annotation_df`).
        - If an error occurs (e.g., missing PSP data), the function returns the original `t_test_df` 
          without modifications.
    """
    try:
        psite_annotation_df = cohorts_db.get_psite_abundance_df(
            cohort_index=cohort_index
        )
        psite_annotation_df = psite_annotation_df[settings.PP_EXTRA_COLUMNS].reset_index()
        psite_annotation_df[settings.PP_EXTRA_COLUMNS] = psite_annotation_df[
            settings.PP_EXTRA_COLUMNS
        ].fillna("n.d.")
        psite_annotation_df = psite_annotation_df.rename(
            columns={"Gene names": "Genes"}
        )
        t_test_df = t_test_df.merge(
            psite_annotation_df,
            left_on="Gene Names",  # Gene names for Phospho is the Modified sequence
            right_on="Modified sequence",
            how="left",
        )
        return t_test_df
    except:
        return t_test_df


def _preparare_input_for_t_test(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    patients_list: list[str],
    level: utils.DataType,
):
    """
    Prepares input data for performing a t-test by fetching relevant data matrices.

    This function retrieves the appropriate data matrix for the specified cohort and data type, 
    filters the matrix to include only the relevant patients, and returns a list of unique 
    protein identifiers along with the formatted input dataframe.

    Args:
        cohorts_db (data_api.CohortDataAPI): The database interface for retrieving cohort data.
        cohort_index (str): The identifier of the cohort to fetch data from.
        patients_list (list[str]): A list of patient identifiers to be included in the analysis.
        level (ef.DataType): The data type (e.g., proteome, transcriptome, TOPAS score, etc.) 
                             used to determine which dataset to retrieve.

    Returns:
        tuple:
            - list[str]: A list of unique protein identifiers.
            - pd.DataFrame: A transposed data matrix containing only the selected patients.

    Notes:
        - If `level` is `TOPAS_SCORE_RTK`, it is replaced with `TOPAS_SCORE`, and only RTK-related 
          identifiers are retrieved.
        - The function fetches the relevant data matrix from `cohorts_db` using the specified 
          intensity unit.
        - Only the patients that exist in both `patients_list` and the data matrix columns 
          are retained.
    """
    identifiers = None
    if level == utils.DataType.TOPAS_SCORE_RTK:
        level = utils.DataType.TOPAS_SCORE
        identifiers = [
            topas
            for topas, category in topas.TOPAS_CATEGORIES.items()
            if category == "RTK"
        ]

    input_df = data.fetch_data_matrix(
        cohorts_db,
        cohort_index,
        level,
        identifiers=identifiers,
        intensity_unit=topas.TOPAS_DIFFERENTIAL_INTENSITY_UNITS[level],
    )
    protein_list = input_df.index.unique().tolist()
    overlapping_patients = utils.intersection(patients_list, input_df.columns.tolist())
    return protein_list, input_df[overlapping_patients].T


def _negative_log10(x):
    try:
        return -math.log10(x)
    except:
        return 0
