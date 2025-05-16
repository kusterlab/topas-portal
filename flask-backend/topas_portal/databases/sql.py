from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, TYPE_CHECKING

import pandas as pd

import topas_portal.basket_preprocess
import db_settings as database
import topas_portal.settings as cn
import topas_portal.utils as utils
import topas_portal.file_loaders.tupac as tupac_loader
import topas_portal.file_loaders.transcriptomics as tp
import topas_portal.file_loaders.genomics as genomics_preprocess
import topas_portal.file_loaders.kinase as kinase_loader
import topas_portal.file_loaders.expression as expression_loader
import topas_portal.file_loaders.sample_annotation as sample_annotation_loader
import topas_portal.file_loaders.patient_metadata as patient_metadata_loader
import topas_portal.file_loaders.phospho_score as phospho_score_loader
import topas_portal.settings as settings

if TYPE_CHECKING:
    from logger import CohortLogger
    from config import CohortConfig

if settings.DATABASE_MODE:
    import models


class SQLProvider:
    def __init__(self, logger: CohortLogger):
        self.logger = logger
        self.basket_complete_df = None
        self.FPKM = None
        self.genomics_data = None
        self.oncoKB_data = None

    def initialize_cohorts(self, cohort_names: List[str]):
        pass

    def load_single_cohort_with_empty_data(self, cohort_name: str):
        pass

    def load_tables(self, config: CohortConfig, cohort_names: List[str] = None):
        if cohort_names is None:
            cohort_names = config.get_cohort_names()

        for cohort_name in cohort_names:
            cohort_index = config.get_cohort_index(cohort_name)
            self.load_single_cohort(cohort_name, cohort_index, config)

        # these are stored in memory for now
        self._load_FPKM(config.get_config())
        self._load_genomics(config.get_config())
        self._load_onkoKB_annotations(config.get_config())
        self._load_basket_annotation_tables(config.get_config())

    def load_single_cohort(
        self, cohort_name: str, cohort_index: int, config: CohortConfig
    ):
        self.load_cohort_to_db_fp_expression_intensity(config, cohort_name)
        self.load_cohort_to_db_fp_expression_z(config, cohort_name)
        self.load_cohort_to_db_pp_expression_intensity(config, cohort_name)
        self.load_cohort_to_db_pp_expression_z(config, cohort_name)
        self.load_cohort_to_db_patient_meta_data(config, cohort_name)
        self.load_cohort_to_db_sample_annotation_df(config, cohort_name)
        self.load_cohort_to_db_protein_seq_mapping_df(config, cohort_name)
        self.load_cohort_to_db_fp_meta_expression(config, cohort_name)
        self.load_cohort_to_db_tupac_scores(config, cohort_name)
        self.load_cohort_to_db_phosphoscores(config, cohort_name)

    def _load_basket_annotation_tables(self, config: Dict):
        """Basket table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading basket tables")
        basket_annotation_path = Path(config["basket_annotation_path"])
        self.basket_complete_df = tupac_loader.load_basket_annotation_df(
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

    def _load_onkoKB_annotations(self, config: Dict):
        """oncoKB annotations table is independent of cohorts and will be treated as a single global variable separately"""
        self.logger.log_message("Loading oncoKB annotations data")
        self.oncoKB_data = genomics_preprocess.load_genomics_table(
            config["oncokb_path"]
        )
        self.logger.log_message("oncoKB annotations data loaded")

    def get_kinase_scores_dataframe(self, result_dir):
        """TODO: store in database"""
        path_to_kinase_df = Path(result_dir) / Path(cn.KINASE_SCORES_FILE)
        return kinase_loader.load_kinase_scores_df(path_to_kinase_df)

    def _db_protein_to_seq_importer(
        self, config: CohortConfig, cohort_index: int, table_class
    ):
        """For importing the protein to seq mapping"""
        cohort_report_dir = config.get_report_directory(cohort_index)
        df = expression_loader.load_modified_seq_protein_name_mapping(
            Path(cohort_report_dir)
        )
        df.columns = settings.PEPTIDE_PROTEIN_MAPPING_COLS.keys()
        df["cohort_id"] = cohort_index
        models.chunkwise_insert(df, table_class)

    def _db_patient_meta_data_importer(
        self,
        config: CohortConfig,
        cohort_index: int,
        table_class,
        data_type="meta_data",
        id_key="meta_type",
        patient_meta_file=True,
    ):
        """For importing the meta_data to the DB"""
        if patient_meta_file:
            meta_data_path = config.get_patients_metadata_path(cohort_index)
            meta_data_df = patient_metadata_loader.load_patient_table(meta_data_path)
        else:  # for sample annotation_df
            meta_data_path = config.get_sample_annotation_path(cohort_index)
            meta_data_df = sample_annotation_loader.load_sample_annotation_table(
                meta_data_path
            )
        meta_data_df = meta_data_df.set_index("Sample name").T
        self._final_importer(
            meta_data_df,
            table_class,
            cohort_index,
            data_type,
            id_key,
            decimal_rounding=False,
        )

    def _db_FP_meta_importer(
        self,
        config: CohortConfig,
        cohort_index: int,
        table_class,
        data_type="FP_meta",
        id_key="protein_name",
    ):
        """For the  insertion of the num_peptides per protein for each patient"""
        cohort_report_dir = config.get_report_directory(cohort_index)
        df_to_insert = expression_loader.load_intensity_meta_data(
            Path(os.path.join(cohort_report_dir, cn.PREPROCESSED_FP_INTENSITY)),
            cn.FP_KEY,
        )
        # df_to_insert = df_to_insert.set_index('Gene names')
        df_to_insert.columns = [str(x).split(" ")[-1] for x in df_to_insert.columns]
        self._final_importer(
            df_to_insert,
            table_class,
            cohort_index,
            data_type,
            id_key,
            decimal_rounding=False,
        )

    def _db_z_scores_importer(
        self,
        config: CohortConfig,
        cohort_index: int,
        table_class,
        key,
        data_type,
        id_key="protein_name",
    ):
        """For importing the z_scores of both FP and PP to the Db"""
        cohort_report_dir = config.get_report_directory(cohort_index)
        df_to_insert = expression_loader.load_expression_data(
            Path(cohort_report_dir), key, data_type
        )
        self._final_importer(df_to_insert, table_class, cohort_index, data_type, id_key)

    def _db_tupac_score_importer(
        self,
        config: CohortConfig,
        cohort_index: int,
        table_class,
        data_type="tupaczscores",
    ):
        """For importing the tupac scores to cohortsDB"""
        cohort_report_dir = config.get_report_directory(cohort_index)
        key = cn.BASKET_Z_SCORES_FILE
        if data_type == "tupacscoresraw":
            key = cn.BASKET_SCORES_FILE
        else:
            key = cn.BASKET_Z_SCORES_FILE
        basket_df = tupac_loader.load_basket_scores_df(
            Path(os.path.join(cohort_report_dir, key))
        )
        basket_df = topas_portal.basket_preprocess.get_basket_scores_long_format(
            basket_df
        )

        selected_cols = {
            "Sample name": "patient_name",
            "Basket_id": "basket_name",
            "Z-score": "value",
        }
        basket_df = basket_df[list(selected_cols.keys())]
        basket_df.columns = list(selected_cols.values())
        basket_df["cohort_id"] = cohort_index
        models.chunkwise_insert(basket_df, table_class)

    def _db_intensity_importer(
        self,
        config: CohortConfig,
        cohort_index: int,
        table_class,
        data_type,
        id_key="protein_name",
    ):

        cohort_report_dir = config.get_report_directory(cohort_index)
        meta_data_path = config.get_sample_annotation_path(cohort_index)
        meta_data_df = sample_annotation_loader.load_sample_annotation_table(
                meta_data_path
            )
        patients_list = meta_data_df['Sample name'].unique().tolist()
        if data_type == "phospho":  # for the phosohopeptides
            intensity_file = cn.PREPROCESSED_PP_INTENSITY
            key = cn.PP_KEY
            df_to_insert = expression_loader.load_annotated_intensity_file(
                Path(os.path.join(cohort_report_dir, intensity_file)), 
                key,
                patients_list
            )

        elif data_type == "phospho_scores":  # for the phospho scores
            intensity_file = cn.PHOSPHORYLATION_SCORES
            key = cn.FP_KEY
            df_to_insert = phospho_score_loader.load_phosphorylation_scores(
                Path(os.path.join(cohort_report_dir, intensity_file)), add_suffix=False
            )

        else:
            intensity_file = cn.PREPROCESSED_FP_INTENSITY
            key = cn.FP_KEY
            df_to_insert = expression_loader.load_annotated_intensity_file(
                Path(os.path.join(cohort_report_dir, intensity_file)),
                key,
                patients_list
            )

        self._final_importer(df_to_insert, table_class, cohort_index, data_type, id_key)

    def _final_importer(
        self,
        df_to_insert,
        table_class,
        cohort_index,
        data_type,
        id_key,
        decimal_rounding=True,
    ):
        if isinstance(df_to_insert, pd.DataFrame):
            df = _prepare_df_for_db(
                df_to_insert,
                cohort_index,
                id_key=id_key,
                decimal_rounding=decimal_rounding,
            )
            models.chunkwise_insert(df, table_class)
            self.logger.log_message(
                f"{data_type} of {cohort_index} was imported to database ##"
            )

    # per cohort
    def load_cohort_to_db_tupac_scores(self, config: CohortConfig, cohort_name):
        cohort_index = config.get_cohort_index(cohort_name)
        tupac_mapping_dic = {
            "tupacscoresraw": models.Tupacscoresraw,
            "tupaczscores": models.Tupaczscores,
        }
        for key in tupac_mapping_dic.keys():
            database.db.execute_sql(
                f"""DELETE FROM {key} WHERE cohort_id={cohort_index}"""
            )
            self._db_tupac_score_importer(
                config, cohort_index, tupac_mapping_dic[key], data_type=key
            )

    def load_cohort_to_db_protein_seq_mapping_df(
        self, config: CohortConfig, cohort_name
    ):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM modsequencetoprotein WHERE cohort_id={cohort_index}"""
        )
        self._db_protein_to_seq_importer(
            config, cohort_index, models.Modsequencetoprotein()
        )

    def load_cohort_to_db_patient_meta_data(self, config: CohortConfig, cohort_name):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM patientmetadata WHERE cohort_id={cohort_index}"""
        )
        self._db_patient_meta_data_importer(
            config, cohort_index, models.Patientmetadata()
        )

    def load_cohort_to_db_sample_annotation_df(self, config: CohortConfig, cohort_name):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM sampleannotation WHERE cohort_id={cohort_index}"""
        )
        self._db_patient_meta_data_importer(
            config, cohort_index, models.Sampleannotation(), patient_meta_file=False
        )

    def load_cohort_to_db_fp_meta_expression(self, config: CohortConfig, cohort_name):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM expressionfpmeta WHERE cohort_id={cohort_index}"""
        )
        self._db_FP_meta_importer(config, cohort_index, models.Expressionfpmeta())

    def load_cohort_to_db_fp_expression_z(self, config: CohortConfig, cohort_name):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM expressionfpzscores WHERE cohort_id={cohort_index}"""
        )
        self._db_z_scores_importer(
            config,
            cohort_index,
            models.Expressionfpzscores(),
            settings.FP_KEY,
            "full_proteome",
            id_key="protein_name",
        )

    def load_cohort_to_db_phosphoscores(self, config: CohortConfig, cohort_name):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM phosphoscores WHERE cohort_id={cohort_index}"""
        )
        self._db_intensity_importer(
            config,
            cohort_index,
            models.Phosphoscores(),
            "phospho_scores",
            id_key="protein_name",
        )

    def load_cohort_to_db_fp_expression_intensity(
        self, config: CohortConfig, cohort_name
    ):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM expressionfpintensity WHERE cohort_id={cohort_index}"""
        )
        self._db_intensity_importer(
            config,
            cohort_index,
            models.Expressionfpintensity(),
            "full_proteome",
            id_key="protein_name",
        )

    def load_cohort_to_db_pp_expression_z(self, config: CohortConfig, cohort_name):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM expressionppzscores WHERE cohort_id={cohort_index}"""
        )
        self._db_z_scores_importer(
            config,
            cohort_index,
            models.Expressionppzscores(),
            settings.PP_KEY,
            "phospho",
            id_key="sequence",
        )

    def load_cohort_to_db_pp_expression_intensity(
        self, config: CohortConfig, cohort_name
    ):
        cohort_index = config.get_cohort_index(cohort_name)
        database.db.execute_sql(
            f"""DELETE FROM expressionppintensity WHERE cohort_id={cohort_index}"""
        )
        self._db_intensity_importer(
            config,
            cohort_index,
            models.Expressionppintensity(),
            "phospho",
            id_key="sequence",
        )

    # all cohorts
    def _general_all_importer(self, config: CohortConfig, func):
        for cohort_name in config.get_cohort_names():
            try:
                func(config, cohort_name)
            except Exception as err:
                print(f"Unexpected {err=}, {type(err)=}")

    def load_all_to_db_to_db_to_db_phosphoscores(self, config: CohortConfig):
        self._general_all_importer(config, self.load_cohort_to_db_phosphoscores)

    def load_all_to_db_to_db_to_db_tupac_scores(self, config: CohortConfig):
        self._general_all_importer(config, self.load_cohort_to_db_tupac_scores)

    def load_all_to_db_to_db_fp_meta_expression(self, config: CohortConfig):
        self._general_all_importer(config, self.load_cohort_to_db_fp_meta_expression)

    def load_all_to_db_protein_seq_mapping_df(self, config: CohortConfig):
        self._general_all_importer(
            config, self.load_cohort_to_db_protein_seq_mapping_df
        )

    def load_all_to_db_fp_expression_z(self, config: CohortConfig):
        self._general_all_importer(config, self.load_cohort_to_db_fp_expression_z)

    def load_all_to_db_fp_expression_intensity(self, config: CohortConfig):
        self._general_all_importer(
            config, self.load_cohort_to_db_fp_expression_intensity
        )

    def load_all_to_db_pp_expression_z(self, config: CohortConfig):
        self._general_all_importer(config, self.load_cohort_to_db_pp_expression_z)

    def load_all_to_db_pp_expression_intensity(self, config: CohortConfig):
        self._general_all_importer(
            config, self.load_cohort_to_db_pp_expression_intensity
        )

    def load_all_to_db_patient_meta_data(self, config: CohortConfig):
        self._general_all_importer(config, self.load_cohort_to_db_patient_meta_data)

    def load_all_to_db_sample_annotation_df(self, config: CohortConfig):
        self._general_all_importer(config, self.load_cohort_to_db_sample_annotation_df)


def _prepare_df_for_db(
    df_to_insert: pd.DataFrame, cohort_id, id_key="protein_name", decimal_rounding=True
):
    df = pd.melt(df_to_insert, ignore_index=False, var_name="patient_name")
    df[id_key] = df.index
    df = df.dropna()
    if decimal_rounding:
        df.value = df.value.round(decimals=2)
    else:
        df.value = df.value.astype(str)  # for meta and sampleannotation dfs
    df["cohort_id"] = cohort_id
    return df
