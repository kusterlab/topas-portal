import os
from typing import Union

import pandas as pd

import topas_portal.settings as cn
import topas_portal.utils as utils
from topas_portal.databases.in_memory import InMemoryProvider
from topas_portal.utils import INTENSITY_UNIT_SUFFIXES, IntensityUnit
from config import CohortConfig
from logger import CohortLogger
from topas_portal.data_api.exceptions import IntensityUnitUnavailableError


def extract_columns_and_remove_suffix(df: pd.DataFrame, intensity_unit: IntensityUnit):
    intensity_suffix = INTENSITY_UNIT_SUFFIXES[intensity_unit]
    df = df.filter(like=intensity_suffix)
    if len(df.columns) == 0:
        raise IntensityUnitUnavailableError(intensity_unit)
    df.columns = df.columns.str.removesuffix(intensity_suffix)
    return df


class InMemoryCohortDataAPI:
    def __init__(self, config_file: os.PathLike):
        self.logger = CohortLogger()
        self.config = CohortConfig(config_file, self.logger)
        self.provider = InMemoryProvider(self.logger)

    def load_all_data(self):
        """Load preprocessed dataframes for all cohorts."""
        self.logger.log_message("################### LOADING ##################")
        self.config.reload_config()
        self.provider.initialize_cohorts(self.config.get_cohort_names())
        self.provider.load_tables(self.config)

    # TODO: the following function needs to be refactored after database was established
    # based on the queries for each cohort
    def get_patients_entities_df(self, cohort_index: str) -> pd.DataFrame:
        patients_df = self.get_patient_metadata_df(cohort_index)
        df = pd.DataFrame(patients_df[cn.ENTITY_COLUMN].unique(), columns=["Entity"])
        df["Entity"] = df["Entity"].str.replace(r"[ ,;]", "_", regex=True)
        return df

    def get_sample_annotation_df(self, cohort_index: str) -> pd.DataFrame:
        """in sample annotaton df the replicates are included"""
        return self.provider.get_dataframe(
            cohort_index, utils.DataType.SAMPLE_ANNOTATION
        )

    def get_patient_metadata_df(self, cohort_index: str) -> pd.DataFrame:
        """in patient meta_df the replicates are not included"""
        return self.provider.get_dataframe(
            cohort_index, utils.DataType.PATIENT_METADATA
        )

    def _filter_expression_df(
        self,
        df,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ):
        if intensity_unit is not None:
            df = extract_columns_and_remove_suffix(df, intensity_unit=intensity_unit)

        if identifier:
            return df.loc[df.index == identifier]
        elif patient_name:
            extra_columns = [c for c in cn.PP_EXTRA_COLUMNS if c in df.columns]
            return df[[patient_name] + extra_columns]
        else:
            return df

    def get_num_pep_fp(self, cohort_index: str, protein_name=None) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, "fp_intensity_meta_df")
        return self._filter_expression_df(
            df, intensity_unit=None, identifier=protein_name, patient_name=None
        )

    def get_protein_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, utils.DataType.FULL_PROTEOME)
        return self._filter_expression_df(df, intensity_unit, identifier, patient_name)

    def get_psite_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, utils.DataType.PHOSPHO_PROTEOME)
        return self._filter_expression_df(df, intensity_unit, identifier, patient_name)

    def get_basket_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, utils.DataType.TUPAC_SCORE)
        return self._filter_expression_df(df, intensity_unit, identifier, patient_name)

    def get_report_dir(self, cohort_index: str) -> str:
        cohortname = list(self.config.config["report_directory"].keys())[
            int(cohort_index)
        ]
        return self.config.config["report_directory"][cohortname]

    def get_phosphorylation_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, utils.DataType.PHOSPHO_SCORE)
        return self._filter_expression_df(df, intensity_unit, identifier, patient_name)

    def get_kinase_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, utils.DataType.KINASE_SCORE)
        return self._filter_expression_df(df, intensity_unit, identifier, patient_name)

    def get_basket_annotation_df(self) -> pd.DataFrame:
        return self.provider.basket_complete_df

    def get_fpkm_df(
        self,
        cohort_index: Union[str, None] = None,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier=None,
        patient_name=None,
    ) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, utils.DataType.TRANSCRIPTOMICS)
        return self._filter_expression_df(df, intensity_unit, identifier, patient_name)

    def get_genomics(self) -> pd.DataFrame:
        return self.provider.genomics_data

    def get_oncoKB_annotations(self) -> pd.DataFrame:
        return self.provider.oncoKB_data

    def get_digestes_peptides_maps(self) -> pd.DataFrame:
        return self.provider.digest_data
