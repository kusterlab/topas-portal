# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import Union

import pandas as pd
import os
from pathlib import Path

import topas_portal.settings as cn
import topas_portal.utils as utils
import topas_portal.tupacs_scores_meta as tupacs




@utils.check_path_exist
def load_basket_annotation_df(path_to_basket_annotation_file: str) -> pd.DataFrame:
    """
    Load all basket annotations as a DataFrame.
    """
    basket_annotations_df = pd.read_excel(path_to_basket_annotation_file)
    return basket_annotations_df


@utils.check_path_exist
def load_basket_scores_df(basket_scores_path: str):
    """Loads DataFrame with basket scores for each sample."""
    basket_scores_df = pd.read_csv(
        basket_scores_path, delimiter="\t", index_col="Sample"
    )

    basket_scores_df = utils.remove_patient_prefix(basket_scores_df, from_col=False)
    basket_scores_df.index.name = "Sample name"

    basket_scores_df.index = basket_scores_df.index.str.strip()
    basket_scores_df.columns = basket_scores_df.columns.str.replace(
        r"[\/]", "_", regex=True
    )

    # remove the "targets_<sample_id>" rows containing the number of scored genes per sample(?)
    basket_scores_df = basket_scores_df.loc[
        ~basket_scores_df.index.str.startswith("targets_")
    ]

    print("Basket score data loaded")
    return basket_scores_df.T


def load_subbasket_table(
    report_dir: str, main_basket: str, return_wide=False
) -> pd.DataFrame:

    SUBBASKET_PREFIX = cn.SUBBASKET_FILES_PREFIX
    for key in tupacs.BASKET_RENAMING.keys():
        if main_basket == key:
            main_basket = tupacs.BASKET_RENAMING[key]
    file_name = f"{report_dir}/{SUBBASKET_PREFIX}{main_basket}.tsv"
    subbasket_scores_long = pd.DataFrame()
    if os.path.exists(file_name):
        subbasket_scores = pd.read_csv(os.path.join(report_dir, file_name), sep="\t")

        # TODO: check if mean and stdev columns are still in here
        subbasket_scores = subbasket_scores[
            ~subbasket_scores["Sample name"].str.contains("targets_")
        ]
        subbasket_scores["Sample name"] = subbasket_scores["index"]
        list_del = subbasket_scores.filter(regex=r"basket_name").columns.to_list()
        list_del = [*list_del, *["index", "Sarcoma Subtype", "Histologic subtype"]]
        columns_to_del = [s for s in list_del if s in subbasket_scores.columns]
        subbasket_scores = subbasket_scores.drop(columns_to_del, axis=1)
        subbasket_scores = subbasket_scores.drop(
            subbasket_scores.filter(regex="total_basket_score").columns, axis=1
        )
        subbasket_scores = utils.remove_patient_prefix(subbasket_scores, from_col=False)
        if return_wide:

            return subbasket_scores
        else:
            basket_names = subbasket_scores.columns[
                subbasket_scores.columns != "Sample name"
            ].values.tolist()
            subbasket_scores_long = pd.melt(
                subbasket_scores.reset_index(),
                id_vars="Sample name",
                value_vars=basket_names,
                value_name="Z-score",
            )
            subbasket_scores_long = subbasket_scores_long.dropna()
            subbasket_scores_long.columns = ["sample", "basket", "score"]

            subbasket_scores_long["color"] = "grey"
            subbasket_scores_long["sizeR"] = 0.5
            subbasket_scores = utils.remove_patient_prefix(subbasket_scores, from_col=False)

            return subbasket_scores_long
