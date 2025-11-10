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

    PATIENT_REPORT_TABLE = "/<int:cohort_index>/patient_reports/<string:patient>/<data_type:level>"
    PATIENT_REPORT_TABLE_XLSX = "/<int:cohort_index>/patient_reports/<string:patients>"

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
    RELOAD_DIGEST = "/reload/digest"
    RELOAD_TOPAS_ANNOTATIONS = "/reload/topasannotations"
    RELOAD_COHORT = "/reload/<string:cohort>"

    PATH_CHECK = "/path/check/<path:path>"

    ANNOTATION_MODALITY = "/annotation/<int:cohort_index>/<string:modality>"
    VENN_PATIENT_COMPARE = (
        "/venn/<int:cohort_index>/patientcompare/<data_type:level>/<string:patientslists>"
    )
    VENN_BATCH_COMPARE = (
        "/venn/<int:cohort_index>/batchcompare/<data_type:level>/<string:batchlists>"
    )

    UPDATE_LOG = "/update/logs"
    ERROR_LOG = "/error/logs"

    PATIENT_CENTRIC_SUMMED_INTENSITY = (
        "/patientcentric/summed_intensity/<int:cohort_index>/<data_type:level>"
    )
    PATIENT_CENTRIC_COUNTS = (
        "/patientcentric/counts/<int:cohort_index>/<data_type:level>"
    )

    TOPAS = "/topas/<int:cohort_index>/<string:topas_names>/<string:score_type>"
    TOPAS_ANNOTATIONS = "/topas/annotations"
    TOPAS_LOLLIPOP = "/topas/lollipopdata/<int:cohort_index>/<string:patient>"
    TOPAS_LOLLIPOP_TUMOR = (
        "/topas/lollipopdata/<int:cohort_index>/<string:patient>/tumor_antigen"
    )
    TOPAS_EXPRESSION_DOWNSTREAM = "/topas/lollipopdata/expression/<int:cohort_index>/<string:patient>/downstream_signaling"
    TOPAS_EXPRESSION_RTK = (
        "/topas/lollipopdata/expression/<int:cohort_index>/<string:patient>/rtk"
    )
    TOPAS_IDS = "/topas/<int:cohort_index>/topasids/<string:categories>"
    TOPAS_SUBSCORE = "/topas/subscore/<int:cohort_index>/<string:topasname>"

    SAMPLE_ANNOTATION = "/<int:cohort_index>/sampleanot"
    PATIENTS = "/<int:cohort_index>/patients"
    PATIENTS_GENOMICS_ANNOTATIONS = (
        "/<int:cohort_index>/patients/genomics_annotations/<string:identifier>"
    )
    PATIENTS_METADATA = "/<int:cohort_index>/metadata"
    PATIENTS_METADATA_FIELDS = "/<int:cohort_index>/metadata/fields"
    PATIENTS_METADATA_FIELD_VALUES = (
        "/<int:cohort_index>/metadata/fields/<string:fieldname>"
    )
    PATIENTS_BY_FIELD_INTEREST = "/<int:cohort_index>/metadata/fields/<string:fieldname>/patients/<string:field_interest>"
    PATIENTS_ALL_ENTITIES = "/patients/<int:cohort_index>/all_entities"

    GENOMICS_IDENTIFIER = "/genomics/<string:identifier>"
    ONCOKB_IDENTIFIER = "/oncokb/<string:identifier>"

    DENSITY_FPKM = "/density/fpkm/<string:identifier>/<intensity_unit:intensity_unit>"
    DENSITY_PROTEIN = "/<int:cohort_index>/density/protein/<string:identifier>/<intensity_unit:intensity_unit>"

    IMPORTANT_PHOSPHO = "/<int:cohort_index>/important_phospho/<string:identifier>"

    ABUNDANCE = "/<int:cohort_index>/<data_type:level>/abundance/<string:identifier>/<string:imputation>/<include_ref:include_ref>"
    CORRELATION = "/<int:cohort_index>/<data_type:level>/correlation/<data_type:level_2>/<string:identifier>/<intensity_unit:intensity_unit>/<string:patients_list>"

    BATCH_EFFECT = "/batcheffect/<data_type:level>/<int:cohort_index>/<string:identifier>/<string:sample_ids>/<string:data_type>"
    DIFFERENTIAL = "/differential/<int:cohort_index>/<data_type:level>/<string:grp1_ind>/<string:grp2_ind>/<string:y_axis_type>"

    PROTEIN_LIST = "/<int:cohort_index>/<string:level>/list"

