import pandas as pd

import topas_portal.utils as ef


@ef.check_path_exist
def load_phosphorylation_scores(
    phosphorylation_scores_path,
    add_suffix=False,
    extra_columns=["Gene names", "mean", "stdev", "std"],
):

    phospho_score_df = pd.read_csv(
        phosphorylation_scores_path, sep="\t", low_memory=False
    )
    phospho_score_df.index = phospho_score_df["Gene names"]
    removing_list = [
        col for col in phospho_score_df.columns.tolist() if col in extra_columns
    ]
    if len(removing_list) > 0:
        phospho_score_df = phospho_score_df.drop(removing_list, axis=1)

    if add_suffix:
        phospho_score_df = phospho_score_df.add_suffix(" Z-score")
    return ef.remove_prefix(phospho_score_df)
