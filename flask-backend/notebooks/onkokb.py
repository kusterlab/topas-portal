import traceback
import sys
import os
import logging
import shutil
import threading
from pathlib import Path
import zipfile

from flask import Flask, render_template, Response, jsonify, send_from_directory
from flask_cors import CORS
from flask_caching import Cache
from flask_compress import Compress

import db
import routing_converters

from topas_portal.routes import ApiRoutes
from topas_portal.data_api.exceptions import (
    CohortDataNotLoadedError,
    DataLayerUnavailableError,
    IntensityUnitUnavailableError,
)
from topas_portal.data_api.data_api import CohortDataAPI

from topas_portal import utils
from topas_portal import transcripts_preprocess as transcript
from topas_portal import settings

from topas_portal import prexp_preprocess as pp
from topas_portal import topas_preprocess as bp
from topas_portal import correlations_preprocess as cp
from topas_portal import fetch_data_matrix as hp
from topas_portal import differential_expression as differential_test
from topas_portal import genomics_preprocess as genomics_process


config = {
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300,
}
UPLOAD_FOLDER = "./uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# global variables
error_log = []
cohorts_db: CohortDataAPI = db.cohorts_db

app = Flask(__name__, static_folder="../dist/static", template_folder="../dist")

app.config.from_mapping(config)
app.config["config_file"] = cohorts_db.config.get_config_path()
app.config["LOCAL_HTTTP"] = cohorts_db.config.get_local_http()
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["integration_http"] = cohorts_db.config.get_integration_test_http()

app.url_map.converters["data_type"] = routing_converters.DataTypeConverter
app.url_map.converters["intensity_unit"] = routing_converters.IntensityUnitConverter
app.url_map.converters["include_ref"] = routing_converters.IncludeRefConverter

cache = Cache(app)
Compress(app)
cohorts_db.load_all_data()
from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from topas_portal import utils
from topas_portal import settings
from topas_portal import fetch_data_matrix as data
import topas_portal.genomics_preprocess as genomics_prep
import topas_portal.psite_annotation as ps
import topas_portal.topas_preprocess as topas_loader

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
        list_patients_batch = utils.intersection(list_patients_batch, df_intensity.columns)
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
    abundances, patients_df, sample_annotation_df, imputation_mode: utils.ImputationMode,
):
    """
    abundances: dataframe with abundances for a single gene/p-site across all patients
    """
    abundances_table = get_expression_data_from_abundance_df(abundances)
    abundances_table = add_is_replicate_column(abundances_table)
    abundances_table = add_occurence_rank(abundances_table)
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
    abundances: dataframe with abundances for a single gene/p-site across all patients
    """
    # Melt the dataframe to long format
    melted_df = abundances.melt(var_name="Measurement", value_name="Value")

    # Extract measurement types and sample names
    melted_df["Type"] = melted_df["Measurement"].str.extract(
        r" (Z-score|FC|Intensity)"
    )[0]
    melted_df["Sample name"] = melted_df["Measurement"].str.replace(
        r" (Z-score|FC|Intensity)", "", regex=True
    )

    # Pivot the dataframe to wide format
    result_df = melted_df.pivot_table(
        index="Sample name",
        columns="Type",
        values="Value",
        aggfunc="first",
        dropna=False,
    ).reset_index()

    for col in ["FC", "Z-score", "Intensity"]:
        if col not in result_df.columns:
            result_df[col] = "N/A"

    return result_df[["Sample name", "FC", "Z-score", "Intensity"]]


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


def add_occurence_rank(df: pd.DataFrame):
    try:
        abundances_table = df.copy()
        abundances_table = abundances_table.sort_values("Z-score", ascending=False)
        occurrence = abundances_table["Z-score"].count()
        abundances_table["Rank"] = list(range(1, occurrence + 1)) + ["n.d."] * (
            len(abundances_table.index) - occurrence
        )
        abundances_table["Occurrence"] = occurrence
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
    samples_list = samples_annotation_df['Sample name'].unique().tolist()
    temp_df = cohorts_db.get_protein_abundance_df(
        cohort_index, intensity_unit=intensity_unit
    )
    count_df_protein = utils.count_df_to_density_plot_df(temp_df, identifier,samples_list)
    return utils.df_to_json(count_df_protein)





def get_batches_proteins_as_json(
    cohorts_db: data_api.CohortDataAPI, cohort_index, pp_fp, batchlists
):
    sample_annotation = cohorts_db.get_sample_annotation_df(cohort_index)
    if pp_fp == utils.DataType.FP:
        df = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
    else:
        df = cohorts_db.get_psite_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
    samples_list = sample_annotation['Sample name'].unique().tolist()
    sample_names = utils.intersection(samples_list,df.columns)
    df = df[sample_names]
    list_batches = batchlists.split(";")
    df_list = []
    for batch in list_batches:
        df_list.append(_get_protein_list_per_batch(batch, sample_annotation, df))

    venn_df = pd.concat(df_list)
    return utils.df_to_json(venn_df)


def get_patients_proteins_as_json(
    cohorts_db: data_api.CohortDataAPI, cohort_index, pp_fp, patientslists
):
    # TODO: replace with utils.DataType
    if pp_fp == utils.DataType.FP:
        df = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
    else:
        df = cohorts_db.get_psite_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )

    sample_annotation = cohorts_db.get_sample_annotation_df(cohort_index)
    samples_list = sample_annotation['Sample name'].unique().tolist()
    sample_names = utils.intersection(samples_list,df.columns)
    df = df[sample_names]
    list_patients = patientslists.split(";")
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


def identifications_across_all_patients(
    cohorts_db: data_api.CohortDataAPI, fp_pp: str, cohort_index: int
):
    # TODO: replace with utils.DataType
    if fp_pp == "fp":
        df = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
        nan_count = pd.DataFrame(df.notna().sum())
    elif fp_pp == "pp":
        df = cohorts_db.get_psite_abundance_df(
            cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
        )
        nan_count = pd.DataFrame(df.notna().sum())
    else:
        df = cohorts_db.get_num_pep_fp(cohort_index).copy()
        df.columns = df.columns.str.replace("Identification metadata ", "", regex=True)
        nan_count = pd.DataFrame(df.sum())
    nan_count.columns = ["identified"]
    nan_count["patients"] = df.columns
    return nan_count


def sum_intensities_across_all_patients(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, dtype = 'pp'
):
    """
    Getting the sum of intensities accross all patients for the PP for the Patient centric tab
    """
    if dtype == 'pp':
        df = cohorts_db.get_psite_abundance_df(
        cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
    )
    else:
        df = cohorts_db.get_protein_abundance_df(
        cohort_index, intensity_unit=utils.IntensityUnit.INTENSITY
    )

    print(df)
    sum_intensities = pd.DataFrame(df.sum())
    sum_intensities.columns = ["sumIntensities"]
    sum_intensities["patients"] = df.columns
    return sum_intensities


def get_reports_per_patient(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    patient: str,
    level: utils.DataType,
    download_method: str = "onfly",
):
    read_from_the_report_dir = download_method == "fromreport"
    if not read_from_the_report_dir:
        final_df = _get_reports_per_patient_on_the_fly(
            cohorts_db, level, cohort_index, patient
        )
    else:
        final_df = _get_reports_per_patient_from_the_reports_folder(
            cohorts_db, level, cohort_index, patient
        )

    return final_df


def _get_reports_per_patient_from_the_reports_folder(
    cohorts_db: data_api.CohortDataAPI,
    level: utils.DataType,
    cohort_index: int,
    patient: str,
):
    reports_dir = cohorts_db.get_report_dir(cohort_index)
    path_to_patient_results = (
        reports_dir + "/Reports/" + patient + "_proteomics_results.xlsx"
    )
    sheetname = _get_sheetname_from_level(level)
    df = pd.read_excel(path_to_patient_results, sheet_name=sheetname)
    df = df.fillna("n.d")
    return df


def _get_sheetname_from_level(level: utils.DataType):
    if level == utils.DataType.PHOSPHO_PROTEOME:
        return "Phospho proteome"
    elif level == utils.DataType.FULL_PROTEOME:
        return "Global proteome"
    elif level == utils.DataType.TOPAS_SCORE:
        return "Topas"
    elif level == utils.DataType.PHOSPHO_SCORE:
        return "Protein phosphorylation"
    elif level == utils.DataType.KINASE_SCORE:
        return "Kinase"
    elif level == utils.DataType.TOPAS_SUBSCORE:
        return "sutopas"
    elif level == utils.DataType.BIOMARKER:
        return "Biomarkers"


def _get_reports_per_patient_on_the_fly(
    cohorts_db: data_api.CohortDataAPI, level, cohort_index, patient
):
    final_df = pd.DataFrame()
    if level == utils.DataType.PHOSPHO_PROTEOME:
        patient_column = patient + " Z-score"
        sub_df = cohorts_db.get_psite_abundance_df(
            cohort_index, patient_name=patient_column,
        )
        sub_df = sub_df.dropna()
        final_df = ps.phospho_annot(sub_df)

    elif level == utils.DataType.FULL_PROTEOME:
        patient_column = patient + " Z-score"
        sub_df = cohorts_db.get_protein_abundance_df(
            cohort_index, patient_name=patient_column,
        )
        sub_df["Gene names"] = sub_df.index
        final_df = sub_df.dropna()

    elif level == utils.DataType.TOPAS_SCORE:
        sub_df = cohorts_db.get_topas_scores_df(
            cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
        )
        sub_df = topas_loader.get_topas_scores_long_format(sub_df)
        sub_df = sub_df[sub_df["Sample name"] == patient]
        final_df = sub_df[["Topas_id", "Z-score"]]
        final_df = final_df.dropna()

    elif level == utils.DataType.KINASE_SCORE:
        sub_df = cohorts_db.get_kinase_scores_df(
            cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
        )
        sub_df["Kinase_names"] = sub_df.index
        final_df = sub_df[["Kinase_names", patient]]
        final_df = final_df.dropna()

    elif level == utils.DataType.PHOSPHO_SCORE:
        sub_df = cohorts_db.get_phosphorylation_scores_df(
            cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
        )
        sub_df["Gene names"] = sub_df.index
        final_df = sub_df[["Gene names", patient]]
        final_df = final_df.dropna()

    elif level == utils.DataType.TRANSCRIPTOMICS:
        sub_df = cohorts_db.get_fpkm_df(intensity_unit=utils.IntensityUnit.Z_SCORE)
        sub_df["Gene names"] = sub_df.index
        final_df = sub_df[["Gene names", patient]]

    return final_df




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
        abundances, patients_df, sample_annotation_df, imputation_mode,
    )

    # adding confidence score at FP level
    if level == utils.DataType.FULL_PROTEOME:
        intensity_df_fp_meta = cohorts_db.get_num_pep_fp(cohort_index, identifier)
        abundances_table = merge_data_with_num_pep(
            abundances_table, intensity_df_fp_meta, identifier, settings.REGEX_META
        )
        abundances_table = utils.calculate_confidence_score(abundances_table)

    if level in [
        utils.DataType.FULL_PROTEOME,
        utils.DataType.TRANSCRIPTOMICS,
        utils.DataType.KINASE_SCORE,
        utils.DataType.PHOSPHO_SCORE,
    ]:
        # adding genomics data

        print('Adding gene annotaion')
        abundances_table = genomics_prep._merge_data_with_genomics_alterations(
            cohorts_db,
            abundances_table,
            identifier,
            annotation_type="genomics_annotations"
        )


        # adding onkoKB annotations
        
        abundances_table = genomics_prep._merge_onkokb_annotation(
            cohorts_db,
            abundances_table,
            identifier
        )

    # filtering the columns with the settings options
    abundances_table = abundances_table[
        utils.intersection(settings.EXPRESSION_TAB_DATA, abundances_table.columns.tolist())
    ]
    abundances_table["index"] = abundances_table.index
    return abundances_table
df = get_abundance(cohorts_db,'0',utils.DataType.FULL_PROTEOME,'EGFR',imputation_mode=utils.ImputationMode.NO_IMPUTE)
genomics_prep.get_all_snv_per_NGS('EGFRENST00000275493.2exon17c.G1946Ap.G649E(functionalTargetfunctionalclinical)','EGFR',cohorts_db.get_oncoKB_annotations())