# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

import topas_portal.genomics_preprocess as gp
from topas_portal import settings
from topas_portal import utils
import topas_portal.topas_scores_meta as topas
import topas_portal.IFN_topas_scoring as topas_scoring
import topas_portal.file_loaders.topas as topas_loader

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


def get_topas_weights(topas_annotations_df: pd.DataFrame) -> pd.DataFrame:
    """Returns a DataFrame with gene weights (not p-sites!) for all topass.

    Adapted for the 4th generation.

    returns:
        pd.DataFrame[gene, weight, topas]
    """
    selected_columns = {
        "GENE NAME": "gene",
        "WEIGHT": "weight",
        "TOPAS_SUBSCORE": "topas",
    }
    weights_df = topas_annotations_df[selected_columns.keys()]
    weights_df = weights_df.rename(columns=selected_columns, errors="raise")

    weights_df["topas"] = weights_df["topas"].str.replace(r"[\s\/-]", "_", regex=True)
    weights_df["weight"] = weights_df["weight"].fillna(1)
    weights_df = weights_df.drop_duplicates(keep="first")

    return weights_df


def _merge_topass_with_metadata(
    topas_df: pd.DataFrame,
    sample_annotation_df: pd.DataFrame,
    patients_df: pd.DataFrame,
):
    """
    Merges topas data with sample annotation and patient metadata, and fills missing patient-related values.

    Args:
        topas_df (pd.DataFrame): The DataFrame containing the topas data (e.g., gene or protein measurements).
        sample_annotation_df (pd.DataFrame): The DataFrame containing the sample annotation (e.g., sample names and groupings).
        patients_df (pd.DataFrame): The DataFrame containing patient metadata (e.g., clinical data).

    Returns:
        pd.DataFrame: The merged DataFrame containing topas data enriched with sample annotation and patient metadata.

    Notes:
        - Merges `topas_df` with `sample_annotation_df` based on sample identifiers.
        - Enriches the merged DataFrame with patient metadata from `patients_df`.
        - Fills missing values in patient-related columns in the resulting DataFrame.

    Example:
        merged_df = _merge_topass_with_metadata(topas_df, sample_annotation_df, patients_df)
    """
    topas_df = utils.merge_with_sample_annotation_df(topas_df, sample_annotation_df)
    topas_df = utils.merge_with_patients_meta_df(topas_df, patients_df)
    topas_df = utils.fill_nans_patient_columns(topas_df)
    return topas_df


def get_topas_subscore_data(
    cohorts_db: data_api.CohortDataAPI, cohort_index: str, topasname: str
):
    """
    Fetches and processes all sub-topas data for a given main topas.

    Args:
        cohorts_db (data_api.CohortDataAPI): The CohortDataAPI instance for accessing cohort data.
        cohort_index (str): The index of the cohort to retrieve data for.
        topasname (str): The name of the main topas for which sub-topas data is fetched.

    Returns:
        dict: A dictionary containing the sub-topas data in JSON format.

    Notes:
        - Retrieves the report directory for the given cohort.
        - Loads the sub-topas data table corresponding to the provided topas name.
        - Strips leading/trailing whitespace and removes tab characters from the "topas" column.

    Example:
        topas_subscore_data = get_topas_subscore_data(cohorts_db, "1", "topas_name")
    """
    cohort_name = cohorts_db.config.get_cohort_name(cohort_index)
    report_dir = cohorts_db.config.get_report_directory(cohort_name)
    topas_sub_df = topas_loader.load_topas_subscore_table(report_dir, topasname)
    topas_sub_df["topas"].str.replace("\t", "")
    topas_sub_df["topas"].str.strip()
    return utils.df_to_json(topas_sub_df)


def get_topas_unique(topas_df: pd.DataFrame):
    """
    Retrieves unique topas names for a cohort, optionally filtered by specified categories.

    Args:
        topas_df (pd.DataFrame): The DataFrame containing topas data (e.g., gene or protein data).
        categories (str): A comma-separated string of categories to filter the topas names by.
                          If set to "all", no filtering is applied.

    Returns:
        dict: A dictionary containing the unique topas names in JSON format.

    Notes:
        - The function retrieves unique topas names from the index of `topas_df`.
        - Appends a predefined value, "IFN_sig", to the list of topas names.
        - If `categories` is not "all", it filters the topas names based on the category mappings defined in `topass.TOPAS_CATEGORIES`.

    Example:
        topas_names = get_topas_unique(topas_df, "category1,category2")
    """

    ids = topas_df.index.unique().tolist()
    ids.append("IFN_sig")
    ids = pd.DataFrame(ids, columns=["ids"])
    return utils.df_to_json(ids)


def get_topas_data(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    topas_names: str,
    score_type: str,
):
    """
    Retrieves and processes topas data for a specific cohort, including merging with metadata
    and genomics annotations.

    Args:
        cohorts_db (data_api.CohortDataAPI): The CohortDataAPI instance for accessing cohort data.
        cohort_index (str): The index of the cohort to retrieve data for.
        topas_names (str): A comma-separated string of topas names to fetch data for.
        score_type (str): The type of score to be used for retrieving topas data.

    Returns:
        dict: A dictionary containing the processed topas data in JSON format.

    Notes:
        - Fetches a subset of the topas data using `get_topas_subset_df`.
        - Merges the topas data with sample annotation and patient metadata.
        - Filters the DataFrame to retain only relevant metadata columns.
        - Merges genomics alterations and OncoKB annotations into the topas data.
        - The final data is returned in JSON format.

    Example:
        topas_data = get_topas_data(cohorts_db, "cohort_1", "topas1,topas2", "score_type1")
    """
    topas_subset_df = get_topas_subset_df(
        cohorts_db, cohort_index, topas_names, score_type
    )

    topas_subset_df = _merge_topass_with_metadata(
        topas_subset_df,
        cohorts_db.get_sample_annotation_df(cohort_index),
        cohorts_db.get_patient_metadata_df(cohort_index),
    )
    selected_columns = utils.intersection(
        settings.TOPAS_META_DATA, topas_subset_df.columns
    )
    topas_subset_df = topas_subset_df[selected_columns]

    try:
        topas_subset_df = gp.merge_data_with_genomics_alterations(
            cohorts_db,
            topas_subset_df,
            topas_names,
            annotation_type="genomics_annotations",
        )
    except:
        pass

    try:
        topas_subset_df = gp._merge_onkokb_annotation(
            cohorts_db, topas_subset_df, topas_names
        )
    except:
        pass

    topas_subset_df = topas_subset_df.sort_values(by="Z-score", ascending=False)

    topas_subset_df = topas_subset_df.reset_index(drop=True)
    topas_subset_df["index"] = topas_subset_df.index

    return utils.df_to_json(topas_subset_df)


def get_topas_scores_long_format(topas_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts a wide-format topas scores DataFrame into a long format, where each row represents
    a single sample and its corresponding topas score.

    Args:
        topas_scores_df (pd.DataFrame): A DataFrame where columns represent topass and rows represent samples,
                                         with Z-scores as the values.

    Returns:
        pd.DataFrame: A DataFrame in long format, where each row represents a sample and its corresponding topas,
                      with columns for 'Sample name', 'Topas_id', and 'Z-score'.

    Notes:
        - The function transposes the input DataFrame, reshaping it from wide format to long format.
        - It drops any rows with missing values (NaNs) from the reshaped DataFrame.
        - The resulting DataFrame has three columns: 'Sample name', 'Topas_id', and 'Z-score'.

    Example:
        long_format_df = get_topas_scores_long_format(topas_scores_df)
    """
    topas_scores_df = topas_scores_df.T
    topas_names = topas_scores_df.columns.tolist()

    topas_scores_long = pd.melt(
        topas_scores_df.reset_index(),
        id_vars="Sample name",
        value_vars=topas_names,
        value_name="Z-score",
    )
    topas_scores_long = topas_scores_long.dropna()
    topas_scores_long.columns = ["Sample name", "Topas_id", "Z-score"]

    return topas_scores_long


def get_topas_subset_df(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    topas_names: str,
    score_type: str,
) -> pd.DataFrame:
    """
    Retrieves a subset of topas scores for a specific cohort, either using pre-calculated topas scores
    or by calculating TOPAS scores for a specified topas.

    Args:
        cohorts_db (data_api.CohortDataAPI): The CohortDataAPI instance for accessing cohort data.
        cohort_index (str): The index of the cohort to retrieve data for.
        topas_names (str): A comma-separated string of topas names to filter the data by.
        score_type (str): The type of score to use, either "topas_score" or another type that defaults to Z-scores.

    Returns:
        pd.DataFrame: A DataFrame containing the subset of topas scores for the specified cohort and topas names.

    Notes:
        - If the topas name is "IFN_sig", TOPAS scores are calculated using protein abundance data.
        - Otherwise, the function filters the topas scores DataFrame based on the provided topas names.
        - The topas scores are returned in long format using `get_topas_scores_long_format`.

    Example:
        topas_subset_df = get_topas_subset_df(cohorts_db, "1", "topas1,topas2", "topas_score")
    """
    if score_type == "topas_score":
        score_unit = utils.IntensityUnit.SCORE
    else:
        score_unit = utils.IntensityUnit.Z_SCORE

    topas_df = cohorts_db.get_topas_rtk_scores_df(cohort_index, score_unit)
    topas_df = get_topas_scores_long_format(topas_df)

    if topas_names == "IFN_sig":

        topas_df = topas_scoring.calculate_TOPAS_scores(
            cohorts_db.get_protein_abundance_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            cohorts_db.get_patient_metadata_df(cohort_index),
            score_type=score_type,
        )
        print(topas_df)
        topas_subset_df = topas_df
    else:
        topas_subset_df = topas_df[topas_df["Topas_id"].isin(topas_names.split(","))]
    return topas_subset_df
