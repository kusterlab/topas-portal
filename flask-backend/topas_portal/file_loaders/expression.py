import os
import re
import pandas as pd
from pathlib import Path

from topas_portal import settings
from topas_portal import utils


def load_expression_data(measure_paths: list[Path], key_col: str):
    """
    reads in TSV files created during/before report generation
    """
    df_patient_measures = []
    for measure_path in measure_paths:
        if not measure_path.is_file():
            print("Some or all of the measures files are unavailable")
            return
        df_patient_measures.append(load_measures(measure_path, key_col))
    df_patient_expressions = pd.concat(df_patient_measures, axis=1)
    df_patient_expressions = utils.remove_patient_prefix(df_patient_expressions)
    print("Expression data loaded")

    return df_patient_expressions


def load_measures(
    measures_path: Path,
    key_col: str,
):
    """
    reads in TSV files created during/before report generation
    """
    intensity_unit = None
    for (
        intensity_unit_candidate,
        file_suffix,
    ) in utils.INTENSITY_UNIT_FILE_SUFFIXES.items():
        if measures_path.stem.endswith(file_suffix):
            intensity_unit = intensity_unit_candidate
            break
    else:
        raise ValueError(
            f"Could not determine intensity unit from measures file name {measures_path}"
        )

    def filter_columns(x: str):
        return (
            x.startswith(utils.INTENSITY_UNIT_PREFIXES[intensity_unit]) or x == key_col
        )

    def rename_columns(x: str):
        if x.startswith(utils.INTENSITY_UNIT_PREFIXES[intensity_unit]):
            return (
                "_".join(x.split("_")[1:]).strip()
                + utils.INTENSITY_UNIT_SUFFIXES[intensity_unit]
            )
        return x

    df_patient_measures = pd.read_csv(
        measures_path,
        sep="\t",
        usecols=filter_columns,
        dtype={key_col: "string"},
        index_col=key_col,
        low_memory=False,
    )
    print(f"{measures_path} finished")
    if intensity_unit == utils.IntensityUnit.RANK:
        df_patient_measures = df_patient_measures.rename(
            columns={"rank_max": "Occurrence"}
        )

    df_patient_measures = df_patient_measures.rename(columns=rename_columns)

    return df_patient_measures


@utils.check_path_exist
def load_annotated_intensity_file(
    annotated_intensity_file: os.PathLike,
    index_col: str,
    extra_columns=None,
    intensity_suffix: str = utils.INTENSITY_UNIT_SUFFIXES[
        utils.IntensityUnit.INTENSITY
    ],
):
    if extra_columns is None:
        extra_columns = []

    annot_df = pd.read_csv(
        annotated_intensity_file, low_memory=False, index_col=index_col
    )
    extra_columns_intersection = annot_df.columns.intersection(extra_columns)
    annot_df.loc[:, extra_columns_intersection] = annot_df.loc[
        :, extra_columns_intersection
    ].fillna("")

    patients_list: pd.Index = annot_df.filter(regex=r"^pat_|^ref_").columns
    patients_list = patients_list.str.replace(pat=r"^pat_", repl="", regex=True)
    patients_list = patients_list.tolist()

    patient_list_prefixed = utils.add_patient_prefix(patients_list)
    identification_metadata_columns = utils.add_identification_metadata_prefix(
        patients_list
    )
    intensity_df = annot_df.loc[
        :,
        annot_df.columns.isin(
            patient_list_prefixed + identification_metadata_columns + extra_columns
        ),
    ]

    identification_metadata_suffix = utils.INTENSITY_UNIT_SUFFIXES[
        utils.IntensityUnit.IDENTIFICATION_METADATA
    ]
    column_rename_dict = {
        c: c.replace(settings.PATIENT_PREFIX, "") + intensity_suffix
        for c in patient_list_prefixed
    } | {
        c: c.replace(settings.IDENTIFICATION_METADATA_PREFIX, "")
        + identification_metadata_suffix
        for c in identification_metadata_columns
    }
    intensity_df = intensity_df.rename(columns=column_rename_dict)

    # in some cases, replicates have the same column name, only keep the first one
    intensity_df = intensity_df.loc[:, ~intensity_df.columns.duplicated()]
    return intensity_df


@utils.check_path_exist
def load_intensity_meta_data(instensitypath, key, regex=settings.REGEX_META):
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
    intensity_df = utils.remove_patient_prefix(intensity_df)
    return intensity_df


def _post_process_meta_intensities(intensity_meta: pd.DataFrame) -> pd.DataFrame:
    intensity_meta = intensity_meta.set_index("Gene names")
    intensity_meta = intensity_meta.fillna("num_peptides=0;")
    intensity_meta = intensity_meta.replace("num_peptides=|;", "", regex=True)
    intensity_meta = intensity_meta.replace("detected in batch", "0", regex=True)
    intensity_meta = intensity_meta.apply(pd.to_numeric, errors="coerce")
    return intensity_meta


def load_modified_seq_protein_name_mapping(dir_path: Path):
    filter_cols = settings.PEPTIDE_PROTEIN_MAPPING_COLS.values()
    df_peptided_protein_df = pd.read_csv(
        dir_path / settings.PHOSPHO_MEASURES,
        usecols=filter_cols,
        sep="\t",
        low_memory=False,
    )
    df_peptided_protein_df.index = df_peptided_protein_df[
        settings.PEPTIDE_PROTEIN_MAPPING_COLS["peptide"]
    ]

    df_peptided_protein_df.index = df_peptided_protein_df.index.str.replace(
        re.compile(r"([STY])\(Phospho \(STY\)\)"),
        lambda pat: f"p{pat.group(1)}",
        regex=True,
    )
    print("Mapping data loaded")
    return df_peptided_protein_df
