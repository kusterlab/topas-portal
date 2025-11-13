import os
import datetime
import json

DATABASE_MODE = False  # True means using Postgres, False means in-memory
DEBUG_MODE = False

PASSWORD = os.getenv(
    "DB_PASSWORD"
)  # this should be either in the environmental variables or in CI/CD or docker compose file

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "topas_portal_is_so_cool")
JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=1)

PRDB_HOST = "https://proteomicsdb.org"
ENRICHMENT_SERVER_HOST = "https://enrichment.kusterlab.org/main_enrichment-server"

# path to the config file, this should be either in the environmental variables or in CI/CD or docker compose file
PORTAL_CONFIG_FILE = os.getenv("CONFIG_FILE_PATH")
if PORTAL_CONFIG_FILE is None:
    raise ValueError("No CONFIG_FILE_PATH environment variable found")

PORTAL_LOG_FILE = "record.log"

CI_BACKEND_PORT = os.getenv("CI_BACKEND_PORT", default=3832)

# the chunked data size for import to DB (10000000) was tested with 512 GB RAM
CHUNK_SIZE_IMPORT = 1000000

PATIENT_PREFIX = "pat_"
REF_CHANNEL_PREFIX = "ref_"
IDENTIFICATION_METADATA_PREFIX = "Identification metadata "

PP_KEY = "Modified sequence"
FP_KEY = "Gene names"

# REGEX PATTERNS FOR THE PATIENTS IDS
# patient identifiers

Z_SCORE_REGEX = r" Z-score"
REGEX_META = (
    r"^Identification metadata"  # to get num identified peptides in FP intensity file
)
NUM_PEPTIDES_REGEX = r"num_peptides=(\d+)"

# PATIENT DATA FILES (Paths are relative to the results folder root)

# normalized intensities with gene/p-site annotations from wp3 pipeline
# includes topas (FP, PP) and PSP annotations (PP)
PREPROCESSED_FP_INTENSITY = "annot_fp.csv"
PREPROCESSED_PP_INTENSITY = "annot_pp.csv"

# phosphorylation scores from wp2 pipeline (FH)
PHOSPHORYLATION_SCORES = "topas_scores/protein_phosphorylation_scores.tsv"

# Drug scores from wp2 pipeline (FH)
DRUG_SCORES = "drug_results/drug_scores.tsv"

TOPAS_CK_SCORES_FILE = "topas_scores/ck_substrate_phosphorylation_scores_expressioncorrected.tsv"  # already z-scored
KINASE_SCORES_FILE = (
    "topas_scores/rtk_substrate_phosphorylation_scores.tsv"  # already z-scored
)

#
TOPAS_SUBSCORE_FILES_PREFIX = "topas_scores/subbasket_scores_"
TOPAS_RTK_SCORES_FILE = "topas_scores/topas_rtk_scores.tsv"
TOPAS_RTK_Z_SCORES_FILE = "topas_scores/topas_rtk_scores_zscored.tsv"


# pp z_scores
PHOSPHO_MEASURES = "phospho_measures_z.tsv"

# meta data entity column
ENTITY_COLUMN = "code_oncotree"

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


# TODO: refactor this, if they need to be loaded from a config it means they are not constants...
def load_json(config_path: str) -> dict:
    with open(config_path, "r") as f:
        config = json.load(f)
    return config


# getting the list of meta data columns for devextreme table
main_config = load_json(PORTAL_CONFIG_FILE)
meta_columns_json = load_json(main_config["meta_data_columns_config"])
front_end_col_names = meta_columns_json["front_end_col_names"]
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
    "fusion_onkoKB",
    "cnv_onkoKB",
    "snv_onkoKB",
    "snv",
    "fusion",
    "cnv",
    "oncoKB_annotations",
    "is_replicate",
    "FC",
]

ANNOTATION_COLUMNS = {
    "Gene names": "Gene names",
    "Proteins": "Proteins",
    "Occurrence": "Occurrence",
    "PSP Kinases": "Kinases (PSP)",
    "POI_REPORT": "POI_REPORT",
    "POI_EXPLORATORY": "POI_EXPLORATORY",
    "POI_PRODICT": "POI_PRODICT",
    "Site positions identified (MQ)": "Site positions (MQ identified - PSP)",
    "Site positions": "Site positions (PSP)",
    "PSP_ON_FUNCTION": "Effects on Modified Protein (PSP)",
    "PSP_ON_PROCESS": "Effects on Biological Process (PSP)",
    "PSP_ON_PROT_INTERACT": "Induce interaction with protein (PSP)",
    "PSP_ON_OTHER_INTERACT": "Induce interaction with other (PSP)",
    "PSP_LT_LIT": "Low throughput studies (PSP)",
    "PSP_MS_LIT": "High throughput studies (PSP)",
}
