import topas_portal.data_api.sql as sql
import db

cohorts_db = db.cohorts_db

def _importer(
    all_cohort_func,
    single_cohort_func,
    cohort_name="all_cohorts",
    data_type="meta_Data",
):
    if cohort_name == "all_cohorts":
        all_cohort_func(cohorts_db.config)
    else:
        single_cohort_func(cohorts_db.config, cohort_name)
    print(f"Import of {data_type} for the {cohort_name} finished")


def import_patient_meta_data(cohorts_db: sql.SQLCohortDataAPI, cohort_name):
    _importer(
        cohorts_db.provider.load_all_to_db_patient_meta_data,
        cohorts_db.provider.load_cohort_to_db_patient_meta_data,
        cohort_name,
        "patient_meta_data",
    )


def import_patient_sample_annotation_data(
    cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"
):
    _importer(
        cohorts_db.provider.load_all_to_db_sample_annotation_df,
        cohorts_db.provider.load_cohort_to_db_sample_annotation_df,
        cohort_name,
        "sample annotation data",
    )


def import_protein_to_sequence_mapping(
    cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"
):
    _importer(
        cohorts_db.provider.load_all_to_db_protein_seq_mapping_df,
        cohorts_db.provider.load_cohort_to_db_protein_seq_mapping_df,
        cohort_name,
        "protein to sequence",
    )


def import_expression_meta_data(
    cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"
):
    _importer(
        cohorts_db.provider.load_all_to_db_to_db_fp_meta_expression,
        cohorts_db.provider.load_cohort_to_db_fp_meta_expression,
        cohort_name,
        "expression meta",
    )


def import_FP_z_scores(cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"):
    _importer(
        cohorts_db.provider.load_all_to_db_fp_expression_z,
        cohorts_db.provider.load_cohort_to_db_fp_expression_z,
        cohort_name,
        "FP z_scores",
    )


def import_PP_z_scores(cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"):
    _importer(
        cohorts_db.provider.load_all_to_db_pp_expression_z,
        cohorts_db.provider.load_cohort_to_db_pp_expression_z,
        cohort_name,
        "PP z_scores",
    )


def import_FP_intensities(cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"):
    _importer(
        cohorts_db.provider.load_all_to_db_fp_expression_intensity,
        cohorts_db.provider.load_cohort_to_db_fp_expression_intensity,
        cohort_name,
        "FP intensities",
    )


def import_PP_intensities(cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"):
    _importer(
        cohorts_db.provider.load_all_to_db_pp_expression_intensity,
        cohorts_db.provider.load_cohort_to_db_pp_expression_intensity,
        cohort_name,
        "PP intensities",
    )


def import_TUPAC_scores(cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"):
    _importer(
        cohorts_db.provider.load_all_to_db_to_db_to_db_tupac_scores,
        cohorts_db.provider.load_cohort_to_db_tupac_scores,
        cohort_name,
        "TUPAC scores",
    )


def import_phospho_scores(cohorts_db: sql.SQLCohortDataAPI, cohort_name="all_cohorts"):
    _importer(
        cohorts_db.provider.load_all_to_db_to_db_to_db_phosphoscores,
        cohorts_db.provider.load_cohort_to_db_phosphoscores,
        cohort_name,
        "Phospho scores",
    )


if __name__ == "__main__":
    """
    USAGE: python -m importer   FP_z   all_cohorts    # to import the z_Scores for all cohorts to DB
           python -m importer   PP_i   INFORM         # to import intensity values of the INFORM cohohrt
    """

    import sys
    import time

    start = time.time()
    cohorts_db.config.reload_config()
    print(cohorts_db.config.get_config_path())
    function_to_call = sys.argv[1]
    cohort_name = sys.argv[2]
    if function_to_call == "FP_z":
        import_FP_z_scores(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "FP_i":
        import_FP_intensities(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "PP_z":
        import_PP_z_scores(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "PP_i":
        import_PP_intensities(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "protein_to_seq":
        import_protein_to_sequence_mapping(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "patient_meta_data":
        import_patient_meta_data(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "sample_annotation_data":
        import_patient_sample_annotation_data(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "expression_meta_data":
        import_expression_meta_data(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "tupac_scores":
        import_TUPAC_scores(cohorts_db, cohort_name=cohort_name)

    elif function_to_call == "phospho_scores":
        import_phospho_scores(cohorts_db, cohort_name=cohort_name)

    end = time.time()
    time_spent = end - start
    print(f"{time_spent} took!")
