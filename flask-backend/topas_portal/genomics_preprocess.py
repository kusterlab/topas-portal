# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import TYPE_CHECKING
import pandas as pd

import topas_portal.utils as utils

# for type hints only
if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


import requests


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