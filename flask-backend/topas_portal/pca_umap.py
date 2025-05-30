# retrieved from the wp3 topas pipeline
import os
import re
from typing import List

import pandas as pd
import numpy as np


from . import settings
from . import utils
from . import fetch_data_matrix as data
from .dimensionality_reduction import get_dimensionality_reduction_method
import db

cohorts_db = db.cohorts_db


def do_pca(
    selected_proteins: List[str],
    results_folder: str,
    plot_types: List[utils.DataType],
    sample_annot_df: pd.DataFrame,
    meta_annot_df: pd.DataFrame,
    min_sample_occurrence_ratio: float = 0.5,
    dimensionality_reduction_method: str = "ppca",
    include_reference_channels: bool = False,
    include_replicates: bool = False,
    only_ref_channels=False,
):
    """_summary_

    Args:
        selected_proteins (List[str]): _description_
        results_folder (str): _description_
        plot_types (List[str]): Available plot types are: proteins, p-peptides, annot-proteins, annot-p-peptides, p-proteins, kinases, topas.
        sample_annot_df (pd.DataFrame): _description_
        meta_annot_df (pd.DataFrame): _description_
        min_sample_occurrence_ratio (float, optional): _description_. Defaults to 0.5.
        dimensionality_reduction_method (str, optional): _description_. Defaults to 'ppca'.
        include_reference_channels (bool, optional): _description_. Defaults to False.
        include_replicates (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """
    if not include_replicates:
        if "Replicate" in sample_annot_df.columns:
            sample_annot_df = sample_annot_df[
                sample_annot_df["Replicate"] != "replicate"
            ]

    metadata_df = merge_sample_and_metadata_annots(
        sample_annot_df,
        meta_annot_df,
        keep_reference=include_reference_channels,
        keep_replicates=include_replicates,
    )
    all_principal_dfs = []
    all_principal_variances = []
    imputed_data = []

    if plot_types[0] == utils.DataType.FP_PP:
        plot_types = ["protein", "psite"]

    list_dfs = []
    for plot_type in plot_types:
        df = load_pca_data(
            results_folder,
            metadata_df["Sample name"],
            plot_type,
            include_reference_channels,
            only_ref_channels=only_ref_channels,
        )
        list_dfs.append(df)

    if len(list_dfs) > 1:
        fp_df = list_dfs[0]
        pp_df = list_dfs[1]
        pp_df = pp_df.set_index(pp_df.index.get_level_values("Modified sequence"))
        df = pd.concat([fp_df, pp_df])
        print("Running multi level FP and PP")

    if len(selected_proteins) > 2:
        final_selected = [
            f for f in selected_proteins if f in df.index
        ]  # this only works for FP otherwise it will be empty list

        if len(final_selected) > 2:
            # this is at full proteome level
            df = df[df.index.isin(final_selected)]
        else:
            # this for the phospho  peptides level
            mask = df.index.get_level_values("Modified sequence").isin(
                selected_proteins
            )
            if len(mask) > 2:
                df = df[mask]

    principal_df, pca, imputed_df = metadata_pca(
        df,
        metadata_df,
        dimensionality_reduction_method,
        min_sample_occurrence_ratio,
    )
    # print(f'df {df}')
    # print(f'imputed data{imputed_data}')
    # print(f'meta data{metadata_df}')
    imputed_data.append(imputed_df)
    all_principal_dfs.append(principal_df)
    if dimensionality_reduction_method == "umap":
        all_principal_variances.append([])
    else:
        all_principal_variances.append(pca.get_explained_variances())

    return all_principal_dfs, all_principal_variances, imputed_data, metadata_df


def load_pca_data(
    results_folder,
    samples,
    plot_type: utils.DataType = utils.DataType.TOPAS_SCORE,
    include_reference_channels: bool = False,
    only_ref_channels=False,
):
    print(plot_type)
    cohort_index = cohorts_db.config.get_cohort_index_from_report_directory(
        results_folder
    )

    intensity_unit = utils.IntensityUnit.Z_SCORE
    if plot_type in [
        utils.DataType.FULL_PROTEOME,
        utils.DataType.FULL_PROTEOME_ANNOTATED,
        utils.DataType.PHOSPHO_PROTEOME,
        utils.DataType.PHOSPHO_PROTEOME_ANNOTATED,
    ]:
        intensity_unit = utils.IntensityUnit.INTENSITY

    include_ref = utils.IncludeRef.EXCLUDE_REF
    if include_reference_channels:
        include_ref = utils.IncludeRef.INCLUDE_REF
    if only_ref_channels:
        include_ref = utils.IncludeRef.ONLY_REF

    df = data.fetch_data_matrix(
        cohorts_db,
        cohort_index,
        intensity_unit=intensity_unit,
        level=plot_type,
        include_ref=include_ref,
    )
    df = _remove_prefix_from_columns(df)

    if not include_reference_channels:  # but then also replicates are kept
        df = df.loc[:, df.columns.isin(samples)]  # MT: not sure what this does
    print(df)
    return df


def filter_for_annotated(df: pd.DataFrame) -> pd.DataFrame:
    # Subset remove where both topas and rtk is empty
    if "rtk" in df.columns:
        return df.dropna(subset=["topas", "rtk"], how="all")
    elif "sub_topas" in df.columns:
        return df.dropna(subset=["topas", "sub_topas"], how="all")
    else:
        print(
            "Error. Wrong topas scoring file. cannot find annotations of type topas & rtk or topas & sub_topas"
        )


def metadata_pca(
    df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    method_name: str = "ppca",
    min_sample_occurrence_ratio: float = 0.5,
):
    print(method_name)
    expression_df = filter_by_occurrence(df, min_sample_occurrence_ratio)

    # calculate ppca
    dim_reduction_method = get_dimensionality_reduction_method(method_name)
    transformed_data = dim_reduction_method.fit_transform(expression_df)
    transformed_data.columns = ["Principal component 1", "Principal component 2"]
    transformed_data["Sample"] = expression_df.index
    principal_df = transformed_data.merge(
        metadata_df, left_on="Sample", right_on="Sample name"
    )

    imputed_data = dim_reduction_method._imputed_data
    imputed_data.index = df.columns

    return principal_df, dim_reduction_method, imputed_data


def _remove_prefix_from_index(df):
    df.index = df.index.str.replace(settings.PATIENT_PREFIX, "")
    return df


def _remove_prefix_from_columns(df):
    df.columns = df.columns.str.replace(settings.PATIENT_PREFIX, "")
    return df


def filter_by_occurrence(df, min_sample_occurrence_ratio: float = 0.5):
    df = df.transpose()
    return df.loc[:, df.count(axis=0) >= df.shape[0] * min_sample_occurrence_ratio]


def merge_sample_and_metadata_annots(
    sample_annotation_df: pd.DataFrame,
    meta_data: pd.DataFrame,
    keep_replicates: bool = False,
    keep_reference: bool = False,
) -> pd.DataFrame:
    meta_data_samples = meta_data["Sample name"].tolist()
    if keep_replicates:
        sample_annotation_df = get_replicate_groups(
            sample_annotation_df, meta_data_samples
        )
    else:
        patient_samples = sample_annotation_df["Sample name"].isin(meta_data_samples)
        if keep_reference:
            patient_samples |= sample_annotation_df["Sample name"].str.startswith(
                settings.REF_CHANNEL_PREFIX
            )
        sample_annotation_df = sample_annotation_df.loc[patient_samples, :]

    merged_annot = pd.merge(
        left=sample_annotation_df,
        right=meta_data,
        how="left",
        left_on="Sample name",
        right_on="Sample name",
        suffixes=("", "_drop"),
    )

    # drop columns present in both dataframes
    merged_annot = merged_annot.drop(
        [col for col in merged_annot.columns if "_drop" in col], axis=1
    )

    merged_annot["Batch_No"] = ""
    merged_annot["Tumor cell content"] = 0  # we bypass the get tumor cell conntent
    merged_annot["Is reference channel"] = merged_annot["Sample name"].str.startswith(
        settings.REF_CHANNEL_PREFIX
    )
    merged_annot = merged_annot.replace(np.nan, "nan")
    return merged_annot


def get_replicate_groups(
    sample_annotation_df: pd.DataFrame, meta_data_samples: list[str]
) -> pd.DataFrame:
    replicates = sample_annotation_df[
        ~(sample_annotation_df["Sample name"].isin(meta_data_samples))
        & ~(
            sample_annotation_df["Sample name"].str.startswith(
                settings.REF_CHANNEL_PREFIX
            )
        )
    ]

    replicates["Sample name"] = replicates["Sample name"].apply(
        lambda x: "-".join(x.split("-")[:-1])
    )
    sample_annotation_df["Replicate group"] = np.nan

    for i, sample in enumerate(
        replicates["Sample name"].unique()
    ):  # with one there is the one without and one with -R2
        group_indices = sample_annotation_df[
            sample_annotation_df["Sample name"].str.contains(sample)
        ].index
        sample_annotation_df.loc[group_indices.values, "Replicate group"] = i + 1

    return sample_annotation_df
