# import pandas as pd

# from pathlib import Path
# from flask import Blueprint

# import db
# import topas_portal.utils as ef
# import topas_portal.settings as cn
# import topas_portal.prexp_preprocess as data_loader


# drugscore_page = Blueprint(
#     "drugscore_page",
#     __name__,
#     static_folder="../dist/static",
#     template_folder="../dist",
# )

# cohorts_db = db.cohorts_db


# def load_drug_scores_df(drug_scores_path):
#     def filter_columns(x):
#         return x.startswith("Drug") or not (
#             x.startswith("targets_") or x.startswith("mean") or x.startswith("stdev")
#         )

#     drug_scores_df = pd.read_csv(drug_scores_path, sep="\t", usecols=filter_columns)
#     drug_scores_df = drug_scores_df.set_index("Drug")
#     drug_scores_df = drug_scores_df.filter(regex=cn.REGEX)
#     return drug_scores_df


# def post_process_drug_scores_df(drug_scores_single_df):
#     drug_scores_single_df.columns = ["Drug_score"]
#     drug_scores_single_df["Sample name"] = drug_scores_single_df.index
#     drug_scores_single_df["is_replicate"] = (
#         drug_scores_single_df["Sample name"].str.split("-").str[-1]
#     )
#     # not replicates
#     drug_scores_single_df.is_replicate[
#         ~drug_scores_single_df["is_replicate"].str.contains("R")
#     ] = "not_replicate"
#     return drug_scores_single_df


# def get_single_drug_scores_df_per_drug(
#     drug_scores_path: str, drug_name: str
# ) -> pd.DataFrame:
#     drug_df = load_drug_scores_df(drug_scores_path).transpose()
#     drug_single_df = drug_df[[drug_name]]
#     drug_single_df = drug_single_df[[str(drug_name)]]
#     drug_single_df = post_process_drug_scores_df(drug_single_df)
#     return drug_single_df


# def get_single_drug_scores_df_per_patient(
#     drug_scores_path: str, patient_name: str
# ) -> pd.DataFrame:
#     drug_scores_df = load_drug_scores_df(drug_scores_path)
#     drug_scores_single_df = drug_scores_df[[str(patient_name)]]
#     drug_scores_single_df = post_process_drug_scores_df(drug_scores_single_df)
#     return drug_scores_single_df


# def get_patients(config, cohort_index: int):
#     """Gives the list of the patients"""
#     reports_dir = list(config["report_directory"].values())[int(cohort_index)]
#     drug_scores_path = Path(reports_dir) / Path(cn.DRUG_SCORES)
#     drug_scores_df = load_drug_scores_df(drug_scores_path)
#     return ef.df_to_json(pd.DataFrame(drug_scores_df.columns, columns=["patients"]))


# def get_drugs(config, cohort_index: int):
#     """Gives the list of the drugs"""
#     reports_dir = list(config["report_directory"].values())[int(cohort_index)]
#     drug_scores_path = Path(reports_dir) / Path(cn.DRUG_SCORES)
#     drug_scores_df = load_drug_scores_df(drug_scores_path)
#     return ef.df_to_json(pd.DataFrame(drug_scores_df.index))


# def get_drug_score_entities(config, cohort_index):
#     patient_annotation_path = list(config["patient_annotation_path"].values())[
#         int(cohort_index)
#     ]
#     patients_df = data_loader.load_patient_table(patient_annotation_path)
#     df = df_fixer(patients_df)
#     df = pd.DataFrame(df[cn.ENTITY_COLUMN].unique(), columns=["Entity"])
#     return ef.df_to_json(df)


# def get_drug_scores_for_all_patients(
#     config, cohort_index: int, item_name: str, entities: list, drug_patient="drug"
# ):
#     """Gets the drug scores for all patients for one drug name as a  json file"""
#     reports_dir = list(config["report_directory"].values())[int(cohort_index)]
#     sample_annotation_path = list(config["sample_annotation_path"].values())[
#         int(cohort_index)
#     ]
#     patient_annotation_path = list(config["patient_annotation_path"].values())[
#         int(cohort_index)
#     ]
#     patients_df = data_loader.load_patient_table(patient_annotation_path)
#     sample_annotation_df = data_loader.load_sample_annotation_table(
#         sample_annotation_path
#     )
#     drug_scores_path = Path(reports_dir) / Path(cn.DRUG_SCORES)
#     if drug_patient == "patient":
#         drug_scores_single_df = get_single_drug_scores_df_per_patient(
#             drug_scores_path, item_name
#         )
#     else:
#         drug_scores_single_df = get_single_drug_scores_df_per_drug(
#             drug_scores_path, item_name
#         )
#         drug_scores_single_df = drug_scores_single_df.merge(
#             sample_annotation_df, on="Sample name", how="left"
#         )
#         if "Batch_No" in patients_df.columns:
#             patients_df.drop("Batch_No", inplace=True, axis=1)

#         drug_scores_single_df["Sample_name_rep_truncated"] = drug_scores_single_df[
#             "Sample name"
#         ].str.replace(r"-R[0-9]$", "", regex=True)
#         new_patients_df = patients_df.rename(columns={"Sample name": "patient_id"})
#         drug_scores_single_df = drug_scores_single_df.merge(
#             new_patients_df,
#             left_on="Sample_name_rep_truncated",
#             right_on="patient_id",
#             how="left",
#         )
#         drug_scores_single_df = df_fixer(drug_scores_single_df)
#         if not entities[0] == "all":
#             drug_scores_single_df = drug_scores_single_df[
#                 drug_scores_single_df[cn.ENTITY_COLUMN].isin(entities)
#             ]

#     drug_scores_single_df = drug_scores_single_df.fillna(
#         "n.d."
#     )  # DO NOT CHANGE THIS LINE; FRONTEND USE THIS
#     drug_scores_single_df = drug_scores_single_df.reset_index()
#     drug_scores_single_df["index"] = drug_scores_single_df.index
#     drug_scores_single_df["colorID"] = "grey"
#     drug_scores_single_df["sizeR"] = 3
#     return ef.df_to_json(drug_scores_single_df)


# def df_fixer(df: pd.DataFrame) -> pd.DataFrame:
#     df[cn.ENTITY_COLUMN] = df[cn.ENTITY_COLUMN].str.replace(r" ", "", regex=True)
#     df[cn.ENTITY_COLUMN] = df[cn.ENTITY_COLUMN].str.replace(r",", "_", regex=True)
#     df[cn.ENTITY_COLUMN] = df[cn.ENTITY_COLUMN].str.replace(r";", "_", regex=True)
#     return df


# #### drug_scores routing functions
# @drugscore_page.route("/drugscore/<cohort_ind>/all_entities")
# def get_entities_per_cohort(cohort_ind):
#     return get_drug_score_entities(cohorts_db.config.get_config(), cohort_ind)


# @drugscore_page.route("/drugscore/<cohort_ind>/drug/<drug_name>/<entities>")
# # http://localhost:3832/drugscore/0/drug/Alectinib
# def get_drug_scores_per_drug(cohort_ind, drug_name, entities):
#     """The list of metadata to show in the QC coloring combobox"""
#     entities = str(entities).split(",")
#     print(entities)
#     return get_drug_scores_for_all_patients(
#         cohorts_db.config.get_config(), cohort_ind, drug_name, entities, "drug"
#     )


# @drugscore_page.route("/drugscore/<cohort_ind>/patient/<patient_name>")
# # http://localhost:3832/drugscore/0/patient/H021-13A4TF-M1
# def get_drug_scores_per_patient(cohort_ind, patient_name):
#     """The list of metadata to show in the QC coloring combobox"""
#     entities = []
#     return get_drug_scores_for_all_patients(
#         cohorts_db.config.get_config(), cohort_ind, patient_name, entities, "patient"
#     )


# @drugscore_page.route("/drugscore/<cohort_ind>/patients_list")
# # http://localhost:3832/drugscore/0/patients_list
# def get_drug_patients_list(cohort_ind):
#     """The list of metadata to show in the QC coloring combobox"""
#     return get_patients(cohorts_db.config.get_config(), cohort_ind)


# @drugscore_page.route("/drugscore/<cohort_ind>/drugs_list")
# # http://localhost:3832/drugscore/0/drugs_list
# def get_drug_drug_list(cohort_ind):
#     """The list of metadata to show in the QC coloring combobox"""
#     return get_drugs(cohorts_db.config.get_config(), cohort_ind)
