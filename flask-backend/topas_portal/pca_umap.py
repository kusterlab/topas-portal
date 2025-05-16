# retrieved from the wp3 topas pipeline
import os
import re
from typing import List

import pandas as pd
import numpy as np


import topas_portal.settings as settings
from . import utils
from .file_loaders import tupac
from .dimensionality_reduction import get_dimensionality_reduction_method
import db
from topas_portal.utils import IntensityUnit
cohorts_db = db.cohorts_db


def do_pca(
    selected_proteins: List[str],
    results_folder: str,
    plot_types: List[utils.DataType],
    sample_annot_df: pd.DataFrame,  # sample_annot: str,
    meta_annot_df: pd.DataFrame,
    min_sample_occurrence_ratio: float = 0.5,
    dimensionality_reduction_method: str = "ppca",
    include_reference_channels: bool = False,
    include_replicates: bool = False,
):
    """_summary_

    Args:
        selected_proteins (List[str]): _description_
        results_folder (str): _description_
        plot_types (List[str]): Available plot types are: proteins, p-peptides, annot-proteins, annot-p-peptides, p-proteins, kinases, tupac.
        sample_annot_df (pd.DataFrame): _description_
        meta_annot_df (pd.DataFrame): _description_
        min_sample_occurrence_ratio (float, optional): _description_. Defaults to 0.5.
        dimensionality_reduction_method (str, optional): _description_. Defaults to 'ppca'.
        include_reference_channels (bool, optional): _description_. Defaults to False.
        include_replicates (bool, optional): _description_. Defaults to False.

    Returns:
        _type_: _description_
    """

    if "QC" in sample_annot_df.columns:
        sample_annot_df = sample_annot_df[
            sample_annot_df["QC"].isin(["passed", "shaky"])
        ]
    if not include_replicates:
        if "Replicate" in sample_annot_df.columns:
            sample_annot_df = sample_annot_df[
                sample_annot_df["Replicate"] != "replicate"
            ]
    if "Material issue" in sample_annot_df.columns:
        sample_annot_df = sample_annot_df[sample_annot_df["Material issue"] != "+"]

    sample_annot_df.columns = sample_annot_df.columns.str.strip()
    # meta_annot_df = pd.read_excel(metadata_annot)
    meta_annot_df = whitespace_remover(meta_annot_df)

    if include_reference_channels:
        sample_annot_df = create_ref_sample_annot(results_folder, sample_annot_df)


    metadata_df = merge_sample_and_metadata_annots(
        sample_annot_df,
        meta_annot_df,
        remove_qc_failed=True,
        keep_reference=include_reference_channels,
        keep_replicates=include_replicates,
    )

    all_principal_dfs = []
    all_principal_variances = []
    imputed_data = []

    if plot_types[0] == "FP_PP":
        plot_types = ["protein", "psite"]

    list_dfs = []
    for plot_type in plot_types:
        df = load_pca_data(
            results_folder,
            metadata_df["Sample name"],
            plot_type,
            include_reference_channels,
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
        df, metadata_df, dimensionality_reduction_method, min_sample_occurrence_ratio,
    )
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
    plot_type: utils.DataType = utils.DataType.TUPAC_SCORE,
    include_reference_channels: bool = False,
):
    print(plot_type)
    cohort_index = cohorts_db.config.get_cohort_index_from_report_directory(results_folder)

    if plot_type == utils.DataType.TUPAC_SCORE:
        df = cohorts_db.get_basket_scores_df(
            cohort_index, intensity_unit=IntensityUnit.Z_SCORE
        )
        df = df.T
        df = _remove_prefix_from_index(df)
    elif plot_type == utils.DataType.KINASE_SCORE:
        df = read_kinase_score(results_folder)
    elif plot_type == utils.DataType.PHOSPHO_SCORE:
        df = read_phosphoprotein_score(results_folder)
    elif plot_type in [
        utils.DataType.FULL_PROTEOME,
        utils.DataType.FULL_PROTEOME_ANNOTATED,
        utils.DataType.PHOSPHO_PROTEOME,
        utils.DataType.PHOSPHO_PROTEOME_ANNOTATED,
    ]:  
        data_type = (
            utils.DataType.FP
            if plot_type
            in [utils.DataType.FULL_PROTEOME, utils.DataType.FULL_PROTEOME_ANNOTATED]
            else utils.DataType.PP
        )

        if include_reference_channels:
            file = f"annot_{data_type}_with_ref.csv"   # in case with reference channels we read it from the resutl folder

        else:
            file = f"annot_{data_type}.csv"   # in case with reference channels we read it from the resutl folder

        index_col = utils.get_index_cols(data_type)
        df = pd.read_csv(os.path.join(results_folder, file), index_col=index_col)
        print(df)
        df.columns = df.columns.str.replace("ref_channel_", "ref-channel-")
        df.columns = df.columns.str.replace("_batch", "-batch")
        df = utils.remove_prefix(df)
        df.columns = df.columns.str.strip()
        if plot_type in [
            utils.DataType.FULL_PROTEOME_ANNOTATED,
            utils.DataType.PHOSPHO_PROTEOME_ANNOTATED,
        ]:
            # Subset remove where both basket and rtk is empty
            if "rtk" in df.columns:
                df = df.dropna(subset=["basket", "rtk"], how="all")
            elif "sub_basket" in df.columns:
                df = df.dropna(subset=["basket", "sub_basket"], how="all")
            else:
                print(
                    "Error. Wrong basket scoring file. cannot find baskets of type basket & rtk or basket & sub_basket"
                )


        samples_df = cohorts_db.get_sample_annotation_df(cohort_index)
        samplenames = samples_df['Sample name'].unique().tolist()
        df = utils.keep_only_sample_columns(df,samplenames)

    # prepare data
    if plot_type in [
        utils.DataType.TUPAC_SCORE,
        utils.DataType.KINASE_SCORE,
        utils.DataType.PHOSPHO_SCORE,
    ]:  
        df = df.transpose()

    if not include_reference_channels:  # but then also replicates are kept
        df = df.loc[:, df.columns.isin(samples)]  # MT: not sure what this does

    return df


def metadata_pca(
    df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    method_name: str = "ppca",
    min_sample_occurrence_ratio: float = 0.5,
):

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


def read_kinase_score(results_folder):
    cohort_index = cohorts_db.config.get_cohort_index_from_report_directory(results_folder)
    df = cohorts_db.get_kinase_scores_df(
            cohort_index, intensity_unit=IntensityUnit.Z_SCORE
        )
    df = df.T
    df = _remove_prefix_from_index(df)
    return df


def read_phosphoprotein_score(results_folder):
    cohort_index = cohorts_db.config.get_cohort_index_from_report_directory(results_folder)
    df = cohorts_db.get_phosphorylation_scores_df(
            cohort_index, intensity_unit=IntensityUnit.Z_SCORE
        )
    df = df.T
    df = _remove_prefix_from_index(df)
    return df


def _remove_prefix_from_index(df):
    df.index = df.index.str.replace(settings.PATIENT_PREFIX, "")
    return df


def filter_by_occurrence(df, min_sample_occurrence_ratio: float = 0.5):
    df = df.transpose()
    return df.loc[:, df.count(axis=0) >= df.shape[0] * min_sample_occurrence_ratio]


def merge_sample_and_metadata_annots(
    sample_annotation_df: pd.DataFrame,
    meta_data: pd.DataFrame,
    remove_qc_failed: bool,
    keep_replicates: bool = False,
    keep_reference: bool = False,
) -> pd.DataFrame:

    if remove_qc_failed:
        if "QC" in sample_annotation_df.columns:
            sample_annotation_df = sample_annotation_df[
                sample_annotation_df["QC"].isin(["passed", "shaky"])
            ]
        else:
            sample_annotation_df = sample_annotation_df[
                sample_annotation_df["Failed"] != "x"
            ]

    meta_data_samples = meta_data["Sample name"].tolist()
    if keep_replicates:  
        sample_annotation_df = get_replicate_groups(
            sample_annotation_df, meta_data_samples
        )

    if not keep_replicates and keep_reference:
        sample_annotation_df = sample_annotation_df.loc[
            (sample_annotation_df["Sample name"].isin(meta_data_samples))
            | (sample_annotation_df["Sample name"].str.startswith("Reporter")),
            :,
        ]

    if not keep_replicates and not keep_reference:
        sample_annotation_df = meta_data.loc[
            meta_data["Sample name"].isin(sample_annotation_df["Sample name"].tolist()),
            :,
        ]

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
        "Reporter"
    )
    merged_annot = merged_annot.replace(np.nan, "nan")
    return merged_annot


def get_replicate_groups(sample_annotation_df, meta_data_samples):
    replicates = sample_annotation_df[
        ~(sample_annotation_df["Sample name"].isin(meta_data_samples))
        & ~(sample_annotation_df["Sample name"].str.startswith("Reporter"))
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



def create_ref_sample_annot(results_folder, sample_annot_df):
    df = pd.read_csv(
        os.path.join(results_folder, f"annot_fp_with_ref.csv"), index_col="Gene names"
    )

    df.columns = df.columns.str.replace("ref_channel_", "ref-channel-")
    df.columns = df.columns.str.replace("_batch", "-batch")
    df = utils.remove_prefix(df)
    df = utils.keep_only_sample_columns(df,sample_annot_df['Sample name'].unique().tolist())

    for sample in df:

        if sample not in sample_annot_df["Sample name"].tolist():
            # retrieve tmt channel, batch
            tmt_channel = re.search("corrected \d{1,2}", sample).group().split(" ")[1]
            cohort = re.search("\d [A-Z,a-z]+_", sample).group().split(" ")[1][:-1]
            # new_sample = {'Sample name': sample, 'Cohort': cohort, 'Batch Name': batch, 'TMT Channel': tmt_channel,'QC': 'passed'}
            new_sample = {
                "Sample name": sample,
                "Cohort": cohort,
                "TMT Channel": tmt_channel,
                "QC": "passed",
            }

            sample_annot_df = sample_annot_df.append(new_sample, ignore_index=True)

    return sample_annot_df


def whitespace_remover(df):
    for col in df.columns:
        if df[col].dtype == "object":
            # applying strip function on column
            df[col] = df[col].astype(str).map(str.strip)
        else:
            pass
    return df
