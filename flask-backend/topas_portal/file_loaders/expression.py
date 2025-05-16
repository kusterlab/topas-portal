import os
import re
import pandas as pd
from pathlib import Path

import topas_portal.settings as cn
import topas_portal.utils as ef


def load_expression_data(report_directory: Path, key_col: str, modality: str):
    """
    reads in TSV files created during/before report generation
    """

    def filter_columns(x: str):
        return x.startswith("fc_") or x.startswith("zscore_") or x == key_col

    def rename_columns(x: str):
        if x.startswith("fc_"):
            return "_".join(x.split("_")[1:]).strip() + " FC"
        elif x.startswith("zscore_"):
            return "_".join(x.split("_")[1:]).strip() + " Z-score"

    if os.path.exists(
        report_directory / f"{modality}_measures_fc.tsv"
    ) and os.path.exists(report_directory / f"{modality}_measures_z.tsv"):
        df_patient_expressions_fc = pd.read_csv(
            report_directory / f"{modality}_measures_fc.tsv",
            sep="\t",
            usecols=filter_columns,
            dtype={key_col: "string"},
            index_col=key_col,
            low_memory=False,
        )
        print(report_directory / f"{modality}_measures_fc.tsv  finished")

        df_patient_expressions_zscore = pd.read_csv(
            report_directory / f"{modality}_measures_z.tsv",
            sep="\t",
            usecols=filter_columns,
            dtype={key_col: "string"},
            index_col=key_col,
            low_memory=False,
        )
        print(report_directory / f"{modality}_measures_z.tsv  finished")
        df_patient_expressions = df_patient_expressions_fc.join(
            df_patient_expressions_zscore
        )

        df_patient_expressions = df_patient_expressions.rename(columns=rename_columns)
        if modality == "phospho":
            df_patient_expressions.index = df_patient_expressions.index.str.replace(
                re.compile(r"([STY])\(Phospho \(STY\)\)"),
                lambda pat: f"p{pat.group(1)}",
                regex=True,
            )
        df_patient_expressions = ef.remove_prefix(df_patient_expressions)
        print("Expression data loaded")
        return df_patient_expressions
    else:
        pass


@ef.check_path_exist
def load_annotated_intensity_file(
    annotated_intensity_file_path: os.PathLike,
    index_col: str,
    patients_list,
    extra_columns=None,
):
    annot_df = pd.read_csv(
        annotated_intensity_file_path, low_memory=False, index_col=index_col
    )
    if index_col == cn.PP_KEY:
        annot_df.index = annot_df.index.str.replace(
            re.compile(r"([STY])\(Phospho \(STY\)\)"),
            lambda pat: f"p{pat.group(1)}",
            regex=True,
        )
    patients_list_prefixed = [cn.PATIENT_PREFIX + x for x in patients_list]
    patients_list = [*patients_list,*patients_list_prefixed]
    final_list_patients = ef.intersection(patients_list,list(annot_df.columns))
    suffix = ef.INTENSITY_UNIT_SUFFIXES[ef.IntensityUnit.INTENSITY]
    intensity_df = annot_df[final_list_patients].add_suffix(suffix)
    if extra_columns:
        intensity_df = intensity_df.join(annot_df[extra_columns])

    # in some cases, replicates have the same column name, only keep the first one
    intensity_df = intensity_df.loc[:, ~intensity_df.columns.duplicated()].copy()
    intensity_df = ef.remove_prefix(intensity_df)
    return intensity_df


@ef.check_path_exist
def load_intensity_meta_data(instensitypath, key, regex=cn.REGEX_META):
    cols = (
        pd.read_csv(instensitypath, low_memory=False, nrows=10)
        .filter(regex=regex)
        .columns.tolist()
    )
    cols.append(key)
    intensity_df = pd.read_csv(instensitypath, low_memory=False, usecols=cols)

    intensity_df.index = intensity_df[key]
    intensity_df = intensity_df.loc[:, ~intensity_df.columns.duplicated()]
    intensity_df = _post_process_meta_intensities(intensity_df)
    intensity_df = ef.remove_prefix(intensity_df)
    return intensity_df


def _post_process_meta_intensities(intensity_meta: pd.DataFrame) -> pd.DataFrame:
    intensity_meta = intensity_meta.set_index("Gene names")
    intensity_meta = intensity_meta.fillna("num_peptides=0;")
    intensity_meta = intensity_meta.replace("num_peptides=|;", "", regex=True)
    intensity_meta = intensity_meta.replace("detected in batch", "0", regex=True)
    intensity_meta = intensity_meta.apply(pd.to_numeric, errors="coerce")
    return intensity_meta


def load_modified_seq_protein_name_mapping(dir_path: Path):
    filter_cols = cn.PEPTIDE_PROTEIN_MAPPING_COLS.values()
    df_peptided_protein_df = pd.read_csv(
        dir_path / cn.PHOSPHO_MEASURES, usecols=filter_cols, sep="\t", low_memory=False
    )
    df_peptided_protein_df.index = df_peptided_protein_df[
        cn.PEPTIDE_PROTEIN_MAPPING_COLS["peptide"]
    ]

    df_peptided_protein_df.index = df_peptided_protein_df.index.str.replace(
        re.compile(r"([STY])\(Phospho \(STY\)\)"),
        lambda pat: f"p{pat.group(1)}",
        regex=True,
    )
    print("Mapping data loaded")
    return df_peptided_protein_df
