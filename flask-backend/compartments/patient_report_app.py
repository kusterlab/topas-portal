
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


import numpy as np
import joblib
import json


from pydantic import BaseModel
from typing import Dict, List, Optional
from umap import UMAP
from pathlib import Path
from flask import Blueprint, jsonify, request, Response


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
    fig, ax = plt.subplots(figsize=(12, 3))

    sns.heatmap(
        fp[new_order].T.fillna(0),
        annot=False,
        fmt="",
        cmap=cmap,
        cbar=None,
        linewidths=0.5,
        linecolor='white',
        norm=norm,
        ax=ax
    )

    mid = len(new_order) // 2
    ax.set_yticks([mid + 0.5])
    ax.set_yticklabels([sample_order[mid]])

    for label in ax.get_xticklabels():
        label.set_rotation(60)
        label.set_ha('right')
        label.set_rotation_mode('anchor')

    ax.xaxis.label.set_visible(False)
    ax.yaxis.label.set_visible(False)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    buf.seek(0)
    svg_data = buf.getvalue().decode("utf-8")

    plt.close(fig)
    return Response(svg_data, mimetype="image/svg+xml")


# PRODICT

MODELS_FOLDER = "/media/kusterlab/internal_projects/active/TOPAS/WP31/Playground/LE_PROdict/paper_classifier_results/03_selected_classifiers_models/model_file"
SIGNATURES_FOLDER = "/media/kusterlab/internal_projects/active/TOPAS/WP31/Playground/CANCER_CLASSIFICATION"


# ===================== HELPER FUNCTIONS =====================


def patient_data_collection(cohort_index: int, patient: str):
    data = cohorts_db.get_protein_abundance_df(
        cohort_index,
        intensity_unit=utils.IntensityUnit.INTENSITY,
        patient_name=patient,
    )
    return data


# Load necessary files - Classification models and Tumor Type Signatues
def load_signatures_from_folder(folder_path):
    folder = Path(folder_path)
    txt_dict = {}

    for file in folder.glob("*.txt"): 
        key = file.stem               
        with open(file, "r") as f:
            lines = [line.strip() for line in f if line.strip() != ""]
        txt_dict[key] = lines

    return txt_dict


def load_sklearn_models(folder_path):
    models = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.pkl'):
            file_path = os.path.join(folder_path, filename)
            model_name = filename.replace('_log_reg_ridge_model.pkl', '')
            try:
                model = joblib.load(file_path)
                models[model_name] = model
            except Exception as e:
                print(f"{filename} not loaded: {e}")
    return models


models = load_sklearn_models(MODELS_FOLDER)


def impute_normal_down_shift_distribution(
    unimputerd_dataframe: pd.DataFrame,
    column_wise: bool = True,
    width: float = 0.3,
    downshift: float = 1.8,
    seed: int = 2
) -> pd.DataFrame:
    """
    Performs imputation across a matrix columnswise
    """
    print('The size of the data Frame before imputation')
    print(unimputerd_dataframe.shape)
    
    unimputerd_df = unimputerd_dataframe.copy()
    unimputerd_df.replace({pd.NA: np.nan}, inplace=True)
    unimputerd_matrix = unimputerd_df.to_numpy()
    columns_names = unimputerd_df.columns
    rownames = unimputerd_df.index
    
    unimputerd_matrix[~np.isfinite(unimputerd_matrix)] = np.nan
    main_mean = np.nanmean(unimputerd_matrix)
    main_std = np.nanstd(unimputerd_matrix)
    np.random.seed(seed=seed)
    
    def impute_normal_per_vector(temp: np.ndarray, width=width, downshift=downshift):
        """Performs imputation for a single vector"""
        if column_wise:
            temp_sd = np.nanstd(temp)
            temp_mean = np.nanmean(temp)
        else:
            temp_sd = main_std
            temp_mean = main_mean
        
        shrinked_sd = width * temp_sd
        downshifted_mean = temp_mean - (downshift * temp_sd)
        n_missing = np.count_nonzero(np.isnan(temp))
        
        if n_missing > 0:
            temp[np.isnan(temp)] = np.random.normal(
                loc=downshifted_mean,
                scale=shrinked_sd,
                size=n_missing
            )
        
        return temp
    
    final_matrix = np.apply_along_axis(impute_normal_per_vector, 0, unimputerd_matrix)
    final_df = pd.DataFrame(final_matrix)
    final_df.index = rownames
    final_df.columns = columns_names
    
    return final_df


def load_txt_folder(folder_path: str) -> Dict[str, List[str]]:
    """Load all .txt files from a folder into a dictionary"""
    folder = Path(folder_path)
    txt_dict = {}
    
    for file in folder.glob("*.txt"):
        key = file.stem
        with open(file, "r") as f:
            lines = [line.strip() for line in f if line.strip() != ""]
        txt_dict[key] = lines
    
    return txt_dict


# UMAP plotting function

class UMAPRequest(BaseModel):
    sample_name: str
    signature_key: str
    n_neighbors: int = 10
    min_dist: float = 0.1
    random_state: int = 93
    width: float = 0.3
    downshift: float = 1.8
    seed: int = 2


def generate_umap_visualization(
    data_clean: pd.DataFrame,
    signatures: Dict[str, List],
    sample_name: str,
    signature_key: str,
    n_neighbors: int = 10,
    min_dist: float = 0.1,
    random_state: int = 93
):
    """Generate UMAP visualization with color coding based on signatures and sample"""
    
    # Validate inputs
    if signature_key not in signatures:
        raise ValueError(f"signature_key '{signature_key}' not found in signatures dictionary")
    
    if 'code_oncotree' not in data_clean.columns:
        raise ValueError("'code_oncotree' column not found in data_clean")
    
    if sample_name not in data_clean.index:
        raise ValueError(f"sample_name '{sample_name}' not found in data_clean index")
    
    # Get signature values to filter by
    signature_values = signatures[signature_key]
    
    # Prepare data for UMAP
    X = data_clean[signature_values].values
    
    # Generate UMAP embedding
    reducer = UMAP(
        n_neighbors=n_neighbors,
        min_dist=min_dist,
        random_state=random_state,
        n_components=2
    )
    embedding = reducer.fit_transform(X)
    
    # Create color array
    colors = []
    for idx in data_clean.index:
        if idx == sample_name:
            colors.append('#B3001B')
        elif data_clean.loc[idx, 'code_oncotree'] == signature_key:
            colors.append('#0468BF')
        else:
            colors.append('silver')
    
    # Create visualization
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Plot points in order
    for color_name, color_code, label in [
        ('silver', 'silver', 'Other'),
        ('#0468BF', '#0468BF', f'{signature_key}'),
        ('#B3001B', '#B3001B', sample_name)
    ]:
        mask = np.array(colors) == color_code
        if np.any(mask):
            ax.scatter(
                embedding[mask, 0],
                embedding[mask, 1],
                c=color_code,
                label=label,
                alpha=0.7 if color_code != '#B3001B' else 1.0,
                s=60 if color_code != '#B3001B' else 100,
                edgecolors='black' if color_code == '#B3001B' else 'white',
                linewidths=1 if color_code == '#B3001B' else 0.5,
                zorder=1 if color_code == 'silver' else (2 if color_code == '#0468BF' else 3)
            )
    
    ax.set_xlabel('UMAP 1', fontsize=6)
    ax.set_ylabel('UMAP 2', fontsize=6)
    ax.set_title(f'UMAP Visualization - {sample_name}', fontsize=10, fontweight='bold')
    ax.legend(loc='best', framealpha=0.9)
    
    plt.tight_layout()
    
    return fig


# ===================== API ENDPOINTS =====================


# Prediction function


def probabilities_calculator(models: dict, input_data: pd.DataFrame) -> dict:
    """
    models: dict of tumor models
    input_data: dict with protein:value pairs (one sample)
    """
    input_df = input_data.copy()  # Convert single sample to DataFrame
    predictions = {}

    for tumor_entity, model in models.items():
        missing_proteins = []

        # Ensure all required proteins exist
        for feature in models[tumor_entity].feature_names_in_:
            if feature not in input_df.columns:
                input_df[feature] = 0
                missing_proteins.append(feature)

        print(f"{len(missing_proteins)} proteins added for {tumor_entity}")

        # Predict probability of class 1
        pred_prob = model.predict_proba(input_df[models[tumor_entity].feature_names_in_])[:, 1]
        predictions[tumor_entity] = float(pred_prob)

    return predictions


def generate_prodict_visualization(predictions: dict):

    row = pd.Series(predictions)

    fig, ax = plt.subplots(figsize=(4, 6))
    ax.hlines(y=row.index, xmin=0, xmax=row.values, color='lightgrey', lw=2)

    # Plot each dot with conditional color
    for feature, value in row.items():
        color = 'red' if value > 0.9 else 'steelblue' if value > 0.5 else 'grey'
        ax.plot(value, feature, 'o', color=color, markersize=8)

    # Add threshold lines
    ax.axvline(x=0.5, color='grey', lw=1, linestyle='--')
    ax.axvline(x=0.9, color='black', lw=1, linestyle='--')

    # Labels
    ax.set_xlabel("Probability")

    # Remove frame box (keep only x & y axes)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(True)
    ax.spines['left'].set_visible(True)

    # Layout and export as SVG
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='svg', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    return buf.getvalue().decode('utf-8')


@patient_report_page.route(PatientReportApiRoutes.PRODICT_PROBABILITES_UMAP)
# http://localhost:3832/cohort_index/patients/patient_id/prodict/score"
def get_probabilities(cohort_index, patient):
    """Returns entity scores for a given patient"""
    try:

        data_df = patient_data_collection(cohort_index, patient)
        if data_df is None or data_df.empty:
            return jsonify({"error": "No input data received"}), 400

        # Convert DataFrame to correct input format... MUST input beforehand 
        input_data = data_df.T.fillna(0)
        predictions = probabilities_calculator(models, input_data)

        svg_output = generate_prodict_visualization(predictions)
        plt.close('all')

        return Response(svg_output, mimetype='image/svg+xml')

    except Exception as e:
        return jsonify({"error during prediction": str(e)}), 50


# patient_PROdictions.route(ApiRoutes.PATIENT_PRODICT_UMAP)
""" async def generate_umap(
    data_file: UploadFile = File(..., description="CSV file with protein intensity data"),
    metadata_file: UploadFile = File(..., description="CSV file with metadata"),
    signatures_file: UploadFile = File(..., description="JSON file with signatures"),
    params: str = Form(..., description="JSON string of UMAPRequest parameters")
):
    ""
    Generate UMAP visualization from uploaded data files
    
    Parameters:
    - data_file: CSV with protein intensity data
    - metadata_file: CSV with metadata including 'code_oncotree' column
    - signatures_file: JSON file with signature dictionary
    - params: JSON string containing UMAPRequest parameters
    ""
    
    try:
        # Parse parameters
        request_params = UMAPRequest.parse_raw(params)
        
        # Read uploaded files
        data = pd.read_csv(data_file.file, index_col=0)
        metadata = pd.read_csv(metadata_file.file, index_col=0)
        signatures = json.load(signatures_file.file)
        
        # Process data
        metadata_oncotree = metadata['code_oncotree']
        
        # Formatting, imputing and removing NAs
        data_initial = data.iloc[:, :int(data.shape[1]/2)].T
        data_initial.index = data_initial.index.str.removeprefix('pat_')
        
        imputed_data = impute_normal_down_shift_distribution(
            data_initial,
            column_wise=True,
            width=request_params.width,
            downshift=request_params.downshift,
            seed=request_params.seed
        )
        
        data_clean = imputed_data.dropna(axis=1, how='all')
        data_clean['code_oncotree'] = metadata_oncotree

        # Generate UMAP figure
        fig = generate_umap_visualization(
            data_clean=data_clean,
            signatures=signatures,
            sample_name=request_params.sample_name,
            signature_key=request_params.signature_key,
            n_neighbors=request_params.n_neighbors,
            min_dist=request_params.min_dist,
            random_state=request_params.random_state
        )

        # Save figure to bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=umap_{request_params.sample_name}.png"}
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
 """


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


    fig, ax = plt.subplots(figsize=figsize)

    sns.stripplot(
        data=df_long[~df_long["subcohort"]],
        x="Gene names",
        y="Expression",
        order=gene_order,
        color="grey",
        alpha=0.5,
        jitter=True,
        size=3,
        ax=ax,
    )

    sns.stripplot(
        data=df_long[df_long["subcohort"]],
        x="Gene names",
        y="Expression",
        order=gene_order,
        color="mediumblue",
        alpha=0.5,
        jitter=True,
        size=3,
        ax=ax,
    )

    sns.stripplot(
        data=df_long[df_long["highlight"]],
        x="Gene names",
        y="Expression",
        order=gene_order,
        color="red",
        jitter=True,
        size=5,
        ax=ax,
    )

    for tick in ax.get_xticklabels():
        gene = tick.get_text()
        if highlight_genes.get(gene, False):
            tick.set_color("red")

    ax.axhline(y=2, linestyle='--', color='red', zorder=10)

    ax.set_xticks(ax.get_xticks())
    ax.set_xticklabels(ax.get_xticklabels(), rotation=60, ha='right', rotation_mode='anchor')
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    ax.tick_params(axis='x', which='both', length=0)
    ax.tick_params(axis='y', which='both', length=0)

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="svg")
    buf.seek(0)
    svg_data = buf.getvalue().decode("utf-8")
    plt.close(fig)
    return svg_data