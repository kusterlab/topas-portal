import pandas as pd

import topas_portal.utils as ef
import topas_portal.settings as cn


@ef.check_path_exist
def load_sample_annotation_table(sample_annotation_path):
    sample_annotation_keys = list(cn.SAMPLE_ANNOTATION.keys())
    sample_annotation_df = pd.read_csv(sample_annotation_path)
    final_keys = [
        col
        for col in sample_annotation_df.columns.tolist()
        if col in sample_annotation_keys
    ]
    sample_annotation_df = sample_annotation_df[final_keys]
    sample_annotation_df = sample_annotation_df.rename(columns=cn.SAMPLE_ANNOTATION)
    if "QC" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df[
            sample_annotation_df["QC"].isin(["shaky", "passed"])
        ]

    sample_annotation_df = ef.QC_channel_nan_values_fill(sample_annotation_df)
    if "Sample name" in sample_annotation_df.columns:
        sample_annotation_df["Sample name"] = sample_annotation_df[
            "Sample name"
        ].str.strip()
        sample_annotation_df = sample_annotation_df.drop_duplicates(
            subset="Sample name"
        )
    sample_annotation_df["Sample name"] = sample_annotation_df[
        "Sample name"
    ].str.replace("ref_channel_", "ref-channel-")
    sample_annotation_df["Sample name"] = sample_annotation_df[
        "Sample name"
    ].str.replace("_batch", "-batch")

    return sample_annotation_df
