from pathlib import Path

import pandas as pd
import numpy as np

import topas_portal.utils as utils


@utils.check_path_exist
def load_FPKM_table(fpkm_path: str) -> pd.DataFrame:
    fpkm_df = pd.read_csv(Path(fpkm_path), index_col="genes")
    # remove the unnamed column at the start of the FPKM file
    fpkm_df = fpkm_df.loc[:, ~fpkm_df.columns.str.contains("^Unnamed")]
    fpkm_df.columns = fpkm_df.columns.str.removesuffix(" Z-score")
    fpkm_df = fpkm_df.replace([np.inf, -np.inf], np.nan)
    return fpkm_df
