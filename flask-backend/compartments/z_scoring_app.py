import pandas as pd
import topas_portal.fetch_data_matrix as data
import topas_portal.tupacs_scores_meta as tupacs
from flask import Blueprint
from topas_portal.utils import calculate_z_scores,df_to_json,DataType,IntensityUnit,merge_with_patients_meta_df
import db



zscoring_page = Blueprint(
    "zscoring_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db

def main(annot_df:pd.DataFrame,meta_df:pd.DataFrame,all_possibiliteis:list,identifier:str,meta_col:str):
    """
    Computes z-scores for annotation data based on metadata and returns the processed results in JSON format.

    Args:
        annot_df (pd.DataFrame): The annotation DataFrame containing sample-related data.
        meta_df (pd.DataFrame): The metadata DataFrame containing patient information.
        all_possibiliteis (List[str]): A list of possible categories or values relevant to the analysis.
        identifier (str): The identifier used for grouping or reference in the analysis.
        meta_col (str): The metadata column to be used for z-score calculations.

    Returns:
        str: A JSON-formatted string containing the processed z-score data.

    Notes:
        - Merges `annot_df` with `meta_df` based on the "Sample name" column.
        - Computes z-scores for the specified metadata column using `calculate_sub_df_zscores`.
        - Applies post-processing using `post_process_final_df`.
        - Fills NaN values in the z-scores column with the minimum value minus one.
        - Converts the final DataFrame into JSON format using `df_to_json`.
    """
    raw_df = merge_with_patients_meta_df(annot_df,meta_df[['Sample name',meta_col]])
    zscores_df = calculate_sub_df_zscores(raw_df,all_possibiliteis,meta_col,identifier)
    zscores_df = post_process_final_df(zscores_df)
    min_value = zscores_df['zscores'].min() - 1
    zscores_df['zscores'] = zscores_df['zscores'].fillna(min_value)
    return df_to_json(zscores_df)

 

def calculate_sub_df_zscores(raw_df:pd.DataFrame,all_possibiliteis:list,meta_col:str,identifier:str) -> pd.DataFrame:
    """
    Computes z-scores for a dataset based on a given identifier and metadata categories.

    Args:
        raw_df (pd.DataFrame): The input DataFrame containing sample data and metadata.
        all_possibiliteis (List[str]): A list of possible categories within the `meta_col` to compute subset z-scores.
        meta_col (str): The metadata column used to categorize the data.
        identifier (str): The column for which z-scores are calculated.

    Returns:
        pd.DataFrame: A DataFrame containing z-scores for the full dataset and subsets, 
                      with additional metadata annotations.

    Notes:
        - Computes z-scores for the entire dataset based on `identifier`.
        - Iterates over `all_possibiliteis`, computing z-scores for each subset.
        - If an error occurs when processing a subset, it is silently skipped.
        - Merges all computed z-score subsets into a final DataFrame.
        - Ensures missing values in `meta_col` are replaced with 'n.d.'.
        - Adds a `data_type` column to distinguish between full and subset calculations.
    """
    raw_df['zscores'] = calculate_z_scores(raw_df[[identifier]],col_name=identifier)
    raw_df['data_type'] = 'all_data'

    sub_dfs = []
    for possibility in all_possibiliteis:
        try:
            sub_df = raw_df[raw_df[meta_col] == possibility]
            sub_df['zscores'] = calculate_z_scores(sub_df[[identifier]],col_name=identifier)
            sub_df['data_type'] = possibility
            sub_dfs.append(sub_df)
        except:
            pass
    sub_dfs = pd.concat(sub_dfs)
    final_df = pd.concat([raw_df,sub_dfs])[['Sample name',meta_col,'zscores','data_type']]
    final_df[meta_col] = final_df[meta_col].fillna('n.d.')
    final_df['meta_column'] = final_df[meta_col]
    return final_df



def post_process_final_df(df:pd.DataFrame) -> pd.DataFrame:
    """
    Adds post-processing attributes to the DataFrame for visualization or further analysis.

    Args:
        df (pd.DataFrame): The input DataFrame to be processed.

    Returns:
        pd.DataFrame: The modified DataFrame with additional columns.

    Modifications:
        - Adds a 'color' column with a default value of 'grey'.
        - Adds a 'sizeR' column with a default value of 0.5.
        - Adds an 'index' column representing the row index in sequential order.
    """
    df['color'] = 'grey'
    df['sizeR'] = 0.5
    df['index'] = range(len(df))
    return df


@zscoring_page.route("/zscore/<level>/<cohort_ind>/<identifier>/<allpossibilities>/<meta_col>")
# http://localhost:3832/zscore/protein/0/EGFR/MASTER,CATCH/Program
def get_onflyzscores_scores_cohort(cohort_ind,identifier,allpossibilities,meta_col,level):
    """
    Fetches data for a cohort, processes it for z-score calculations based on a specified level,
    and returns the processed z-scores using the `main` function.

    Args:
        cohort_ind (str): The cohort index to fetch the data for.
        identifier (str): The identifier (e.g., gene or protein) for which z-scores are calculated.
        allpossibilities (str): A comma-separated string of possible categories in the metadata column.
        meta_col (str): The metadata column used to group the data for z-score calculations.
        level (str): The data type level (e.g., TUPAC_SCORE, KINASE_SCORE, PHOSPHO_SCORE) to determine the intensity unit.

    Returns:
        pd.DataFrame: A DataFrame containing the processed z-scores, returned by the `main` function.

    Notes:
        - Fetches the data matrix for the cohort using the `fetch_data_matrix` function.
        - Transposes the DataFrame to switch rows and columns.
        - Adjusts the DataFrame based on the specified `level`, resetting the index or adding a 'Sample name' column.
        - Limits the `allpossibilities` list to the first 7 items if it contains more than 8 elements.
        - Passes the data to the `main` function for z-score calculation and processing.

    Example:
        result_df = get_onflyzscores_scores_cohort(
            cohort_ind="123", 
            identifier="gene1", 
            allpossibilities="A,B,C", 
            meta_col="group", 
            level="PHOSPHO_SCORE"
        )
    """
    all_possibitlitiese = allpossibilities.split(',')

    # Data modalities for the z scoring 
    if level == DataType.TUPAC_SCORE:
        unit = IntensityUnit.SCORE
    elif level == DataType.KINASE_SCORE or level == DataType.PHOSPHO_SCORE:
        unit = IntensityUnit.Z_SCORE
    else:
        unit = IntensityUnit.INTENSITY 

    

    raw_df = data.fetch_data_matrix(
        cohorts_db,
        cohort_ind,
        DataType(level),
        identifiers=[identifier],
        intensity_unit=unit,
    )

    input_df = raw_df.T  # we transpose dataframe 

    if level == DataType.TUPAC_SCORE:
        input_df = input_df.reset_index()
    else: 
        input_df['Sample name'] = input_df.index
    
    print(input_df)
    meta_df = cohorts_db.get_patient_metadata_df(cohort_ind)
    if len(all_possibitlitiese) > 8:
        all_possibitlitiese = all_possibitlitiese[0:7]

    return main(input_df,meta_df,all_possibitlitiese,identifier,meta_col)


    