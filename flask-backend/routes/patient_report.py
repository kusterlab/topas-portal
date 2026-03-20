from .base import ApiBase

class PatientReportApiRoutes(ApiBase):
    PATIENT_REPORT_TABLE = "/<int:cohort_index>/patient_reports/<string:patient>/<data_type:level>"
    PATIENT_REPORT_TABLE_XLSX = "/<int:cohort_index>/patient_reports/<string:patients>"
    PATIENT_REPORT_PPTX = "/<int:cohort_index>/patient_reports/<string:patient>/pptx?background_cohort=<background_cohort>"

    TUMOR_ANTIGENS_SWARM_PLOT = "/<int:cohort_index>/patients/<string:patient>/tumor-antigens/swarm?background_cohort=<background_cohort>&subcohort_column=<subcohort_column>"
    RTKS_SWARM_PLOT = "/<int:cohort_index>/patients/<string:patient>/rtks/swarm?background_cohort=<background_cohort>&subcohort_column=<subcohort_column>"
    CKS_NKS_SWARM_PLOT = "/<int:cohort_index>/patients/<string:patient>/cks-nks/swarm?background_cohort=<background_cohort>&subcohort_column=<subcohort_column>"
    IMMUNE_STATUS_HEATMAP = "/<int:cohort_index>/patients/<string:patient>/immune-status/heatmap"
    PRODICT_PATIENT_PROBABILITES = "/<int:cohort_index>/patients/<string:patient>/prodict/score"
    PRODICT_PATIENT_UMAP = "/<int:cohort_index>/patients/<string:patient>/prodict/umap?background_cohort=<background_cohort>"
