# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import Union

import pandas as pd
import os
from pathlib import Path

import topas_portal.settings as cn
import topas_portal.utils as utils
import topas_portal.topas_scores_meta as topass




@utils.check_path_exist
def load_topas_annotation_df(path_to_topas_annotation_file: str) -> pd.DataFrame:
    """
    Load all topas annotations as a DataFrame.
    """
    topas_annotations_df = pd.read_excel(path_to_topas_annotation_file)
    return topas_annotations_df


@utils.check_path_exist
def load_topas_scores_df(topas_scores_path: str):
    """Loads DataFrame with topas scores for each sample."""
    topas_scores_df = pd.read_csv(
        topas_scores_path, delimiter="\t", index_col="Sample"
    )

    topas_scores_df = utils.remove_patient_prefix(topas_scores_df, from_col=False)
    topas_scores_df.index.name = "Sample name"

    topas_scores_df.index = topas_scores_df.index.str.strip()
    topas_scores_df.columns = topas_scores_df.columns.str.replace(
        r"[\/]", "_", regex=True
    )

    # remove the "targets_<sample_id>" rows containing the number of scored genes per sample(?)
    topas_scores_df = topas_scores_df.loc[
        ~topas_scores_df.index.str.startswith("targets_")
    ]

    print("Topas score data loaded")
    return topas_scores_df.T


def load_subtopas_table(
    report_dir: str, main_topas: str, return_wide=False
) -> pd.DataFrame:

    SUBTOPAS_PREFIX = cn.SUBTOPAS_FILES_PREFIX
    for key in topass.TOPAS_RENAMING.keys():
        if main_topas == key:
            main_topas = topass.TOPAS_RENAMING[key]
    file_name = f"{report_dir}/{SUBTOPAS_PREFIX}{main_topas}.tsv"
    subtopas_scores_long = pd.DataFrame()
    if os.path.exists(file_name):
        subtopas_scores = pd.read_csv(os.path.join(report_dir, file_name), sep="\t")

        # TODO: check if mean and stdev columns are still in here
        subtopas_scores = subtopas_scores[
            ~subtopas_scores["Sample name"].str.contains("targets_")
        ]
        subtopas_scores["Sample name"] = subtopas_scores["index"]
        list_del = subtopas_scores.filter(regex=r"topas_name").columns.to_list()
        list_del = [*list_del, *["index", "Sarcoma Subtype", "Histologic subtype"]]
        columns_to_del = [s for s in list_del if s in subtopas_scores.columns]
        subtopas_scores = subtopas_scores.drop(columns_to_del, axis=1)
        subtopas_scores = subtopas_scores.drop(
            subtopas_scores.filter(regex="total_topas_score").columns, axis=1
        )
        subtopas_scores = utils.remove_patient_prefix(subtopas_scores, from_col=False)
        if return_wide:

            return subtopas_scores
        else:
            topas_names = subtopas_scores.columns[
                subtopas_scores.columns != "Sample name"
            ].values.tolist()
            subtopas_scores_long = pd.melt(
                subtopas_scores.reset_index(),
                id_vars="Sample name",
                value_vars=topas_names,
                value_name="Z-score",
            )
            subtopas_scores_long = subtopas_scores_long.dropna()
            subtopas_scores_long.columns = ["sample", "topas", "score"]

            subtopas_scores_long["color"] = "grey"
            subtopas_scores_long["sizeR"] = 0.5
            subtopas_scores = utils.remove_patient_prefix(subtopas_scores, from_col=False)

            return subtopas_scores_long
