from pathlib import Path
from typing import Dict
import pandas as pd


from topas_portal import settings
from topas_portal import utils
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


def load_patient_metadata(cohort_name: str, config: Dict) -> pd.DataFrame:
    return patient_metadata_loader.load_patient_table(
        Path(config["patient_annotation_path"][cohort_name])
    )


def load_sample_annotation(cohort_name: str, config: Dict) -> pd.DataFrame:
    return sample_annotation_loader.load_sample_annotation_table(
        Path(config["sample_annotation_path"][cohort_name])
    )


@cacheable(utils.DataType.TRANSCRIPTOMICS)
def load_transcriptomics_data(cohort_name: str, config: Dict) -> pd.DataFrame:
    fpkm_df = tp.load_FPKM_table(config["transcriptomics_path_z_scored"])
    fpkm_not_zscored_df = tp.load_FPKM_table(
        config["transcriptomics_path_not_z_scored"]
    )
    return fpkm_df.join(
        fpkm_not_zscored_df,
        lsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE],
        rsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.INTENSITY],
    )


@cacheable(utils.DataType.GENOMICS)
def load_genomics_data(cohort_name: str, config: Dict) -> pd.DataFrame:
    return genomics_preprocess.load_genomics_table(config["genomics_path"])


@cacheable(utils.DataType.FULL_PROTEOME)
def load_fp_data(cohort_name: str, config: Dict) -> pd.DataFrame:
    if not config["FP"].get(cohort_name, 0):
        return pd.DataFrame()

    report_dir = Path(config["report_directory"][cohort_name])
    sample_df = load_sample_annotation(cohort_name, config)
    patients_list = sample_df["Sample name"].unique().tolist()

    fp_intensity = expression_loader.load_annotated_intensity_file(
        report_dir / settings.PREPROCESSED_FP_INTENSITY,
        settings.FP_KEY,
        patients_list,
    )
    fp_df = expression_loader.load_expression_data(
        report_dir, settings.FP_KEY, "full_proteome"
    )
    return fp_df.join(fp_intensity, how="right")


@cacheable(utils.DataType.PHOSPHO_PROTEOME)
def load_pp_data(cohort_name: str, config: Dict) -> pd.DataFrame:
    if not config["PP"].get(cohort_name, 0):
        return pd.DataFrame()

    report_dir = Path(config["report_directory"][cohort_name])
    sample_df = load_sample_annotation(cohort_name, config)
    patients_list = sample_df["Sample name"].unique().tolist()

    pp_intensity = expression_loader.load_annotated_intensity_file(
        report_dir / settings.PREPROCESSED_PP_INTENSITY,
        settings.PP_KEY,
        patients_list,
        extra_columns=list(settings.ANNOTATION_COLUMNS.keys()),
    )
    pp_df = expression_loader.load_expression_data(
        report_dir, settings.PP_KEY, "phospho"
    )
    return pp_df.join(pp_intensity, how="right")


@cacheable(utils.DataType.TOPAS_RTK_SCORE)
def load_topas_rtk_scores(cohort_name: str, config: Dict) -> pd.DataFrame:
    report_dir = Path(config["report_directory"][cohort_name])
    df = topas_loader.load_topas_scores_df(report_dir / settings.TOPAS_RTK_SCORES_FILE)
    if isinstance(df, pd.DataFrame):
        z_df = topas_loader.load_topas_scores_df(
            report_dir / settings.TOPAS_RTK_Z_SCORES_FILE
        )
        df = df.join(
            z_df,
            lsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.SCORE],
            rsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE],
        )
    df.index.name = "TOPAS identifier"
    return df


@cacheable(utils.DataType.TOPAS_CK_SCORE)
def load_topas_ck_scores(cohort_name: str, config: Dict) -> pd.DataFrame:
    report_dir = Path(config["report_directory"][cohort_name])
    return topas_loader.load_topas_scores_df(
        report_dir / settings.TOPAS_CK_SCORES_FILE,
        index_col="Sample name",
        intensity_unit_suffix=utils.INTENSITY_UNIT_SUFFIXES[
            utils.IntensityUnit.Z_SCORE
        ],
    )


@cacheable(utils.DataType.KINASE_SCORE)
def load_kinase_scores(cohort_name: str, config: Dict) -> pd.DataFrame:
    report_dir = Path(config["report_directory"][cohort_name])
    rtk_df = topas_loader.load_topas_scores_df(
        report_dir / settings.KINASE_SCORES_FILE,
        index_col="Sample name",
        intensity_unit_suffix=utils.INTENSITY_UNIT_SUFFIXES[
            utils.IntensityUnit.Z_SCORE
        ],
    )
    ck_df = topas_loader.load_topas_scores_df(
        report_dir / settings.TOPAS_CK_SCORES_FILE,
        index_col="Sample name",
        intensity_unit_suffix=utils.INTENSITY_UNIT_SUFFIXES[
            utils.IntensityUnit.Z_SCORE
        ],
    )
    if isinstance(rtk_df, pd.DataFrame) and isinstance(ck_df, pd.DataFrame):
        return pd.concat([rtk_df, ck_df], axis=0)
    return rtk_df


@cacheable(utils.DataType.PHOSPHO_SCORE)
def load_phospho_scores(cohort_name: str, config: Dict) -> pd.DataFrame:
    report_dir = Path(config["report_directory"][cohort_name])
    return phospho_score_loader.load_phosphorylation_scores(
        report_dir / settings.PHOSPHORYLATION_SCORES,
        add_suffix=True,
    )


# -------------------------------------------------------------------
# Orchestrator
# -------------------------------------------------------------------


def load_all_tables(cohort_name: str, config: Dict):
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
