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
    selected_columns = {"GENE NAME": "gene", "WEIGHT": "weight", "TOPAS_SUBSCORE": "topas"}
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
    report_dir = cohorts_db.config.get_report_directory(cohort_index)
    topas_sub_df = topas_loader.load_topas_subscore_table(report_dir, topasname)
    topas_sub_df["topas"].str.replace("\t", "")
    topas_sub_df["topas"].str.strip()
    return utils.df_to_json(topas_sub_df)


def get_topas_unique(topas_df: pd.DataFrame, categories: str):
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
    if categories != "all":
        ids = [
            topas_id
            for topas_id in ids
            if topas.TOPAS_CATEGORIES.get(topas_id, None) in categories.split(",")
        ]
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
    selected_columns = utils.intersection(settings.TOPAS_META_DATA, topas_subset_df.columns)
    topas_subset_df = topas_subset_df[selected_columns]
    topas_subset_df = gp._merge_data_with_genomics_alterations(
        cohorts_db,
        topas_subset_df,
        topas_names,
        annotation_type="genomics_annotations",
    )
    topas_subset_df = gp._merge_data_with_genomics_alterations(
        cohorts_db, topas_subset_df, topas_names, annotation_type="oncoKB_annotations"
    )
    topas_subset_df = topas_subset_df.sort_values(by='Z-score', ascending=False)

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

    topas_df = cohorts_db.get_topas_scores_df(cohort_index, score_unit)
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
        topas_subset_df = topas_df[
            topas_df["Topas_id"].isin(topas_names.split(","))
        ]
    return topas_subset_df


def get_circular_barplot_data_pathways(topas_df: pd.DataFrame, patient: str):
    """
    Retrieves data for visualizing a circular barplot of pathway-related scores for a specific patient.

    This function processes the topas scores to create data formatted for a circular barplot or a 
    lollipop plot, representing the patient's scores across various sub-pathways. The data is filtered 
    to include only the topass that are relevant to the patient and maps pathway categories to color codes.

    Args:
        topas_df (pd.DataFrame): DataFrame containing topas scores with sample names and topas IDs.
        patient (str): The identifier of the patient for whom the data is being retrieved.

    Returns:
        pd.DataFrame: A DataFrame containing the following columns:
            - 'label': The pathway name (topas ID).
            - 'value': The Z-score for the pathway.
            - 'type': The category of the pathway based on predefined rules.
            - 'color': The color assigned to each pathway based on its type.

    Notes:
        - The function filters the data for the given patient, ensuring that only relevant pathways are included.
        - The "Topas_id" is mapped to pathway categories and colors using predefined rules.
        - The data is sorted by pathway type and Z-score in descending order to prioritize higher scores.

    Example:
        circular_barplot_data = get_circular_barplot_data_pathways(topas_df, "Patient_123")
    """
    topas_df = get_topas_scores_long_format(topas_df)
    interested_topass = list(set(topas.TOPAS_CATEGORIES.keys()))
    df = topas_df[topas_df["Sample name"] == str(patient)].set_index("Sample name")
    df = df[df.Topas_id.isin(interested_topass)]
    df = df[["Topas_id", "Z-score"]]
    df = df.fillna(0)
    df.columns = ["label", "value"]
    df["type"] = df.label.map(topas.TOPAS_CATEGORIES)
    df["color"] = df.type.map(topas.TOPAS_COLORING_RULE)
    df = df.sort_values(by=["type", "value"], ascending=[False, False])
    return df


def get_circular_barplot_data_tumor_antigens(
    expression_z_scores_df: pd.DataFrame, patient: str
):
    """
    Retrieves data for visualizing a circular barplot of tumor antigen-related scores for a specific patient.

    This function processes the expression Z-scores to create data formatted for a circular barplot or a 
    lollipop plot, representing the patient's expression levels across various tumor antigens. The data 
    is filtered to include only proteins categorized as tumor antigens and maps the protein categories to color codes.

    Args:
        expression_z_scores_df (pd.DataFrame): DataFrame containing Z-scores of protein expressions, with proteins as rows and samples as columns.
        patient (str): The identifier of the patient for whom the data is being retrieved.

    Returns:
        pd.DataFrame: A DataFrame containing the following columns:
            - 'label': The protein name (for tumor antigens).
            - 'value': The Z-score for the protein expression.
            - 'type': The category of the protein (all labeled as "Tumor_Antigen" for this function).
            - 'color': The color assigned to each protein based on its type.

    Notes:
        - The function filters the data to only include proteins that are classified as tumor antigens.
        - The proteins are mapped to predefined categories and assigned specific colors based on their category.
        - The data is sorted by category and expression value in descending order to prioritize higher values.

    Example:
        tumor_antigen_data = get_circular_barplot_data_tumor_antigens(expression_z_scores_df, "Patient_123")
    """
    df = pd.DataFrame.from_dict(
        topas.TOPAS_CATEGORIES, orient="index", columns=["type"]
    )
    interested_proteins = df.index[df.type == "Tumor_Antigen"].tolist()
    expression_df = expression_z_scores_df[
        expression_z_scores_df.index.isin(interested_proteins)
    ]
    expression_df = expression_df[[patient]]
    expression_df.columns = ["value"]
    expression_df = expression_df.dropna()
    expression_df["label"] = expression_df.index
    expression_df["type"] = expression_df.label.map(topas.TOPAS_CATEGORIES)
    expression_df["color"] = expression_df.type.map(topas.TOPAS_COLORING_RULE)
    expression_df = expression_df.sort_values(
        by=["type", "value"], ascending=[False, False]
    )
    return expression_df


def getlolipop_expression_topas(
    expression_z_scores_df: pd.DataFrame,
    topas_z_scores_df: pd.DataFrame,
    patient: str,
    type_to_filter: str = "RTK",
):
    """
    Retrieves and merges expression Z-scores and topas Z-scores for a specific patient,
    preparing the data for a lollipop plot to visualize the relationship between expression scores
    and topas scores for different protein groups.

    This function filters the expression scores for proteins mapped in `TOPAS_EXPRESSION_MAPPING` 
    and the topas scores for a specified patient. It processes the data, ensuring that expression 
    and topas scores are merged in a way that allows for easy visualization in a lollipop plot. 
    Negative scores are converted to zero, and topas scores are inverted to show them as downward 
    bars in the plot.

    Args:
        expression_z_scores_df (pd.DataFrame): DataFrame containing protein expression Z-scores, 
                                                with proteins as rows and samples as columns.
        topas_z_scores_df (pd.DataFrame): DataFrame containing topas Z-scores, with topass as 
                                           rows and samples as columns.
        patient (str): The identifier of the patient whose data is being retrieved.
        type_to_filter (str, optional): The topas category to filter the data by. Defaults to "RTK".

    Returns:
        pd.DataFrame: A DataFrame formatted for use in a lollipop plot, containing the following columns:
            - 'label': The protein or topas name.
            - 'type': The protein or topas category.
            - 'expression_score': The expression Z-score for the protein.
            - 'topas_score': The inverted topas Z-score for the corresponding topas.
            - 'type2': The category of the topas.
            - 'color': The color assigned to the category based on `TOPAS_COLORING_RULE`.

    Notes:
        - The data is filtered to include only the proteins specified in `TOPAS_EXPRESSION_MAPPING`.
        - Expression scores are set to zero if they are negative.
        - Topas scores are also set to zero if they are negative, and are inverted to show downward bars.
        - The output DataFrame is filtered by `type_to_filter` to show only the specified category (e.g., "RTK").

    Example:
        lollipop_data = getlolipop_expression_topas(expression_z_scores_df, topas_z_scores_df, "Patient_123")
    """
    expression_z_scores_df = utils.unnest_proteingroups(expression_z_scores_df)
    # patient_col = patient  + ' Z-score'
    protein_keys = [
        x
        for x in topas.TOPAS_EXPRESSION_MAPPING.keys()
        if x in expression_z_scores_df.index
    ]

    # expression_df = expression_z_scores_df.loc[protein_keys, [patient_col]]
    expression_df = expression_z_scores_df.loc[protein_keys, :]
    expression_df = expression_df.fillna(0)
    expression_df.columns = ["expression_score"]
    expression_df["label"] = expression_df.index
    expression_df["expression_score"][expression_df["expression_score"] < 0] = 0

    topas_z_scores_df = get_topas_scores_long_format(topas_z_scores_df)
    topas_df = topas_z_scores_df[
        (
            topas_z_scores_df["Sample name"].isin([patient])
            & topas_z_scores_df["Topas_id"].isin(
                topas.TOPAS_EXPRESSION_MAPPING.values()
            )
        )
    ].set_index("Topas_id")[["Z-score"]]
    topas_df = topas_df.fillna(0)

    topas_df.columns = ["topas_score"]
    topas_df["type"] = topas_df.index
    topas_df["topas_score"][topas_df["topas_score"] < 0] = 0
    topas_df["topas_score"] = (
        -1 * topas_df["topas_score"]
    )  # to show them downward of the lolipop plot
    expression_df["type"] = expression_df["label"].map(topas.TOPAS_EXPRESSION_MAPPING)

    merged_df = expression_df.merge(topas_df, on="type", how="outer")
    merged_df["expression_score"] = merged_df["expression_score"].fillna(0)

    merged_df = merged_df.dropna(subset=["type", "label"])
    merged_df["topas_score"] = merged_df["topas_score"].fillna(0)

    final_df = pd.melt(
        merged_df,
        value_vars=["expression_score", "topas_score"],
        id_vars=["label", "type"],
    )
    final_df["type2"] = final_df["type"].map(topas.TOPAS_CATEGORIES)
    final_df["color"] = final_df.type2.map(topas.TOPAS_COLORING_RULE)
    final_df["type"] = final_df.type2
    return final_df[final_df.type == type_to_filter]


def get_topas_subscore_data_per_type(
    report_dir: str,
    topas_name: str,
    sub_type: str = "important phosphorylation",
    return_json: bool = False,
):
    """
    Retrieves sub-topas data for a specific topas and sub-type (e.g., phosphorylation), 
    and optionally returns the data in JSON format.

    This function loads sub-topas data from a report directory, filters it by the specified 
    sub-type (e.g., "important phosphorylation"), and returns the data either as a DataFrame 
    or in JSON format, based on the `return_json` flag. If the sub-topas data for the specified 
    topas is not found, it raises an error.

    Args:
        report_dir (str): The directory where the report data is stored.
        topas_name (str): The name of the topas for which the sub-topas data is being retrieved.
        sub_type (str, optional): The type of sub-topas data to filter by. Defaults to "important phosphorylation".
        return_json (bool, optional): Flag indicating whether to return the data in JSON format. Defaults to False.

    Returns:
        pd.DataFrame or str: A DataFrame containing the filtered sub-topas data with Z-scores, or 
                             a JSON string if `return_json` is True.

    Raises:
        ValueError: If no sub-topas data is found for the specified topas name.

    Example:
        # To get sub-topas data as a DataFrame for the topas "Topas1" and sub-type "important phosphorylation"
        df = get_topas_subscore_data_per_type(report_dir="path/to/reports", topas_name="Topas1")
        
        # To get the same data in JSON format
        json_data = get_topas_subscore_data_per_type(report_dir="path/to/reports", topas_name="Topas1", return_json=True)
    """
    try:
        df = topas_loader.load_topas_subscore_table(
            report_dir, topas_name, return_wide=True
        )
        df = df.set_index("Sample name")
        df = df.filter(regex=sub_type)
        if return_json:
            df.columns = ["Z-score"]
            df["Sample name"] = df.index
            df = df.dropna()
            return utils.df_to_json(df)

        df = df.T
        df.columns = df.columns + " Z-score"
    except:
        raise ValueError(f"no data found for the TOPAS subscore {topas_name}")
    return df
