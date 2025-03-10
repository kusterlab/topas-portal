import os

import numpy as np
from flask import Blueprint, jsonify
import pandas as pd

import db
import topas_portal.utils as ef


drug_page = Blueprint(
    "drug_page", __name__, static_folder="../dist/static", template_folder="../dist"
)

cohorts_db = db.cohorts_db

# TODO: store drug_df in DataProvider
drug_df = []


def get_drug_kinobeads(drug_df, sortfunc, gene_input):
    genes_lst = gene_input.split("_")
    p_filter = gene_input.replace("_", "|")
    drug_g_df = drug_df[
        drug_df["Kinobeads_TargetGenes"].astype("str").str.contains(p_filter)
    ]  # primary filtering to speed up
    s = drug_g_df.shape[0], len(genes_lst)
    potency_mat = np.zeros(
        s
    )  # potency numpy matrix where the rows are drugs and columns are kino genes
    to_remove_inds = []
    for i in range(len(drug_g_df.index)):
        exp = drug_g_df.loc[drug_g_df.index[i], "Kinobeads_TargetGenes"]
        exp = exp.split(",")
        for j in range(len(genes_lst)):
            gene = genes_lst[j]
            pot = 0
            for z in exp:
                k = z.split("|")
                if gene in k[0]:
                    pot = k[1]
            if pot == 0:
                if i not in to_remove_inds:
                    to_remove_inds.append(i)
            potency_mat[i, j] = pot

    drug_g_df.drop(drug_g_df.index[to_remove_inds], axis=0, inplace=True)
    to_remove_inds = tuple(to_remove_inds)
    potency_mat = np.delete(potency_mat, to_remove_inds, axis=0)
    row_means = []
    if sortfunc == "median":
        for i in range((potency_mat.shape)[0]):
            a = potency_mat[i,].tolist()
            row_means.append(np.median(a))

    if sortfunc == "mean":
        row_means = potency_mat.mean(
            axis=1
        )  # getting the means of potency for the genes

    if sortfunc == "min":
        row_means = potency_mat.min(
            axis=1
        )  # getting the means of potency for the genes

    indices = np.argsort(row_means)  # re-indexes after sorting
    drug_g_df = drug_g_df.iloc[indices]
    return drug_g_df


def load_drug_db(drug_annotation_path):
    """dataFrame for the drug-kino beasds"""
    print(f"reading {drug_annotation_path}")
    drug_df = pd.read_excel(drug_annotation_path, sheet_name="Drug List")
    drug_df = drug_df[
        [
            "Drug",
            "Kinobeads Target List",
            "Designated targets",
            "Other targets",
            "Clinical Phase",
        ]
    ]
    drug_df.columns = drug_df.columns.str.replace(
        "Kinobeads Target List", "Kinobeads_TargetGenes"
    )
    drug_df.columns = drug_df.columns.str.replace(
        "Designated targets", "Designated_TargetGenes"
    )
    # drug_df['Kinobeads_TargetGenes'] = drug_df['Kinobeads_TargetGenes'].str.replace(r"\([^()]*\)", "")   #removing potency values
    drug_df["Kinobeads_TargetGenes"] = drug_df["Kinobeads_TargetGenes"].str.replace(
        r" \(", "|", regex=True
    )
    drug_df["Kinobeads_TargetGenes"] = drug_df["Kinobeads_TargetGenes"].str.replace(
        r"\)", "", regex=True
    )
    drug_df["Kinobeads_TargetGenes"] = drug_df["Kinobeads_TargetGenes"].str.replace(
        r" ", "", regex=True
    )
    drug_df["Kinobeads_TargetGenes"] = drug_df["Kinobeads_TargetGenes"].str.replace(
        r"\//", ",", regex=True
    )
    drug_df = drug_df.fillna(-1)
    return drug_df


### Drug routings
@drug_page.route("/drugs/load")
def load_drug_table():
    """Drug_Kino beads table is independent of cohorts and will be treated as a single global variable separately"""
    global drug_df
    drug_df = []
    try:
        drug_annotation_path = cohorts_db.config.get_drug_annotation_path()
        if os.path.exists(drug_annotation_path):
            drug_df = load_drug_db(drug_annotation_path)
            print("Drug Table Loaded ## ")
            # load_log.append(ef.time_now() + 'Drug_table_loaded')
            # load_log.append(' topas_separator ')
            return {"Success": "Drug Table Loaded"}

    except IOError as e:
        print(e)
        return jsonify(e)


@drug_page.route("/drug_genes/<sortfunc>/<gene_input>")
def drug_to_KB(sortfunc, gene_input):
    drug_g_df = get_drug_kinobeads(drug_df, sortfunc, gene_input)
    return ef.df_to_json(drug_g_df)


@drug_page.route("/drugs")
def drugs():
    return ef.df_to_json(drug_df)
