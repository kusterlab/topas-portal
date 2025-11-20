from __future__ import annotations

from typing import TYPE_CHECKING
import re

import pandas as pd
import numpy as np

from topas_portal import utils
from topas_portal import settings
import topas_portal.genomics_preprocess as genomics_prep
from . import patient_report

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


def get_protein_list_per_patient(patient_identifier, intensity_df):
    """Gets the unique list of the proteins for one patient as a dataFrame"""
    if isinstance(intensity_df, pd.DataFrame):
        patient_df = intensity_df[[str(patient_identifier)]]
        patient_df = patient_df.dropna()
        patient_proteins = pd.DataFrame(list(set(patient_df.index)))
        patient_proteins.columns = ["sample"]
        patient_proteins["group"] = str(patient_identifier)
        return patient_proteins
    else:
        pass


def get_pep_number_from_protein_name(
    num_pep_meta_df: pd.DataFrame, protein_name: str, regex_pattern
) -> pd.DataFrame:
    """
    Get the number of the identified peptides from a protein across all patients.
    :intensity_df: A pandas dataframe of the intensities with Identification metadata columns for each patient
    :protein_name: the name of the protein
    :USAGE :
        get_pep_number_from_protein_name(fp_df,'EGFR')

    """
    try:
        premeta_df = num_pep_meta_df.T.filter(regex=regex_pattern, axis=0)
        premeta_df[protein_name] = pd.to_numeric(premeta_df[protein_name])
        premeta_df["Sample name"] = premeta_df.index.str.replace(
            "Identification metadata ", "", regex=True
        )
        premeta_df.columns = ["num_pep", "Sample name"]
        return premeta_df
    except:
        pass


def _get_protein_list_per_batch(batchNo, sample_annotation, df_intensity):
    """Gets the list of the proteins for one batch as a dataFrame"""
    if isinstance(sample_annotation, pd.DataFrame) & isinstance(
        df_intensity, pd.DataFrame
    ):
        list_patients_batch = list(
            sample_annotation["Sample name"][
                sample_annotation["Batch_No"].astype(str) == str(batchNo)
            ]
        )
        list_patients_batch = utils.intersection(
            list_patients_batch, df_intensity.columns
        )
        if len(list_patients_batch) == 0:
            return pd.DataFrame(columns=["sample", "group"])  # return an empty df
        else:
            batch_df = df_intensity[list_patients_batch]
            batch_df = batch_df.dropna()
            batch_proteins = pd.DataFrame(list(set(batch_df.index)))
            batch_proteins.columns = ["sample"]
            batch_proteins["group"] = batchNo
            return batch_proteins
    else:
        pass


def merge_data_with_num_pep(
    abundances_df: pd.DataFrame, num_pep_meta_df: pd.DataFrame, identifier: str, regex
):
    """
    Merges the num_pep for a protein as a confidence measurement over all patients to the abundance table for  each protein
    """
    try:
        num_pep_df = get_pep_number_from_protein_name(
            num_pep_meta_df, identifier, regex
        )
        if isinstance(num_pep_df, pd.DataFrame) and (
            "Sample name" in num_pep_df.columns.tolist()
        ):
            abundances_table = abundances_df.merge(num_pep_df, on="Sample name")
            return abundances_table
        else:
            return abundances_df
    except Exception as err:
        print(f"{err} in merging with Num identified peptides")
        return abundances_df


def get_expression_data_per_analyte(
    abundances,
    patients_df,
    sample_annotation_df,
    imputation_mode: utils.ImputationMode,
):
    """
    abundances: dataframe with abundances for a single gene/p-site across all patients
    """
    abundances_table = get_expression_data_from_abundance_df(abundances)
    abundances_table = add_is_replicate_column(abundances_table)
    abundances_table = add_occurrence_and_fill_na_ranks(abundances_table)
    abundances_table = utils.merge_with_sample_annotation_df(
        abundances_table, sample_annotation_df
    )
    abundances_table = utils.merge_with_patients_meta_df(abundances_table, patients_df)
    abundances_table = min_impute_handler(abundances_table, imputation_mode)
    abundances_table = utils.fill_nans_patient_columns(abundances_table)
    abundances_table = utils.post_process_for_front_end(abundances_table)
    return abundances_table


def get_expression_data_from_abundance_df(abundances: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a wide-format abundance DataFrame into a tidy expression table,
    automatically recognizing measurement types based on configured suffixes.
    """
    # Build pattern from known suffixes
    suffixes = list(utils.INTENSITY_UNIT_SUFFIXES.values())
    pattern = r"(" + "|".join(map(re.escape, suffixes)) + r")$"

    # Melt to long format
    melted_df = abundances.melt(var_name="Measurement", value_name="Value")

    # Extract measurement type and sample name
    melted_df["Type"] = melted_df["Measurement"].str.extract(pattern)[0].str.strip()
    melted_df["Sample name"] = melted_df["Measurement"].str.replace(
        pattern, "", regex=True
    )

    # Pivot to wide format
    result_df = melted_df.pivot_table(
        index="Sample name",
        columns="Type",
        values="Value",
        aggfunc="first",
        dropna=False,
    ).reset_index()

    # Consistent column order (Sample name first)
    ordered_cols = ["Sample name"] + [s.strip() for s in suffixes]
    result_df = result_df.reindex(columns=ordered_cols, fill_value=pd.NA)
    return result_df.sort_values(
        by=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.INTENSITY].strip(),
        ascending=False,
    )


def add_is_replicate_column(abundance_df: pd.DataFrame):
    """
    Adds a column to indicate whether a sample is a replicate.

    This function processes the 'Sample name' column in the input DataFrame to determine
    whether a sample is a replicate. It extracts the last part of the sample name
    (after the last "-") and assigns it to a new column called 'is_replicate'.
    If the extracted part does not contain "R", it is labeled as "not_replicate".

    Args:
        abundance_df (pd.DataFrame): A DataFrame containing an 'Sample name' column.

    Returns:
        pd.DataFrame: A modified DataFrame with an additional 'is_replicate' column.

    Notes:
        - The function makes a copy of the input DataFrame before modifying it.
        - It assumes that replicate samples are indicated by "-R" followed by a number
          (e.g., "Sample1-R1").
        - If an error occurs, the function returns the original DataFrame unchanged.
    """

    try:
        abundances_table = abundance_df.copy()
        abundances_table["is_replicate"] = (
            abundances_table["Sample name"].str.split("-").str[-1]
        )
        abundances_table.loc[
            ~abundances_table["is_replicate"].str.contains("R"), "is_replicate"
        ] = "not_replicate"
        return abundances_table
    except:
        return abundance_df


def add_occurrence_and_fill_na_ranks(df: pd.DataFrame):
    try:
        abundances_table = df.copy()
        abundances_table["Occurrence"] = abundances_table["Rank"].max()
        return abundances_table
    except:
        return df


def min_impute_handler(df: pd.DataFrame, imputation_mode: utils.ImputationMode):
    for col in ["Z-score", "Intensity"]:
        if col in df.columns.tolist():
            if imputation_mode == utils.ImputationMode.IMPUTE:
                min_value = df[col].min()
                df[col] = df[col].fillna(min_value)
            elif imputation_mode == utils.ImputationMode.NO_IMPUTE:
                df[col] = df[col].fillna("n.d.")
            else:
                raise ValueError(f"Unknown imputation mode {imputation_mode.value}")
    return df


def get_density_calc_protein(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index,
    identifier,
    intensity_unit: utils.IntensityUnit,
):
    samples_annotation_df = cohorts_db.get_sample_annotation_df(cohort_index)
    samples_list = samples_annotation_df["Sample name"].unique().tolist()
    temp_df = cohorts_db.get_protein_abundance_df(
        cohort_index, intensity_unit=intensity_unit
    )
    count_df_protein = utils.count_df_to_density_plot_df(
        temp_df, identifier, samples_list
    )
    return utils.df_to_json(count_df_protein)


def get_abundance(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    level: utils.DataType,
    identifier: str,
    imputation_mode: utils.ImputationMode,
    include_ref: utils.IncludeRef = utils.IncludeRef.EXCLUDE_REF,
):
    """_summary_

    Args:
        cohorts_db (data_api.CohortDataAPI): _description_
        cohort_index (int): _description_
        level (ef.DataType): _description_
        identifier (str): _description_
        imputation_mode (ef.ImputationMode): this imputes NAs in the correlation plot for visualization

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if level == utils.DataType.FULL_PROTEOME:
        abundances = cohorts_db.get_protein_abundance_df(
            cohort_index, identifier=identifier, include_ref=include_ref
        )
    elif level == utils.DataType.PHOSPHO_PROTEOME:
        abundances = cohorts_db.get_psite_abundance_df(
            cohort_index, identifier=identifier, include_ref=include_ref
        )
    elif level == utils.DataType.TRANSCRIPTOMICS:
        abundances = cohorts_db.get_fpkm_df(identifier=identifier)
    elif level == utils.DataType.KINASE_SCORE:
        abundances = cohorts_db.get_kinase_scores_df(
            cohort_index, identifier=identifier
        )
    elif level == utils.DataType.PHOSPHO_SCORE:
        abundances = cohorts_db.get_phosphorylation_scores_df(
            cohort_index, identifier=identifier
        )
    else:
        raise ValueError(f"Unknown data type for get_abundance: {level.value}")

    if len(abundances.index) == 0:
        return "", f'400 {level} "{identifier}" not found in dataset'

    if len(abundances.index) > 1:
        return "", f'400 {level} "{identifier}" found multiple times in dataset'

    patients_df = cohorts_db.get_patient_metadata_df(cohort_index)
    sample_annotation_df = cohorts_db.get_sample_annotation_df(cohort_index)
    abundances_table = get_expression_data_per_analyte(
        abundances,
        patients_df,
        sample_annotation_df,
        imputation_mode,
    )

    # adding num_pep and confidence score at FP level
    if level == utils.DataType.FULL_PROTEOME:
        abundances_table["num_pep"] = (
            abundances_table["Identification metadata"]
            .str.extract(settings.NUM_PEPTIDES_REGEX)
            .fillna(0)
            .astype(int)
        )
        abundances_table = utils.calculate_confidence_score(abundances_table)

    if level in [
        utils.DataType.FULL_PROTEOME,
        utils.DataType.TRANSCRIPTOMICS,
        utils.DataType.KINASE_SCORE,
        utils.DataType.PHOSPHO_SCORE,
    ]:
        # adding genomics data
        try:
            abundances_table = genomics_prep.merge_data_with_genomics_alterations(
                cohorts_db,
                abundances_table,
                identifier,
                annotation_type="genomics_annotations",
            )
        except:
            pass

        # adding onkoKB annotations
        try:
            abundances_table = genomics_prep._merge_onkokb_annotation(
                cohorts_db, abundances_table, identifier
            )
        except:
            pass

    # filtering the columns with the settings options
    abundances_table = abundances_table[
        utils.intersection(
            settings.EXPRESSION_TAB_DATA, abundances_table.columns.tolist()
        )
    ]
    abundances_table["index"] = abundances_table.index
    return utils.df_to_json(abundances_table)


def get_batches_proteins_as_json(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    level: utils.DataType,
    batchlists,
):
    if level == utils.DataType.FULL_PROTEOME:
        df = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
    elif level == utils.DataType.PHOSPHO_PROTEOME:
        df = cohorts_db.get_psite_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
    else:
        raise ValueError(f"Cannot compute protein overlap for data type {level.value}")

    sample_annotation = cohorts_db.get_sample_annotation_df(cohort_index)
    samples_list = sample_annotation["Sample name"].unique().tolist()
    sample_names = utils.intersection(samples_list, df.columns)
    df = df[sample_names]
    list_batches = batchlists.split(",")
    df_list = []
    for batch in list_batches:
        df_list.append(_get_protein_list_per_batch(batch, sample_annotation, df))

    venn_df = pd.concat(df_list)
    return utils.df_to_json(venn_df)


def get_patients_proteins_as_json(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    level: utils.DataType,
    patientslists: str,
):
    if level == utils.DataType.FULL_PROTEOME:
        df = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
    elif level == utils.DataType.PHOSPHO_PROTEOME:
        df = cohorts_db.get_psite_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
    else:
        raise ValueError(f"Cannot compute protein overlap for data type {level.value}")
    sample_annotation = cohorts_db.get_sample_annotation_df(cohort_index)
    samples_list = sample_annotation["Sample name"].unique().tolist()
    sample_names = utils.intersection(samples_list, df.columns)
    df = df[sample_names]
    list_patients = patientslists.split(",")
    df_list = []
    for patient in list_patients:
        df_list.append(get_protein_list_per_patient(patient, df))

    venn_df = pd.concat(df_list)
    return utils.df_to_json(venn_df)


def get_list_by_selected_modality_per_cohort(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, modality: str
):
    """Gets all items of the modality = batches or patients from the annotation file"""
    sample_annotation = cohorts_db.get_sample_annotation_df(cohort_index)
    if modality == "allbatch":
        result = sample_annotation["Batch_No"].unique()
    elif modality == "allpatients":
        result = sample_annotation["Sample name"].unique()
    else:
        result = sample_annotation["Entity"].unique()
    df = pd.DataFrame(result)
    df = df.dropna()
    df.columns = ["result"]
    return utils.df_to_json(df)


def num_identifications_per_patient(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, level: utils.DataType
):
    num_ids_df = cohorts_db.get_search_qc_df(cohort_index)
    if level == utils.DataType.FULL_PROTEOME:
        num_ids_df = num_ids_df[["Proteins_fp"]]
    elif level == utils.DataType.PHOSPHO_PROTEOME:
        num_ids_df = num_ids_df[["Mod_peptides_pp"]]
    elif level == utils.DataType.FULL_PROTEOME_NUM_PEPTIDES:
        num_ids_df = num_ids_df[["Mod_peptides_fp"]]
    else:
        raise ValueError(f"Unsupported data type for num identifications {level}")

    num_ids_df = num_ids_df.drop(
        index=num_ids_df.filter(regex=f"^{settings.REF_CHANNEL_PREFIX}", axis=0).index
    )
    num_ids_df = num_ids_df.reset_index()
    num_ids_df = num_ids_df.dropna()
    num_ids_df.columns = ["patients", "identified"]
    return num_ids_df


def summed_intensities_per_patient(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, level: utils.DataType
):
    """
    Getting the sum of intensities accross all patients for the PP for the Patient centric tab
    """
    summed_intensity_df = cohorts_db.get_search_qc_df(cohort_index)
    if level == utils.DataType.FULL_PROTEOME:
        summed_intensity_df = summed_intensity_df[["Summed peptide intensity_fp"]]
    elif level == utils.DataType.PHOSPHO_PROTEOME:
        summed_intensity_df = summed_intensity_df[["Summed phosphopeptide intensity"]]
    else:
        raise ValueError(f"Unsupported data type for summed intensity {level}")

    summed_intensity_df: pd.DataFrame = np.log10(summed_intensity_df)
    summed_intensity_df = summed_intensity_df.drop(
        index=summed_intensity_df.filter(
            regex=f"^{settings.REF_CHANNEL_PREFIX}", axis=0
        ).index
    )
    summed_intensity_df = summed_intensity_df.reset_index()
    summed_intensity_df = summed_intensity_df.dropna()
    summed_intensity_df.columns = ["patients", "sumIntensities"]
    return summed_intensity_df


def get_reports_per_patient(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    patient: str,
    level: utils.DataType,
):
    return patient_report.get_reports_per_patient(
        cohorts_db, level, cohort_index, patient
    )
