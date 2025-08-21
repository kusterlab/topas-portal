import os
from pathlib import Path
from typing import Union

import pandas as pd

import topas_portal.data_api.in_memory as in_memory
import topas_portal.file_loaders.expression as expression_loader
from topas_portal import settings
from topas_portal import utils
from topas_portal.databases.sql import SQLProvider
from config import CohortConfig
from logger import CohortLogger

if settings.DATABASE_MODE:
    import models


class SQLCohortDataAPI:
    def __init__(self, config_file: os.PathLike):
        self.logger = CohortLogger()
        self.config = CohortConfig(config_file, self.logger)
        self.provider = SQLProvider(self.logger)

    def load_all_data(self):
        """Load preprocessed dataframes for all cohorts."""
        self.logger.log_message("################### LOADING ##################")
        self.config.reload_config()
        self.provider.initialize_cohorts(self.config.get_cohort_names())
        print(self.config.get_cohort_names())
        self.provider.load_tables(self.config)

    # based on the queries for each cohort
    def get_patients_entities_df(self, cohort_index: str) -> pd.DataFrame:
        patients_df = self.get_patient_metadata_df(cohort_index)
        df = pd.DataFrame(patients_df[settings.ENTITY_COLUMN].unique(), columns=["Entity"])
        df["Entity"] = df["Entity"].str.replace(r"[ ,;]", "_", regex=True)
        return df

    def get_sample_annotation_df(self, cohort_index: str) -> pd.DataFrame:
        """in sample annotaton df the replicates are included"""
        query = f"""SELECT patient_name,meta_type,value FROM sampleannotation WHERE cohort_id={cohort_index}  """
        df = self._convert_query_to_df(models.Sampleannotation.raw(query))
        df = self._post_process_query_result(df, data_type="patients_meta_data").T
        df["Sample name"] = df.index
        return df

    def get_patient_metadata_df(self, cohort_index: str) -> pd.DataFrame:
        """in patient meta_df the replicates are not included"""
        query = f"""SELECT patient_name,meta_type,value FROM patientmetadata WHERE cohort_id={cohort_index}  """
        df = self._convert_query_to_df(models.Patientmetadata.raw(query))
        df = self._post_process_query_result(df, data_type="patients_meta_data").T
        # df = df[[utils.intersection(df.columns,cn.PATIENTS_META_DATA)]]
        df["Sample name"] = df.index
        df = df.reset_index()
        df["index"] = df.index
        return df

    def _convert_query_to_df(self, query_result) -> pd.DataFrame:
        """
        Converts select query calls from peewee to pandas df
        """
        df = pd.DataFrame(query_result.dicts())
        return df

    def _post_process_query_result(
        self, df: pd.DataFrame, data_type="full proteome"
    ) -> pd.DataFrame:
        """
        for DB mode pivotize the resulting query df and columns names
        """
        if isinstance(df, pd.DataFrame) and len(df) > 0:
            if data_type == "full proteome":
                indexes = ["patient_name", "protein_name"]
            elif data_type == "patients_meta_data":
                indexes = ["patient_name", "meta_type"]
            else:
                indexes = ["patient_name", "sequence"]

            df = df.drop_duplicates(subset=indexes)
            df = df.set_index(indexes)
            df = df.unstack()

            df.columns = [x[1] for x in df.columns]
            df = df.T
        return df

    def get_num_pep_fp(self, cohort_index: str, protein_name=None) -> pd.DataFrame:
        if protein_name:
            query = f"""SELECT patient_name,protein_name,value FROM Expressionfpmeta WHERE cohort_id={cohort_index} AND protein_name='{protein_name}' """
        else:
            query = f"""SELECT patient_name,protein_name,value FROM Expressionfpmeta WHERE cohort_id={cohort_index}  """
        df = self._convert_query_to_df(models.Expressionfpmeta.raw(query))
        df = self._post_process_query_result(df, data_type="full proteome")
        df = df.T
        df.index = ["Identification metadata " + x for x in df.index]
        return df

    def get_protein_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier=None,
        patient_name=None,
    ) -> pd.DataFrame:

        if intensity_unit == utils.IntensityUnit.INTENSITY:
            if identifier:
                query = f"""SELECT patient_name,protein_name,value FROM expressionfpintensity WHERE cohort_id={cohort_index} AND protein_name='{identifier}' """
            elif patient_name:
                query = f"""SELECT patient_name,protein_name,value FROM expressionfpintensity WHERE cohort_id={cohort_index} AND patient_name='{patient_name}' """
            else:
                query = f"""SELECT patient_name,protein_name,value FROM expressionfpintensity WHERE cohort_id={cohort_index} """

            if identifier or patient_name:
                df = self._convert_query_to_df(models.Expressionfpintensity.raw(query))
                return self._post_process_query_result(df, data_type="full proteome")
            else:
                cohort_report_dir = self.config.get_report_directory(cohort_index)
                sample_annotations_df = self.get_sample_annotation_df(cohort_index)
                patient_list = sample_annotations_df['Sample name'].unique().tolist()
                return expression_loader.load_annotated_intensity_file(
                    Path(os.path.join(cohort_report_dir, settings.PREPROCESSED_FP_INTENSITY)),
                    settings.FP_KEY, patient_list
                )
        elif intensity_unit == utils.IntensityUnit.Z_SCORE:
            if identifier:
                query = f"""SELECT patient_name,protein_name,value FROM expressionfpzscores WHERE cohort_id={cohort_index} AND protein_name='{identifier}' """
            elif patient_name:
                query = f"""SELECT patient_name,protein_name,value FROM expressionfpzscores WHERE cohort_id={cohort_index} AND patient_name='{patient_name}' """
            else:
                query = f"""SELECT patient_name,protein_name,value FROM expressionfpzscores WHERE cohort_id={cohort_index} """

            if identifier or patient_name:
                df = self._convert_query_to_df(models.Expressionfpzscores.raw(query))
                return self._post_process_query_result(df, data_type="full proteome")
            else:
                cohort_report_dir = self.config.get_report_directory(cohort_index)
                return expression_loader.load_expression_data(
                    Path(cohort_report_dir), settings.FP_KEY, "full_proteome"
                )

    def get_psite_abundance_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier=None,
        patient_name=None,
    ) -> pd.DataFrame:
        if intensity_unit == utils.IntensityUnit.INTENSITY:
            if identifier:
                query = f"""SELECT patient_name,sequence,value FROM expressionppintensity WHERE cohort_id={cohort_index} AND sequence='{identifier}' """
            elif patient_name:
                query = f"""SELECT patient_name,protein_name,value FROM expressionppintensity WHERE cohort_id={cohort_index} AND patient_name='{patient_name}' """
            else:
                query = f"""SELECT patient_name,sequence,value FROM expressionppintensity WHERE cohort_id={cohort_index} """

            if identifier or patient_name:
                df = self._convert_query_to_df(models.Expressionppintensity.raw(query))
                return self._post_process_query_result(df, data_type="phospho")
            else:
                cohort_report_dir = self.config.get_report_directory(cohort_index)
                sample_annotations_df = self.get_sample_annotation_df(cohort_index)
                patient_list = sample_annotations_df['Sample name'].unique().tolist()
                return expression_loader.load_annotated_intensity_file(
                    Path(os.path.join(cohort_report_dir, settings.PREPROCESSED_PP_INTENSITY)),
                    settings.PP_KEY,patient_list
                )
        elif intensity_unit == utils.IntensityUnit.Z_SCORE:
            if identifier:
                query = f"""SELECT patient_name,sequence,value FROM expressionppzscores WHERE cohort_id={cohort_index} AND sequence='{identifier}' """
            elif patient_name:
                query = f"""SELECT patient_name,protein_name,value FROM expressionppzscores WHERE cohort_id={cohort_index} AND patient_name='{patient_name}' """
            else:
                query = f"""SELECT patient_name,sequence,value FROM expressionppzscores WHERE cohort_id={cohort_index} """

            if identifier or patient_name:
                df = self._convert_query_to_df(models.Expressionppzscores.raw(query))
                return self._post_process_query_result(df, data_type="phospho")
            else:
                cohort_report_dir = self.config.get_report_directory(cohort_index)
                return expression_loader.load_expression_data(
                    Path(cohort_report_dir), settings.PP_KEY, "phospho"
                )

    def _get_protein_peptide_mapping_df(self, cohort_index: str) -> pd.DataFrame:
        # TODO: add this as a join to get_psite_abundance_df()
        query = f"""SELECT gene_name,peptide,Proteins FROM modsequencetoprotein WHERE cohort_id={cohort_index} """
        df = self._convert_query_to_df(models.Modsequencetoprotein.raw(query))
        df.index = df["peptide"]
        df.columns = settings.PEPTIDE_PROTEIN_MAPPING_COLS.values()
        return df

    def _general_topas_query_obtainer(self, cohort_index, table_name, table_class):
        query = f"""SELECT patient_name,topas_name,value FROM {table_name} WHERE cohort_id={cohort_index} """
        df = self._convert_query_to_df(table_class.raw(query))
        df.columns = ["Sample name", "Topas_id", "Z-score"]
        df["Sample"] = df["Sample name"]
        return df

    def get_topas_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None],
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        if intensity_unit == utils.IntensityUnit.SCORE:
            return self._general_topas_query_obtainer(
                cohort_index, "topasscoresraw", models.Topasscoresraw
            )
        elif intensity_unit == utils.IntensityUnit.Z_SCORE:
            return self._general_topas_query_obtainer(
                cohort_index, "topaszscores", models.Topaszscores
            )
        else:
            raise ValueError(
                f"Cannot return topas scores for intensity unit {intensity_unit}"
            )

    def get_report_dir(self, cohort_index: str) -> str:
        cohortname = list(self.config.config["report_directory"].keys())[
            int(cohort_index)
        ]
        return self.config.config["report_directory"][cohortname]

    # TODO : Completing the DB models for the phospho scores and the kinase scores
    def get_phosphorylation_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None],
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        query = f"""SELECT patient_name,protein_name,value FROM phosphoscores WHERE cohort_id={cohort_index} """
        df = self._convert_query_to_df(models.Phosphoscores.raw(query))
        return self._post_process_query_result(
            df, data_type="full proteome", add_prefix=True
        )

    def get_kinase_scores_df(
        self,
        cohort_index: str,
        intensity_unit: Union[utils.IntensityUnit, None],
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        cohort_report_dir = self.get_report_dir(cohort_index)
        return self.provider.get_kinase_scores_dataframe(cohort_report_dir)

    """
    TODO: add special cases for load_FPKM and load_topas_annotation_tables in
    provider.get_dataframe. This way, we don't have to expose the dataframes directly.
    """

    def get_topas_annotation_df(self) -> pd.DataFrame:
        return self.provider.topas_complete_df

    def get_fpkm_df(
        self,
        cohort_index: Union[str, None] = None,
        intensity_unit: Union[utils.IntensityUnit, None] = None,
        identifier: str = None,
        patient_name: str = None,
    ) -> pd.DataFrame:
        fpkm_df = self.provider.FPKM
        if intensity_unit is not None:
            fpkm_df = in_memory.extract_columns_and_remove_suffix(
                fpkm_df, intensity_unit=intensity_unit
            )
        return fpkm_df

    def get_genomics(self) -> pd.DataFrame:
        return self.provider.genomics_data

    def get_oncoKB_annotations(self) -> dict:
        return self.provider.oncoKB_data
