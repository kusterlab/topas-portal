
from flask import Blueprint, jsonify, current_app, send_from_directory, Response, request
import db
import pandas as pd
import zipfile
from pathlib import Path
import shutil
import os
import io

from extensions import cache
from topas_portal import utils
from topas_portal.routes import PatientReportApiRoutes
from topas_portal import prexp_preprocess as pp
import matplotlib
matplotlib.use('svg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import seaborn as sns
from topas_portal import patient_report_excel

patient_report_page = Blueprint(
    "patient_report_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db


antigens = [
    "MAGEA4",
    "ERBB2",
    "BTN3A3",
    "PTK7",
    "CTAG1A",
    "NECTIN2",
    "SLC39A6",
    "GPC3",
    "F3",
    "CD276",
    "KAT6B",
    "CDH6",
    "ERBB3",
    "BTN3A1",
    "IL1RAP",
    "ANKRD30A",
    "FAP",
    "BTN3A2",
    "TACSTD2",
    "CDH3",
    "NECTIN4",
    "CSF1R",
    "CDH17",
    "PMEL",
    "MSLN",
    "FOLR1",
    "MUC1",
    "ROR2",
    "FOLH1",
    "SEZ6",
    "B4GALNT1",
    "PGR",
    "CLDN18-2;CLDN18",
    "SLC39A1",
    "AR",
    "KAT6A",
    "ROR1",
    "VTCN1",
    "CLDN6",
    "ESR1",
    "SSTR2"
]


immune_status_genes = [
    "TAP1",
    "CD163",
    "HLA-DRA",
    "PSMB8",
    "HLA-E",
    "CD276",
    "HLA-A",
    "PSMB10",
    "HLA-DQB1",
    "HLA-C",
    "HLA-B",
    "CD1A",
    "HLA-DPB1",
    "CD5",
    "CD3E",
    "GZMA",
    "TAP2",
    "APOL3",
    "TAPBP",
    "HLA-DRB4",
    "PRF1",
    "HLA-F",
    "HLA-DMB",
    "HLA-DPA1",
    "PSMB9",
    "HLA-DQA1",
    "HLA-G",
    "SIGIRR",
    "LAG3",
    "CD68",
    "CD274",
    "CD38",
    "RUNX3",
    "HLA-DRB1",
    "CD8A",
    "MS4A1",
    "HLA-DQB2",
    "CD4",
    "HLA-DMA",
    "CD1E",
    "GNLY",
    "HLA-DRB3",
    "HLA-DRB5",
    "CD3G",
    "CD84",
    "CD8B",
    "CD1B",
    "CD19",
    "HAVCR2",
    "ZBTB16",
    "CD79B",
    "CD79A",
    "GZMB",
    "CD27",
    "HLA-DOA",
    "HHLA2",
    "CD2",
    "CD1C",
    "HLA-DOB",
    "HLA-H",
    "CD3D",
    "CD22",
    "GZMH"
]

@cache.cached(timeout=50)
@patient_report_page.route(PatientReportApiRoutes.PATIENT_REPORT_TABLE)
def get_patient_report_table(cohort_index: int, patient: str, level: utils.DataType):
    """Returns tables from the patient reports.

    Example: http://localhost:3832/0/patient_reports/I007-031-108742/protein

    Args:
        cohort_index (int): cohort index
        patient (str): patient identifier
        level (utils.DataType): modality (e.g. full proteome, topas, etc.) to get
            reports for, see utils.DataType.

    Returns:
        Response: jsonified dataframe with patient report table.
    """
    return utils.df_to_json(
        pp.get_reports_per_patient(
            cohorts_db,
            cohort_index,
            patient,
            utils.DataType(level),
        )
    )


@cache.cached(timeout=50)
@patient_report_page.route(PatientReportApiRoutes.PATIENT_REPORT_TABLE_XLSX)
# http://localhost:3832/0/patient_reports/I007-031-108742
def get_patient_reports_as_attachment(cohort_index: int, patients: str):
    """Returns patient report excel files. For multiple reports, a zip file is returned.

    Args:
        cohort_index (int): cohort index
        patient (str): patient identifiers separated by semicolons

    Returns:
        Response: excel or zip file with patient report(s)
    """
    reports_dir = Path(cohorts_db.get_report_dir(cohort_index)) / "Reports"
    reports_dir.mkdir(exist_ok=True)

    def get_patient_report_path(patient_identifier: str):
        return reports_dir / f"{patient_identifier}_proteomics_results.xlsx"

    patients = patients.split(",")
    for patient in patients:
        path_to_patient_results = get_patient_report_path(patient)
        patient_report_excel.generate_patient_report(
            cohorts_db, cohort_index, patient, path_to_patient_results
        )

    if len(patients) == 1:
        path_to_patient_results = get_patient_report_path(patients[0])
        if not os.path.exists(path_to_patient_results):
            return f"Unable to download report for {patients[0]}", 400
        shutil.copy(path_to_patient_results, current_app.config["UPLOAD_FOLDER"])
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"],
            Path(path_to_patient_results).name,
            as_attachment=True,
        )
    elif len(patients) > 1:
        paths_to_patient_results = []
        for patient in patients:
            path_to_patient_results = get_patient_report_path(patient)
            if not os.path.exists(path_to_patient_results):
                return f"Unable to download report for {patient}", 400
            paths_to_patient_results.append(path_to_patient_results)

        output_zipfile = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "patient_reports.zip"
        )
        with zipfile.ZipFile(output_zipfile, "w") as zipFile:
            for path_to_patient_results in paths_to_patient_results:
                zipFile.write(
                    path_to_patient_results,
                    Path(path_to_patient_results).name,
                    compress_type=zipfile.ZIP_STORED,
                )  # no compression, because Excel files are already binary
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"], Path(output_zipfile).name, as_attachment=True
        )


@patient_report_page.route(PatientReportApiRoutes.TUMOR_ANTIGENS_SWARM_PLOT)
def get_tumor_antigens_swarm_plot(cohort_index: int, patient: str):
    if len(patient.split(";")) > 1:
        return "Can only handle 1 patient at a time", 400

    subcohort_column = request.args.get("subcohort_column", type=str, default="code_oncotree")
    samples = cohorts_db.get_patient_metadata_df(cohort_index)

    subcohort = get_subcohort_index(samples, subcohort_column, patient)

    fp = cohorts_db.get_protein_abundance_df(cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE)

    genes = fp.index.intersection(antigens)

    df_long = (
        fp.loc[genes]
        .reset_index()
        .melt(id_vars='Gene names',
                var_name='Sample names',
                value_name='Expression')
    )

    df_long["subcohort"] = df_long["Sample names"].isin(subcohort)
    df_long["highlight"] = df_long["Sample names"].eq(patient)

    gene_order = (
        df_long[df_long["highlight"]]
            .sort_values("Expression", ascending=False)["Gene names"]
            .tolist()
    )

    svg_data = get_swarm_plot_svg(df_long, gene_order, "", "Protein abundance (z-score)")    

    return Response(svg_data, mimetype="image/svg+xml")

@patient_report_page.route(PatientReportApiRoutes.RTKS_SWARM_PLOT)
def get_rtk_swarm_plot(cohort_index: int, patient: str):
    if len(patient.split(";")) > 1:
        return "Can only handle 1 patient at a time", 400

    subcohort_column = request.args.get("subcohort_column", type=str, default="code_oncotree")
    samples = cohorts_db.get_patient_metadata_df(cohort_index)

    subcohort = get_subcohort_index(samples, subcohort_column, patient)

    rtk = cohorts_db.get_topas_rtk_scores_df(cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE)
    
    df_long = (
        rtk
        .rename_axis("Gene names")
        .reset_index()
        .melt(id_vars="Gene names",
            var_name="Sample names",
            value_name="Expression")
    )
    df_long["subcohort"] = df_long["Sample names"].isin(subcohort)
    df_long["highlight"] = df_long["Sample names"].eq(patient)

    gene_order = (
        df_long[df_long["highlight"]]
            .sort_values("Expression", ascending=False)["Gene names"]
            .tolist()
    )

    svg_data = get_swarm_plot_svg(df_long, gene_order, "", "RTK-TOPAS (z-score)")    

    return Response(svg_data, mimetype="image/svg+xml")

@patient_report_page.route(PatientReportApiRoutes.CKS_NKS_SWARM_PLOT)
def get_ck_nk_swarm_plot(cohort_index: int, patient: str):
    if len(patient.split(";")) > 1:
        return "Can only handle 1 patient at a time", 400

    subcohort_column = request.args.get("subcohort_column", type=str, default="code_oncotree")
    samples = cohorts_db.get_patient_metadata_df(cohort_index)

    subcohort = get_subcohort_index(samples, subcohort_column, patient)

    ck_nk = cohorts_db.get_topas_ck_scores_df(cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE)
    
    df_long = (
        ck_nk
        .rename_axis("Gene names")
        .reset_index()
        .melt(id_vars="Gene names",
            var_name="Sample names",
            value_name="Expression")
    )

    df_long["subcohort"] = df_long["Sample names"].isin(subcohort)
    df_long["highlight"] = df_long["Sample names"].eq(patient)

    gene_order = (
        df_long[df_long["highlight"]]
            .sort_values("Expression", ascending=False)["Gene names"]
            .tolist()
    )
    svg_data = get_swarm_plot_svg(df_long, gene_order, "", "CK/NK-TOPAS (z-score)")    
    return Response(svg_data, mimetype="image/svg+xml")


@patient_report_page.route(PatientReportApiRoutes.IMMUNE_STATUS_HEATMAP)
def get_immune_status_heatmap(cohort_index: int, patient: str):
    if len(patient.split(";")) > 1:
        return "Can only handle 1 patient at a time", 400

    fp = cohorts_db.get_protein_abundance_df(cohort_index, intensity_unit=utils.IntensityUnit.Z_SCORE)
    
    fp = fp.loc[fp.index.intersection(immune_status_genes)]

    def classify(x):
        if x >= 2:
            return 2
        elif x >= 1:
            return 1
        else:
            return 0
    sample_order = (fp.applymap(classify) > 0).sum(axis=0).sort_values(ascending=False).index.to_list()
    
    sample_order.remove(patient)
    new_order = sample_order[:5] + [patient] + sample_order[-5:]

    cmap = ListedColormap(["aliceblue", "orange", "red"])
    norm = BoundaryNorm([-10, 1.5, 2, 10], cmap.N)
    plt.figure(figsize=(12, 3))

    ax = sns.heatmap(
        fp[new_order].T.fillna(0),
        annot=False,
        fmt="",
        cmap=cmap,
        cbar=None,
        linewidths=0.5,
        linecolor='white',
        norm=norm
    )
    mid = len(new_order) // 2
    ax.set_yticks([mid + 0.5])
    ax.set_yticklabels([sample_order[mid]])
    plt.xticks(rotation=60, ha='right', rotation_mode='anchor')
    ax.xaxis.label.set_visible(False)
    ax.yaxis.label.set_visible(False)

    buf = io.BytesIO()
    plt.savefig(buf, format="svg", bbox_inches="tight")
    buf.seek(0)
    svg_data = buf.getvalue().decode("utf-8")
    plt.close()
    return Response(svg_data, mimetype="image/svg+xml")


def get_subcohort_index(samples_df, column, sample_name):
    return samples_df[
        samples_df[column] == samples_df.loc[samples_df["Sample name"] == sample_name, column].iloc[0]
    ]["Sample name"].to_list() if column in samples_df.columns else []

def get_swarm_plot_svg(df_long, gene_order, xlabel, ylabel, figsize=(10, 4)):
    highlight_genes = (
        df_long[df_long["highlight"]].groupby("Gene names")["Expression"]
        .max()
        .gt(2)
    )


    plt.figure(figsize=figsize)
    sns.stripplot(
        data=df_long[~df_long["subcohort"]],
        x="Gene names",
        y="Expression",
        order=gene_order,
        color="grey",
        alpha=0.5,
        jitter=True,
        size=3
    )

    sns.stripplot(
        data=df_long[df_long["subcohort"]],
        x="Gene names",
        y="Expression",
        order=gene_order,
        color="mediumblue",
        alpha=0.5,
        jitter=True,
        size=3
    )

    sns.stripplot(
        data=df_long[df_long["highlight"]],
        x="Gene names",
        y="Expression",
        order=gene_order,
        color="red",
        jitter=True,
        size=5
    )

    for tick in plt.gca().get_xticklabels():
        gene = tick.get_text()
        if highlight_genes.get(gene, False):
            tick.set_color("red")


    plt.axhline(y=2, linestyle='--', color='red', zorder=10)
    plt.xticks(rotation=60, ha='right', rotation_mode='anchor')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.tick_params(axis='x', which='both', length=0)  # remove x-axis tick lines
    plt.tick_params(axis='y', which='both', length=0)  # remove y-axis tick lines

    buf = io.BytesIO()
    plt.savefig(buf, format="svg")
    buf.seek(0)
    svg_data = buf.getvalue().decode("utf-8")
    plt.close()
    return svg_data