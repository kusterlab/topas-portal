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
        self._add_within_batch_ranks(cohort_data)
        self._add_annotations(cohort_data)
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

    def _add_annotations(self, cohort_data: dict):
        for data_type in [
            utils.DataType.FULL_PROTEOME,
            utils.DataType.PHOSPHO_PROTEOME,
            utils.DataType.PHOSPHO_SCORE,
        ]:
            self.logger.log_message(
                f"Adding Protein of Interest (POI) annotations for {data_type.value}."
            )
            merge_with_poi_annotations_inplace(
                cohort_data[data_type], self.poi_annotation_df
            )
        self.logger.log_message("Protein of Interest (POI) annotations added")

    def _add_within_batch_ranks(self, cohort_data: dict):
        """Adds rank of sample within its own TMT batch based on its z-score.

        Takes 1.5 minutes for 2000 samples and 200k p-sites.

        Args:
            cohort_data (dict): _description_
        """        
        for data_type in [
            utils.DataType.FULL_PROTEOME,
            utils.DataType.PHOSPHO_PROTEOME,
            utils.DataType.PHOSPHO_SCORE,
        ]:
            self.logger.log_message(f"Adding within batch ranks for {data_type.value}.")
            add_within_batch_ranks_inplace(
                cohort_data[data_type], cohort_data[utils.DataType.SAMPLE_ANNOTATION]
            )
        self.logger.log_message("Within batch ranks metrics added")

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


def merge_with_poi_annotations_inplace(
    df: pd.DataFrame, poi_annotation_df: pd.DataFrame
):
    utils.merge_by_delimited_field(
        df,
        poi_annotation_df[
            ["Gene names", "POI_REPORT", "POI_EXPLORATORY", "POI_PRODICT"]
        ],
        field_name="Gene names",
        inplace=True,
    )


def add_within_batch_ranks_inplace(
    df: pd.DataFrame, sample_annotation_df: pd.DataFrame
):
    z_score_df = df.filter(
        like=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE]
    )
    sample_to_batch_mapping = sample_annotation_df.set_index("Sample name")["Batch_No"]
    sample_to_batch_mapping.index = (
        sample_to_batch_mapping.index
        + utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE]
    )
    batch_rank_columns = z_score_df.columns.str.replace(
        utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE],
        utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.BATCH_RANK],
    )
    df.loc[:, batch_rank_columns] = (
        z_score_df.groupby(
            by=z_score_df.columns.map(sample_to_batch_mapping),
            axis=1,
        ).rank(method="min", ascending=False)
        .values
    )
