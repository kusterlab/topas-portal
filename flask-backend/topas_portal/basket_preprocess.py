# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

import topas_portal.genomics_preprocess as gp
import topas_portal.settings as cn
import topas_portal.utils as utils
import topas_portal.tupacs_scores_meta as tupacs
import topas_portal.IFN_tupac_scoring as tupac_scoring
import topas_portal.file_loaders.tupac as tupac_loader

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


def get_basket_weights(basket_annotations_df: pd.DataFrame) -> pd.DataFrame:
    """Returns a DataFrame with gene weights (not p-sites!) for all baskets.

    Adapted for the 4th generation.

    returns:
        pd.DataFrame[gene, weight, basket]
    """
    selected_columns = {"GENE NAME": "gene", "WEIGHT": "weight", "SUBBASKET": "basket"}
    weights_df = basket_annotations_df[selected_columns.keys()]
    weights_df = weights_df.rename(columns=selected_columns, errors="raise")

    weights_df["basket"] = weights_df["basket"].str.replace(r"[\s\/-]", "_", regex=True)
    weights_df["weight"] = weights_df["weight"].fillna(1)
    weights_df = weights_df.drop_duplicates(keep="first")

    return weights_df


def _merge_baskets_with_metadata(
    basket_df: pd.DataFrame,
    sample_annotation_df: pd.DataFrame,
    patients_df: pd.DataFrame,
):
    """
    Merges basket data with sample annotation and patient metadata, and fills missing patient-related values.

    Args:
        basket_df (pd.DataFrame): The DataFrame containing the basket data (e.g., gene or protein measurements).
        sample_annotation_df (pd.DataFrame): The DataFrame containing the sample annotation (e.g., sample names and groupings).
        patients_df (pd.DataFrame): The DataFrame containing patient metadata (e.g., clinical data).

    Returns:
        pd.DataFrame: The merged DataFrame containing basket data enriched with sample annotation and patient metadata.
    
    Notes:
        - Merges `basket_df` with `sample_annotation_df` based on sample identifiers.
        - Enriches the merged DataFrame with patient metadata from `patients_df`.
        - Fills missing values in patient-related columns in the resulting DataFrame.
    
    Example:
        merged_df = _merge_baskets_with_metadata(basket_df, sample_annotation_df, patients_df)
    """
    basket_df = utils.merge_with_sample_annotation_df(basket_df, sample_annotation_df)
    basket_df = utils.merge_with_patients_meta_df(basket_df, patients_df)
    basket_df = utils.fill_nans_patient_columns(basket_df)
    return basket_df


def get_subbasket_data(
    cohorts_db: data_api.CohortDataAPI, cohort_index: str, basketname: str
):
    """
    Fetches and processes all sub-basket data for a given main basket.

    Args:
        cohorts_db (data_api.CohortDataAPI): The CohortDataAPI instance for accessing cohort data.
        cohort_index (str): The index of the cohort to retrieve data for.
        basketname (str): The name of the main basket for which sub-basket data is fetched.

    Returns:
        dict: A dictionary containing the sub-basket data in JSON format.

    Notes:
        - Retrieves the report directory for the given cohort.
        - Loads the sub-basket data table corresponding to the provided basket name.
        - Strips leading/trailing whitespace and removes tab characters from the "basket" column.
    
    Example:
        subbasket_data = get_subbasket_data(cohorts_db, "1", "basket_name")
    """
    report_dir = cohorts_db.config.get_report_directory(cohort_index)
    basket_sub_df = tupac_loader.load_subbasket_table(report_dir, basketname)
    basket_sub_df["basket"].str.replace("\t", "")
    basket_sub_df["basket"].str.strip()
    return utils.df_to_json(basket_sub_df)


def get_basket_unique(basket_df: pd.DataFrame, categories: str):
    """
    Retrieves unique basket names for a cohort, optionally filtered by specified categories.

    Args:
        basket_df (pd.DataFrame): The DataFrame containing basket data (e.g., gene or protein data).
        categories (str): A comma-separated string of categories to filter the basket names by. 
                          If set to "all", no filtering is applied.

    Returns:
        dict: A dictionary containing the unique basket names in JSON format.

    Notes:
        - The function retrieves unique basket names from the index of `basket_df`.
        - Appends a predefined value, "IFN_sig", to the list of basket names.
        - If `categories` is not "all", it filters the basket names based on the category mappings defined in `tupacs.TUPAC_CATEGORIES`.
    
    Example:
        basket_names = get_basket_unique(basket_df, "category1,category2")
    """

    ids = basket_df.index.unique().tolist()
    ids.append("IFN_sig")
    if categories != "all":
        ids = [
            tupac_id
            for tupac_id in ids
            if tupacs.TUPAC_CATEGORIES.get(tupac_id, None) in categories.split(",")
        ]
    ids = pd.DataFrame(ids, columns=["ids"])
    return utils.df_to_json(ids)


def get_basket_data(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    basket_names: str,
    score_type: str,
):
    """
    Retrieves and processes basket data for a specific cohort, including merging with metadata 
    and genomics annotations.

    Args:
        cohorts_db (data_api.CohortDataAPI): The CohortDataAPI instance for accessing cohort data.
        cohort_index (str): The index of the cohort to retrieve data for.
        basket_names (str): A comma-separated string of basket names to fetch data for.
        score_type (str): The type of score to be used for retrieving basket data.

    Returns:
        dict: A dictionary containing the processed basket data in JSON format.

    Notes:
        - Fetches a subset of the basket data using `get_basket_subset_df`.
        - Merges the basket data with sample annotation and patient metadata.
        - Filters the DataFrame to retain only relevant metadata columns.
        - Merges genomics alterations and OncoKB annotations into the basket data.
        - The final data is returned in JSON format.

    Example:
        basket_data = get_basket_data(cohorts_db, "cohort_1", "basket1,basket2", "score_type1")
    """
    basket_subset_df = get_basket_subset_df(
        cohorts_db, cohort_index, basket_names, score_type
    )

    basket_subset_df = _merge_baskets_with_metadata(
        basket_subset_df,
        cohorts_db.get_sample_annotation_df(cohort_index),
        cohorts_db.get_patient_metadata_df(cohort_index),
    )
    selected_columns = utils.intersection(cn.BASKET_META_DATA, basket_subset_df.columns)
    basket_subset_df = basket_subset_df[selected_columns]
    basket_subset_df = gp._merge_data_with_genomics_alterations(
        cohorts_db,
        basket_subset_df,
        basket_names,
        annotation_type="genomics_annotations",
    )
    basket_subset_df = gp._merge_data_with_genomics_alterations(
        cohorts_db, basket_subset_df, basket_names, annotation_type="oncoKB_annotations"
    )

    return utils.df_to_json(basket_subset_df)


def get_basket_scores_long_format(basket_scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts a wide-format basket scores DataFrame into a long format, where each row represents 
    a single sample and its corresponding basket score.

    Args:
        basket_scores_df (pd.DataFrame): A DataFrame where columns represent baskets and rows represent samples, 
                                         with Z-scores as the values.

    Returns:
        pd.DataFrame: A DataFrame in long format, where each row represents a sample and its corresponding basket, 
                      with columns for 'Sample name', 'Basket_id', and 'Z-score'.

    Notes:
        - The function transposes the input DataFrame, reshaping it from wide format to long format.
        - It drops any rows with missing values (NaNs) from the reshaped DataFrame.
        - The resulting DataFrame has three columns: 'Sample name', 'Basket_id', and 'Z-score'.

    Example:
        long_format_df = get_basket_scores_long_format(basket_scores_df)
    """
    basket_scores_df = basket_scores_df.T
    basket_names = basket_scores_df.columns.tolist()

    basket_scores_long = pd.melt(
        basket_scores_df.reset_index(),
        id_vars="Sample name",
        value_vars=basket_names,
        value_name="Z-score",
    )
    basket_scores_long = basket_scores_long.dropna()
    basket_scores_long.columns = ["Sample name", "Basket_id", "Z-score"]

    return basket_scores_long


def get_basket_subset_df(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    basket_names: str,
    score_type: str,
) -> pd.DataFrame:
    """
    Retrieves a subset of basket scores for a specific cohort, either using pre-calculated basket scores 
    or by calculating TUPAC scores for a specified basket.

    Args:
        cohorts_db (data_api.CohortDataAPI): The CohortDataAPI instance for accessing cohort data.
        cohort_index (str): The index of the cohort to retrieve data for.
        basket_names (str): A comma-separated string of basket names to filter the data by.
        score_type (str): The type of score to use, either "basket_score" or another type that defaults to Z-scores.

    Returns:
        pd.DataFrame: A DataFrame containing the subset of basket scores for the specified cohort and basket names.

    Notes:
        - If the basket name is "IFN_sig", TUPAC scores are calculated using protein abundance data.
        - Otherwise, the function filters the basket scores DataFrame based on the provided basket names.
        - The basket scores are returned in long format using `get_basket_scores_long_format`.
    
    Example:
        basket_subset_df = get_basket_subset_df(cohorts_db, "1", "basket1,basket2", "basket_score")
    """
    if score_type == "basket_score":
        score_unit = utils.IntensityUnit.SCORE
    else:
        score_unit = utils.IntensityUnit.Z_SCORE

    basket_df = cohorts_db.get_basket_scores_df(cohort_index, score_unit)
    basket_df = get_basket_scores_long_format(basket_df)

    if basket_names == "IFN_sig":

        tupac_df = tupac_scoring.calculate_TUPAC_scores(
            cohorts_db.get_protein_abundance_df(
                cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
            ),
            cohorts_db.get_patient_metadata_df(cohort_index),
            score_type=score_type,
        )
        print(tupac_df)
        basket_subset_df = tupac_df
    else:
        basket_subset_df = basket_df[
            basket_df["Basket_id"].isin(basket_names.split(","))
        ]
    return basket_subset_df


def get_circular_barplot_data_pathways(basket_df: pd.DataFrame, patient: str):
    """
    Retrieves data for visualizing a circular barplot of pathway-related scores for a specific patient.

    This function processes the basket scores to create data formatted for a circular barplot or a 
    lollipop plot, representing the patient's scores across various sub-pathways. The data is filtered 
    to include only the baskets that are relevant to the patient and maps pathway categories to color codes.

    Args:
        basket_df (pd.DataFrame): DataFrame containing basket scores with sample names and basket IDs.
        patient (str): The identifier of the patient for whom the data is being retrieved.

    Returns:
        pd.DataFrame: A DataFrame containing the following columns:
            - 'label': The pathway name (basket ID).
            - 'value': The Z-score for the pathway.
            - 'type': The category of the pathway based on predefined rules.
            - 'color': The color assigned to each pathway based on its type.

    Notes:
        - The function filters the data for the given patient, ensuring that only relevant pathways are included.
        - The "Basket_id" is mapped to pathway categories and colors using predefined rules.
        - The data is sorted by pathway type and Z-score in descending order to prioritize higher scores.

    Example:
        circular_barplot_data = get_circular_barplot_data_pathways(basket_df, "Patient_123")
    """
    basket_df = get_basket_scores_long_format(basket_df)
    interested_baskets = list(set(tupacs.TUPAC_CATEGORIES.keys()))
    df = basket_df[basket_df["Sample name"] == str(patient)].set_index("Sample name")
    df = df[df.Basket_id.isin(interested_baskets)]
    df = df[["Basket_id", "Z-score"]]
    df = df.fillna(0)
    df.columns = ["label", "value"]
    df["type"] = df.label.map(tupacs.TUPAC_CATEGORIES)
    df["color"] = df.type.map(tupacs.TUPAC_COLORING_RULE)
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
        tupacs.TUPAC_CATEGORIES, orient="index", columns=["type"]
    )
    interested_proteins = df.index[df.type == "Tumor_Antigen"].tolist()
    expression_df = expression_z_scores_df[
        expression_z_scores_df.index.isin(interested_proteins)
    ]
    expression_df = expression_df[[patient]]
    expression_df.columns = ["value"]
    expression_df = expression_df.dropna()
    expression_df["label"] = expression_df.index
    expression_df["type"] = expression_df.label.map(tupacs.TUPAC_CATEGORIES)
    expression_df["color"] = expression_df.type.map(tupacs.TUPAC_COLORING_RULE)
    expression_df = expression_df.sort_values(
        by=["type", "value"], ascending=[False, False]
    )
    return expression_df


def getlolipop_expression_basket(
    expression_z_scores_df: pd.DataFrame,
    basket_z_scores_df: pd.DataFrame,
    patient: str,
    type_to_filter: str = "RTK",
):
    """
    Retrieves and merges expression Z-scores and basket Z-scores for a specific patient,
    preparing the data for a lollipop plot to visualize the relationship between expression scores
    and basket scores for different protein groups.

    This function filters the expression scores for proteins mapped in `TUPAC_EXPRESSION_MAPPING` 
    and the basket scores for a specified patient. It processes the data, ensuring that expression 
    and basket scores are merged in a way that allows for easy visualization in a lollipop plot. 
    Negative scores are converted to zero, and basket scores are inverted to show them as downward 
    bars in the plot.

    Args:
        expression_z_scores_df (pd.DataFrame): DataFrame containing protein expression Z-scores, 
                                                with proteins as rows and samples as columns.
        basket_z_scores_df (pd.DataFrame): DataFrame containing basket Z-scores, with baskets as 
                                           rows and samples as columns.
        patient (str): The identifier of the patient whose data is being retrieved.
        type_to_filter (str, optional): The basket category to filter the data by. Defaults to "RTK".

    Returns:
        pd.DataFrame: A DataFrame formatted for use in a lollipop plot, containing the following columns:
            - 'label': The protein or basket name.
            - 'type': The protein or basket category.
            - 'expression_score': The expression Z-score for the protein.
            - 'basket_score': The inverted basket Z-score for the corresponding basket.
            - 'type2': The category of the basket.
            - 'color': The color assigned to the category based on `TUPAC_COLORING_RULE`.

    Notes:
        - The data is filtered to include only the proteins specified in `TUPAC_EXPRESSION_MAPPING`.
        - Expression scores are set to zero if they are negative.
        - Basket scores are also set to zero if they are negative, and are inverted to show downward bars.
        - The output DataFrame is filtered by `type_to_filter` to show only the specified category (e.g., "RTK").

    Example:
        lollipop_data = getlolipop_expression_basket(expression_z_scores_df, basket_z_scores_df, "Patient_123")
    """
    expression_z_scores_df = utils.unnest_proteingroups(expression_z_scores_df)
    # patient_col = patient  + ' Z-score'
    protein_keys = [
        x
        for x in tupacs.TUPAC_EXPRESSION_MAPPING.keys()
        if x in expression_z_scores_df.index
    ]

    # expression_df = expression_z_scores_df.loc[protein_keys, [patient_col]]
    expression_df = expression_z_scores_df.loc[protein_keys, :]
    expression_df = expression_df.fillna(0)
    expression_df.columns = ["expression_score"]
    expression_df["label"] = expression_df.index
    expression_df["expression_score"][expression_df["expression_score"] < 0] = 0

    basket_z_scores_df = get_basket_scores_long_format(basket_z_scores_df)
    basket_df = basket_z_scores_df[
        (
            basket_z_scores_df["Sample name"].isin([patient])
            & basket_z_scores_df["Basket_id"].isin(
                tupacs.TUPAC_EXPRESSION_MAPPING.values()
            )
        )
    ].set_index("Basket_id")[["Z-score"]]
    basket_df = basket_df.fillna(0)

    basket_df.columns = ["basket_score"]
    basket_df["type"] = basket_df.index
    basket_df["basket_score"][basket_df["basket_score"] < 0] = 0
    basket_df["basket_score"] = (
        -1 * basket_df["basket_score"]
    )  # to show them downward of the lolipop plot
    expression_df["type"] = expression_df["label"].map(tupacs.TUPAC_EXPRESSION_MAPPING)

    merged_df = expression_df.merge(basket_df, on="type", how="outer")
    merged_df["expression_score"] = merged_df["expression_score"].fillna(0)

    merged_df = merged_df.dropna(subset=["type", "label"])
    merged_df["basket_score"] = merged_df["basket_score"].fillna(0)

    final_df = pd.melt(
        merged_df,
        value_vars=["expression_score", "basket_score"],
        id_vars=["label", "type"],
    )
    final_df["type2"] = final_df["type"].map(tupacs.TUPAC_CATEGORIES)
    final_df["color"] = final_df.type2.map(tupacs.TUPAC_COLORING_RULE)
    final_df["type"] = final_df.type2
    return final_df[final_df.type == type_to_filter]


def get_subbasket_data_per_type(
    report_dir: str,
    basket_name: str,
    sub_type: str = "important phosphorylation",
    return_json: bool = False,
):
    """
    Retrieves sub-basket data for a specific basket and sub-type (e.g., phosphorylation), 
    and optionally returns the data in JSON format.

    This function loads sub-basket data from a report directory, filters it by the specified 
    sub-type (e.g., "important phosphorylation"), and returns the data either as a DataFrame 
    or in JSON format, based on the `return_json` flag. If the sub-basket data for the specified 
    basket is not found, it raises an error.

    Args:
        report_dir (str): The directory where the report data is stored.
        basket_name (str): The name of the basket for which the sub-basket data is being retrieved.
        sub_type (str, optional): The type of sub-basket data to filter by. Defaults to "important phosphorylation".
        return_json (bool, optional): Flag indicating whether to return the data in JSON format. Defaults to False.

    Returns:
        pd.DataFrame or str: A DataFrame containing the filtered sub-basket data with Z-scores, or 
                             a JSON string if `return_json` is True.

    Raises:
        ValueError: If no sub-basket data is found for the specified basket name.

    Example:
        # To get sub-basket data as a DataFrame for the basket "Basket1" and sub-type "important phosphorylation"
        df = get_subbasket_data_per_type(report_dir="path/to/reports", basket_name="Basket1")
        
        # To get the same data in JSON format
        json_data = get_subbasket_data_per_type(report_dir="path/to/reports", basket_name="Basket1", return_json=True)
    """
    try:
        df = tupac_loader.load_subbasket_table(
            report_dir, basket_name, return_wide=True
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
        raise ValueError(f"no data found for the subbasket {basket_name}")
    return df
