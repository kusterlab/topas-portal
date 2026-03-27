from enum import Enum

# the corresponding constants are automatically updated in vue-frontend/src/constants.js


class ColumnNames(str, Enum):
    SAMPLE_NAME = "Sample name"
    GENE_NAME = "Gene names"


class SampleFilter(str, Enum):
    ALL = "all"
    PATIENTS_AND_EXCLUDED = "pat_and_excl"
    PATIENTS_AND_REF = "pat_and_ref"
    ONLY_PATIENTS = "only_pat"
    ONLY_REF = "only_ref"


class ImputationMode(str, Enum):
    NO_IMPUTE = "noimpute"
    IMPUTE = "impute"


class IntensityUnit(str, Enum):
    INTENSITY = "intensity"
    Z_SCORE = "z_scored"
    FOLD_CHANGE = "fc"
    RANK = "rank"
    BATCH_RANK = "batchrank"
    SCORE = "score"
    IDENTIFICATION_METADATA = "identification_metadata"


INTENSITY_UNIT_PREFIXES = {
    IntensityUnit.Z_SCORE: "zscore_",
    IntensityUnit.FOLD_CHANGE: "fc_",
    IntensityUnit.RANK: "rank_",
    IntensityUnit.BATCH_RANK: "batchrank_",
    IntensityUnit.IDENTIFICATION_METADATA: "Identification metadata ",
}

INTENSITY_UNIT_SUFFIXES = {
    IntensityUnit.INTENSITY: " Intensity",
    IntensityUnit.Z_SCORE: " Z-score",
    IntensityUnit.FOLD_CHANGE: " FC",
    IntensityUnit.RANK: " Rank",
    IntensityUnit.BATCH_RANK: " BatchRank",
    IntensityUnit.SCORE: " Score",
    IntensityUnit.IDENTIFICATION_METADATA: " Identification metadata",
}

INTENSITY_UNIT_FILE_SUFFIXES = {
    IntensityUnit.Z_SCORE: "_z",
    IntensityUnit.FOLD_CHANGE: "_fc",
    IntensityUnit.RANK: "_rank",
    IntensityUnit.BATCH_RANK: "_batchrank",
}

# regex patterns
PATIENT_PREFIX = "pat_"
REF_CHANNEL_PREFIX = "ref_"
EXCLUDED_CHANNEL_PREFIX = "excl_"
IDENTIFICATION_METADATA_PREFIX = "Identification metadata "
Z_SCORE_REGEX = r" Z-score"
REGEX_META = (
    r"^Identification metadata"  # to get num identified peptides in FP intensity file
)
NUM_PEPTIDES_REGEX = r"num_peptides=(\d+)"

# default index columns
PP_KEY = "Modified sequence group"
FP_KEY = "Gene names"

PEPTIDE_PROTEIN_MAPPING_COLS = {
    "gene_name": "Gene names",
    "peptide": "Modified sequence",
    "Proteins": "Proteins",
}
