from .base import ApiBase

class PatientReportApiRoutes(ApiBase):
    PATIENT_REPORT_TABLE = "/<int:cohort_index>/patient_reports/<string:patient>/<data_type:level>"
    PATIENT_REPORT_TABLE_XLSX = "/<int:cohort_index>/patient_reports/<string:patients>"

    TUMOR_ANTIGENS_SWARM_PLOT = "/<int:cohort_index>/patients/<string:patient>/<string:background_cohort>/tumor-antigens/swarm"
    RTKS_SWARM_PLOT = "/<int:cohort_index>/patients/<string:patient>/<string:background_cohort>/rtks/swarm"
    CKS_NKS_SWARM_PLOT = "/<int:cohort_index>/patients/<string:patient>/<string:background_cohort>/cks-nks/swarm"
    IMMUNE_STATUS_HEATMAP = "/<int:cohort_index>/patients/<string:patient>/immune-status/heatmap"
    PRODICT_PATIENT_PROBABILITES = "/<int:cohort_index>/patients/<string:patient>/prodict/score"
    PRODICT_PATIENT_UMAP = "/<int:cohort_index>/patients/<string:patient>/prodict/umap"
