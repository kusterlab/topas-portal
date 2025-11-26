from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pandas as pd

from topas_portal import utils
from topas_portal import settings
import topas_portal.topas_preprocess as topas_loader

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


def get_reports_per_patient(
    cohorts_db: data_api.CohortDataAPI,
    level: utils.DataType,
    cohort_index: int,
    patient: str,
) -> pd.DataFrame:
    level_func_map = {
        utils.DataType.REPORT_SUMMARY: _report_summary,
        utils.DataType.PHOSPHO_PROTEOME: _phospho_proteome,
        utils.DataType.FULL_PROTEOME: _full_proteome,
        utils.DataType.TOPAS_RTK_SCORE: _topas_rtk_score,
        utils.DataType.TOPAS_CK_SCORE: _topas_ck_score,
        utils.DataType.KINASE_SCORE: _kinase_score,
        utils.DataType.PHOSPHO_SCORE: _phospho_score,
        utils.DataType.TRANSCRIPTOMICS: _transcriptomics,
    }

    # Call the corresponding function or return empty DataFrame if level not found
    return level_func_map.get(level, lambda: pd.DataFrame())(
        cohorts_db, cohort_index, patient
    )


def _report_summary(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
):
    # receptor tyrosine kinases
    topas_rtk_df = _topas_rtk_score(cohorts_db, cohort_index, patient)
    topas_rtk_df["Score type"] = "RTK-TOPAS"

    # cytoplasmic kinases
    topas_ck_df = _topas_ck_score(cohorts_db, cohort_index, patient)
    topas_ck_df["Score type"] = "CK-TOPAS"

    # proteins of interest
    fp_df = _full_proteome(
        cohorts_db, cohort_index, patient, intensity_units=[utils.IntensityUnit.Z_SCORE]
    )
    fp_df = fp_df.reset_index(drop=True)

    topas_poi_df = fp_df[fp_df["POI_REPORT"] != ""]
    topas_poi_df = topas_poi_df.rename(
        columns={f"{patient} Z-score": "Z-score", "Gene names": "Topas_id"}
    )
    topas_poi_df["Score type"] = "POI-REPORT (" + topas_poi_df["POI_REPORT"] + ")"

    topas_df = pd.concat([topas_ck_df, topas_rtk_df, topas_poi_df], axis=0)

    return (
        topas_df[["Topas_id", "Score type", "Z-score"]]
        .dropna()
        .sort_values(by="Z-score", ascending=False)
    )


def _phospho_proteome(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    patient: str,
    intensity_units: list[utils.IntensityUnit] = None,
) -> pd.DataFrame:
    sub_df = _load_proteome(
        cohort_index,
        patient,
        cohorts_db.get_psite_abundance_df,
        intensity_units,
    )
    return sub_df.rename(columns=settings.ANNOTATION_COLUMNS)


def _full_proteome(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    patient: str,
    intensity_units: list[utils.IntensityUnit] = None,
) -> pd.DataFrame:
    return _load_proteome(
        cohort_index,
        patient,
        cohorts_db.get_protein_abundance_df,
        intensity_units,
    )


def _load_proteome(
    cohort_index: int,
    patient: str,
    get_abundance_df: Callable[..., pd.DataFrame],
    intensity_units: list[utils.IntensityUnit] = None,
) -> pd.DataFrame:
    if intensity_units is None:
        intensity_units = [
            utils.IntensityUnit.RANK,
            utils.IntensityUnit.Z_SCORE,
            utils.IntensityUnit.FOLD_CHANGE,
            utils.IntensityUnit.BATCH_RANK,
            utils.IntensityUnit.INTENSITY,
            utils.IntensityUnit.IDENTIFICATION_METADATA,
        ]

    extra_columns = settings.ANNOTATION_COLUMNS.keys()
    cohort_df = get_abundance_df(cohort_index, extra_columns=extra_columns)
    extra_columns = cohort_df.columns.intersection(extra_columns).to_list()

    patient_columns = {
        patient
        + utils.INTENSITY_UNIT_SUFFIXES[intensity_unit]: utils.INTENSITY_UNIT_SUFFIXES[
            intensity_unit
        ].strip()
        for intensity_unit in intensity_units
    }

    proteome_df = cohort_df[list(patient_columns.keys()) + extra_columns]
    proteome_df = proteome_df.rename(columns=patient_columns)
    proteome_df = proteome_df.reset_index()  # make "Gene names" a regular column
    zscore_col = utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE].strip()

    return proteome_df.dropna(subset=zscore_col).sort_values(
        by=zscore_col, ascending=False
    )


def _topas_rtk_score(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    sub_df = cohorts_db.get_topas_rtk_scores_df(
        cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
    )
    sub_df = topas_loader.get_topas_scores_long_format(sub_df)
    sub_df = sub_df[sub_df["Sample name"] == patient]
    return sub_df[["Topas_id", "Z-score"]].dropna()


def _topas_ck_score(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    sub_df = cohorts_db.get_topas_ck_scores_df(
        cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
    )
    sub_df = topas_loader.get_topas_scores_long_format(sub_df)
    sub_df = sub_df[sub_df["Sample name"] == patient]
    return sub_df[["Topas_id", "Z-score"]].dropna()


def _kinase_score(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    sub_df = cohorts_db.get_kinase_scores_df(
        cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
    )
    sub_df["Kinase_names"] = sub_df.index
    return sub_df[["Kinase_names", patient]].dropna()


def _phospho_score(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    intensity_units = [
        utils.IntensityUnit.RANK,
        utils.IntensityUnit.Z_SCORE,
        utils.IntensityUnit.BATCH_RANK,
    ]
    return _load_proteome(
        cohort_index,
        patient,
        cohorts_db.get_phosphorylation_scores_df,
        intensity_units,
    )


def _transcriptomics(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    sub_df = cohorts_db.get_fpkm_df(intensity_unit=utils.IntensityUnit.Z_SCORE)
    sub_df["Gene names"] = sub_df.index
    return sub_df[["Gene names", patient]]
