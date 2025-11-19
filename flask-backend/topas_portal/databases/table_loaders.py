import pandas as pd

from topas_portal import settings
from topas_portal import utils
from topas_portal.config import CohortConfig
from topas_portal.file_loaders.cacheable import cacheable
import topas_portal.file_loaders.topas as topas_loader
import topas_portal.file_loaders.transcriptomics as tp
import topas_portal.file_loaders.genomics as genomics_preprocess
import topas_portal.file_loaders.phospho_score as phospho_score_loader
import topas_portal.file_loaders.expression as expression_loader
import topas_portal.file_loaders.sample_annotation as sample_annotation_loader
import topas_portal.file_loaders.patient_metadata as patient_metadata_loader


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


@cacheable(utils.DataType.TRANSCRIPTOMICS)
def load_transcriptomics_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    fpkm_path, fpkm_zscored_path = config.get_transcriptomics_paths(cohort_name)
    fpkm_df = tp.load_FPKM_table(fpkm_zscored_path)
    fpkm_not_zscored_df = tp.load_FPKM_table(fpkm_path)
    return fpkm_df.join(
        fpkm_not_zscored_df,
        lsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE],
        rsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.INTENSITY],
    )


@cacheable(utils.DataType.GENOMICS)
def load_genomics_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    return genomics_preprocess.load_genomics_table(
        config.get_genomics_path(cohort_name)
    )


@cacheable(utils.DataType.FULL_PROTEOME)
def load_fp_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    fp_annotated_intensity_path, *fp_measures_paths = config.get_fp_data_paths(
        cohort_name
    )
    if fp_annotated_intensity_path is None:
        return pd.DataFrame()

    fp_intensity = expression_loader.load_annotated_intensity_file(
        fp_annotated_intensity_path,
        settings.FP_KEY,
    )
    fp_df = expression_loader.load_expression_data(fp_measures_paths, settings.FP_KEY)
    return fp_df.join(fp_intensity, how="right")


@cacheable(utils.DataType.PHOSPHO_PROTEOME)
def load_pp_data(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    pp_annotated_intensity_path, *pp_measures_paths = config.get_pp_data_paths(
        cohort_name
    )
    if pp_annotated_intensity_path is None:
        return pd.DataFrame()

    pp_intensity = expression_loader.load_annotated_intensity_file(
        pp_annotated_intensity_path,
        settings.PP_KEY,
        extra_columns=list(settings.ANNOTATION_COLUMNS.keys()),
    )
    pp_df = expression_loader.load_expression_data(pp_measures_paths, settings.PP_KEY)
    return pp_df.join(pp_intensity, how="right")


@cacheable(utils.DataType.TOPAS_RTK_SCORE)
def load_topas_rtk_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    topas_rtk_scores_path, topas_rtk_scores_zscored_path = (
        config.get_topas_rtk_scores_paths(cohort_name)
    )
    df = topas_loader.load_topas_scores_df(topas_rtk_scores_path)
    if isinstance(df, pd.DataFrame):
        z_df = topas_loader.load_topas_scores_df(topas_rtk_scores_zscored_path)
        df = df.join(
            z_df,
            lsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.SCORE],
            rsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE],
        )
    df.index.name = "TOPAS identifier"
    return df


@cacheable(utils.DataType.TOPAS_CK_SCORE)
def load_topas_ck_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    return topas_loader.load_topas_scores_df(
        config.get_topas_ck_scores_path(cohort_name),
        index_col="Sample name",
        intensity_unit_suffix=utils.INTENSITY_UNIT_SUFFIXES[
            utils.IntensityUnit.Z_SCORE
        ],
    )


@cacheable(utils.DataType.KINASE_SCORE)
def load_kinase_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    rtk_df = topas_loader.load_topas_scores_df(
        config.get_topas_rtk_substrate_phos_scores_path(cohort_name),
        index_col="Sample name",
        intensity_unit_suffix=utils.INTENSITY_UNIT_SUFFIXES[
            utils.IntensityUnit.Z_SCORE
        ],
    )
    ck_df = topas_loader.load_topas_scores_df(
        config.get_topas_ck_scores_path(cohort_name),
        index_col="Sample name",
        intensity_unit_suffix=utils.INTENSITY_UNIT_SUFFIXES[
            utils.IntensityUnit.Z_SCORE
        ],
    )
    if isinstance(rtk_df, pd.DataFrame) and isinstance(ck_df, pd.DataFrame):
        return pd.concat([rtk_df, ck_df], axis=0)
    return rtk_df


@cacheable(utils.DataType.PHOSPHO_SCORE)
def load_phospho_scores(cohort_name: str, config: CohortConfig) -> pd.DataFrame:
    return phospho_score_loader.load_phosphorylation_scores(
        config.get_protein_phosphorylation_scores_path(cohort_name),
        intensity_unit_suffix=utils.INTENSITY_UNIT_SUFFIXES[
            utils.IntensityUnit.Z_SCORE
        ],
    )


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
        utils.DataType.PATIENT_METADATA: load_patient_metadata,
        utils.DataType.SAMPLE_ANNOTATION: load_sample_annotation,
        utils.DataType.FULL_PROTEOME: load_fp_data,
        utils.DataType.PHOSPHO_PROTEOME: load_pp_data,
        utils.DataType.TOPAS_RTK_SCORE: load_topas_rtk_scores,
        utils.DataType.TOPAS_CK_SCORE: load_topas_ck_scores,
        utils.DataType.KINASE_SCORE: load_kinase_scores,
        utils.DataType.PHOSPHO_SCORE: load_phospho_scores,
    }

    results = {}
    for key, loader_fn in loaders.items():
        try:
            df = loader_fn(cohort_name, config)
            results[key] = df
        except Exception as e:
            print(f"[WARN] Could not load {key}: {e}")
            results[key] = pd.DataFrame()

    return results
