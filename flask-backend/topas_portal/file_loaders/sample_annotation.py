import pandas as pd

from .. import utils
from .. import settings


@utils.check_path_exist
def load_sample_annotation_table(sample_annotation_path: str):
    sample_annotation_df = pd.read_csv(sample_annotation_path)
    sample_annotation_df = sample_annotation_df[
        sample_annotation_df.columns.intersection(settings.SAMPLE_ANNOTATION.keys())
    ]
    sample_annotation_df = sample_annotation_df.rename(
        columns=settings.SAMPLE_ANNOTATION
    )
    if "QC" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df[
            sample_annotation_df["QC"].isin(["shaky", "passed"])
        ]
    if "Material issue" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df[
            sample_annotation_df["Material issue"] != "+"
        ]

    sample_annotation_df = utils.QC_channel_nan_values_fill(sample_annotation_df)
    if "Sample name" in sample_annotation_df.columns:
        sample_annotation_df["Sample name"] = sample_annotation_df[
            "Sample name"
        ].str.strip()
        sample_annotation_df = sample_annotation_df.drop_duplicates(
            subset="Sample name"
        )

    return sample_annotation_df
