import pandas as pd
import topas_portal.utils as utility

import topas_portal.topas_scores_meta as topass
from topas_portal.utils import calculate_z_scores


def calculate_TOPAS_scores(
    z_scores_df: pd.DataFrame,
    patients_df: pd.DataFrame,
    signatures_proteins: list = topass.IFN_proteins,
    score_type="topas_score",
) -> pd.DataFrame:

    alpha_signatures_df = z_scores_df[z_scores_df.index.isin(signatures_proteins)]
    # alpha_signatures_df = alpha_signatures_df.filter(regex="Z-score")
    sum_z_scores = pd.DataFrame(alpha_signatures_df.sum(axis=0, skipna=True)).T
    sum_z_scores.index = ["sum"]
    final = pd.concat([alpha_signatures_df, sum_z_scores], axis=0)
    z_scores_df = final.T

    # adding LOO z_scores
    if score_type != "topas_score":
        df = pd.DataFrame(z_scores_df["sum"].copy())
        df.columns = ["sum"]
        new_z_scors = calculate_z_scores(df, col_name="sum")
        z_scores_df["z_scores_sum_LOO"] = new_z_scors

    z_scores_df = _post_process_z_scores_df(z_scores_df, score_type)
    z_scores_df = utility.merge_with_patients_meta_df(z_scores_df, patients_df)
    z_scores_df = utility.fill_nans_patient_columns(z_scores_df)
    return z_scores_df


def _post_process_z_scores_df(z_scores_df, score_type):

    z_scores_df["Sample name"] = z_scores_df.index
    z_scores_df["Sample name"] = z_scores_df["Sample name"].str.replace(" Z-score", "")

    if score_type != "topas_score":
        final_df = z_scores_df[["Sample name", "z_scores_sum_LOO"]]
    else:
        final_df = z_scores_df[["Sample name", "sum"]]
    final_df.columns = ["Sample name", "Z-score"]
    return final_df
