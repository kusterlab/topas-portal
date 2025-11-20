import pandas as pd

from .. import utils


@utils.check_path_exist
def load_search_qc_table(search_qc_table_path: str):
    search_qc_df = pd.read_csv(search_qc_table_path, sep="\t")
    return search_qc_df
