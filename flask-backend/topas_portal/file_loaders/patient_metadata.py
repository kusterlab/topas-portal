import pandas as pd

import topas_portal.utils as ef
import topas_portal.settings as cn


@ef.check_path_exist
def load_patient_table(patient_annotation_path):
    """Patients meta data"""
    patients_df = pd.read_excel(patient_annotation_path)
    patients_df["Sample name"] = patients_df["Sample name"].str.strip()
    patients_df = patients_df.drop_duplicates(subset="Sample name")
    patients_df = patients_df[
        ef.intersection(cn.PATIENTS_META_DATA, patients_df.columns)
    ]
    patients_df = ef.fill_nans_patient_columns(patients_df)
    patients_df["index"] = patients_df.index
    patients_df = ef.QC_channel_nan_values_fill(patients_df)

    patients_df = ef.whitespace_remover(patients_df)
    return patients_df
