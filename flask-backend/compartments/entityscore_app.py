import pandas as pd
import pickle
import numpy as np
from flask import Blueprint, jsonify

import db
from topas_portal import utils
from topas_portal import settings 


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



def get_the_probalities_df(df_Z_scores_clean,final_models):
    all_probalities = {x:calculation_entity_probabilities(df_Z_scores_clean,final_models[x]) for x in list(final_models.keys())}
    first_key = list(final_models.keys())[0]
    ref_model_df = all_probalities[first_key]
    ref_model_df = ref_model_df.rename(columns={'Probability':first_key})
    list_all_entities = list(all_probalities.keys())
    list_all_entities.remove(first_key)
    for entity in list_all_entities:
        try:
            other_entity_df = all_probalities[entity]
            other_entity_df = other_entity_df.rename(columns={'Probability':entity})
            ref_model_df = ref_model_df.merge(other_entity_df,on='Gene names',how='outer')
        except:
            continue
        
    ref_model_df = ref_model_df.round(3)
    return ref_model_df.rename(columns={utils.ColumnNames.GENE_NAME:utils.ColumnNames.SAMPLE_NAME})



def run_preprocessing_pipeline(df_Z_scores_cj,FINAL_MODELS_PICKLE):
    model_proteins, final_models = prepare_model_proteins(FINAL_MODELS_PICKLE)

    #df_normalized_ = do_protein_normalization(PROTEINS_NORMALIZED_PICKLE,model_proteins,df_prt_,df_ent_)
    df_Z_scores_clean = do_protein_imputaiton(df_Z_scores_cj,model_proteins)
    return df_Z_scores_clean, final_models



def prepare_model_proteins(picklize_file_path):
    final_models = read_picke_file(picklize_file_path)
    model_prote = []
    for i in final_models.values():
        model_prote += list(i.columns)   

    model_prote = set(model_prote)
    model_prote.remove('Intercept')
    model_prote.remove('F1_1')
    model_prote.remove('F1_0')
    model_prote.remove('F1_weighted')
    model_prote.remove('MCC_score')
    model_proteins = list(model_prote)
    return model_proteins, final_models


def calculation_entity_probabilities (df_clean , df_coefficients):
    """
    df_clean: Dataframe used for calculate coefficients. Initial dataset, with  Sample name	+ code_oncotree + proteins intensities. and imputated, or removed NaN values 
    
    df_coefficients: result from the coefficients analysis, obtained from the function "log_reg_results_stats"
    example: CHDM_probs = calculation_entity_probabilities(df_Z_scores_clean,final_models['CHDM'])
    
    """  
    try:  
        df = df_clean.iloc[:, :1].copy()
        
        # Initialize coeff with the appropriate shape based on df_initial_HO
        coeff = np.zeros(df.shape[0])
        
        for i in df_coefficients.iloc[:, :-5].columns:
            print(i)
            try:
                # Perform dot product and accumulate results in coeff
                coeff += df_clean[i] * df_coefficients.iloc[0][i]
            except KeyError:
                print(f"Protein {i} not found. Check its intensity")
                continue
        
        coeff_sum = coeff
        probability = logistic_function(coeff_sum + df_coefficients.iloc[0]['Intercept'])
        
        # Insert probability into df
        df.insert(1, "Probability", probability)
        return df
    except:
        return pd.DataFrame()



def picklize_file(what_to_picklize:dict,where_to_save:str):
    import pickle
    # save dictionary to person_data.pkl file
    with open(where_to_save, 'wb') as fp:
        pickle.dump(what_to_picklize, fp)
        print('dictionary saved successfully to file')



def logistic_function(x):    
    return 1/ (1 + np.exp(-x))



def normalization_new_data(dataframe, dict_mean_std):
    normalized_df = dataframe.copy()
    for column in dataframe.columns:
        if column in dict_mean_std:
            mean = dict_mean_std[column]['mean']
            std = dict_mean_std[column]['std']
            normalized_df[column] = (dataframe[column] - mean) / std
    return normalized_df
    


def impute_normal_down_shift_distribution(unimputerd_dataframe:pd.DataFrame ,column_wise=True, width=0.3, downshift=1.8, seed=2):
    """ 
    Performs imputation across a matrix columnswise
    https://rdrr.io/github/jdreyf/jdcbioinfo/man/impute_normal.html#google_vignette
    :width: Scale factor for the standard deviation of imputed distribution relative to the sample standard deviation.
    :downshift: Down-shifted the mean of imputed distribution from the sample mean, in units of sample standard deviation.
    :seed: Random seed
    
    """
    print('The size of the data Frame before imputation')
    print(unimputerd_dataframe.shape)
    unimputerd_df = unimputerd_dataframe.iloc[:,:]
    unimputerd_matrix = unimputerd_df.replace({pd.NA: np.nan}, inplace=True) #Added to modify pandas's NAN values into  numpy NAN values
    unimputerd_matrix = unimputerd_df.to_numpy()
    columns_names = unimputerd_df.columns
    rownames = unimputerd_df.index
    unimputerd_matrix[~np.isfinite(unimputerd_matrix)] = None
    main_mean = np.nanmean(unimputerd_matrix)
    main_std = np.nanstd(unimputerd_matrix)
    np.random.seed(seed = seed)
    def impute_normal_per_vector(temp:np.ndarray,width=width, downshift=downshift):
        """ Performs imputation for a single vector """
        if column_wise:
            temp_sd = np.nanstd(temp)
            temp_mean = np.nanmean(temp)
        else:
            # over all matrix
            temp_sd = main_std
            temp_mean = main_mean

        shrinked_sd = width * temp_sd
        downshifted_mean = temp_mean - (downshift * temp_sd) 
        n_missing = np.count_nonzero(np.isnan(temp))
        temp[np.isnan(temp)] = np.random.normal(loc=downshifted_mean, scale=shrinked_sd, size=n_missing)
        if n_missing > 0:
            print 
        return temp
    final_matrix = np.apply_along_axis(impute_normal_per_vector, 0, unimputerd_matrix)
    final_df = pd.DataFrame(final_matrix)
    final_df.index = rownames
    final_df.columns = columns_names
    
    return final_df




def clean_df (intensity_df:pd.DataFrame, metadata_df:pd.DataFrame ):
    intensity_df = intensity_df.transpose()
    intensity_df.reset_index(inplace=True)
    intensity_df = intensity_df.rename(columns=intensity_df.iloc[0]).drop([0])
    #return intensity_df
    metadata_df = metadata_df[[utils.ColumnNames.SAMPLE_NAME, "code_oncotree"]] #Selection of columns for later concatenate
    intensity_df[utils.ColumnNames.GENE_NAME] = intensity_df[utils.ColumnNames.GENE_NAME].str.replace('pat_','',regex=True)
    df_merged = metadata_df.merge(intensity_df, left_on=utils.ColumnNames.SAMPLE_NAME, right_on=utils.ColumnNames.GENE_NAME) #merging both data sets by Sample Name
    df_merged.drop(utils.ColumnNames.GENE_NAME, axis=1, inplace=True)
    return df_merged




def read_picke_file(file_name:str):
    with (open(file_name, "rb")) as openfile:
        while True:
            try:
                return pickle.load(openfile)
            except EOFError:
                break




def do_protein_normalization(path_to_picke_file,model_proteins,df_prt_,df_ent_):
    prot_norm_stats = read_picke_file(path_to_picke_file)
    df_raw = clean_df (df_prt_,df_ent_)  # Creating dataset with patien info + prot intensities
    df_raw  #Dataset with all samples and all proteins intensities. Cotains NANs
    raw_df_intensities_ = pd.concat([df_raw.iloc[:,:2], df_raw.filter(items=model_proteins)], axis=1) #filter by proteins that are only used by models 
    df_normalized_ = normalization_new_data(raw_df_intensities_, prot_norm_stats)
    return df_normalized_




def do_protein_imputaiton(df_Z_scores_cj,model_proteins):
    df_Z_scores = df_Z_scores_cj.transpose(copy=True) #Transforming Z-scores file to obtain values and info
    df_Z_scores = df_Z_scores.reset_index()
    df_Z_scores = df_Z_scores.replace('zscore_','', regex=True) 
    df_Z_scores.rename(columns = df_Z_scores.iloc[0], inplace=True)
    df_Z_scores.drop(axis=0, index=0, inplace=True)
    df_Z_scores = pd.concat([df_Z_scores.iloc[:,:2], df_Z_scores.filter(items=model_proteins)], axis=1)# filter by proteins from model 
    df_z_imputed = impute_normal_down_shift_distribution(df_Z_scores.iloc[:,1:]) #Imputated dataframe of the Z-scored values
    # Checking for possible remaining columns/proteins still with NA values
    na_columns = df_z_imputed.isna().any()
    # Filter to get only columns where there are NaN values
    na_columns_true = na_columns[na_columns].index.tolist()
    print("Columns with NaN values:", na_columns_true)
    return pd.concat([df_Z_scores.iloc[:,0], df_z_imputed], axis=1)# filter by proteins from model 




@entityscore_page.route("/entityscore/classifiers_list")
# http://localhost:3832/entityscore/classifiers_list
def get_list_classifiers():
    MODELS_LIST = cohorts_db.config.config.get('models_list', [])
    return jsonify(MODELS_LIST)





@entityscore_page.route("/entityscore/<cohort_ind>")
# http://localhost:3832/entityscore/0
def get_entity_scores_cohort(cohort_ind):
    """"""

    df_Z_scores = cohorts_db.get_protein_abundance_df(cohort_ind,intensity_unit=utils.IntensityUnit.Z_SCORE)
    df_Z_scores[utils.ColumnNames.GENE_NAME] = df_Z_scores.index
    first_column = df_Z_scores.pop(utils.ColumnNames.GENE_NAME) 
    df_Z_scores.insert(0, utils.ColumnNames.GENE_NAME, first_column) 
    df_Z_scores.reset_index(drop=True, inplace=True)

    df_ent_ = cohorts_db.get_patient_metadata_df(cohort_ind)
    df_Z_scores_clean, final_models = run_preprocessing_pipeline(df_Z_scores,FINAL_MODELS_PICKLE)
    all_probalities = get_the_probalities_df(df_Z_scores_clean,final_models)
    all_probalities = all_probalities.fillna(0)
    all_probalities[utils.ColumnNames.SAMPLE_NAME] = all_probalities[utils.ColumnNames.SAMPLE_NAME].str.replace(settings.PATIENT_PREFIX,'',regex=True)
    try:
        final_df = all_probalities.merge(df_ent_[[utils.ColumnNames.SAMPLE_NAME,'code_oncotree']],on=utils.ColumnNames.SAMPLE_NAME)
    except:
        final_df = all_probalities  # in case code_oncotree does not exist in the data
    list_cols_to_exclude = ['EPIS','DDLS','MPNS','MFH'] # these classifiers are not reliable
    list_cols_to_exclude = [x for x in list_cols_to_exclude if x in  final_df.columns]
    try:
        final_df = final_df.drop(columns = list_cols_to_exclude)
    except:
        pass
    print(final_df.columns)
    return utils.df_to_json(final_df)

