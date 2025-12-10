# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from topas_portal import utils
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
        - If `categories` is not "all", it filters the topas names based on the category mappings defined in `topass.TOPAS_CATEGORIES`.

    Example:
        topas_names = get_topas_unique(topas_df, "category1,category2")
    """

    ids = topas_df.index.unique().tolist()
    ids = pd.DataFrame(ids, columns=["ids"])
    return utils.df_to_json(ids)


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
