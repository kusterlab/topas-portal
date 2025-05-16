from pathlib import Path
import json

import topas_portal.settings as cn
import topas_portal.utils as utils

# imports just for type hints
from logger import CohortLogger


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
        self.config = utils.config_reader(self.config_path)
        return list(self.config["report_directory"].keys())

    def get_cohort_index(self, cohort_name: str) -> int:
        self.config = utils.config_reader(self.config_path)
        return self.cohort_names.index(cohort_name)

    def get_cohort_index_from_report_directory(self, report_dir: str):
        self.config = utils.config_reader(self.config_path)
    
        # Iterate over the dictionary to find the key associated with the value
        for index, (key, value) in enumerate(self.config["report_directory"].items()):
            if value == report_dir:
                return index
        return -1  # Return -1 if the report_dir is not found


    def get_local_http(self) -> str:
        return self.config.get("local_http", "http://localhost:3832/")
    
    def get_integration_test_http(self) -> str:
        return self.config['local_http']

    def get_config_path(self) -> str:
        return self.config_path

    def get_config(self):
        self.config = utils.config_reader(self.config_path)
        return self.config

    def add_new_cohort_placeholder(self,cohort_name:str):
        config = utils.config_reader(self.config_path)
        config['FP'][cohort_name] = 1
        config['PP'][cohort_name] = 1
        config['patient_annotation_path'][cohort_name] = '-'
        config['report_directory'][cohort_name] = '-'
        config['sample_annotation_path'][cohort_name] = '-'
        with open(self.config_path, "w+") as jsonFile:
            jsonFile.write(json.dumps(config, indent=4))
        self.reload_config()
        self.logger.log_message(
            f"{cohort_name} added please update the config"
        )



    def update_config_values(self, key: str, cohort_name: str, value: str):
        """Updates config.json on disk with newly submitted values."""
        with open(self.config_path, "r") as jsonFile:
            config = json.load(jsonFile)

        new_value = value.replace("topas_slash", "/")
        config[key][cohort_name] = new_value

        with open(self.config_path, "w+") as jsonFile:
            jsonFile.write(json.dumps(config, indent=4))

        self.reload_config()
        self.logger.log_message(
            f"{key} for {cohort_name} updated with value {new_value}"
        )

    def get_report_directory(self, cohort_index) -> str:
        """ return path to the results folder"""
        return list(self.config["report_directory"].values())[int(cohort_index)]

    def get_PP_directory(self, cohort_index) -> str:
        """The path to the  MQ search folder for PP"""
        return list(self.config["PP_directory"].values())[int(cohort_index)]

    def get_FP_directory(self, cohort_index) -> str:
        """The path to the  MQ search folder for FP"""
        return list(self.config["FP_directory"].values())[int(cohort_index)]

    def get_patients_metadata_path(self, cohort_index) -> str:
        return list(self.config["patient_annotation_path"].values())[int(cohort_index)]

    def get_sample_annotation_path(self, cohort_index) -> str:
        return list(self.config["sample_annotation_path"].values())[int(cohort_index)]

    def get_basket_annotation_path(self) -> str:
        return self.config["basket_annotation_path"]
    
    def get_drug_annotation_path(self) -> str:
        return self.config["drug_annotation_path"]


def get_config_path():
    config_path = cn.PORTAL_CONFIG_FILE
    print(f"path to the config_file: {config_path}")
    return config_path
