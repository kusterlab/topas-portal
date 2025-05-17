import os
import random
import json
from enum import Enum

import pandas as pd
import numpy as np
from flask import Response
from typing import List
from datetime import datetime

import topas_portal.settings as cn
import topas_portal.plotly_preprocess as plotlyprepare
from topas_portal.config_reader import *


# remember to update the corresponding constant in vue-frontend/src/constants.js
class DataType(str, Enum):
    FP = "fp"
    PP = "pp"
    FULL_PROTEOME = "protein"
    FULL_PROTEOME_ANNOTATED = "protein_annotated"
    PHOSPHO_PROTEOME = "psite"
    FP_PP = "FP_PP"
    PHOSPHO_PROTEOME_ANNOTATED = "psite_annotated"
    PHOSPHO_SCORE = "phospho_score"
    PHOSPHO_SCORE_PSITE = "phospho_psite"
    KINASE_SCORE = "kinase"
    KINASE_SUBSTRATE = "kinase_substrate"
    TOPAS_KINASE_SCORE = "topas_kinase"
    TOPAS_KINASE_SUBSTRATE = "topas_kinase_substrate"
    TOPAS_IMPORTANT_PHOSPHO = "important_phosphorylation"
    TOPAS_PHOSPHO_SCORE = "topas_phospho"
    TOPAS_PHOSPHO_SCORE_PSITE = (
        "topas_phospho_psite"  # p-sites making up a phosphoprotein score
    )
    TOPAS_PROTEIN = "topas_expression"
    TOPAS_SCORE = "topas"
    TOPAS_SCORE_RTK = "topas_rtk"
    TRANSCRIPTOMICS = "fpkm"
    TOPAS_SUBSCORE = "topas_subscore"
    BIOMARKER = "biomarker"

    PATIENT_METADATA = "patients_df"
    SAMPLE_ANNOTATION = "sample_annotation_df"

    CUSTOM = "custom"


class ColumnNames(str, Enum):
    SAMPLE_NAME = "Sample name"
    GENE_NAME = "Gene names"


def get_selection_list_data_type(level: DataType):
    if level == DataType.KINASE_SUBSTRATE:
        return DataType.KINASE_SCORE
    elif level == DataType.PHOSPHO_SCORE_PSITE:
        return DataType.PHOSPHO_SCORE
    else:
        return level


class IntensityUnit(str, Enum):
    INTENSITY = "intensity"
    Z_SCORE = "z_scored"
    SCORE = "score"


INTENSITY_UNIT_SUFFIXES = {
    IntensityUnit.INTENSITY: " Intensity",
    IntensityUnit.Z_SCORE: " Z-score",
    IntensityUnit.SCORE: " Score",
}


class ImputationMode(str, Enum):
    NO_IMPUTE = "noimpute"
    IMPUTE = "impute"


def add_patient_prefix(patient_list: list[str]):
    return [cn.PATIENT_PREFIX + x for x in patient_list]


def remove_patient_prefix(df, from_col=True) -> pd.DataFrame:
    if from_col:
        try:
            df.columns = df.columns.str.replace(cn.PATIENT_PREFIX, "", regex=True)
        except:
            pass
    else:
        try:
            df.index = df.index.str.replace(cn.PATIENT_PREFIX, "", regex=True)
        except:
            pass

        if "Sample name" in df.columns or "sample" in df.columns:
            try:
                df["Sample name"] = df["Sample name"].str.replace(
                    cn.PATIENT_PREFIX, "", regex=True
                )
            except:
                pass

    return df


def check_path_exist(func):
    """
    General  Decorator to check the file path before openening
    returns list if the path doesnot exist and dataframe if exists
    USAGE:

    @check_path_exist
    def your_pandas_function(path):
        <code>
    """

    def wrapper(path: str, *args, **kwargs):
        if os.path.exists(path):
            print("###")
            print(f"Reading the file {path}")
            try:
                df = func(path, *args, **kwargs)
                print(f"{path} loaded with success!")
                return df
            except Exception as err:
                print(f"# ERROR in OPENING {path}: {type(err).__name__}: {err}.")
                return [
                    f"{type(err).__name__}: {err} in reading the file {path}. Check if it is opened somewhere"
                ]
                # raise PermissionError(f'error in reading the file {path} probably opened somewhere')
        else:
            print(f"{path} does not exist")
            return [f"{path} does not exist"]
            # raise FileNotFoundError(f'{path} does not exist')

    return wrapper


def QC_channel_nan_values_fill(df):
    if "QC" in df.columns:
        df["QC"] = df["QC"].fillna("n.d.")
    return df


def fill_nans_patient_columns(patients_df):
    """The na values will make issues inside devesxreme to avoid this we fill them with defaut values"""
    if isinstance(patients_df, pd.DataFrame):
        string_cols = cn.PATIENT_TABLE_NAN_STRING
        int_cols = cn.PATIENT_TABLE_NAN_INT
        string_cols = [s for s in string_cols if s in patients_df.columns]
        int_cols = [s for s in int_cols if s in patients_df.columns]
        patients_df[string_cols] = patients_df[string_cols].fillna("")
        patients_df[int_cols] = patients_df[int_cols].fillna(-1)
        return patients_df
    else:
        pass


def count_df_to_density_plot_df(temp_df, identifier, samples_list):
    list_samples = [x for x in list(temp_df.columns) if x in samples_list]
    background = temp_df[list_samples].to_numpy().flatten()
    backgournd_count_df = data_to_count_df(background, color="blue", opacity=0.15)
    abundances = temp_df[temp_df.index == identifier]
    abundances = abundances[list_samples].to_numpy()
    abundances_count_df = data_to_count_df(
        abundances, color="red", opacity=0.8, density=False
    )
    final_count_df = pd.concat([backgournd_count_df, abundances_count_df])
    final_count_df = final_count_df.sort_values(by="X")
    return final_count_df


def data_to_count_df(data: np.array, color="red", bins=50, opacity=0.3, density=True):
    inp = data[~np.isnan(data)]
    inp = data[np.isfinite(data)]
    hs = np.histogram(inp, bins=bins, density=density)
    counts = np.interp(hs[0], (hs[0].min(), hs[0].max()), (0, +1))
    edges = np.round(hs[1][0 : len(hs[1]) - 1], decimals=2)
    df = pd.DataFrame(list(zip(edges, counts)))
    df.columns = ["X", "Y"]  # X refer to the edges and Y to the counts
    df["color"] = color
    df["opacity"] = opacity
    df["ind"] = df["X"]
    return df


def ranodom_color_genetator(num: int):
    """
    Generates a list with  num random colors

    """
    no_of_colors = num
    colors = [
        "#" + "".join([random.choice("0123456789ABCDEF") for i in range(6)])
        for j in range(10000)
    ]
    color = random.sample(list(set(colors)), no_of_colors)
    return color


def unnest_proteingroups(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unnest the protein_groups A;B as two separate rows with the same values
    the protein groups are the index of the the pandas dataframe df
    """
    temp_df = df
    temp_df["index"] = temp_df.index.str.split(";")
    temp_df = temp_df.explode("index")
    temp_df = temp_df.set_index("index")
    return temp_df


def get_index_cols(data_type: str) -> List[str]:
    index_cols = ["Gene names"]
    if data_type == "pp":
        index_cols = ["Gene names", "Modified sequence", "Proteins"]
    return index_cols


def keep_only_sample_columns(df: pd.DataFrame, samples_list: list, keep_ref_channels: bool = False) -> pd.DataFrame:
    """Returns the columns which matches the samples Regex in the dataframe
    :df: pandas data frame
    :output : pandas data frame with filtered columns
    """
    list_patients = intersection(df.columns, samples_list)
    if not keep_ref_channels:
        return df[[x for x in list_patients if not str(x).__contains__("ref-")]]
    else:
        return df[list_patients]


def calculate_confidence_score(df: pd.DataFrame) -> pd.DataFrame:
    try:
        df_temp = (
            df[["num_pep", "Z-score"]].copy().apply(pd.to_numeric, errors="coerce")
        )
        df_temp["confidence_score"] = df_temp["num_pep"] * df_temp["Z-score"]
        df["confidence_score"] = df_temp["confidence_score"].fillna("n.d.")
        return df
    except:
        print("some thing wrong with confidence scoring")
        return df


def post_process_for_front_end(df: pd.DataFrame, defaultcolor="grey", defaultsize=2):
    if not isinstance(df, pd.DataFrame):
        return df

    abundances_table = df.copy()
    abundances_table["colorID"] = (
        defaultcolor  # default value for the color on the frontend
    )
    abundances_table["sizeR"] = (
        defaultsize  # default value for the point size on the frontend
    )
    abundances_table = abundances_table.reset_index(drop=True)
    abundances_table["index"] = abundances_table.index
    return abundances_table


def merge_with_sample_annotation_df(
    scores_df: pd.DataFrame, sample_annotation_df: pd.DataFrame
):
    if not isinstance(sample_annotation_df, pd.DataFrame):
        return scores_df

    if "Entity" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df.drop("Entity", axis=1)

    try:
        merged_table = scores_df.merge(
            sample_annotation_df, on="Sample name", how="left"
        )
        return merged_table
    except Exception as err:
        print(err)
        return scores_df


def merge_with_patients_meta_df(scores_df: pd.DataFrame, patients_df: pd.DataFrame):
    if not isinstance(patients_df, pd.DataFrame):
        return scores_df

    try:
        new_patients_df = patients_df.drop_duplicates(
            subset="Sample name", keep="first"
        )
        if "Batch_No" in new_patients_df.columns:
            new_patients_df = new_patients_df.drop(["Batch_No"], axis=1)
        scores_table = scores_df.copy()
        scores_table["Sample_name_rep_truncated"] = scores_table[
            "Sample name"
        ].str.replace(r"-R[0-9]$", "", regex=True)
        new_patients_df = new_patients_df.rename(columns={"Sample name": "patient_id"})
        scores_table = scores_table.dropna(subset=["Sample_name_rep_truncated"])
        new_patients_df = new_patients_df.dropna(subset=["patient_id"])
        if len(scores_table) > 0 and len(new_patients_df) > 0:
            merged_table = scores_table.merge(
                new_patients_df,
                left_on="Sample_name_rep_truncated",
                right_on="patient_id",
                how="left",
            )
            merged_table = merged_table.drop(["patient_id"], axis=1)
            return merged_table
        else:
            return scores_df
    except Exception as err:
        print(err)
        return scores_df


def time_now():
    now = datetime.now()
    current_time = now.strftime("%D:%H:%M")
    return str(current_time) + ": "


def log_delete(fileName):
    with open(fileName, "r+") as file:
        file.truncate(0)


def write_log(msg, fileName):
    f = open(fileName, "a")
    f.write(time_now())
    f.write(msg)
    f.close()


def read_log(fileName):
    f = open(fileName, "r")
    lines = f.readline()
    f.close()
    return lines


def check_all_config_file(configs):
    import os

    cohorts = list(configs["report_directory"].keys())
    final_dic = {}
    important_keys = [
        str(x)
        for x in list(configs.keys())
        if str(x).__contains__("file")
        or str(x).__contains__("directory")
        or str(x).__contains__("path")
    ]
    for path_to_check in important_keys:
        for cohort in cohorts:
            try:
                dic_key = path_to_check + ":" + cohort
                final_dic[dic_key] = os.path.exists(configs[path_to_check][cohort])
            except:
                try:
                    dic_key = path_to_check
                    final_dic[dic_key] = os.path.exists(configs[path_to_check])
                except Exception as err:
                    final_dic[path_to_check] = str(err)
                    pass
    try:
        df = pd.DataFrame([final_dic])
        df = df.melt()
        df.columns = ["path", "path exists"]
        return df_to_json(df)
    except:
        return {}


def df_to_json(df):
    """
    Makes flask JSON response from a dataframe
    """
    return Response(
        json.dumps(df.to_dict(orient="records")), mimetype="application/json"
    )


def get_cohort_names_from_config(config_path):
    """
    returns the list of cohorts in the config file
    """
    config = config_reader(config_path)
    return list(config["patient_annotation_path"].keys())


def intersection(lst1, lst2):
    return sorted(list(set(lst1) & set(lst2)))


def setdiff(lst1, lst2):
    return sorted(list(set(lst1) - set(lst2)))


def check_complete_or_fp_or_pp(
    fp_df_patients: pd.DataFrame, pp_df_patients: pd.DataFrame
) -> str:
    """Check if the the cohort is complete or its only fp or pp"""
    cohort_type = ""
    if isinstance(fp_df_patients, pd.DataFrame) & (pp_df_patients, pd.DataFrame):
        cohort_type = "complete"
    else:
        if isinstance(fp_df_patients, pd.DataFrame):
            cohort_type = "fp_only"
        else:
            cohort_type = "pp_only"
    return cohort_type


def merged_df_to_json(data_type: str, merged_df: pd.DataFrame, title="Scores"):
    sample_annot_cols = [
        x
        for x in merged_df.columns.tolist()
        if x in list(cn.SAMPLE_ANNOTATION.values())
    ]
    if data_type == "plot":
        merged_df.index = (
            merged_df["Sample name"] + "_" + merged_df["TMT_channel"].astype(str)
        )

        plot_df = merged_df.drop(sample_annot_cols, axis=1)
        return plotlyprepare.get_simple_heatmap(plot_df, title)
    else:
        meta_data = merged_df[sample_annot_cols]
        return df_to_json(meta_data)


def calculate_z_scores(df: pd.DataFrame, col_name="sum"):
    """
    This will calculate z-scores using LOO method
    :df: a unicolumn pandas dataFrame
    :col_name:  the column the zscoring is based on tha column
    """
    print("Calculating zscores")
    try:
        z_scores = []
        # TODO: replace this with Metrics LOO z-scoring function from topas-pipeline
        for i in df.index:
            loo_df = df.drop(i, axis=0)
            median = float(loo_df.median())
            stdev = float(loo_df.std())
            z_scores.append((df.loc[i, col_name] - median) / stdev)
        return z_scores
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
        return ["n.d."]*len(df.index)
