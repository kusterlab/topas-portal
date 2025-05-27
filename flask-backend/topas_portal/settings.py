import os
from topas_portal.config_reader import *


DATABASE_MODE = False  # True means using Postgres, False means in-memory
DEBUG_MODE = False 

PASSWORD = os.getenv("DB_PASSWORD")  # this should be either in the environmental variables or in CI/CD or docker compose file

# path to the config file, this should be either in the environmental variables or in CI/CD or docker compose file
PORTAL_CONFIG_FILE = os.getenv("CONFIG_FILE_PATH")
if PORTAL_CONFIG_FILE is None:
    raise ValueError("No PORTAL_CONFIG_FILE environment variable found")

PORTAL_LOG_FILE = "record.log"

CI_BACKEND_PORT = os.getenv("CI_BACKEND_PORT", default=3832)

# the chunked data size for import to DB (10000000) was tested with 512 GB RAM
CHUNK_SIZE_IMPORT = 1000000

PATIENT_PREFIX = "pat_"
REF_CHANNEL_PREFIX = "ref_"

PP_KEY = "Modified sequence"
FP_KEY = "Gene names"

# REGEX PATTERNS FOR THE PATIENTS IDS
# patient identifiers

Z_SCORE_REGEX = (
    r" Z-score"
)
REGEX_META = (
    r"^Identification metadata"  # to get num identified pepetides in FP intensity file
)

# normalized intensities with gene/p-site annotations from wp3 pipeline
# includes topas (FP, PP) and PSP annotations (PP)
PREPROCESSED_FP_INTENSITY = "annot_fp.csv"
PREPROCESSED_PP_INTENSITY = "annot_pp.csv"

# phosphorylation scores from wp2 pipeline (FH)
PHOSPHORYLATION_SCORES = "protein_results/protein_scores.tsv"

# Drug scores from wp2 pipeline (FH)
DRUG_SCORES = "drug_results/drug_scores.tsv"

# meta data entity column
ENTITY_COLUMN = "code_oncotree"


# THE FILES WITH RESPECT TO THE MAIN RESULT FOLDER
KINASE_SCORES_FILE = "kinase_results/kinase_scores.tsv"
KINASE_PEPTIDES_SCORES = "kinase_results/scored_peptides.tsv"

#
TOPAS_SUBSCORE_FILES_PREFIX = "subbasket_scores_"
TOPAS_SCORES_FILE = "basket_scores_4th_gen.tsv"
TOPAS_Z_SCORES_FILE = "basket_scores_4th_gen_zscored.tsv"

# pp z_scores
PHOSPHO_MEASURES = "phospho_measures_z.tsv"

PEPTIDE_PROTEIN_MAPPING_COLS = {
    "gene_name": "Gene names",
    "peptide": "Modified sequence",
    "Proteins": "Proteins",
}

# the columns names to load before merging with metadata from sample annotation file
# the idea of this file is to keep the batch information for the Replicates
# ** IN CASE THE COLUMNS NAMES OF THE ANNOTATION FILE WAS CHAGNED CHANGE THE KEYs the VALUES ARE HARDCODED IN THE BACKEND and Models of the database
SAMPLE_ANNOTATION = {
    "Sample name": "Sample name",
    "Histologic Subtype": "Entity",
    "Batch Name": "Batch_No",
    "TMT Channel": "TMT_channel",
    "QC": "QC",
}


# getting the list of meta data columns for devextreme table
main_config = config_reader(PORTAL_CONFIG_FILE)
meta_columns_json = config_reader(main_config['meta_data_columns_config'])
front_end_col_names = meta_columns_json['front_end_col_names']
COMMON_META_DATA = [x["dataField"] for x in front_end_col_names]

# add number type columns for -1 replacement of NaN values
PATIENT_TABLE_NAN_INT = ["FC", "Batch_No", "TMT_channel", "AH_PGE2 signature score"]


# add string columns for n.d. replacement of NaN values
PATIENT_TABLE_NAN_STRING = [
    "Sample name",
    *COMMON_META_DATA,
    "patient_id",
    "Localisation",
]


############## DIFFERENT TABS meta data ##########
#  Topas scores tab
TOPAS_META_DATA = [
    "Sample name",
    "Z-score",
    *COMMON_META_DATA,
    "Localisation",
    "TMT_channel",
    "Batch_No",
]

# Differential expresson tab
PATIENTS_META_DATA = [*COMMON_META_DATA, "Sample name"]

# QC tab
QC_STRING_META = [*COMMON_META_DATA, "Sample", "Localisation", "TMT_channel"]

QC_INT_META = [
    "Batch_No"
]  # this field should come from the annotation file NOT METADATA

QC_PCS = ["pc1", "pc2"]

# expression tab
EXPRESSION_TAB_DATA = [
    "Sample name",
    "Z-score",
    "Intensity",
    "Rank",
    "Batch_No",
    *COMMON_META_DATA,
    "confidence_score",
    "ICD03 - Morpho",
    "TMT_channel",
    "Occurrence",
    "colorID",
    "sizeR",
    "num_pep",
    "genomics_annotations",
    "oncoKB_annotations",
    "is_replicate",
    "FC",
]

PP_EXTRA_COLUMNS = [
    "Gene names",
    "Proteins",
    "PSP Kinases",
    "Site positions identified (MQ)",
]
