import os
import json
import urllib.request
import random

import pandas as pd

from topas_portal import settings
from topas_portal import utils
import topas_portal.databases.in_memory as cl

def check_portal_main_config_exist(config):
    if os.path.exists(config):
        return "The main config file of the portal exists"
    else:
        return f"{config} does not exist"


def check_integretability_cohort(cohort):
    final_msg = []

    config = utils.config_reader(settings.PORTAL_CONFIG_FILE)
    try:
        all_data = cl._load_all_tables(cohort, config)
        if len(all_data[utils.DataType.PATIENT_METADATA].columns) > 0 & set(
            all_data[utils.DataType.PATIENT_METADATA].columns
        ).issubset(settings.PATIENTS_META_DATA):
            final_msg.append(f"{cohort}:The patients_meta_data_columns_matching")
        else:
            final_msg.append(f"{cohort}:The columns mismatch in patients data")
        
        if len(all_data[utils.DataType.SAMPLE_ANNOTATION].columns) > 0 & set(
            all_data[utils.DataType.SAMPLE_ANNOTATION].columns
        ).issubset(settings.SAMPLE_ANNOTATION):
            final_msg.append(f"{cohort}:The sample_annotation_data_columns_matching")
        else:
            final_msg.append(f"{cohort}:The columns mismatch in sample annotation file")
        
        num_patients = str(
            len(all_data[utils.DataType.PHOSPHO_SCORE].filter(regex=settings.Z_SCORE_REGEX).columns)
        )
        final_msg.append(f"Number_patients_in_phospho_scores:{num_patients}")
        num_patients = str(
            len(all_data[utils.DataType.PHOSPHO_PROTEOME].filter(regex=settings.Z_SCORE_REGEX).columns)
        )
        final_msg.append(f"Number_patients_in_pp_df_patientes:{num_patients}")
        num_patients = str(
            len(all_data[utils.DataType.FULL_PROTEOME].filter(regex=settings.Z_SCORE_REGEX).columns)
        )
        final_msg.append(f"Number_patients_in_fp_df_patients:{num_patients}")
    # needs more tests for   topas_df_z_scored
    except IOError as e:
        final_msg.append(e)
    return (" topas_separator ").join(final_msg)


def endpoint_reader(LOCAL_HTTTP, endpoint="0/protein/abundance/EGFR/Z-score"):
    adress = f"{LOCAL_HTTTP}/{endpoint}"
    print(adress)
    try:

        with urllib.request.urlopen(adress) as url:
            data = url.read()
        res = json.loads(data)
        return res
    except Exception as err:
        print(f'error{err} in running the url {adress}')


def z_score_checker(PORTAL_CONFIG_FILE, LOCAL_HTTTP, cohort, protein_name="EGFR"):
    """
    Checks the validity of z_score for a protein in the specific cohort for a random patient
    :cohort: the name of the cohort
    :protein_name: protein name
    """
    config = utils.config_reader(PORTAL_CONFIG_FILE)
    report_dir = config["report_directory"][cohort]
    list_cohorts = list(config["report_directory"].keys())
    cohort_index = get_cohort_index(cohort, list_cohorts)
    expresison_z_scores = endpoint_reader(
        LOCAL_HTTTP,
        endpoint=f"{cohort_index}/protein/abundance/{protein_name}/noimpute"
    )
    print(expresison_z_scores)
    random_index_patient = random.randint(0, len(expresison_z_scores) - 1)
    patient_sample_name = expresison_z_scores[random_index_patient]["Sample name"]
    portal_z_score = expresison_z_scores[random_index_patient]["Z-score"]
    patient_sample_name = f"zscore_{settings.PATIENT_PREFIX}{patient_sample_name}"
    pipeline_data = pd.read_csv(
        f"{report_dir}/full_proteome_measures_z.tsv",
        usecols=[settings.FP_KEY, patient_sample_name],
        sep="\t",
    )
    pipeline_z_score = pipeline_data[patient_sample_name][
        pipeline_data[settings.FP_KEY] == protein_name
    ]
    # pipeline_z_score = pd.to_numeric(pipeline_z_score,errors='coerce')
    print(type(pipeline_z_score))
    print(type(portal_z_score))
    res = pipeline_z_score == portal_z_score
    res_df = pd.DataFrame(res)
    res_df["cohort"] = cohort
    res_df["protein"] = protein_name
    res_df["portal_z_score"] = portal_z_score
    res_df["pipeline_z_score"] = pipeline_z_score
    return res_df


def topas_score_checker(PORTAL_CONFIG_FILE, LOCAL_HTTTP, cohort, topas_name="ABL"):
    """
    Checks the validity of the topas-scores for a specific topas name
    :cohort: the name of the cohort
    :topas_name: topas name
    """
    print(PORTAL_CONFIG_FILE)
    config = utils.config_reader(PORTAL_CONFIG_FILE)
    report_dir = config["report_directory"][cohort]
    list_cohorts = list(config["report_directory"].keys())
    cohort_index = get_cohort_index(cohort, list_cohorts)
    end_point = f"/topas/{cohort_index}/{topas_name}/topas_score"
    topas_z_scores = endpoint_reader(LOCAL_HTTTP, endpoint=end_point)
    random_index_patient = random.randint(0, len(topas_z_scores) - 1)
    patient_sample_name = topas_z_scores[random_index_patient]["Sample name"]
    patient_sample_name = f'{settings.PATIENT_PREFIX}{patient_sample_name}'
    portal_z_score = topas_z_scores[random_index_patient]["Z-score"]
    topas_scores = os.path.join(report_dir, settings.TOPAS_SCORES_FILE)
    topas_scores_df = pd.read_csv(topas_scores, sep="\t", index_col="Sample")
    print("####")
    pipeline_topas_score = topas_scores_df.loc[patient_sample_name, topas_name]
    print(type(portal_z_score))
    print(portal_z_score)
    res_df = pd.DataFrame([portal_z_score], columns=["portal_z_score"])
    res_df["cohort"] = cohort
    res_df["protein"] = topas_name
    res_df["pipeline_z_score"] = pipeline_topas_score
    print(res_df)
    return res_df


def get_cohort_index(cohort: str, all_cohorts: list):
    """
    Gets the index for the current cohort from a list of the cohorts
    """
    ind = 100  # the index for the cohort supposed to be updated
    for j, cohortName in enumerate(all_cohorts):
        if cohort == cohortName:
            ind = j
    return ind
