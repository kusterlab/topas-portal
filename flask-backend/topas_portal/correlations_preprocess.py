# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

import pandas as pd
import numpy as np
from scipy.stats import t

import topas_portal.utils as ef
import topas_portal.topas_preprocess as topas_utils
import topas_portal.settings as cn
import topas_portal.fetch_data_matrix as data
import topas_portal.data_api.data_api as data_api


def compute_correlation_df(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    identifier: str,
    level: ef.DataType,
    level_2: ef.DataType,
    intensity_unit: ef.IntensityUnit,
    subtopas_type: str = "important phosphorylation",
    patients_list=None,
):
    """
    Wrapper function to calculate correlations between different modalities such as protein vs FPKM 
    or phospho-proteins vs total proteome.

    This function handles the retrieval of data for different modalities and computes the correlation 
    between them. It can work with different levels such as `TOPAS_IMPORTANT_PHOSPHO`, `TOPAS_SCORE`, 
    `PHOSPHO_PROTEOME`, etc. It also handles merging additional annotations like topas weights or psite abundances.

    Args:
        cohorts_db (data_api.CohortDataAPI): The cohort data API object used to access cohort data.
        cohort_index (int): The index of the cohort to analyze.
        identifier (str): The identifier for the specific protein or topas for correlation.
        level (ef.DataType): The first data type to correlate (e.g., protein, FPKM).
        level_2 (ef.DataType): The second data type to correlate (e.g., phospho-proteins, total proteome).
        intensity_unit (ef.IntensityUnit): The intensity unit to use for the data (e.g., SCORE, Z_SCORE).
        subtopas_type (str, optional): The type of sub-topas data to use if level is `TOPAS_IMPORTANT_PHOSPHO`. 
                                        Defaults to "important phosphorylation".
        patients_list (list, optional): List of patients to consider for correlation computation. Defaults to None.

    Returns:
        str: A JSON string representing the correlation DataFrame.
        str: An error message or empty string if no error occurred.

    Raises:
        ValueError: If the data for the provided identifier is not found in the dataset.

    Example:
        # Compute correlation between protein and phospho-protein data
        correlation_json, error_code = compute_correlation_df(
            cohorts_db=cohorts_db,
            cohort_index=1,
            identifier="ProteinA",
            level=ef.DataType.TOPAS_SCORE,
            level_2=ef.DataType.PHOSPHO_PROTEOME,
            intensity_unit=ef.IntensityUnit.SCORE,
            patients_list=["Patient1", "Patient2"]
        )
    """
    if not cohorts_db.provider:
        return "", "500 Cohort data not loaded"

    if level == ef.DataType.TOPAS_IMPORTANT_PHOSPHO:
        report_dir = cohorts_db.get_report_dir(cohort_index)
        abundances = topas_utils.get_subtopas_data_per_type(
            report_dir, identifier, sub_type=subtopas_type
        )
    else:
        abundances = data.fetch_data_matrix(
            cohorts_db,
            cohort_index,
            ef.DataType(level),
            identifiers=[identifier],
            intensity_unit=intensity_unit,
        )

    if len(abundances.index) != 1:
        return "", f'400 {level} "{identifier}" not found in dataset'

    all_abundances = data.fetch_data_matrix(
        cohorts_db,
        cohort_index,
        ef.DataType(level_2),
        identifiers=None,
        intensity_unit=intensity_unit,
    )
    correlation_df, error_code = _get_correlations(
        all_abundances, abundances, patients_list=patients_list
    )

    if level == ef.DataType.TOPAS_SCORE:
        # add "Topas weight column" to correlation table
        topas_complete_df = cohorts_db.get_topas_annotation_df()
        topas_annotation_df = topas_utils.get_topas_weights(topas_complete_df)
        topas_annotation_df = topas_annotation_df[
            topas_annotation_df["topas"] == identifier
        ]
        correlation_df = correlation_df.merge(
            topas_annotation_df, left_on="index", right_on="gene", how="left"
        )
        correlation_df = correlation_df.fillna("")

    if level_2 == ef.DataType.PHOSPHO_PROTEOME:
        psite_annotation_df = cohorts_db.get_psite_abundance_df(
            cohort_index=cohort_index
        )
        correlation_df = correlation_df.merge(
            psite_annotation_df[cn.PP_EXTRA_COLUMNS].reset_index(),
            left_on="index",
            right_on="Modified sequence",
        )
        correlation_df = correlation_df.drop(columns=["Modified sequence"])
        correlation_df = correlation_df.fillna("")

    return ef.df_to_json(correlation_df), error_code


def _subset_to_overlapping_patients(
    all_abundances: pd.DataFrame, abundances: pd.DataFrame, patients_list=None
):
    """
    Subsets the input data frames to include only the overlapping patients before computing correlations.

    This function ensures that the patient data in both data frames match by finding the intersection of 
    patient identifiers across the two data frames. If a list of specific patients is provided, it further 
    restricts the subset to only those patients that are present in both data frames.

    Args:
        all_abundances (pd.DataFrame): A gene or p-site abundance matrix containing data for multiple patients.
        abundances (pd.DataFrame): A single gene or p-site abundance data for multiple patients.
        patients_list (list, optional): A list of specific patients to include in the subset. Defaults to None, 
                                        meaning all overlapping patients will be considered.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The subset of `all_abundances` for the overlapping patients.
            - pd.DataFrame: The subset of `abundances` for the overlapping patients.
            - str: An error message if no overlapping patients are found ("400 No overlapping patients found"), 
                   or an empty string if no error occurred.

    Example:
        # Subset to overlapping patients and compute correlation
        all_abundances, abundances = _subset_to_overlapping_patients(
            all_abundances=all_abundances_df,
            abundances=abundances_df,
            patients_list=["Patient1", "Patient2"]
        )
    """
    overlapping_patients = ef.intersection(all_abundances.columns, abundances.columns)
    if patients_list:
        overlapping_patients = ef.intersection(overlapping_patients, patients_list)
    if (
        len(overlapping_patients) == 0
        and len(all_abundances.columns) > 0
        and len(abundances.columns) > 0
    ):
        return pd.DataFrame(), "400 No overlapping patients found"

    abundances = abundances[overlapping_patients]
    all_abundances = all_abundances[overlapping_patients]
    return all_abundances, abundances


def _get_correlations(
    all_abundances: pd.DataFrame, abundances: pd.DataFrame, patients_list: list
):
    """
    Computes Pearson correlations and p-values between a single gene/p-site and all other genes/p-sites.

    This function calculates the Pearson correlation coefficient between the provided gene or p-site 
    (represented by the `abundances` DataFrame) and each gene or p-site in the `all_abundances` DataFrame. 
    It then computes the corresponding p-value using a two-sided t-test. The correlation results are 
    returned along with the number of valid patients, p-values, and False Discovery Rate (FDR) adjustment.

    Args:
        all_abundances (pd.DataFrame): A gene or p-site abundance matrix containing data for multiple genes/p-sites and patients.
        abundances (pd.DataFrame): A single gene or p-site abundance data.
        patients_list (list): A list of patients to consider for the correlation calculation. Only overlapping patients will be used.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: A DataFrame with Pearson correlation coefficients, p-values, number of valid patients, and FDR values.
            - int: HTTP status code (200 on success).

    Example:
        # Compute correlations between a gene and all other genes/p-sites
        correlation_df, status = _get_correlations(
            all_abundances=all_abundances_df,
            abundances=abundances_df,
            patients_list=["Patient1", "Patient2"]
        )
    """
    all_abundances, abundances = _subset_to_overlapping_patients(
        all_abundances, abundances, patients_list=patients_list
    )

    X = all_abundances.values
    Y = np.tile(abundances.values, (len(all_abundances.index), 1))

    null_mask = np.isnan(X) | np.isnan(Y)
    num_valid = np.nansum(~null_mask, axis=1, keepdims=True)

    row_valid = np.where(num_valid >= 8)[0]
    X = X[row_valid]
    Y = Y[row_valid]
    num_valid = num_valid[row_valid]
    null_mask = null_mask[row_valid]
    index = all_abundances.index[row_valid]

    X[null_mask] = np.nan
    Y[null_mask] = np.nan

    Xdiff = X - np.nanmean(X, axis=1, keepdims=True)
    Ydiff = Y - np.nanmean(Y, axis=1, keepdims=True)

    diff_dot_product = np.nansum(Xdiff * Ydiff, axis=1, keepdims=True)

    Xnorm = np.sqrt(np.nansum(np.square(Xdiff), axis=1, keepdims=True))
    Ynorm = np.sqrt(np.nansum(np.square(Ydiff), axis=1, keepdims=True))

    pearson_r = diff_dot_product / (Xnorm * Ynorm)
    pearson_r = np.minimum(pearson_r, np.nextafter(1.0, -1))

    t_statistic = (
        pearson_r * np.sqrt(num_valid - 2) / np.sqrt(1 - pearson_r * pearson_r)
    )
    p_value = 2 * (1 - t.cdf(np.abs(t_statistic), num_valid - 2))  # two-sided t-test

    result = np.concatenate([pearson_r, num_valid, p_value], axis=1)

    correlation_df = pd.DataFrame(
        result, columns=["correlation", "num_patients", "p-value"], index=index
    )
    correlation_df["abs_correlation"] = np.abs(correlation_df["correlation"])

    correlation_df.index.name = "index"
    correlation_df = correlation_df.dropna()
    correlation_df = correlation_df.reset_index()
    correlation_df = correlation_df.sort_values(
        ["p-value", "num_patients", "abs_correlation"], ascending=[True, False, False]
    )
    correlation_df["rank"] = range(1, len(correlation_df.index) + 1)
    correlation_df["FDR"] = _monotonize(
        correlation_df["p-value"] * len(correlation_df.index) / correlation_df["rank"]
    )
    return correlation_df, 200


def _monotonize(fdrs):
    """
    Makes a list of FDRs (False Discovery Rates) monotonically increasing.

    This function takes a list of FDR values and ensures that the list is monotonically non-decreasing
    by applying a technique often referred to as "monotonization". It is commonly used to adjust p-values 
    in statistical analysis, particularly in multiple testing corrections, ensuring that the FDR values 
    do not decrease as the index progresses.

    Args:
        fdrs (array-like): A list or array of FDR values (e.g., p-values adjusted by the Benjamini-Hochberg procedure).

    Returns:
        np.ndarray: A monotonically increasing version of the input FDR values.

    Example:
        fdrs = [0.05, 0.02, 0.07, 0.01]
        monotonized_fdrs = _monotonize(fdrs)
        # monotonized_fdrs will be [0.01, 0.02, 0.07, 0.07]
    """
    return np.minimum.accumulate(fdrs[::-1])[::-1]


def _filter_df_columns(df: pd.DataFrame, like_or_regex: str, pattern: str):
    if not isinstance(df, pd.DataFrame):
        raise ValueError(f"Expected dataframe, received {type(df)}")

    if like_or_regex == "like":
        return df.filter(like=pattern, axis=1)

    return df.filter(regex=pattern)


def _get_correlation_for_one_patient(
    patient: str, df1: pd.DataFrame, df2: pd.DataFrame
):
    """
    Computes the Pearson correlation between protein and transcript Z-scores for a single patient.

    This function calculates the correlation between the protein Z-scores (from `df1`) 
    and the transcript Z-scores (from `df2`) for a specific patient. It returns the 
    correlation value if there are enough valid protein-transcript pairs (at least 20), 
    and the number of proteins used in the correlation calculation.

    Args:
        patient (str): The identifier for the patient to compute the correlation for.
        df1 (pd.DataFrame): A DataFrame containing protein Z-scores, with proteins as rows and patients as columns.
        df2 (pd.DataFrame): A DataFrame containing transcript Z-scores, with proteins as rows and patients as columns.

    Returns:
        tuple: A tuple containing:
            - float or None: The Pearson correlation between the protein and transcript Z-scores for the patient, 
              or None if there are insufficient data points.
            - int: The number of proteins used in the correlation calculation.

    Example:
        correlation, num_proteins = _get_correlation_for_one_patient("patient_001", protein_df, transcript_df)
        # correlation will be the Pearson correlation, and num_proteins will be the count of proteins used.
    """
    ans = None
    try:
        df1 = pd.DataFrame(df1.loc[:, patient])
        df2 = pd.DataFrame(df2.loc[:, patient])
        all_df = pd.concat([df1, df2], axis=1)
        all_df = all_df.dropna()
        if len(all_df) > 20:  # at least 20 proteins are needed for the
            ans = all_df.corr().iloc[0, 1]
    except:
        print(f"{patient} lead to error we put NA")
        pass
    return ans, len(all_df)


def wrapper_get_correlation_across_patients(
    protein_df: pd.DataFrame, transcripts_df: pd.DataFrame
):
    """
    Computes the correlation between protein and transcript Z-scores across patients. THIS FUNCTION IS USED IN THE PATIENTS REPORT TAB OF THE PORTAL

    This function calculates the Pearson correlation between protein and transcript 
    expression values (Z-scores) for each patient. It first processes the input 
    DataFrames to ensure that the protein and transcript data are aligned by the 
    common set of proteins and patients. Then, for each patient, it computes the 
    correlation across the corresponding proteins' Z-scores from both the protein 
    and transcript datasets.

    Args:
        protein_df (pd.DataFrame): A DataFrame containing protein Intensities, with proteins as rows and patients as columns. ** THE COLUMNS PATTERN SHOULD BE "PATIENT Intensity"
        transcripts_df (pd.DataFrame): A DataFrame containing transcript fpkms, with proteins as rows and patients as columns.** THE COLUMNS PATTERN SHOULD BE "PATIENT Z-score"

    Returns:
        pd.DataFrame: A DataFrame with the patients as rows and two columns: 
                      'correlation' (Pearson correlation between protein and transcript Z-scores) and 
                      'num_proteins' (number of proteins used in the correlation calculation).

    Example:
        correlation_df = wrapper_get_correlation_across_patients(protein_df, transcripts_df)
        # correlation_df will contain correlations for each patient between protein and transcript data.
    """
    transcripts_df.columns = transcripts_df.columns.str.replace(
        " Z-score", " Intensity"
    )
    protein_df = protein_df.filter(regex='Intensity')
    protein_df.columns = protein_df.columns.str.replace(' Intensity','')
    unested_protein_df = ef.unnest_proteingroups(protein_df)

    overlappling_patients = [
        x for x in transcripts_df.columns if x in unested_protein_df.columns
    ]
    overlapping_proteins = [
        x for x in transcripts_df.index if x in unested_protein_df.index
    ]

    Z_SCORES_df_proteome = unested_protein_df.loc[
        overlapping_proteins, overlappling_patients
    ]
    transcripts_z_scores = transcripts_df.loc[
        overlapping_proteins, overlappling_patients
    ]

    correlation_df = pd.DataFrame(overlappling_patients, columns=["patients"])
    correlation_df["correlation"] = None
    correlation_df["num_proteins"] = None
    for i in range(len(correlation_df)):
        protein_correlaiton, num_proteins = _get_correlation_for_one_patient(
            correlation_df["patients"][i], Z_SCORES_df_proteome, transcripts_z_scores
        )
        correlation_df["correlation"][i] = protein_correlaiton
        correlation_df["num_proteins"][i] = num_proteins
    return correlation_df



