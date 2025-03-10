import os

from flask import Blueprint, jsonify

import db
import topas_portal.utils as ef
import topas_portal.settings as cn
import topas_portal.kinase_scores_prepare as kinase_prepare
import topas_portal.genomics_preprocess as genomics_prep


kinasescore_page = Blueprint(
    "kinasescore_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db


#### Kinase scores related routings
@kinasescore_page.route(
    "/kinasescores/<cohort_index>/<patient_or_entity>/<selected_patient_or_entities>/<selected_kinases>/<plot_type>/<one_vs_all>"
)
# http://localhost:3832/kinasescores/0/entity/UCEC/ABL1/heatmap/none_vs_all
# http://localhost:3832/kinasescores/0/entity/UCEC/ABL1/dendro/none_vs_all
# http://localhost:3832/kinasescores/0/entity/UCEC/ABL1/swarm/none_vs_all
def kinase_scores_plot(
    cohort_index,
    patient_or_entity,
    selected_patient_or_entities,
    selected_kinases,
    plot_type,
    one_vs_all=False,
):
    """Returns a plotly heatmap with dendrograms as json"""
    sample_annotation_df = cohorts_db.get_sample_annotation_df(cohort_index)
    if "Entity" in sample_annotation_df.columns:
        sample_annotation_df = sample_annotation_df.drop(["Entity"], axis=1)
    patien_meta_df = cohorts_db.get_patient_metadata_df(cohort_index)
    final_df = ef.merge_with_patients_meta_df(sample_annotation_df, patien_meta_df)
    annotation_df = final_df.dropna()

    if one_vs_all == "one_vs_all":
        one_vs_all = True
    else:
        one_vs_all = False
    return kinase_prepare.kinase_score_plots_prepare(
        cohorts_db.get_kinase_scores_df(
            cohort_index, intensity_unit=ef.IntensityUnit.Z_SCORE
        ),
        annotation_df,
        patient_or_entity,
        selected_patient_or_entities,
        selected_kinases,
        plot_type,
        one_vs_all,
    )
