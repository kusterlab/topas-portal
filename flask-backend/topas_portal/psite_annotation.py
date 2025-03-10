# retrieved from the wp3_pipeline
import pandas as pd
from itertools import compress
import psite_annotation as pa
import db


cohorts_db = db.cohorts_db
pspFastaFile = cohorts_db.config.config['pspFastaFile']
pspAnnotationFile = cohorts_db.config.config['pspAnnotationFile']
pspRegulatoryFile = cohorts_db.config.config['pspRegulatoryFile']


def phospho_annot(
    df: pd.DataFrame,
    pspFastaFile=pspFastaFile,
    pspAnnotationFile=pspAnnotationFile,
    pspRegulatoryFile=pspRegulatoryFile,
) -> pd.DataFrame:
    """
    Phospho-site annotation of experimental data using in-house developed tool (MT) based mainly on Phosphosite Plus but also in vitro
    experiments from the lab of Ishihama.

    :param df: dataframe with measured peptide intensities
    :param pspFastaFile: file used for adding peptide and psite positions
    :param pspKinaseSubstrateFile: file used for adding kinase substrate annotation
    :param pspAnnotationFile: file used for adding annotations from Phosphosite Plus
    :param pspRegulatoryFile: file used for adding regulatory information
    """
    try:
        df = df.reset_index(level="Modified sequence")
        df = pa.addPeptideAndPsitePositions(
            df, pspFastaFile, pspInput=True, returnAllPotentialSites=False
        )
        df = pa.addPSPAnnotations(df, pspAnnotationFile)
        df = pa.addPSPRegulatoryAnnotations(df, pspRegulatoryFile)

        df["PSP_LT_LIT"] = df["PSP_LT_LIT"].apply(lambda x: max(x.split(";")))
        df["PSP_MS_LIT"] = df["PSP_MS_LIT"].apply(lambda x: max(x.split(";")))
        df["PSP_MS_CST"] = df["PSP_MS_CST"].apply(lambda x: max(x.split(";")))
        df.rename(
            columns={"Site positions": "Site positions identified (MQ)"}, inplace=True
        )
        df = pa.addPeptideAndPsitePositions(
            df, pspFastaFile, pspInput=True, returnAllPotentialSites=True
        )
    except Exception as e:
        print(e)
        pass
    return df


def add_psp_urls(pp: pd.DataFrame) -> pd.DataFrame:
    """
    Function to add column to dataframe with URLs to proteins/isoforms that the
    peptides in the data belongs to:  https://www.phosphosite.org/. It uses already
    annotated information from PSP to check if any annotation exists. If it does, the URL
    is created from template and concatenated with the uniprot ID.

    :param pp: df to annotate with URL to PhosphoSitePlus
    :return: df with added annotation of URL to PhosphoSitePlus
    """
    pp[["PSP_URL", "PSP_URL_extra"]] = pp[["Start positions", "Proteins"]].apply(
        add_url_columns, axis=1, result_type="expand"
    )
    return pp


def add_url_columns(row):
    start_positions, proteins = row
    # create boolean list for (p-site, protein) pairs found in PSP or not
    # check for any modified peptide with start position different from -1
    found_psites = [
        int(value) > 0 for value in start_positions.split(";") if value != ""
    ]
    # row[0] is integer index of row and row[1] is column value
    proteins = list(compress(proteins.split(";"), found_psites))

    URLs = list()
    main_url = ""
    main_found = False

    # There can be found more than one main protein URL but then the first is used
    # and the rest goes with the isoform URLs
    url_start = "https://www.phosphosite.org/uniprotAccAction?id="
    for index, protein in enumerate(proteins):
        # don't allow isoforms (recognizable by "-" in their protein IDs) as main protein
        if "-" not in protein and not main_found:
            main_url = '=HYPERLINK("' + str(url_start) + str(protein) + '")'
            main_found = True
        else:
            URLs.append(str(url_start) + str(protein))

    return main_url, URLs
