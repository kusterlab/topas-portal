import pandas as pd

from topas_portal import utils


@utils.check_path_exist
def load_phosphorylation_scores(
    phosphorylation_scores_path,
    intensity_unit_suffix: str = "",
):
    phospho_score_df = pd.read_csv(
        phosphorylation_scores_path, sep="\t", low_memory=False, index_col=0
    )
    phospho_score_df = phospho_score_df.T
    phospho_score_df.index.name = "Gene names"

    if len(intensity_unit_suffix) > 0:
        phospho_score_df = phospho_score_df.add_suffix(intensity_unit_suffix)
    return utils.remove_patient_prefix(phospho_score_df)
