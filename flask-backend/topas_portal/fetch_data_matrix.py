from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pandas as pd

import topas_portal.utils as ef
import topas_portal.topas_scores_meta as topass

if TYPE_CHECKING:
    from .data_api import data_api


def fetch_data_matrix_with_sample_annotations(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    identifiers: list[str],
    sample_ids: list[str],
    level: ef.DataType,
    intensity_unit: ef.IntensityUnit = ef.IntensityUnit.Z_SCORE,
) -> pd.DataFrame:
    z_scores_df = fetch_data_matrix(
        cohorts_db, cohort_index, level, identifiers, intensity_unit,
    )

    sample_annotation_df = cohorts_db.get_sample_annotation_df(cohort_index)
    sample_subset_df = _filter_sample_annotation_df(sample_annotation_df, sample_ids)
    return _merge_with_sample_annotation_df(
        z_scores_df, sample_subset_df, drop_nans=False
    )


def fetch_data_matrix(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: str,
    level: ef.DataType,
    identifiers: list[str] | None,
    intensity_unit: ef.IntensityUnit = ef.IntensityUnit.Z_SCORE,
) -> pd.DataFrame:
    if level in topass.TOPAS_LEVEL_MAPPING:
        topas_df = cohorts_db.get_topas_annotation_df()
        level, identifiers = _update_level_and_identifiers(
            topas_df, level, identifiers
        )

    if level == ef.DataType.FULL_PROTEOME:
        z_scores_df = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=intensity_unit
        )
    elif level == ef.DataType.PHOSPHO_PROTEOME:
        z_scores_df = cohorts_db.get_psite_abundance_df(
            cohort_index, intensity_unit=intensity_unit
        )
    elif level == ef.DataType.KINASE_SCORE:
        z_scores_df = cohorts_db.get_kinase_scores_df(
            cohort_index, intensity_unit=intensity_unit
        )
    elif level == ef.DataType.PHOSPHO_SCORE:
        z_scores_df = cohorts_db.get_phosphorylation_scores_df(
            cohort_index, intensity_unit=intensity_unit
        )
    elif level == ef.DataType.PHOSPHO_SCORE_PSITE:
        z_scores_df, identifiers = _get_phosphorylation_psite_df(
            cohorts_db.get_psite_abundance_df(cohort_index), identifiers,
        )
    elif level == ef.DataType.KINASE_SUBSTRATE:
        z_scores_df, identifiers = _get_kinase_substrates_df(
            cohorts_db.get_psite_abundance_df(cohort_index), identifiers,
        )
    elif level == ef.DataType.TOPAS_SCORE:
        z_scores_df = cohorts_db.get_topas_scores_df(
            cohort_index, intensity_unit=intensity_unit
        )
    elif level == ef.DataType.TRANSCRIPTOMICS:
        z_scores_df = cohorts_db.get_fpkm_df(intensity_unit=intensity_unit)
    else:
        raise ValueError(f"Unknown data layer for fetch_data_matrix: {level.value}.")

    if level == ef.DataType.TRANSCRIPTOMICS:
        # Unnest the protein_groups A;B as two separate rows with the same values
        z_scores_df = ef.unnest_proteingroups(z_scores_df)

    if identifiers is not None:
        z_scores_df = z_scores_df.loc[ef.intersection(z_scores_df.index, identifiers)]

    return z_scores_df


def _update_level_and_identifiers(
    topas_df: pd.DataFrame, level: ef.DataType, identifiers: list[str]
):
    scoring_rule_level = topass.TOPAS_LEVEL_MAPPING[level]["scoring_rule_level"]
    level = topass.TOPAS_LEVEL_MAPPING[level]["data_level"]
    identifiers = _get_topas_proteins(topas_df, identifiers, level=scoring_rule_level)
    return level, identifiers


def _get_kinase_substrates_df(
    z_scores_df: pd.DataFrame, kinases: list[str] | None,
) -> pd.DataFrame:
    """Filters p-site abundance dataframe for p-sites that are substrates of one or more kinases.

    The substrates do not have to be unique substrates for a kinase.

    Args:
        z_scores_df (pd.DataFrame): dataframe with p-site abundances and a column with upstream kinases called "PSP Kinases".
        kinases (list[str]): list of kinases

    Returns:
        pd.DataFrame: _description_
    """
    regex_match_string = "^\s*$"
    if kinases is not None:
        regex_match_string = "|".join(re.escape(k) for k in kinases)
    kinase_substrates = z_scores_df.index[
        z_scores_df["PSP Kinases"]
        .fillna("")
        .str.contains(regex_match_string, regex=True)
    ].tolist()
    z_scores_df = z_scores_df.filter(like=" Z-score")
    z_scores_df.columns = z_scores_df.columns.str.removesuffix(" Z-score")
    return z_scores_df, kinase_substrates


def _get_phosphorylation_psite_df(
    z_scores_df: pd.DataFrame, phosphoproteins: list[str],
) -> pd.DataFrame:
    """At phospho level"""
    # we intentionally do not consider protein group matches as these are not
    # used for TOPAS scoring
    topas_phosphoproteins_psites = z_scores_df.index[
        z_scores_df["Gene names"].isin(phosphoproteins)
    ].tolist()
    z_scores_df = z_scores_df.filter(like=" Z-score")
    z_scores_df.columns = z_scores_df.columns.str.removesuffix(" Z-score")
    return z_scores_df, topas_phosphoproteins_psites


def _merge_with_sample_annotation_df(
    data_matrix_df: pd.DataFrame, sample_df: pd.DataFrame, drop_nans: bool,
) -> pd.DataFrame:
    """Merges data matrix with sample annotations dataframe.

    Args:
        data_matrix_df (pd.DataFrame): dataframe with gene/p-site/TOPAS identifiers as rows and samples as columns.
        sample_df (pd.DataFrame): dataframe with samples to filter for.
        drop_nans (bool): drop samples with only NaNs.

    Returns:
        pd.DataFrame: sample_df merged with data matrix.
    """
    sample_list = ef.intersection(data_matrix_df.columns, sample_df["Sample name"])
    filtered_data_matrix_df = data_matrix_df[sample_list].transpose()
    if drop_nans:
        filtered_data_matrix_df = filtered_data_matrix_df.dropna()

    return sample_df.merge(
        filtered_data_matrix_df, left_on="Sample name", right_index=True
    )


def _get_topas_proteins(
    topas_annotation_df: pd.DataFrame, topas_names: list[str], level: ef.DataType,
) -> list:
    """
    Gives the list of the protein based on the given criteria
    :level: the selected criteria to show the protesin : expression, phosphorylation, kinase
    """
    if level in topass.TOPAS_SCORING_RULES:
        scoring_rule = topass.TOPAS_SCORING_RULES[level]
    else:
        raise ValueError(f"Unknown scoring rule for TOPAS score: {level.value}.")

    topas_proteins = topas_annotation_df[
        topas_annotation_df["SUBTOPAS"].isin(topas_names)
    ]
    topas_proteins = topas_proteins[topas_proteins["SCORING RULE"] == scoring_rule]
    topas_proteins = topas_proteins["GENE NAME"].unique().tolist()
    return topas_proteins


def _filter_sample_annotation_df(
    sample_annotation_df: pd.DataFrame, sample_ids: list[str]
) -> pd.DataFrame:
    """
    Gives the subset of the sample_annotation_df for the given batach or bathces
    :sample_annotation_df: A dataframe as sample annotation with Batch_No column
    :sample_ids: A list of sample identifiers
    """
    sample_annotation_subset_df = sample_annotation_df[
        sample_annotation_df["Sample name"].isin(sample_ids)
    ]
    sample_annotation_subset_df = sample_annotation_subset_df.sort_values(
        by="Sample name", key=lambda col: col.apply(lambda x: sample_ids.index(x))
    )
    return sample_annotation_subset_df
