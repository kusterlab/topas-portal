from pathlib import Path
import os
import json
from typing import List, Optional

from flask import jsonify, Blueprint, Response, request
import pandas as pd
import numpy as np

import db
import topas_portal.utils as ef
import topas_portal.settings as cn
import topas_portal.pca_umap as qc_meta
from topas_portal.dimensionality_reduction import get_pca_objects

from sklearn.metrics import silhouette_samples

qc_page = Blueprint(
    "qc_page", __name__, static_folder="../dist/static", template_folder="../dist"
)

cohorts_db = db.cohorts_db


def main(
    input_data_type: ef.DataType,
    cohort_index: str,
    dimensionality_reduction_method: str,
    use_ref: str,
    use_replicate: str,
    topas_genes: Optional[List[str]] = None,
    meta_col_silhoutte: str = "Paper Entity",
    do_only_silhouette: bool = False,
    min_num_patients: int = 4,
    before_cluster: bool = True,
    custom_list_patients = [],
    min_sample_occurrence_ratio = 0.9
):
    """
    Performs PCA or UMAP dimensionality reduction on proteomics or phospho-proteomics data 
    for a given cohort and returns the transformed data along with variance information.

    Args:
        input_data_type (ef.DataType): The type of input data (e.g., proteome, phospho-proteome).
        cohort_index (str): The index of the cohort to analyze.
        dimensionality_reduction_method (str): The method used for dimensionality reduction (e.g., PCA, UMAP).
        use_ref (str): Whether to include reference channels in the analysis ("ref" for True).
        use_replicate (str): Whether to include replicates in the analysis ("replicate" for True).
        topas_genes (Optional[List[str]]): A list of selected genes for analysis. Defaults to None.
        meta_col_silhoutte (str): Metadata column used for silhouette score calculation. Defaults to "Paper Entity".
        do_only_silhouette (bool): If True, only calculates silhouette scores. Defaults to False.
        min_num_patients (int): Minimum number of patients required for silhouette calculation. Defaults to 4.
        before_cluster (bool): If True, uses data before clustering for silhouette analysis. Defaults to True.
        custom_list_patients (Any): A list of patient sample names or 'all' to use all samples. Defaults to an empty list.
        min_sample_occurrence_ratio (float): Minimum required occurrence ratio for a sample to be considered. Defaults to 0.9.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "dataFrame": Transformed data with principal components (PCs) or UMAP.
            - "pcVars": A list containing the variance explained by the first two principal components.

    Raises:
        ValueError: If an unknown data type is provided for PCA/UMAP analysis.

    Notes:
        - Converts `cohort_index` to an integer.
        - Fetches sample annotation and metadata for the specified cohort.
        - Performs PCA or UMAP analysis on filtered data.
        - If `do_only_silhouette` is True, returns silhouette scores instead of dimensionality reduction results.
        - Scales the principal components between -1 and 1 for consistency.
    """
    cohort_index = int(cohort_index)

    use_ref = use_ref == "ref"
    use_replicate = use_replicate == "replicate"
    if topas_genes is None:
        print('No custom set of genes are selelcted')
        topas_genes = []

    
    # the column names of the two pc vectors
    pc_cols = cn.QC_PCS
    reports_dir = cohorts_db.config.get_report_directory(cohort_index)
    sample_annotation_df = cohorts_db.get_sample_annotation_df(cohort_index)
    
    # example: custom_list_patients = 'H021-UQBN7H-T2,H021-E381AV-T2-E2,H021-S1WQZ5-M1,H021-YTWLBM-T3-E1,H021-9DVBZG-M1-E2,H021-3P7FPW-T1-E1'
    custom_list_patients = 'all' if custom_list_patients== 'all' else (custom_list_patients).split(',')
    if not custom_list_patients == 'all':
        sample_annotation_df = sample_annotation_df[sample_annotation_df['Sample name'].isin(custom_list_patients)]

    if len(sample_annotation_df.index) > 0:
        patients_df = cohorts_db.get_patient_metadata_df(cohort_index)
        if not custom_list_patients == 'all':
            patients_df = patients_df[patients_df['Sample name'].isin(custom_list_patients)]
        all_principal_dfs, all_principal_variances, imputed_data, metadata_df = (
            qc_meta.do_pca(
                topas_genes,
                reports_dir,
                [input_data_type],
                sample_annotation_df,
                patients_df,
                min_sample_occurrence_ratio=min_sample_occurrence_ratio,
                include_reference_channels=use_ref,
                dimensionality_reduction_method=dimensionality_reduction_method,
                include_replicates=use_replicate,
            )
        )

        if do_only_silhouette:
            sil_input = []
            if before_cluster:
                sil_input = imputed_data[0]
            else:
                sil_input = pd.DataFrame(all_principal_dfs[0]).set_index("Sample name")
                sil_input = sil_input.filter(regex="Principal component")

            return calculate_silhouette_scores(
                sil_input,
                metadata_df.set_index("Sample name"),
                meta_col_silhoutte,
                min_num_patients=min_num_patients,
            )

        pc_df = pd.DataFrame(all_principal_dfs[0])
        pc_df = pc_df.rename(
            columns={"Principal component 1": "pc1", "Principal component 2": "pc2"}
        )
        pc_df["Sample name"] = pc_df["Sample"]
        pc_df = pc_df[["Sample name", "pc1", "pc2", "Sample"]]
        pc_df = ef.merge_with_sample_annotation_df(pc_df, sample_annotation_df)
        pc_df = ef.merge_with_patients_meta_df(pc_df, patients_df)
        pcs_vars = all_principal_variances[0]
        string_cols = cn.QC_STRING_META  # meta data with string values
        int_cols = cn.QC_INT_META  # meta data with number values
        sel_cols = [*pc_cols, *string_cols, *int_cols]
        sel_cols = ef.intersection(sel_cols, pc_df.columns)
        pc_df = pc_df[sel_cols]
        string_cols = ef.intersection(pc_df.columns, string_cols)
        int_cols = ef.intersection(pc_df.columns, int_cols)
        pc_df[string_cols] = pc_df[string_cols].fillna("n.d.")

        if "Batch_No" in pc_df.columns:
            pc_df["Batch_No"][pc_df["Sample"].str.contains("Batch")] = pc_df["Sample"][
                pc_df["Sample"].str.contains("Batch")
            ].apply(lambda x: x.split("Batch")[1])

        pc_df[int_cols] = pc_df[int_cols].fillna(-1)

    else:  # running PCA for the cohorts with no meta data
        if input_data_type == ef.DataType.PHOSPHO_PROTEOME:
            intensity_df = pd.read_csv(
                Path(reports_dir) / Path(cn.PREPROCESSED_PP_INTENSITY),
                index_col=cn.PP_KEY,
            )
        elif input_data_type == ef.DataType.FULL_PROTEOME:
            intensity_df = pd.read_csv(
                Path(reports_dir) / Path(cn.PREPROCESSED_FP_INTENSITY),
                index_col=cn.FP_KEY,
            )
        else:
            raise ValueError(f"Unknown data type for PCA/UMAP: {input_data_type.value}")


        list_patients = sample_annotation_df["Sample name"].unique().tolist()
        list_patients_suffixed = [cn.PATIENT_PREFIX + x for x in list_patients_suffixed]
        list_patients = [*list_patients,list_patients_suffixed]
        list_patients = ef.intersection(list_patients,df.columns)
        df = intensity_df[list_patients]
        pca_objects_list, pcs_vars = get_pca_objects(
            [df], pct_threshold=[0.5], do_pca=False
        )
        pc_df = pd.DataFrame(data=pca_objects_list[0].transform(), columns=cn.QC_PCS)
        pc_df = pc_df.reset_index()
        pc_df["Sample"] = df.columns

    var1 = 0
    var2 = 0
    if dimensionality_reduction_method == "ppca":
        var1 = round(pcs_vars[0], 2)
        var2 = round(pcs_vars[1], 2)

    # SCALING THE PCS BETWEEN -1 AND 1
    pc_df[pc_cols[0]] = np.interp(
        pc_df[pc_cols[0]], (pc_df[pc_cols[0]].min(), pc_df[pc_cols[0]].max()), (-1, +1)
    )
    pc_df[pc_cols[1]] = np.interp(
        pc_df[pc_cols[1]], (pc_df[pc_cols[1]].min(), pc_df[pc_cols[1]].max()), (-1, +1)
    )
    pc_df["index"] = pc_df.index
    pcs_dict = pc_df.to_dict(orient="records")
    pcs_dict = {"dataFrame": pcs_dict, "pcVars": [var1, var2]}

    return pcs_dict


def calculate_silhouette_scores(
    silhoutte_input_df: pd.DataFrame,
    meta_df: pd.DataFrame,
    meta_col_silhoutte: str,
    min_num_patients: int = 4,
) -> pd.DataFrame:
    """
    calculates the silhoette score per sample
    :silhoutte_input_df: an indexed data frame with the patients as the index
    :meta_data_df: an indexed data frame with the patient ids as the index
    :meta_col_silhouette: the column name used as the class labels
    """
    meta_data_df = meta_df.copy()
    count_dict = meta_data_df[meta_col_silhoutte].value_counts().to_dict()
    meta_data_df["count"] = meta_data_df[meta_col_silhoutte].map(count_dict)
    meta_data_df = meta_data_df[meta_data_df["count"] >= int(min_num_patients)]

    common_samples = ef.intersection(meta_data_df.index, silhoutte_input_df.index)
    silhoutte_input_df = silhoutte_input_df.loc[common_samples, :].to_numpy()
    meta_data = meta_data_df.loc[common_samples, meta_col_silhoutte].to_numpy()

    silhouete_df = pd.DataFrame(
        list(zip(silhouette_samples(silhoutte_input_df, meta_data), meta_data)),
        columns=["silhouette_score", "meta_data"],
    )

    silhouete_df.index = common_samples
    silhouete_df["sample"] = silhouete_df.index
    av_dict = silhouete_df.groupby("meta_data").mean().to_dict()
    silhouete_df["average"] = silhouete_df["meta_data"].map(av_dict["silhouette_score"])
    silhouete_df = silhouete_df.sort_values(
        by=["average", "meta_data", "silhouette_score"], ascending=[False, True, False]
    )

    silhouete_df.columns = ["value", "type", "label", "average"]
    colors_df = pd.DataFrame(
        list(
            zip(
                ef.ranodom_color_genetator(len(silhouete_df.type.unique())),
                silhouete_df.type.unique().tolist(),
            )
        )
    )
    colors_df.columns = ["color", "type"]
    colors_dict = colors_df.set_index("type").to_dict()["color"]
    silhouete_df["color"] = silhouete_df.type.map(colors_dict)
    return silhouete_df


#### QC routing functions
@qc_page.route("/qc/metadata")
def metadata():
    """The list of metadata to show in the QC coloring combobox"""
    list_of_metadataTypes = [*cn.QC_STRING_META, *cn.QC_INT_META]
    return jsonify(list_of_metadataTypes)


@qc_page.route(
    "/qc/all/<input_data_type>/<cohort_index>/<dimensionality_reduction_method>/<use_ref>/<use_replicate>/<custom_patients>/<imputation_ratio>"
)
# http://localhost:3832/qc/all/fp/Intensity/0/ppca/noref/replicate/0.9
def quality_control_all_genes(
    input_data_type,
    cohort_index,
    dimensionality_reduction_method,
    use_ref,
    use_replicate,
    custom_patients,
    imputation_ratio
):
    selected_genes = []  # if empty considers all genes
    imputation_ratio = float(imputation_ratio)
    PCA_umap_dic = main(
        ef.DataType(input_data_type),
        cohort_index,
        dimensionality_reduction_method,
        use_ref,
        use_replicate,
        topas_genes=selected_genes,
        custom_list_patients = custom_patients,
        min_sample_occurrence_ratio=imputation_ratio
    )
    return Response(json.dumps(PCA_umap_dic), mimetype="application/json")


@qc_page.route("/uploadGenes", methods=["POST"])
def useruploadGenes():
    """Upload a file with the names of the proteins one perline as a one column csv"""
    curr_dir = os.getcwd()
    selected_proteins_file = os.path.join(curr_dir, "selected_proteins.csv")
    if os.path.exists(selected_proteins_file):
        os.remove(selected_proteins_file)
    try:
        topas_file = request.files["file"]
        lines = topas_file.read().decode("UTF-8")
        lines = lines.splitlines()
        lines = list(filter(None, lines))
        df_proteins = pd.DataFrame(lines)
        df_proteins.columns = ["selected_genes"]
        df_proteins.to_csv(selected_proteins_file, index=False)
        return jsonify("Successfully uploaded identifier list")
    except Exception as err:
        return Response(f"{type(err).__name__}: {err}")



def _get_selected_genes():
    curr_dir = os.getcwd()
    selected_proteins_file = os.path.join(curr_dir, "selected_proteins.csv")
    if os.path.exists(selected_proteins_file):
        df = pd.read_csv(selected_proteins_file)
        os.remove(selected_proteins_file)
        selected_genes = list(df["selected_genes"])
        return selected_genes



@qc_page.route(
    "/qc/selected/<input_data_type>/<cohort_index>/<dimensionality_reduction_method>/<use_ref>/<use_replicate>/<custom_patients>/<imputation_ratio>"
)
def quality_control_selected_genes(
    input_data_type,
    cohort_index,
    dimensionality_reduction_method,
    use_ref,
    use_replicate,
    custom_patients,
    imputation_ratio
):
    """
    get the list of the selected proteins and perform PCA or UMAP with the selected list of Proteins
    bk_genes = topas_annotation_dfs.values()
    topas_genes = []
    for genes in bk_genes:
        topas_genes = [*topas_genes,*genes.gene]
    """
    selected_genes = _get_selected_genes()
    imputation_ratio = float(imputation_ratio)

    PCA_umap_dic = main(
        ef.DataType(input_data_type),
        cohort_index,
        dimensionality_reduction_method,
        use_ref,
        use_replicate,
        topas_genes=selected_genes,
        custom_list_patients = custom_patients,
        min_sample_occurrence_ratio = imputation_ratio
    )
    return Response(json.dumps(PCA_umap_dic), mimetype="application/json")


@qc_page.route(
    "/qc/sil/all/<input_data_type>/<cohort_index>/<dimensionality_reduction_method>/<use_ref>/<use_replicate>/<meta_col>/<min_num>/<beforeCluster>/<allorselected>/<custom_patients>/<imputation_ratio>"
)
# http://localhost:3832/qc/sil/all/fp/Intensity/0/ppca/noref/replicate/code_oncotree/4/beforeCluster/all
# http://localhost:3832/qc/sil/all/fp/Intensity/0/ppca/noref/replicate/code_oncotree/4/beforeCluster/selected
def sil_df_all_genes(
    input_data_type,
    cohort_index,
    dimensionality_reduction_method,
    use_ref,
    use_replicate,
    meta_col,
    min_num,
    imputation_ratio,
    beforeCluster="beforeCluster",
    allorselected='all',
    custom_patients=[],
):
    beforeCluster = beforeCluster == "beforeCluster"
    allgenes = (allorselected == 'all')
    imputation_ratio = float(imputation_ratio)

    if allgenes:
        selected_genes = []  # if empty conssiders all genes
    else:
        selected_genes = _get_selected_genes()
    print(selected_genes)
    #selected_genes = []  # if empty conssiders all genes
    sil_df = main(
        ef.DataType(input_data_type),
        cohort_index,
        dimensionality_reduction_method,
        use_ref,
        use_replicate,
        topas_genes=selected_genes,
        do_only_silhouette=True,
        meta_col_silhoutte=meta_col,
        min_num_patients=min_num,
        before_cluster=beforeCluster,
        custom_list_patients = custom_patients,
        min_sample_occurrence_ratio=imputation_ratio
    )

    return ef.df_to_json(sil_df)
