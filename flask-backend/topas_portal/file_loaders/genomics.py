from pathlib import Path
import pandas as pd

import topas_portal.utils as utils


@utils.check_path_exist
def load_genomics_table(genomics_path: str) -> pd.DataFrame:
    # TODO: convert this to long data format to save memory(?)
    genomics_df = pd.read_csv(Path(genomics_path), dtype=pd.StringDtype())
    genomics_df = genomics_df.loc[:, ~genomics_df.columns.str.contains("^Unnamed")]
    genomics_df = genomics_df.fillna("missing")
    return genomics_df
