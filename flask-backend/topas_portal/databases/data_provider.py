from __future__ import annotations

from typing import Protocol, List, TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from config import CohortConfig


class DataProvider(Protocol):
    topas_complete_df: pd.DataFrame
    FPKM: pd.DataFrame

    def initialize_cohorts(self, cohort_names: List[str]):
        """"""

    def load_tables(self, config: CohortConfig, cohort_names: List[str] = None):
        """"""

    def load_single_cohort(
        self, cohort_name: str, cohort_index: int, config: CohortConfig
    ):
        """"""
