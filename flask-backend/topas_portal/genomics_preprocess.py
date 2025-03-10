# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path
import pandas as pd

import topas_portal.utils as utils

# for type hints only
if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


import requests


AUTHENTICATION_KEY = "Bearer  d7eeee3f-cb5a-4c5d-8f95-5a85f7de61c2"  # this token was from FH and is valid for 180 days since 24/04/2024
# the key for the authentication can be retrieved after registering in the OncoKB portal


def get_data_from_the_ONKOKB_api(
    gene_name, alteration, AUTHENTICATION_KEY=AUTHENTICATION_KEY, data_type="oncogenic"
):
    """
    this function retrives the oncoKB annoation from oncoKB API as string
    :gene_name: is the symbol gene name
    :alteration is the SNV mutation like R989H
    :data_type is the field you like to extract
    """
    url = f"https://www.oncokb.org/api/v1/annotate/mutations/byProteinChange?hugoSymbol={gene_name}&alteration={alteration}"
    headers = {"accept": "application/json", "Authorization": AUTHENTICATION_KEY}
    final = requests.get(url, headers=headers).json()[data_type]
    # logger.info(f'{final} for ## {alteration} ## on {gene_name}')
    return final


def get_cnv_from_the_ONKOKB_api(
    gene_name, cnv_type="AMPLIFICATION", AUTHENTICATION_KEY=AUTHENTICATION_KEY
):
    """
    this function retrives the copynumber variation from oncoKB API as JSON
    :gene_name: is the symbol gene name
    :cnv_type: can be deletion
    """
    url = f"https://www.oncokb.org/api/v1/annotate/copyNumberAlterations?hugoSymbol={gene_name}&copyNameAlterationType={cnv_type}"
    headers = {"accept": "application/json", "Authorization": AUTHENTICATION_KEY}
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
        return annotated_abundance_df
    except Exception as err:
        print(f"{type(err).__name__}: {err} in merging with Genomics data")
        return abundances_df
