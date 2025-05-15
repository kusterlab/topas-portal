import topas_portal.settings as cn
import topas_portal.utils as ef
from app import app  # Flask instance of the API

import json
import os
import pandas as pd


def test_portal_main_config_exist():

    assert os.path.exists(cn.PORTAL_CONFIG_FILE)


def _config_cheker(path_to_check: str, type_to_check="dictionary"):
    """To check if the file in tha main config file exist"""

    if type_to_check == "dictionary":
        assert type(path_to_check) is dict
        for key in path_to_check.keys():
            print(path_to_check[key])
            assert os.path.exists(path_to_check[key])
    else:
        print(path_to_check)
        assert os.path.exists(path_to_check)


def test_config_cohorts():
    """
    Checking all items in the config path

    """
    response = app.test_client().get("/config")
    assert response.status_code == 200

    for config_key_dictionaries in [
        "report_directory",
        "sample_annotation_path",
        "patient_annotation_path",
    ]:

        res = json.loads(response.data.decode("utf-8")).get(config_key_dictionaries)
        _config_cheker(res)
    for config_key_list in [
        "drug_annotation_path",
        "transcriptomics_path_not_z_scored",
        "transcriptomics_path_z_scored",
        "basket_annotation_path",
    ]:
        res = json.loads(response.data.decode("utf-8")).get(config_key_list)
        _config_cheker(res, type_to_check="list")


def test_cohort_names():
    """TO check whether the cohorts endpoint work"""
    response = app.test_client().get("/cohort_names")
    assert response.status_code == 200


def _check_colnames_between_config_and_setting(
    key=cn.PATIENTS_META_DATA, file_to_check="patient_annotation_path"
):
    """check to see all columns refering to patients meta data are in the files of the related cohorts"""
    response = app.test_client().get("/config")
    config_file_path_keys = json.loads(response.data.decode("utf-8")).get(file_to_check)
    for k in config_file_path_keys.keys():
        meta_data_file = pd.read_excel(config_file_path_keys[k])
        col_names = meta_data_file.columns.to_list()
        print(ef.setdiff(key, col_names))
        assert set(key).issubset(col_names)


def test_check_patients_meta_data():
    _check_colnames_between_config_and_setting(
        key=cn.PATIENTS_META_DATA, file_to_check="patient_annotation_path"
    )


# TODO
# list of the files to be checked in each of the report_directory
# full_proteome_measures_fc.tsv
# full_proteome_measures_z.tsv
# phospho_measures_z.tsv
# phospho_measures_fc.tsv
# preprocessed_fp.csv
# preprocessed_pp.csv
# topas_scores_4th_gen
