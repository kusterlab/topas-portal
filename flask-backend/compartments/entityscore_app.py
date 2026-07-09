import pandas as pd
import pickle
import numpy as np
from flask import Blueprint, jsonify

import db
from topas_portal import utils
from topas_portal import settings
import compartments.patient_report.utils as prutils
import topas_portal.utils as common_utils
from topas_portal.constants import IntensityUnit
from sklearn.preprocessing import StandardScaler

cohorts_db = db.cohorts_db
config = cohorts_db.config


entityscore_page = Blueprint(
    "entityscore_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db

# the list of parameters in the config file of the portal
FINAL_MODELS_PICKLE = cohorts_db.config.config.get('entity_models', '')
PROTEINS_NORMALIZED_PICKLE = cohorts_db.config.config.get('entity_models_normalized', '')
MODELS = prutils.load_sklearn_models(config.get_models_folder())
NORMALIZATION_PARAMS = prutils.load_normalization_parameters(config.get_prodict_normalization_parameters())


def probabilities_calculator(models: dict, input_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates the probability of a sample for every classifier avaialeble
    models: dict of classifier models
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
        pred_prob = model.predict_proba(
            input_df[models[tumor_entity].feature_names_in_]
        )[:, 1]
        print('-' * 50)
        print(type(pred_prob))
        print(len(pred_prob))
        print('-' * 50)
        predictions[tumor_entity] = pred_prob


    return pd.DataFrame(predictions)


def normalize_dataframe(df: pd.DataFrame, normalization_params: StandardScaler) -> pd.DataFrame:
    """
    Normalizes the input DataFrame using the provided normalization parameters.
    df: Intensities with gene names as columns and samples as rows
    normalization_params: sklearn object containing mean and scale for each feature used during model training
    """

    try:
        expected = pd.Index(normalization_params.feature_names_in_)
        common = expected.intersection(df.columns)

        if len(common) == 0:
            print("Normalization not successful. No matching columns found.")
            return None

        normalized_df = df.copy()

        idx = expected.get_indexer(common)

        values = normalized_df.loc[:, common].to_numpy(dtype=np.float64, copy=True)

        values = (
            values - normalization_params.mean_[idx]
        ) / normalization_params.scale_[idx]

        normalized_df.loc[:, common] = values

        return normalized_df

    except Exception as e:
        print(f"Normalization not successful. Error: {e}.")
        return None


@entityscore_page.route("/entityscore/classifiers_list")
# http://localhost:3832/entityscore/classifiers_list
def get_list_classifiers():
    MODELS_LIST = cohorts_db.config.config.get('models_list', [])
    return jsonify(MODELS_LIST)


@entityscore_page.route("/entityscore/<cohort_ind>")
# http://localhost:3832/entityscore/0
def get_entity_scores_cohort(cohort_ind):
    """"""
    models = MODELS
    normalization_params = NORMALIZATION_PARAMS

    data_intensities = cohorts_db.get_protein_abundance_df(
        cohort_ind, intensity_unit=IntensityUnit.INTENSITY)

    data_imputed = prutils.impute_normal_down_shift_distribution(data_intensities)
    data_imputed = data_imputed.T

    data_normalized = normalize_dataframe(data_imputed, normalization_params)

    predictions = probabilities_calculator(models, data_normalized)
    predictions.index = data_normalized.index

    df_ent_ = cohorts_db.get_patient_metadata_df(cohort_ind)
    df_ent_ = df_ent_.set_index("Sample name", drop=False)
    predictions = predictions.join(df_ent_[['Sample name', 'code_oncotree']], how='left')


    return utils.df_to_json(predictions)

