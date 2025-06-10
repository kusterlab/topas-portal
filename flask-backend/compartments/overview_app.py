
from topas_portal.plotly_preprocess import get_piechart
from flask import Blueprint, jsonify
from topas_portal import settings
import db
import pandas as pd



overview_page = Blueprint(
    "overview_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db

def get_entity_count(meta_df,meta_type:str,least_number:int=10):
    """
    meta_df: pd.dataframe: it is the patients meta data
    meta_type:str : the meta data to make the plot based on
    least_number: the minimum number to make a group based on 
    """
    meta_df['meta_data_size'] = meta_df.groupby([meta_type]).transform('size')
    meta_df[meta_type][meta_df['meta_data_size'] < least_number] = 'others'
    countsdata = meta_df[meta_type].value_counts()
    value_list = countsdata.tolist()
    label_list = countsdata.index.tolist()
    return get_piechart(label_list,value_list)



@overview_page.route("/overview/entity_count/<cohort_ind>/<meta_type>/<least_number>")
# http://localhost:3832/overview/entity_count/0/code_oncotree/10
def get_entity_scores_cohort(cohort_ind,meta_type,least_number):
    return get_entity_count(cohorts_db.get_patient_metadata_df(cohort_ind).copy(),meta_type=meta_type,least_number=int(least_number))


# http://localhost:3832/overview/meta_types
@overview_page.route("/overview/meta_types")
def get_meta_types():
    return jsonify(settings.COMMON_META_DATA)

    

@overview_page.route("/overview/mod_seq_type/<cohort_ind>")
# http://localhost:3832/overview/mod_seq_type/0
def get_phospho_data_type(cohort_ind):
    df = cohorts_db.get_psite_abundance_df(cohort_ind).dropna(how='all')
    df['mod_type'] = None
    df['mod_type'][df.index.str.contains('pT')] = 'Phospho Threonine'
    df['mod_type'][df.index.str.contains('pS')] = 'Phospho Serine'
    df['mod_type'][df.index.str.contains('pY')] = 'Phospho Tyrosine'
    countsdata = df['mod_type'].value_counts()
    value_list = countsdata.tolist()
    label_list = countsdata.index.tolist()
    return get_piechart(label_list,value_list)


