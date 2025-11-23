"""
IN MEMORY MODE: loading precomputed data to memory for none DB mode
all data will be loaded to the memory as a global variable
this mode cannot be scaled up with Gunicorn
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING, Union

import pandas as pd

from topas_portal.data_api.exceptions import (
    CohortDataNotLoadedError,
    DataLayerUnavailableError,
)
from topas_portal import utils
from . import table_loaders
import topas_portal.file_loaders.topas as topas_loader
import topas_portal.file_loaders.transcriptomics as tp
import topas_portal.file_loaders.genomics as genomics_preprocess
import topas_portal.file_loaders.digest_load as digest_load

if TYPE_CHECKING:
    from logger import CohortLogger
    from topas_portal.config import CohortConfig

# in memory dataframes for each cohort
DICT_ALL_DATA = {
    utils.DataType.PATIENT_METADATA: [],
    utils.DataType.SAMPLE_ANNOTATION: [],
    utils.DataType.PHOSPHO_PROTEOME: [],
    utils.DataType.FULL_PROTEOME: [],
    utils.DataType.TOPAS_RTK_SCORE: [],
    utils.DataType.TOPAS_CK_SCORE: [],
    utils.DataType.KINASE_SCORE: [],
    utils.DataType.PHOSPHO_SCORE: [],
    utils.DataType.SEARCH_QC: [],
}

SHARED_COHORT = "shared"


class InMemoryProvider:
    def __init__(self, logger: CohortLogger):
        self.logger = logger
        self.dict_all_data = DICT_ALL_DATA
        self.topas_complete_df = None
        self.poi_annotation_df = None
        self.FPKM = None
        self.genomics_data = None
        self.oncoKB_data = None

    def initialize_cohorts(self, cohort_names: List[str]):
        self.dict_all_data = DICT_ALL_DATA
        for cohort_name in cohort_names:
            self.load_single_cohort_with_empty_data(cohort_name)

    def load_single_cohort_with_empty_data(self, cohort_name: str):
        for data_layer in self.dict_all_data.keys():
            print(data_layer)
            # reserving a df for each data layer
            self.dict_all_data[data_layer].append(
                {"name": cohort_name, "data_frame": []}
            )

    def load_tables(self, config: CohortConfig, cohort_names: List[str] = None):
        if cohort_names is None:
            cohort_names = config.get_cohort_names()

        self._load_poi_annotations(config.get_poi_annotation_path())
        self._load_topas_annotation_tables(config.get_topas_annotation_path())
        self._load_onkoKB_annotations(config.get_oncokb_annotation_path())
        self._load_FPKM(config)
        self._load_genomics(config)

        for cohort_name in cohort_names:
            cohort_index = config.get_cohort_index(cohort_name)
            self.load_single_cohort(cohort_name, cohort_index, config)

    def load_single_cohort(
        self, cohort_name: str, cohort_index: int, config: CohortConfig
    ):
        """
        Load tables for a single cohort.
        We pass both the cohort_name and cohort_index to check for consistency.
        """
        self.logger.log_message(f"loading ############ {cohort_name}")
        cohort_data = table_loaders.load_all_tables(cohort_name, config)
        for data_layer in cohort_data.keys():
            data_layer_cohort_name = self.dict_all_data[data_layer][cohort_index][
                "name"
            ]
            if data_layer_cohort_name != cohort_name:
                self.logger.log_message(
                    f"Cohort name does not match {cohort_name} vs. {data_layer_cohort_name}. Please re-deploy the Portal."
                )
                continue

            if not isinstance(cohort_data[data_layer], pd.DataFrame):
                self.logger.log_message(
                    f"{data_layer} of {cohort_name} was not loaded {cohort_data[data_layer]}"
                )
                continue

            self.dict_all_data[data_layer][cohort_index]["data_frame"] = cohort_data[
                data_layer
            ]
            self.logger.log_message(f"{data_layer} of {cohort_name} was Updated ##")

    def _load_topas_annotation_tables(self, topas_annotation_path: Path):
        """Topas table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading topas tables")
        self.topas_complete_df = topas_loader.load_topas_annotation_df(
            topas_annotation_path
        )
        self.logger.log_message("Topas tables loaded")

    def _load_poi_annotations(self, poi_annotation_path: Path):
        """The protein of interest (POI) table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading POI annotation table")
        self.poi_annotation_df = topas_loader.load_poi_annotation_df(
            poi_annotation_path
        )
        self.logger.log_message("POI annotation tables loaded")

    def _load_FPKM(self, config: CohortConfig):
        """FPKM table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading FPKM data")
        self.FPKM = table_loaders.load_transcriptomics_data(SHARED_COHORT, config)
        self.logger.log_message("FPKM data loaded")

    def _load_genomics(self, config: CohortConfig):
        """Genomics table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading Genomics data")
        self.genomics_data = table_loaders.load_genomics_data(SHARED_COHORT, config)
        self.logger.log_message("Genomics data loaded")

    def _load_insilicodigest(self, config: Dict):
        """Genomics table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Start in silico digest")
        self.digest_data = digest_load.load_in_silico_digestion(config["fasta_file"])
        self.logger.log_message("Digestion of fasta data loaded")

    def _load_onkoKB_annotations(self, oncokb_annotation_path: Path):
        """oncoKB annotations table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading oncoKB annotations data")
        self.oncoKB_data = genomics_preprocess.load_onkoKB_dictionary(
            oncokb_annotation_path
        )
        self.logger.log_message("oncoKB annotations data loaded")

    def get_dataframe(
        self, cohort_index: Union[str, None], data_layer: utils.DataType
    ) -> pd.DataFrame:
        if data_layer == utils.DataType.TRANSCRIPTOMICS:
            df = self.FPKM
        else:
            if int(cohort_index) >= len(self.dict_all_data[data_layer]):
                raise CohortDataNotLoadedError()
            df = self.dict_all_data[data_layer][int(cohort_index)]["data_frame"]

        if not isinstance(df, pd.DataFrame) or len(df.index) == 0:
            raise DataLayerUnavailableError(data_layer)

        return df
