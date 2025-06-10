import pandas as pd
from typing import List

from topas_portal import utils
from topas_portal import settings
import topas_portal.plotly_preprocess as plotlyprepare


def _is_subsetted_list(customlist: List):
    return len(customlist) >= 1 and customlist[0] != "all"


def kinase_get_patients_list(
    annotation_file, patients_comma_sep, patient_or_entity, one_vs_all=False
):
    """Returns a list of patients from the entity"""
    if patient_or_entity == "patient":
        selected_patients = patients_comma_sep
        patients_list = selected_patients.split(",")
    else:
        selected_entities_list = patients_comma_sep.split(",")
        if one_vs_all:
            selected_df = annotation_file
        else:
            selected_df = annotation_file[
                annotation_file[settings.ENTITY_COLUMN].isin(selected_entities_list)
            ]
        patients_list = list(selected_df["Sample name"])

    return patients_list


def subset_scores_df(primary_scores_df, patients_list, kinase_list):
    data = primary_scores_df.copy()
    if _is_subsetted_list(patients_list):  # if not all
        final_list = utils.intersection(data.columns, patients_list)
        data = data[final_list]

    if _is_subsetted_list(kinase_list):  # if not all
        data = data[data.index.isin(kinase_list)]
    return data


def kinase_score_plots_prepare(
    kinase_scores: pd.DataFrame,
    sample_annotation: pd.DataFrame,
    patient_or_entity: str,
    selected_patient_or_entities: str,
    selected_kinases: str,
    plot_type: str,
    one_vs_all: bool = False,
):
    print(kinase_scores)
    patients_list = kinase_get_patients_list(
        sample_annotation, selected_patient_or_entities, patient_or_entity, one_vs_all
    )
    kinase_list = selected_kinases.split(",")
    data = subset_scores_df(kinase_scores, patients_list, kinase_list)
    print(data)
    if patient_or_entity == "entity":
        temp_data = data.transpose()  # we first transpose before merging
        merged_data_entity = pd.merge(
            temp_data, sample_annotation, left_index=True, right_on="Sample name"
        )
        print(merged_data_entity)
        merged_data_entity.index = (
            merged_data_entity["Sample name"].astype(str)
            + "_entity_"
            + merged_data_entity[settings.ENTITY_COLUMN].astype(str)
        )
        extra_cols = [
            *settings.COMMON_META_DATA,
            *[
                "Batch_No",
                "TMT_channel",
                "QC",
                "Sample_name_rep_truncated",
                "index",
                "Sample name",
            ],
        ]
        cols_to_del = [x for x in extra_cols if x in merged_data_entity]
        merged_data_entity = merged_data_entity.drop(cols_to_del, axis=1)
        data = merged_data_entity.transpose()

    data = data.transform(pd.to_numeric, errors="coerce")
    if plot_type == "swarm":
        fig_data = get_multi_swarm_json(data, one_vs_all, selected_patient_or_entities)
    else:  # dendrogram
        fig_data = get_dendro_or_heatmap_json(data, plot_type)
    return fig_data


def get_multi_swarm_json(data, one_vs_all, selected_patient_or_entities):
    data = data.transpose()
    fig_data = {}
    data["Sample"] = data.index
    id_vars = ["Sample"]
    cols_list = data.columns[data.columns != "Sample"].values.tolist()
    if all(data["Sample"].str.contains("_entity_")):
        data["entity"] = data["Sample"].apply(lambda x: str(x).split("_entity_")[1])
        if one_vs_all:
            data["color"] = "blue"  # the background patients
            data["color"][
                data["entity"] == selected_patient_or_entities
            ] = "red"  # the patients with the entity
        else:
            clr_labels = data["entity"].unique()
            lut = dict(zip(clr_labels, utils.ranodom_color_genetator(len(clr_labels))))
            data["color"] = data["entity"].map(lut)
        id_vars.append("color")
    if (
        len(cols_list) < 10
    ):  # for only less than 10 kinases it makes sense to have visualization
        data_long = pd.melt(
            data, id_vars=id_vars, value_vars=cols_list, value_name="score"
        )
        data_long = data_long.dropna()
        if not "color" in data.columns:
            data_long["color"] = "grey"
        else:
            data_long.columns = ["Sample", "color", "Gene names", "score"]

        data_long["sizeR"] = 1
        fig_data = utils.df_to_json(data_long)
    else:
        fig_data = utils.df_to_json(pd.DataFrame())
    return fig_data


def get_dendro_or_heatmap_json(data: pd.DataFrame, plot_type="heatmap"):
    fig_data = {}
    if plot_type == "heatmap":
        fig_data = plotlyprepare.get_simple_heatmap(data)
    else:
        data = data.fillna(0)
        fig_data = plotlyprepare.get_dendrogram(data)
    return fig_data
