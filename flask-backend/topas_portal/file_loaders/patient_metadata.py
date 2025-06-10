import pandas as pd

from topas_portal import utils
from topas_portal import settings


@utils.check_path_exist
def load_patient_table(patient_annotation_path):
    """Patients meta data"""
    patients_df = pd.read_excel(patient_annotation_path)
    patients_df["Sample name"] = patients_df["Sample name"].str.strip()
    patients_df = patients_df.drop_duplicates(subset="Sample name")
    patients_df = patients_df[
        utils.intersection(settings.PATIENTS_META_DATA, patients_df.columns)
    ]
    patients_df = utils.fill_nans_patient_columns(patients_df)
    patients_df["index"] = patients_df.index
    patients_df = utils.QC_channel_nan_values_fill(patients_df)

    patients_df = utils.whitespace_remover(patients_df)
    return patients_df
