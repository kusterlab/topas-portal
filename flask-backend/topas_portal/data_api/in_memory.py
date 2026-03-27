import os
from typing import Union, Optional

import pandas as pd

from topas_portal import settings
from topas_portal.data_type import DataType
from topas_portal import constants
from topas_portal.constants import (
    IntensityUnit,
    IncludeRef,
)
from topas_portal.databases.in_memory import InMemoryProvider
from topas_portal.config import CohortConfig
from logger import CohortLogger
from topas_portal.data_api.exceptions import IntensityUnitUnavailableError


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
        df = pd.DataFrame(
            patients_df[settings.ENTITY_COLUMN].unique(), columns=["Entity"]
        )
        df["Entity"] = df["Entity"].str.replace(r"[ ,;]", "_", regex=True)
        return df

    def get_report_dir(self, cohort_index: str) -> str:
        cohortname = list(self.config.config["report_directory"].keys())[
            int(cohort_index)
        ]
        return self.config.config["report_directory"][cohortname]

    def get_sample_annotation_df(
        self,
        cohort_index: str,
        include_ref: IncludeRef = IncludeRef.INCLUDE_REF,
    ) -> pd.DataFrame:
        """in sample annotaton df the replicates are included"""
        sample_annotation_df = self.provider.get_dataframe(
            cohort_index, DataType.SAMPLE_ANNOTATION
        )
        sample_annotation_df = _filter_for_ref_sample_annotation(
            sample_annotation_df, include_ref
        )
        return sample_annotation_df

    def get_patient_metadata_df(self, cohort_index: str) -> pd.DataFrame:
        """in patient meta_df the replicates are not included"""
        return self.provider.get_dataframe(
            cohort_index, DataType.PATIENT_METADATA
        )

    def get_search_qc_df(self, cohort_index: str) -> pd.DataFrame:
        """MaxQuant search QC statistics, e.g. #peptides, summed intensity"""
        return self.provider.get_dataframe(cohort_index, DataType.SEARCH_QC)

    def _get_filtered_df(
        self,
        cohort_index: str,
        data_layer: DataType,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier: str = None,
        patient_name: str = None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        df = self.provider.get_dataframe(cohort_index, data_layer)

        if extra_columns is None:
            extra_columns = []
        extra_columns = df.columns.intersection(extra_columns).to_list()

        df = _filter_expression_df(
            df, intensity_unit, identifier, patient_name, extra_columns
        )
        df = _filter_for_ref(df, include_ref, extra_columns)
        return df

    def get_protein_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier: str = None,
        patient_name: str = None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        return self._get_filtered_df(
            cohort_index,
            DataType.FULL_PROTEOME,
            intensity_unit,
            identifier,
            patient_name,
            include_ref,
            extra_columns,
        )

    def get_psite_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier: str = None,
        patient_name: str = None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        return self._get_filtered_df(
            cohort_index,
            DataType.PHOSPHO_PROTEOME,
            intensity_unit,
            identifier,
            patient_name,
            include_ref,
            extra_columns,
        )

    def get_topas_rtk_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier: str = None,
        patient_name: str = None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        return self._get_filtered_df(
            cohort_index,
            DataType.TOPAS_RTK_SCORE,
            intensity_unit,
            identifier,
            patient_name,
            include_ref,
            extra_columns,
        )

    def get_topas_ck_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier: str = None,
        patient_name: str = None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        return self._get_filtered_df(
            cohort_index,
            DataType.TOPAS_CK_SCORE,
            intensity_unit,
            identifier,
            patient_name,
            include_ref,
            extra_columns,
        )

    def get_phosphorylation_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier: str = None,
        patient_name: str = None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        return self._get_filtered_df(
            cohort_index,
            DataType.PHOSPHO_SCORE,
            intensity_unit,
            identifier,
            patient_name,
            include_ref,
            extra_columns,
        )

    def get_kinase_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier: str = None,
        patient_name: str = None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        return self._get_filtered_df(
            cohort_index,
            DataType.KINASE_SCORE,
            intensity_unit,
            identifier,
            patient_name,
            include_ref,
            extra_columns,
        )

    def get_fpkm_df(
        self,
        cohort_index: Union[str, None] = None,
        intensity_unit: Optional[IntensityUnit] = None,
        identifier=None,
        patient_name=None,
        include_ref: IncludeRef = IncludeRef.EXCLUDE_REF,
        extra_columns: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        return self._get_filtered_df(
            cohort_index,
            DataType.TRANSCRIPTOMICS,
            intensity_unit,
            identifier,
            patient_name,
            include_ref,
            extra_columns,
        )

    def get_genomics(self) -> pd.DataFrame:
        return self.provider.genomics_data

    def get_oncoKB_annotations(self) -> dict:
        return self.provider.oncoKB_data

    def get_topas_annotation_df(self) -> pd.DataFrame:
        return self.provider.topas_complete_df

    def get_poi_annotation_df(self) -> pd.DataFrame:
        return self.provider.poi_annotation_df


def _filter_for_ref(
    df: pd.DataFrame,
    include_ref: IncludeRef,
    extra_columns: Optional[list[str]] = None,
) -> pd.DataFrame:
    if include_ref == IncludeRef.EXCLUDE_REF:
        df = df.loc[:, ~df.columns.str.startswith(constants.REF_CHANNEL_PREFIX)]
    elif include_ref == IncludeRef.ONLY_REF:
        df = df.loc[
            :,
            df.columns.str.startswith(constants.REF_CHANNEL_PREFIX)
            | df.columns.isin(extra_columns),
        ]
    return df


def _filter_for_ref_sample_annotation(
    df: pd.DataFrame, include_ref: IncludeRef
) -> pd.DataFrame:
    if include_ref == IncludeRef.EXCLUDE_REF:
        df = df.loc[~df["Sample name"].str.startswith(constants.REF_CHANNEL_PREFIX)]
    elif include_ref == IncludeRef.ONLY_REF:
        df = df.loc[df["Sample name"].str.startswith(constants.REF_CHANNEL_PREFIX)]
    return df


def extract_columns_and_remove_suffix(
    df: pd.DataFrame,
    intensity_unit: IntensityUnit,
    extra_columns: list[str],
):
    intensity_suffix = constants.INTENSITY_UNIT_SUFFIXES[intensity_unit]
    filtered_df = df.filter(like=intensity_suffix)
    if len(filtered_df.columns) == 0:
        raise IntensityUnitUnavailableError(intensity_unit)
    filtered_df.columns = filtered_df.columns.str.removesuffix(intensity_suffix)
    return filtered_df.join(df[extra_columns])


def _filter_expression_df(
    df: pd.DataFrame,
    intensity_unit: Optional[IntensityUnit],
    identifier: str,
    patient_name: str,
    extra_columns: list[str],
):
    if intensity_unit is not None:
        df = extract_columns_and_remove_suffix(
            df, intensity_unit=intensity_unit, extra_columns=extra_columns
        )

    if identifier:
        return df.loc[df.index == identifier]
    elif patient_name:
        return df[[patient_name] + extra_columns]

    return df
