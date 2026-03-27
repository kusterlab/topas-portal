import traceback

import pandas as pd

from topas_portal.data_type import DataType
from topas_portal.constants import IntensityUnit
from topas_portal import constants

from .. import settings
from ..config import CohortConfig
from ..file_loaders.cacheable import cacheable
from ..file_loaders import topas as topas_loader
from ..file_loaders import transcriptomics as tp
from ..file_loaders import genomics as genomics_preprocess
from ..file_loaders import phospho_score as phospho_score_loader
from ..file_loaders import expression as expression_loader
from ..file_loaders import sample_annotation as sample_annotation_loader
from ..file_loaders import patient_metadata as patient_metadata_loader
from ..file_loaders import search_qc as search_qc_loader

# -------------------------------------------------------------------
# Loader functions (one per output key)
# -------------------------------------------------------------------


def load_patient_metadata(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    return patient_metadata_loader.load_patient_table(
        config.get_patients_metadata_path(cohort_name)
    )


def load_sample_annotation(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    return sample_annotation_loader.load_sample_annotation_table(
        config.get_sample_annotation_path(cohort_name)
    )


@cacheable(DataType.TRANSCRIPTOMICS)
def load_transcriptomics_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    zscore_path, fpkm_path = config.get_transcriptomics_paths(cohort_name)
    zscore_df = tp.load_FPKM_table(zscore_path)
    fpkm_df = tp.load_FPKM_table(fpkm_path)
    return zscore_df.join(
        fpkm_df,
        lsuffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.Z_SCORE],
        rsuffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.INTENSITY],
    )


@cacheable(DataType.GENOMICS)
def load_genomics_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    return genomics_preprocess.load_genomics_table(
        config.get_genomics_path(cohort_name)
    )


@cacheable(DataType.FULL_PROTEOME)
def load_fp_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    if not config.has_fp(cohort_name):
        return pd.DataFrame()

    fp_annotated_intensity_path, *fp_measures_paths = config.get_fp_data_paths(
        cohort_name
    )

    fp_intensity = expression_loader.load_annotated_intensity_file(
        fp_annotated_intensity_path,
        constants.FP_KEY,
        extra_columns=list(settings.ANNOTATION_COLUMNS.keys()),
    )
    fp_df = expression_loader.load_expression_data(fp_measures_paths, constants.FP_KEY)
    return fp_df.join(fp_intensity, how="right")


@cacheable(DataType.PHOSPHO_PROTEOME)
def load_pp_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    if not config.has_pp(cohort_name):
        return pd.DataFrame()

    pp_annotated_intensity_path, *pp_measures_paths = config.get_pp_data_paths(
        cohort_name
    )

    pp_intensity = expression_loader.load_annotated_intensity_file(
        pp_annotated_intensity_path,
        constants.PP_KEY,
        extra_columns=list(settings.ANNOTATION_COLUMNS.keys()),
    )
    pp_df = expression_loader.load_expression_data(pp_measures_paths, constants.PP_KEY)
    return pp_df.join(pp_intensity, how="right")


@cacheable(DataType.TOPAS_RTK_SCORE)
def load_topas_rtk_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    topas_rtk_scores_path, topas_rtk_scores_zscored_path = (
        config.get_topas_rtk_scores_paths(cohort_name)
    )
    df = topas_loader.load_topas_scores_df(topas_rtk_scores_path)
    if isinstance(df, pd.DataFrame):
        z_df = topas_loader.load_topas_scores_df(topas_rtk_scores_zscored_path)
        df = df.join(
            z_df,
            lsuffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.SCORE],
            rsuffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.Z_SCORE],
        )
    df.index.name = "TOPAS identifier"
    return df


@cacheable(DataType.TOPAS_CK_SCORE)
def load_topas_ck_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    return topas_loader.load_topas_scores_df(
        config.get_topas_ck_scores_path(cohort_name),
        index_col="Sample name",
        intensity_unit_suffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.Z_SCORE],
    )


@cacheable(DataType.KINASE_SCORE)
def load_substrate_phos_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    topas_rtk_substrate_phos_path, topas_ck_scores_path = (
        config.get_topas_substrate_phos_paths(cohort_name)
    )
    rtk_df = topas_loader.load_topas_scores_df(
        topas_rtk_substrate_phos_path,
        index_col="Sample name",
        intensity_unit_suffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.Z_SCORE],
    )
    ck_df = topas_loader.load_topas_scores_df(
        topas_ck_scores_path,
        index_col="Sample name",
        intensity_unit_suffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.Z_SCORE],
    )
    if isinstance(rtk_df, pd.DataFrame) and isinstance(ck_df, pd.DataFrame):
        return pd.concat([rtk_df, ck_df], axis=0)
    return rtk_df


@cacheable(DataType.PHOSPHO_SCORE)
def load_protein_phos_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    protein_phos_path, *protein_phos_measures_paths = (
        config.get_protein_phos_data_paths(cohort_name)
    )

    protein_phos_df = expression_loader.load_annotated_intensity_file(
        protein_phos_path,
        constants.FP_KEY,
        extra_columns=list(settings.ANNOTATION_COLUMNS.keys()),
        intensity_suffix=constants.INTENSITY_UNIT_SUFFIXES[IntensityUnit.Z_SCORE],
    )
    protein_measures_df = expression_loader.load_expression_data(
        protein_phos_measures_paths, constants.FP_KEY
    )
    return protein_phos_df.join(protein_measures_df, how="right")


def load_search_qc(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    search_qc_path_fp, search_qc_path_pp = config.get_search_qc_paths(cohort_name)
    search_qc_df_fp = search_qc_loader.load_search_qc_table(search_qc_path_fp)
    search_qc_df_pp = search_qc_loader.load_search_qc_table(search_qc_path_pp)
    search_qc_df = search_qc_df_fp.merge(
        search_qc_df_pp, on=["Sample", "Channel", "Experiment"], suffixes=("_fp", "_pp")
    )
    return search_qc_df.set_index("Sample")


# -------------------------------------------------------------------
# Orchestrator
# -------------------------------------------------------------------


def load_all_tables(cohort_name: str, config: CohortConfig):
    """
    Load all required tables for a cohort.
    Uses per-dataset caching if 'cache_dir' is defined in config.
    """

    print(f"Loading all data for cohort '{cohort_name}'")

    loaders = {
        DataType.PATIENT_METADATA: load_patient_metadata,
        DataType.SAMPLE_ANNOTATION: load_sample_annotation,
        DataType.FULL_PROTEOME: load_fp_data,
        DataType.PHOSPHO_PROTEOME: load_pp_data,
        DataType.TOPAS_RTK_SCORE: load_topas_rtk_scores,
        DataType.TOPAS_CK_SCORE: load_topas_ck_scores,
        DataType.KINASE_SCORE: load_substrate_phos_scores,
        DataType.PHOSPHO_SCORE: load_protein_phos_scores,
        DataType.SEARCH_QC: load_search_qc,
    }

    results = {}
    for key, loader_fn in loaders.items():
        try:
            df = loader_fn(cohort_name, config)
            results[key] = df
        except Exception as e:
            print(f"[WARN] Could not load {key}: {e}")
            traceback.print_exc()
            results[key] = pd.DataFrame()

    return results
