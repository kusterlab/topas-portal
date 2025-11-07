from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pandas as pd
import xlsxwriter

from topas_portal import utils
from topas_portal import settings
import topas_portal.psite_annotation as ps
import topas_portal.topas_preprocess as topas_loader

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


def get_reports_per_patient_on_the_fly(
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
        cohorts_db,
        cohort_index,
        patient,
        cohorts_db.get_psite_abundance_df,
        intensity_units,
    )
    return sub_df.rename(columns=settings.PP_EXTRA_COLUMNS)


def _full_proteome(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    patient: str,
    intensity_units: list[utils.IntensityUnit] = None,
) -> pd.DataFrame:
    return _load_proteome(
        cohorts_db,
        cohort_index,
        patient,
        cohorts_db.get_protein_abundance_df,
        intensity_units,
    )


def _load_proteome(
    cohorts_db: data_api.CohortDataAPI,
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
            utils.IntensityUnit.INTENSITY,
            utils.IntensityUnit.IDENTIFICATION_METADATA,
        ]

    sub_dfs = []
    for i, intensity_unit in enumerate(intensity_units):
        print(f"Loading {intensity_unit.value} column")
        extra_columns = list(settings.PP_EXTRA_COLUMNS.keys()) if i == 0 else None

        sub_df = get_abundance_df(
            cohort_index,
            patient_name=patient,
            intensity_unit=intensity_unit,
            extra_columns=extra_columns,
        )
        sub_df = sub_df.rename(
            columns={patient: utils.INTENSITY_UNIT_SUFFIXES[intensity_unit].strip()}
        )
        sub_dfs.append(sub_df)

    proteome_df = pd.concat(sub_dfs, axis=1)
    proteome_df = proteome_df.reset_index()  # make "Gene names" a regular column

    proteome_df = merge_with_poi_annotations(
        proteome_df, cohorts_db.get_poi_annotation_df()
    )
    zscore_col = utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE].strip()
    return proteome_df.dropna(subset=zscore_col).sort_values(
        by=zscore_col, ascending=False
    )


def merge_with_poi_annotations(df: pd.DataFrame, poi_annotation_df: pd.DataFrame):
    df = utils.merge_by_delimited_field(
        df,
        poi_annotation_df[
            ["Gene names", "POI_REPORT", "POI_EXPLORATORY", "POI_PRODICT"]
        ],
        field_name="Gene names",
    )

    return df


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
    sub_df = cohorts_db.get_phosphorylation_scores_df(
        cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE
    )
    sub_df["Gene names"] = sub_df.index
    sub_df = sub_df[["Gene names", patient]].dropna()
    zscore_col = utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE].strip()
    sub_df = sub_df.rename(columns={patient: zscore_col}).sort_values(
        by=zscore_col, ascending=False
    )

    sub_df = merge_with_poi_annotations(sub_df, cohorts_db.get_poi_annotation_df())
    return sub_df


def _transcriptomics(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    sub_df = cohorts_db.get_fpkm_df(intensity_unit=utils.IntensityUnit.Z_SCORE)
    sub_df["Gene names"] = sub_df.index
    return sub_df[["Gene names", patient]]


def get_reports_per_patient_from_reports_folder(
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


def _get_sheetname_from_level(level: utils.DataType) -> str:
    level_to_sheetname = {
        utils.DataType.PHOSPHO_PROTEOME: "Phospho proteome",
        utils.DataType.FULL_PROTEOME: "Global proteome",
        utils.DataType.TOPAS_RTK_SCORE: "Topas",
        utils.DataType.PHOSPHO_SCORE: "Protein phosphorylation",
        utils.DataType.KINASE_SCORE: "Kinase",
        utils.DataType.BIOMARKER: "Biomarkers",
    }

    if level not in level_to_sheetname:
        raise ValueError(f"No sheet name specified for data type '{level.name}'")

    return level_to_sheetname.get(level)
