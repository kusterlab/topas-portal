from __future__ import annotations

from typing import Union, Protocol, TYPE_CHECKING

import pandas as pd

import topas_portal.utils as utils

if TYPE_CHECKING:
    from topas_portal.databases.data_provider import DataProvider
    from config import CohortConfig
    from logger import CohortLogger


class CohortDataAPI(Protocol):
    """Defines a protocol for retrieving cohort data from a data provider."""

    logger: CohortLogger
    config: CohortConfig
    provider: DataProvider

    def get_sample_annotation_df(self, cohort_index: str) -> pd.DataFrame:
        """in sample_annotaton_df the replicates are included"""

    def get_patient_metadata_df(self, cohort_index: str) -> pd.DataFrame:
        """in patient_metadata_df the replicates are not included"""

    def get_protein_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        """Z-scored protein intensities per sample on full proteome level"""

    def get_psite_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        """Z-scored p-site intensities per sample on phospho proteome level"""

    def get_topas_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        """Topas scores per sample"""

    def get_phosphorylation_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        """Protein phosphorylation scores per sample"""

    def get_kinase_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        """Protein Kinase scores per sample"""

    def get_fpkm_df(
        self,
        cohort_index: Union[str, None] = None,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        """"""

    def get_num_pep_fp(self, cohort_index: str) -> pd.DataFrame:
        """"""

    def get_topas_annotation_df(self) -> pd.DataFrame:
        """"""

    def get_genomics(self) -> pd.DataFrame:
        """"""

    def get_oncoKB_annotations(self) -> pd.DataFrame:
        """"""
