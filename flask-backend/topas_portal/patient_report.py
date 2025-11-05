from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from topas_portal import utils
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
    fp_df = _full_proteome(cohorts_db, cohort_index, patient)
    fp_df = fp_df.reset_index(drop=True)

    poi_annotation_df = cohorts_db.get_poi_annotation_df()
    poi_report_annotation_df = poi_annotation_df[
        poi_annotation_df["POI_REPORT"].notna()
    ]
    
    topas_poi_df = fp_df.merge(
        poi_report_annotation_df[["Gene names", "POI_REPORT"]],
        on="Gene names",
        how="right",
    )
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
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    patient_column = patient + " Z-score"
    sub_df = cohorts_db.get_psite_abundance_df(
        cohort_index, patient_name=patient_column
    )
    sub_df = sub_df.dropna()
    return ps.phospho_annot(sub_df)


def _full_proteome(
    cohorts_db: data_api.CohortDataAPI, cohort_index: int, patient: str
) -> pd.DataFrame:
    patient_column = patient + " Z-score"
    sub_df = cohorts_db.get_protein_abundance_df(
        cohort_index, patient_name=patient_column
    )
    sub_df["Gene names"] = sub_df.index
    return sub_df.dropna()


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
    return sub_df[["Gene names", patient]].dropna()


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
        utils.DataType.TOPAS_SUBSCORE: "TOPAS subscores",
        utils.DataType.BIOMARKER: "Biomarkers",
    }

    if level not in level_to_sheetname:
        raise ValueError(f"No sheet name specified for data type '{level.name}'")

    return level_to_sheetname.get(level)
