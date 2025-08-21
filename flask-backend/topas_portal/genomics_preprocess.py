# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import TYPE_CHECKING
import pandas as pd

import topas_portal.utils as utils

# for type hints only
if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


import requests



def split_fusion(x):
    if str(x).__contains__(','): 
        x0 = x.split('|')[0]
        x1 = x.split('|')[1].split(',')[0]
        x2 = x.split('|')[1].split(',')[1]
        return [f'{x0}|{x1}',f'{x0}|{x2}']
    else:
        return [x]
    
    
def get_all_fusions_per_NGS(x,fusion_dic,pattern_alteration = r'[A-Z1-9]+\|[A-Z1-9,]+'):
    try:
        all_alteration = x.split('_fusion:')[-1]     
        all_matches = re.finditer(pattern_alteration,all_alteration)
        all_possibilities = [split_fusion(match.group()) for match in all_matches]
        return (';').join([fusion_dic.get(x,x) for x in list(set(sum(all_possibilities,start=[])))])
    except:
        return ''


def get_all_cnvs_per_NGS(x,gene_name,cnv_dic,pattern_alteration = r'AMP|DEL|GAIN|LOSS'):
    onkokb_definitions = {'AMP':'AMPLIFICATION','DEL':'DELETION'}
    try:
        all_alteration = x.split('_snv:')[0]
        all_matches = re.finditer(pattern_alteration,all_alteration)
        all_possibilities = [[match.group()] for match in all_matches]
        res = [f'{gene_name}_{onkokb_definitions.get(x,x)}' for x in list(set(sum(all_possibilities,start=[])))]
        return (';').join([cnv_dic.get(x,x) for x in list(set(res))])
    except:
        return ''
    



def get_all_snv_per_NGS(X,protein_name,snv_dic,pattern_alteration = r'p.[A-Z][0-9]+[A-Z]'):
    """
    This function is the wrapper around the function for extracting the SNVs
    :X: should be like cnv:CNN_snv:C_T_exonic_20_P266S_fusion:n.d        if it is multi they shold be seprated by ;
    """
    try:


        all_alteration = X.split('snv:')[-1].split('fusion:')[0]
        all_matches = re.finditer(pattern_alteration,all_alteration)
        all_possibilities = [match.group() for match in all_matches]

        if len(all_possibilities) > 0:
            res = [f'{protein_name}_{x}' for x in all_possibilities]
            return (';').join([snv_dic.get(x,x) for x in list(set(res))])
        else:
            return ''
    except:
        return ''




    
def add_onkokb_annotation(df,genomics_df,gene_name, onkokb_dic,column_name='fusion_onkoKB'):
    try:
        
        sub_df = genomics_df[['Sample name',gene_name]]
        
        if column_name == 'fusion_onkoKB':
            function_to_get = get_all_fusions_per_NGS
            sub_df[column_name] = sub_df[gene_name].apply(lambda x:function_to_get(x,onkokb_dic))
            
        if column_name == 'cnv_onkoKB':
            function_to_get = get_all_cnvs_per_NGS
            sub_df[column_name] = sub_df[gene_name].apply(lambda x:function_to_get(x,gene_name,onkokb_dic))
            
            
        if column_name == 'snv_onkoKB':
            function_to_get = get_all_snv_per_NGS
            sub_df[column_name] = sub_df[gene_name].apply(lambda x:function_to_get(x,gene_name,onkokb_dic))
            
            
            
        return df.merge(sub_df[['Sample name',column_name]],on='Sample name',how='left')
    except:
        return df





def _merge_onkokb_annotation(
    cohorts_db: data_api.CohortDataAPI,
    df:pd.dataFrame, 
    identifier: str
):
    try:
        genomics_df = cohorts_db.get_genomics()
        onkokb_dic = cohorts_db.get_oncoKB_annotations()
        df = add_onkokb_annotation(df, genomics_df, identifier, onkokb_dic,column_name='fusion_onkoKB')
        df = add_onkokb_annotation(df, genomics_df, identifier, onkokb_dic,column_name='cnv_onkoKB')
        df = add_onkokb_annotation(df, genomics_df, identifier, onkokb_dic,column_name='snv_onkoKB')
        df['fusion_onkoKB'] = df['fusion_onkoKB'].fillna('n.d.')
        df['cnv_onkoKB'] = df['cnv_onkoKB'].fillna('n.d.')
        df['snv_onkoKB'] = df['snv_onkoKB'].fillna('n.d.')
        return df
    except:
        return df




def get_data_from_the_ONKOKB_api(
    gene_name, alteration, oncokb_api_token, data_type="oncogenic"
):
    """
    this function retrives the oncoKB annoation from oncoKB API as string
    :gene_name: is the symbol gene name
    :alteration is the SNV mutation like R989H
    :data_type is the field you like to extract
    """
    if len(oncokb_api_token) == 0:
        return "{}"
    
    url = f"https://www.oncokb.org/api/v1/annotate/mutations/byProteinChange?hugoSymbol={gene_name}&alteration={alteration}"
    headers = {"accept": "application/json", "Authorization": f"Bearer  {oncokb_api_token}"}
    final = requests.get(url, headers=headers).json()[data_type]
    # logger.info(f'{final} for ## {alteration} ## on {gene_name}')
    return final


def get_cnv_from_the_ONKOKB_api(
    gene_name, cnv_type, oncokb_api_token
):
    """
    this function retrives the copynumber variation from oncoKB API as JSON
    :gene_name: is the symbol gene name
    :cnv_type: can be deletion
    """
    if len(oncokb_api_token) == 0:
        return "{}"
    
    url = f"https://www.oncokb.org/api/v1/annotate/copyNumberAlterations?hugoSymbol={gene_name}&copyNameAlterationType={cnv_type}"
    headers = {"accept": "application/json", "Authorization": f"Bearer  {oncokb_api_token}"}
    final = requests.get(url, headers=headers).json()
    return final


def get_genomics_alterations_per_identifier(
    cohorts_db: data_api.CohortDataAPI,
    identifier: str,
    annotation_type="genomics_annotations",
):
    if annotation_type == "genomics_annotations":
        genomics_df = cohorts_db.get_genomics()
    else:
        genomics_df = cohorts_db.get_oncoKB_annotations()

    identifiers_list = identifier.split(";")
    # this is to cover if only one protein of a protein group matches to the genomics data
    identifiers_list = utils.intersection(identifiers_list, genomics_df.columns)
    try:
        sub_df = genomics_df[[*["Sample name"], *identifiers_list]].set_index(
            "Sample name"
        )
        sub_df = sub_df.dropna()
        genomics_annotation_list = []

        for i in range(len(sub_df)):
            temp = sub_df.iloc[i, :].tolist()
            temp = (";").join(temp)
            genomics_annotation_list.append(temp)

        sub_df[annotation_type] = genomics_annotation_list
        return sub_df[[annotation_type]]
    except Exception as err:
        print(f"{type(err).__name__}: {err} in getting Genomics data")
        return f"Unexpected {err=}, {type(err)=}"


def _clean_annotation(x):
    return str(x).replace('cnv','').replace(':','').replace('_','')




def _split_genomics_annotation(x:str):
    try:
        if x == 'missing':
            return {'cnv':'missing','snv':'missing','fusion':'missing'}
        else:
            cnv = x.split('snv:')[0]
            snv = x.split('snv')[1].split('fusion:')[0]
            fusion = x.split('snv')[1].split('fusion:')[1]
            return {'cnv':_clean_annotation(cnv),'snv':_clean_annotation(snv),'fusion':_clean_annotation(fusion)}
    except:
        return {'cnv':'missing','snv':'missing','fusion':'missing'}



def make_final_genomics_annotation(df):
    try:
        df['snv'] = df.genomics_annotations.apply(lambda x:_split_genomics_annotation(x)['snv'])
        df['cnv'] = df.genomics_annotations.apply(lambda x:_split_genomics_annotation(x)['cnv'])
        df['fusion'] = df.genomics_annotations.apply(lambda x:_split_genomics_annotation(x)['fusion'])
    except:
        pass
    return df





def _merge_data_with_genomics_alterations(
    cohorts_db: data_api.CohortDataAPI,
    abundances_df: pd.DataFrame,
    identifier: str,
    annotation_type="oncoKB_annotations",
):
    """
    Merges data with genomic alterations, if available for the cohort.
    :abundances_df: a dataFrame with Sample name column
    :returns dataFrame with extra column with the name of annotation_type
    """
    try:
        genomics_alterations_df = get_genomics_alterations_per_identifier(
            cohorts_db, identifier, annotation_type=annotation_type
        )

        annotated_abundance_df = abundances_df.merge(
            genomics_alterations_df, right_index=True, left_on="Sample name", how="left"
        )
        annotated_abundance_df[annotation_type] = annotated_abundance_df[
            annotation_type
        ].fillna("missing")

        if annotation_type == "genomics_annotations":
            annotated_abundance_df = make_final_genomics_annotation(annotated_abundance_df)


        return annotated_abundance_df
    except Exception as err:
        print(f"{type(err).__name__}: {err} in merging with Genomics data")
        return abundances_df