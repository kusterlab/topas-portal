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
import topas_portal.settings as cn
import topas_portal.utils as utils
import topas_portal.file_loaders.topas as topas_loader
import topas_portal.file_loaders.transcriptomics as tp
import topas_portal.file_loaders.genomics as genomics_preprocess
import topas_portal.file_loaders.kinase as kinase_loader
import topas_portal.file_loaders.phospho_score as phospho_score_loader
import topas_portal.file_loaders.expression as expression_loader
import topas_portal.file_loaders.sample_annotation as sample_annotation_loader
import topas_portal.file_loaders.patient_metadata as patient_metadata_loader
import topas_portal.file_loaders.digest_load as digest_load

if TYPE_CHECKING:
    from logger import CohortLogger
    from config import CohortConfig

# in memory dataframes for each cohort
DICT_ALL_DATA = {
    utils.DataType.PATIENT_METADATA: [],
    utils.DataType.SAMPLE_ANNOTATION: [],
    utils.DataType.PHOSPHO_PROTEOME: [],
    utils.DataType.FULL_PROTEOME: [],
    utils.DataType.TOPAS_SCORE: [],
    utils.DataType.KINASE_SCORE: [],
    utils.DataType.PHOSPHO_SCORE: [],
    "fp_intensity_meta_df": [],
}


class InMemoryProvider:
    def __init__(self, logger: CohortLogger):
        self.logger = logger
        self.dict_all_data = DICT_ALL_DATA
        self.basket_complete_df = None
        self.FPKM = None
        self.genomics_data = None
        self.oncoKB_data = None

    def initialize_cohorts(self, cohort_names: List[str]):
        self.dict_all_data = DICT_ALL_DATA
        for cohort_name in cohort_names:
            for data_layer in self.dict_all_data.keys():
                # reserving a df for each data layer
                self.dict_all_data[data_layer].append(
                    {"name": cohort_name, "data_frame": []}
                )

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

        for cohort_name in cohort_names:
            cohort_index = config.get_cohort_index(cohort_name)
            self.load_single_cohort(cohort_name, cohort_index, config)

        self._load_FPKM(config.get_config())
        self._load_genomics(config.get_config())
        self._load_onkoKB_annotations(config.get_config())
        self._load_basket_annotation_tables(config.get_config())

    def load_single_cohort(
        self, cohort_name: str, cohort_index: int, config: CohortConfig
    ):
        """
        Load tables for a single cohort.
        We pass both the cohort_name and cohort_index to check for consistency.
        """
        self.logger.log_message(f"loading ############ {cohort_name}")
        disease_data = _load_all_tables(cohort_name, config.get_config())
        for data_layer in disease_data.keys():
            data_layer_cohort_name = self.dict_all_data[data_layer][cohort_index][
                "name"
            ]
            if data_layer_cohort_name != cohort_name:
                self.logger.log_message(
                    f"Cohort name does not match {cohort_name} vs. {data_layer_cohort_name}. Please re-deploy the Portal."
                )
                continue

            if not isinstance(disease_data[data_layer], pd.DataFrame):
                self.logger.log_message(
                    f"{data_layer} of {cohort_name} was not loaded {disease_data[data_layer]}"
                )
                continue

            self.dict_all_data[data_layer][cohort_index]["data_frame"] = disease_data[
                data_layer
            ]
            self.logger.log_message(f"{data_layer} of {cohort_name} was Updated ##")

    def _load_basket_annotation_tables(self, config: Dict):
        """Basket table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading basket tables")
        basket_annotation_path = Path(config["basket_annotation_path"])
        self.basket_complete_df = topas_loader.load_basket_annotation_df(
            basket_annotation_path
        )
        self.logger.log_message("Basket tables loaded")

    def _load_FPKM(self, config: Dict):
        """FPKM table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading FPKM data")
        self.FPKM = tp.load_FPKM_table(config["transcriptomics_path_z_scored"])
        FPKM_not_z_scored = tp.load_FPKM_table(
            config["transcriptomics_path_not_z_scored"]
        )
        self.FPKM = self.FPKM.join(
            FPKM_not_z_scored,
            lsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE],
            rsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.INTENSITY],
        )

        self.logger.log_message("FPKM data loaded")

    def _load_genomics(self, config: Dict):
        """Genomics table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading Genomics data")
        self.genomics_data = genomics_preprocess.load_genomics_table(
            config["genomics_path"]
        )
        self.logger.log_message("Genomics data loaded")

    def _load_insilicodigest(self, config: Dict):
        """Genomics table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Start in silico digest")
        self.digest_data = digest_load.load_in_silico_digestion(config["fasta_file"])
        self.logger.log_message("Digestion of fasta data loaded")

    def _load_onkoKB_annotations(self, config: Dict):
        """oncoKB annotations table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading oncoKB annotations data")
        self.oncoKB_data = genomics_preprocess.load_genomics_table(
            config["oncokb_path"]
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


def _load_all_tables(cohort, config: Dict, do_return_place_holder: bool = False):
    """For a single cohort type makes a dictionary of dataframes"""

    basket_df, pp_df_patients = [], []
    sample_annotation_df, patients_df = [], []
    fp_df_patients, fp_intensity_meta = [], []
    kinase_score_df, phospho_score_df = [], []

    if not do_return_place_holder:
        cohort_report_dir = config["report_directory"][cohort]
        print(f"report dir #########{cohort_report_dir}")
        basket_df = topas_loader.load_basket_scores_df(
            Path(os.path.join(cohort_report_dir, cn.BASKET_SCORES_FILE))
        )
        if isinstance(basket_df, pd.DataFrame):
            basket_df_z_scored = topas_loader.load_basket_scores_df(
                Path(os.path.join(cohort_report_dir, cn.BASKET_Z_SCORES_FILE))
            )
            basket_df = basket_df.join(
                basket_df_z_scored,
                lsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.SCORE],
                rsuffix=utils.INTENSITY_UNIT_SUFFIXES[utils.IntensityUnit.Z_SCORE],
            )

        sample_annotation_df = sample_annotation_loader.load_sample_annotation_table(
            Path(config["sample_annotation_path"][cohort])
        )
        patients_df = patient_metadata_loader.load_patient_table(
            Path(config["patient_annotation_path"][cohort])
        )
        patients_list = sample_annotation_df['Sample name'].unique().tolist()
        ## preprocessed intensities at FP level
        if config["FP"][cohort] == 1:
            print("Reading the data at the FP level")
            fp_intensity_meta = expression_loader.load_intensity_meta_data(
                Path(os.path.join(cohort_report_dir, cn.PREPROCESSED_FP_INTENSITY)),
                cn.FP_KEY,
            )
            fp_intensity = expression_loader.load_annotated_intensity_file(
                Path(os.path.join(cohort_report_dir, cn.PREPROCESSED_FP_INTENSITY)),
                cn.FP_KEY, patients_list
            )
            fp_df_patients = expression_loader.load_expression_data(
                Path(cohort_report_dir), cn.FP_KEY, "full_proteome"
            )
            fp_df_patients = fp_df_patients.join(fp_intensity)

        ## Loading Phospho data to the portal
        if config["PP"][cohort] == 1:
            print("Reading the data at at the PP level")
            pp_intensity = expression_loader.load_annotated_intensity_file(
                Path(os.path.join(cohort_report_dir, cn.PREPROCESSED_PP_INTENSITY)),
                cn.PP_KEY, patients_list,
                extra_columns=cn.PP_EXTRA_COLUMNS,
            )
            pp_df_patients = expression_loader.load_expression_data(
                Path(cohort_report_dir), cn.PP_KEY, "phospho"
            )
            pp_df_patients = pp_df_patients.join(pp_intensity)

            kinase_score_df = kinase_loader.load_kinase_scores_df(
                Path(cohort_report_dir) / Path(cn.KINASE_SCORES_FILE)
            )
            phospho_score_df = phospho_score_loader.load_phosphorylation_scores(
                Path(os.path.join(cohort_report_dir, cn.PHOSPHORYLATION_SCORES)),
                add_suffix=True,
            )

    return {
        utils.DataType.PATIENT_METADATA: patients_df,  # meta data per cohort the Sample name column refer to the patient, no replicates
        utils.DataType.SAMPLE_ANNOTATION: sample_annotation_df,  # meta data with replicates Sample name column refer to the patients, keeps replicates
        utils.DataType.PHOSPHO_PROTEOME: pp_df_patients,  # phospho sites Z-scores of normalized logged intensities
        utils.DataType.FULL_PROTEOME: fp_df_patients,  # full proteome Z-scores of normalized logged intensities
        utils.DataType.TOPAS_SCORE: basket_df,  # topas scores not z_scored
        utils.DataType.KINASE_SCORE: kinase_score_df,  # kinase scores Z-scores
        utils.DataType.PHOSPHO_SCORE: phospho_score_df,  # phospho scores Z-scores
        "fp_intensity_meta_df": fp_intensity_meta,  # number of peptides detected at full proteome
    }
