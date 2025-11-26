import json
from pathlib import Path

from topas_portal import settings
from topas_portal import utils

# imports just for type hints
from logger import CohortLogger


def get_config_path():
    config_path = settings.PORTAL_CONFIG_FILE
    print(f"path to the config_file: {config_path}")
    return config_path


def load(config_path: str) -> dict:
    with open(config_path, "r") as f:
        config = json.load(f)
    return config


def write(config: dict, config_path: str) -> None:
    with open(config_path, "w+") as config_file:
        config_file.write(json.dumps(config, indent=4))


class CohortConfig:
    def __init__(self, config_file: str, logger: CohortLogger):
        self.config_path = config_file
        self.logger = logger
        self.reload_config()
        print(f"backend address: {self.get_local_http()}")

    def reload_config(self):
        self.cohort_names = self.get_cohort_names()
        print(self.cohort_names)

    def get_cohort_names(self) -> list[str]:
        self.config = load(self.config_path)
        return list(self.config["report_directory"].keys())

    def get_cohort_index(self, cohort_name: str) -> int:
        self.config = load(self.config_path)
        return self.cohort_names.index(cohort_name)

    def get_cohort_name(self, cohort_index: int) -> str:
        return self.get_cohort_names()[cohort_index]

    def get_cohort_index_from_report_directory(self, report_dir: str):
        self.config = load(self.config_path)

        # Iterate over the dictionary to find the key associated with the value
        for index, (key, value) in enumerate(self.config["report_directory"].items()):
            if value == report_dir:
                return index
        return -1  # Return -1 if the report_dir is not found

    def get_local_http(self) -> str:
        return self.config.get("local_http", "http://localhost:3832/")

    def get_integration_test_http(self) -> str:
        return self.config["local_http"]

    def get_oncokb_api_token(self) -> str:
        return self.config.get("oncokb_api_token", "")

    def get_config_path(self) -> str:
        return self.config_path

    def do_load_data_on_startup(self) -> str:
        return self.config.get("load_data_on_startup", False)

    def get_config(self):
        self.config = load(self.config_path)
        return self.config

    def add_new_cohort_placeholder(self, cohort_name: str):
        config = load(self.config_path)
        config["FP"][cohort_name] = 1
        config["PP"][cohort_name] = 1
        config["patient_annotation_path"][cohort_name] = "-"
        config["report_directory"][cohort_name] = "-"
        config["sample_annotation_path"][cohort_name] = "-"
        write(config, self.config_path)

        self.reload_config()
        self.logger.log_message(f"{cohort_name} added please update the config")

    def update_config_values(self, key: str, cohort_name: str, value: str):
        """Updates config.json on disk with newly submitted values."""
        config = load(self.config_path)

        new_value = value.replace("topas_slash", "/")
        config[key][cohort_name] = new_value
        write(config, self.config_path)

        self.reload_config()
        self.logger.log_message(
            f"{key} for {cohort_name} updated with value {new_value}"
        )

    def get_cache_directory(self) -> Path:
        return Path(self.config.get("cache_dir", "non_existent_path"))

    def get_report_directory(self, cohort_name: str) -> Path:
        """return path to the results folder"""
        return Path(self.config["report_directory"][cohort_name])

    def get_patients_metadata_path(self, cohort_name: str) -> Path:
        return Path(self.config["patient_annotation_path"][cohort_name])

    def get_sample_annotation_path(self, cohort_name: str) -> Path:
        return Path(self.config["sample_annotation_path"][cohort_name])

    def get_search_qc_paths(self, cohort_name: str) -> tuple[Path, Path]:
        report_dir = self.get_report_directory(cohort_name)
        return (
            report_dir / settings.SEARCH_QC_FILE_FP,
            report_dir / settings.SEARCH_QC_FILE_PP,
        )

    def has_fp(self, cohort_name: str) -> bool:
        return self.config["FP"].get(cohort_name, 0) == 1

    def get_fp_annotated_intensity_path(self, cohort_name: str) -> Path:
        if not self.has_fp(cohort_name):
            return None

        return (
            Path(self.config["report_directory"][cohort_name])
            / settings.PREPROCESSED_FP_INTENSITY
        )

    def get_fp_data_paths(self, cohort_name: str) -> tuple[Path, Path, Path, Path]:
        fp_data_paths = [self.get_fp_annotated_intensity_path(cohort_name)]
        report_dir = self.get_report_directory(cohort_name)
        for intensity_unit in [
            utils.IntensityUnit.FOLD_CHANGE,
            utils.IntensityUnit.Z_SCORE,
            utils.IntensityUnit.RANK,
            utils.IntensityUnit.BATCH_RANK,
        ]:
            fp_data_paths.append(
                report_dir
                / f"full_proteome_measures{utils.INTENSITY_UNIT_FILE_SUFFIXES[intensity_unit]}.tsv"
            )
        return tuple(fp_data_paths)

    def get_pp_annotated_intensity_path(self, cohort_name: str) -> Path:
        if not self.has_pp(cohort_name):
            return None

        return (
            Path(self.config["report_directory"][cohort_name])
            / settings.PREPROCESSED_PP_INTENSITY
        )

    def get_pp_data_paths(self, cohort_name: str) -> tuple[Path, Path, Path, Path]:
        pp_data_paths = [self.get_pp_annotated_intensity_path(cohort_name)]
        report_dir = self.get_report_directory(cohort_name)
        for intensity_unit in [
            utils.IntensityUnit.FOLD_CHANGE,
            utils.IntensityUnit.Z_SCORE,
            utils.IntensityUnit.RANK,
            utils.IntensityUnit.BATCH_RANK,
        ]:
            pp_data_paths.append(
                report_dir
                / f"phospho_measures{utils.INTENSITY_UNIT_FILE_SUFFIXES[intensity_unit]}.tsv"
            )
        return tuple(pp_data_paths)

    def has_pp(self, cohort_name: str) -> bool:
        return self.config["PP"].get(cohort_name, 0) == 1

    def get_transcriptomics_paths(self, cohort_name: str) -> tuple[Path, Path]:
        return (
            Path(self.config["transcriptomics_path_z_scored"]),
            Path(self.config["transcriptomics_path_not_z_scored"]),
        )

    def get_topas_rtk_scores_paths(self, cohort_name: str) -> tuple[Path, Path]:
        report_dir = self.get_report_directory(cohort_name)
        return (
            report_dir / settings.TOPAS_RTK_SCORES_FILE,
            report_dir / settings.TOPAS_RTK_Z_SCORES_FILE,
        )

    def get_topas_ck_scores_path(self, cohort_name: str) -> Path:
        report_dir = self.get_report_directory(cohort_name)
        return report_dir / settings.TOPAS_CK_SCORES_FILE

    def get_topas_rtk_substrate_phos_scores_path(self, cohort_name: str) -> Path:
        report_dir = self.get_report_directory(cohort_name)
        return report_dir / settings.KINASE_SCORES_FILE

    def get_topas_substrate_phos_paths(self, cohort_name: str) -> tuple[Path, Path]:
        return self.get_topas_rtk_substrate_phos_scores_path(
            cohort_name
        ), self.get_topas_ck_scores_path(cohort_name)

    def get_protein_phosphorylation_scores_path(self, cohort_name: str) -> Path:
        report_dir = self.get_report_directory(cohort_name)
        return report_dir / settings.PHOSPHORYLATION_Z_SCORES

    def get_protein_phos_data_paths(
        self, cohort_name: str
    ) -> tuple[Path, Path, Path, Path]:
        protein_phos_data_paths = [
            self.get_protein_phosphorylation_scores_path(cohort_name)
        ]
        report_dir = self.get_report_directory(cohort_name)
        for intensity_unit in [
            utils.IntensityUnit.RANK,
            utils.IntensityUnit.BATCH_RANK,
        ]:
            protein_phos_data_paths.append(
                report_dir
                / f"phospho_score_measures{utils.INTENSITY_UNIT_FILE_SUFFIXES[intensity_unit]}.tsv"
            )
        return tuple(protein_phos_data_paths)

    def get_genomics_path(self, cohort_name: str) -> Path:
        return Path(self.config["genomics_path"])

    def get_poi_annotation_path(self) -> Path:
        return Path(self.config["poi_annotation_path"])

    def get_topas_annotation_path(self) -> Path:
        return Path(self.config["basket_annotation_path"])

    def get_oncokb_annotation_path(self) -> Path:
        return Path(self.config["oncokb_path"])

    def get_drug_annotation_path(self) -> Path:
        return Path(self.config["drug_annotation_path"])

    def get_input_file_paths(
        self, cohort_name: str, data_type: utils.DataType
    ) -> list[Path]:
        """For the caching functionality"""
        input_file_dict = {
            utils.DataType.TRANSCRIPTOMICS: self.get_transcriptomics_paths,
            utils.DataType.GENOMICS: self.get_genomics_path,
            utils.DataType.FULL_PROTEOME: self.get_fp_data_paths,
            utils.DataType.PHOSPHO_PROTEOME: self.get_pp_data_paths,
            utils.DataType.TOPAS_RTK_SCORE: self.get_topas_rtk_scores_paths,
            utils.DataType.TOPAS_CK_SCORE: self.get_topas_ck_scores_path,
            utils.DataType.KINASE_SCORE: self.get_topas_substrate_phos_paths,
            utils.DataType.PHOSPHO_SCORE: self.get_protein_phos_data_paths,
        }
        input_files = input_file_dict[data_type](cohort_name)
        if isinstance(input_files, tuple):
            return [Path(p) for p in input_files]
        return [Path(input_files)]
