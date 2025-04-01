import pandas as pd

import topas_portal.utils as utils


@utils.check_path_exist
def load_kinase_scores_df(kinase_scores_path):
    kinase_scores_df = pd.read_csv(
        kinase_scores_path, sep="\t", index_col="PSP Kinases"
    )
    kinase_scores_df.index.name = "Gene names"

    # remove the "targets_<sample_id>" rows containing the number of detected p-sites per kinase per patient
    kinase_scores_df = kinase_scores_df.loc[
        :, ~kinase_scores_df.columns.str.startswith("targets_")
    ]
    kinase_scores_df = kinase_scores_df.drop(
        ["mean", "stdev", "No. of total targets"], axis=1, errors="ignore"
    )

    kinase_scores_df = kinase_scores_df.add_suffix(" Z-score")

    return utils.remove_patient_prefix(kinase_scores_df)
