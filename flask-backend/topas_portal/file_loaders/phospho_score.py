import pandas as pd

from topas_portal import utils


@utils.check_path_exist
def load_phosphorylation_scores(
    phosphorylation_scores_path,
    add_suffix=False,
):
    phospho_score_df = pd.read_csv(
        phosphorylation_scores_path, sep="\t", low_memory=False
    )
    phospho_score_df = phospho_score_df.T
    phospho_score_df.index.name = "Gene names"

    if add_suffix:
        phospho_score_df = phospho_score_df.add_suffix(
            utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE]
        )
    return utils.remove_patient_prefix(phospho_score_df)
