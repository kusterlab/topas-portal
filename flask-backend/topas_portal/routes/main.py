from .base import ApiBase

class ApiRoutes(ApiBase):
    INDEX = "/"
    FAVICON = "/favicon.ico"

    CONFIG = "/config"
    CONFIG_PATH = "/config/config_path"
    CONFIG_CHECKALL = "/config/checkall"
    ADD_COHORT = "/config/addcohort/<string:cohort>"
    CONFIG_UPDATE = "/config/update/<string:key>/<string:cohort>/<string:value>"

    AUTH_LOGIN = "/auth/login"
    AUTH_ME = "/auth/me"

    COHORT_NAMES = "/cohort_names"
    COLUMN_NAMES = "/colnames"

    ENTITY_STATUS = "/entityscore/status"
    CORRELATION_FPKM_PROTEIN = "/correlation/fpkmprotein/<int:cohort_index>"
    ONCOKB_CNV = "/oncokb/api/cnv/<string:identifier>/<string:cnv_type>"

    RELOAD = "/reload"
    RELOAD_DB_ZSCORES = "/reloaddbz"
    RELOAD_DB_INTENSITY = "/reloaddbi"
    RELOAD_METADATA = "/reloadmeta"
    RELOAD_FP_INTENSITY_META = "/reloadfpintensitymeta"
    RELOAD_MAPPING_PROTEIN_SEQ = "/reloadmapping"
    RELOAD_TOPAS = "/reloadtopass"
    RELOAD_TRANSCRIPTS = "/reload/transcripts"
    RELOAD_TOPAS_ANNOTATIONS = "/reload/topasannotations"
    RELOAD_COHORT = "/reload/<string:cohort>"

    PATH_CHECK = "/path/check/<path:path>"

    ANNOTATION_MODALITY = "/annotation/<int:cohort_index>/<string:modality>"
    VENN_PATIENT_COMPARE = (
        "/venn/<int:cohort_index>/patientcompare/<data_type:level>/<string:patients>"
    )
    VENN_BATCH_COMPARE = (
        "/venn/<int:cohort_index>/batchcompare/<data_type:level>/<string:batchlists>"
    )

    UPDATE_LOG = "/update/logs"
    ERROR_LOG = "/error/logs"

    TOPAS = "/topas/<int:cohort_index>/<string:topas_names>/<string:score_type>"
    TOPAS_ANNOTATIONS = "/topas/annotations"
    TOPAS_IDS = "/topas/<int:cohort_index>/topasids"
    TOPAS_SUBSCORE = "/topas/subscore/<int:cohort_index>/<string:topasname>"

    SAMPLE_ANNOTATION = "/<int:cohort_index>/sampleanot"
    PATIENTS = "/<int:cohort_index>/patients"
    PATIENTS_GENOMICS_ANNOTATIONS = (
        "/<int:cohort_index>/patients/genomics_annotations/<string:identifier>"
    )
    PATIENTS_METADATA = "/<int:cohort_index>/metadata/<include_ref:include_ref>"
    PATIENT_CENTRIC_SUMMED_INTENSITY = (
        "/patientcentric/summed_intensity/<int:cohort_index>/<data_type:level>/<include_ref:include_ref>"
    )
    PATIENT_CENTRIC_COUNTS = (
        "/patientcentric/counts/<int:cohort_index>/<data_type:level>/<include_ref:include_ref>"
    )
    PATIENTS_METADATA_FIELDS = "/<int:cohort_index>/metadata/fields"
    PATIENTS_METADATA_FIELD_VALUES = (
        "/<int:cohort_index>/metadata/fields/<string:fieldname>"
    )
    PATIENTS_BY_FIELD_INTEREST = "/<int:cohort_index>/metadata/fields/<string:fieldname>/patients/<string:field_interest>"
    PATIENTS_ALL_ENTITIES = "/patients/<int:cohort_index>/all_entities"

    GENOMICS_IDENTIFIER = "/genomics/<string:identifier>"

    DENSITY_FPKM = "/density/fpkm/<string:identifier>/<intensity_unit:intensity_unit>"
    DENSITY_PROTEIN = "/<int:cohort_index>/density/protein/<string:identifier>/<intensity_unit:intensity_unit>"

    ABUNDANCE = "/<int:cohort_index>/<data_type:level>/abundance/<string:identifier>/<string:imputation>/<include_ref:include_ref>"
    CORRELATION = "/<int:cohort_index>/<data_type:level>/correlation/<data_type:level_2>/<string:identifier>/<intensity_unit:intensity_unit>/<string:patients_list>"

    HEATMAP = "/heatmap/<int:cohort_index>/<data_type:level>/<string:identifier>/<string:sample_ids>/<string:output_format>"
    DIFFERENTIAL = "/differential/<int:cohort_index>/<data_type:level>/<string:grp1_ind>/<string:grp2_ind>/<string:y_axis_type>"

    PROTEIN_LIST = "/<int:cohort_index>/<string:level>/list"

    # qc_app.py
    PCA_UMAP = "/qc/<string:selected_genes_mode>/<data_type:level>/<int:cohort_index>/<string:dimensionality_reduction_method>/<include_ref:include_ref>/<string:use_replicate>/<string:custom_patients>/<float:imputation_ratio>"

