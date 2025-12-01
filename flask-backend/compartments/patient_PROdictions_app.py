import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import joblib
import json
import db
import os
import io

from pydantic import BaseModel
from typing import Dict, List, Optional
from umap import UMAP
from pathlib import Path

from sklearn.linear_model import LogisticRegression
from flask import Blueprint, jsonify, request, Response
from topas_portal import utils
from topas_portal import settings 
from topas_portal.routes import ApiRoutes


patient_PROdictions = Blueprint(
    "patient_PROdictions",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db

# calculates the probability of tumor type for each patient.
# Takes full proteome data, it need to be imputes, or take an imputed fullproteome dataframe.


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


@patient_PROdictions.route(ApiRoutes.PATIENT_PRODICT_SCORES)
# http://localhost:3832/patient_entity_score/0/05BR029-T2
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

        return Response(svg_output, mimetype='image/svg+xml')

    except Exception as e:
        return jsonify({"error during prediction": str(e)}), 500

# patient_PROdictions.route(ApiRoutes.PATIENT_PRODICT_UMAP)
def generate_umap_endpoint(
    data_file,
    metadata_file ,
    signatures_file ,
    params: str 
):
    """
    Generate UMAP visualization from uploaded data files
    
    Parameters:
    - data_file: CSV with protein intensity data
    - metadata_file: CSV with metadata including 'code_oncotree' column
    - signatures_file: JSON file with signature dictionary
    - params: JSON string containing UMAPRequest parameters
    """
    
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

