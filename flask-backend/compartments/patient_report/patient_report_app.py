from flask import (
    Blueprint,
    jsonify,
    current_app,
    send_from_directory,
    Response,
    request,
    send_file,
)
import db
import pandas as pd
import zipfile
from pathlib import Path
import traceback
import shutil
import os

from extensions import cache
import topas_portal.utils as common_utils
from routes import PatientReportApiRoutes
from topas_portal import prexp_preprocess as pp

from topas_portal import patient_report_excel

from pptx import Presentation
from pptx.util import Inches
from io import BytesIO
import re


from pathlib import Path
from flask import Blueprint, jsonify, request, Response
import compartments.patient_report.utils as utils

patient_report_page = Blueprint(
    "patient_report_page",
    __name__,
    static_folder="../dist/static",
    template_folder="../dist",
)

cohorts_db = db.cohorts_db
config = cohorts_db.config


antigens = [
    "MAGEA4",
    "ERBB2",
    "BTN3A3",
    "PTK7",
    "CTAG1A",
    "NECTIN2",
    "SLC39A6",
    "GPC3",
    "F3",
    "CD276",
    "KAT6B",
    "CDH6",
    "ERBB3",
    "BTN3A1",
    "IL1RAP",
    "ANKRD30A",
    "FAP",
    "BTN3A2",
    "TACSTD2",
    "CDH3",
    "NECTIN4",
    "CSF1R",
    "CDH17",
    "PMEL",
    "MSLN",
    "FOLR1",
    "MUC1",
    "ROR2",
    "FOLH1",
    "SEZ6",
    "B4GALNT1",
    "PGR",
    "CLDN18-2;CLDN18",
    "SLC39A1",
    "AR",
    "KAT6A",
    "ROR1",
    "VTCN1",
    "CLDN6",
    "ESR1",
    "SSTR2",
    "PRAME",
]


immune_status_genes = [
    "TAP1",
    "CD163",
    "HLA-DRA",
    "PSMB8",
    "HLA-E",
    "CD276",
    "HLA-A",
    "PSMB10",
    "HLA-DQB1",
    "HLA-C",
    "HLA-B",
    "CD1A",
    "HLA-DPB1",
    "CD5",
    "CD3E",
    "GZMA",
    "TAP2",
    "APOL3",
    "TAPBP",
    "HLA-DRB4",
    "PRF1",
    "HLA-F",
    "HLA-DMB",
    "HLA-DPA1",
    "PSMB9",
    "HLA-DQA1",
    "HLA-G",
    "SIGIRR",
    "LAG3",
    "CD68",
    "CD274",
    "CD38",
    "RUNX3",
    "HLA-DRB1",
    "CD8A",
    "MS4A1",
    "HLA-DQB2",
    "CD4",
    "HLA-DMA",
    "CD1E",
    "GNLY",
    "HLA-DRB3",
    "HLA-DRB5",
    "CD3G",
    "CD84",
    "CD8B",
    "CD1B",
    "CD19",
    "HAVCR2",
    "ZBTB16",
    "CD79B",
    "CD79A",
    "GZMB",
    "CD27",
    "HLA-DOA",
    "HHLA2",
    "CD2",
    "CD1C",
    "HLA-DOB",
    "HLA-H",
    "CD3D",
    "CD22",
    "GZMH",
]


@cache.cached(timeout=50)
@patient_report_page.route(PatientReportApiRoutes.PATIENT_REPORT_TABLE)
def get_patient_report_table(
    cohort_index: int, patient: str, level: common_utils.DataType
):
    """Returns tables from the patient reports.

    Example: http://localhost:3832/0/patient_reports/I007-031-108742/protein

    Args:
        cohort_index (int): cohort index
        patient (str): patient identifier
        level (DataType): modality (e.g. full proteome, topas, etc.) to get
            reports for, see DataType.

    Returns:
        Response: jsonified dataframe with patient report table.
    """
    return common_utils.df_to_json(
        pp.get_reports_per_patient(
            cohorts_db,
            cohort_index,
            patient,
            common_utils.DataType(level),
        )
    )


@cache.cached(timeout=50)
@patient_report_page.route(PatientReportApiRoutes.PATIENT_REPORT_TABLE_XLSX)
# http://localhost:3832/0/patient_reports/I007-031-108742
def get_patient_reports_as_attachment(cohort_index: int, patients: str):
    """Returns patient report excel files. For multiple reports, a zip file is returned.

    Args:
        cohort_index (int): cohort index
        patient (str): patient identifiers separated by semicolons

    Returns:
        Response: excel or zip file with patient report(s)
    """
    reports_dir = Path(cohorts_db.get_report_dir(cohort_index)) / "Reports"
    reports_dir.mkdir(exist_ok=True)

    def get_patient_report_path(patient_identifier: str):
        return reports_dir / f"{patient_identifier}_proteomics_results.xlsx"

    patients = patients.split(",")
    for patient in patients:
        path_to_patient_results = get_patient_report_path(patient)
        patient_report_excel.generate_patient_report(
            cohorts_db, cohort_index, patient, path_to_patient_results
        )

    if len(patients) == 1:
        path_to_patient_results = get_patient_report_path(patients[0])
        if not os.path.exists(path_to_patient_results):
            return f"Unable to download report for {patients[0]}", 400
        shutil.copy(path_to_patient_results, current_app.config["UPLOAD_FOLDER"])
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"],
            Path(path_to_patient_results).name,
            as_attachment=True,
        )
    elif len(patients) > 1:
        paths_to_patient_results = []
        for patient in patients:
            path_to_patient_results = get_patient_report_path(patient)
            if not os.path.exists(path_to_patient_results):
                return f"Unable to download report for {patient}", 400
            paths_to_patient_results.append(path_to_patient_results)

        output_zipfile = os.path.join(
            current_app.config["UPLOAD_FOLDER"], "patient_reports.zip"
        )
        with zipfile.ZipFile(output_zipfile, "w") as zipFile:
            for path_to_patient_results in paths_to_patient_results:
                zipFile.write(
                    path_to_patient_results,
                    Path(path_to_patient_results).name,
                    compress_type=zipfile.ZIP_STORED,
                )  # no compression, because Excel files are already binary
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"],
            Path(output_zipfile).name,
            as_attachment=True,
        )


@patient_report_page.route(PatientReportApiRoutes.TUMOR_ANTIGENS_SWARM_PLOT.path)
def get_tumor_antigens_swarm_plot(cohort_index: int, patient: str):
    if len(patient.split(";")) > 1:
        return "Can only handle 1 patient at a time", 400

    background_cohort = request.args.get("background_cohort", default="", type=str)
    metadata = cohorts_db.get_patient_metadata_df(cohort_index)
    metadata = metadata.set_index("Sample name")
    background_cohort = utils.get_background_cohort(
        metadata, background_cohort, patient
    )

    svg_data = cache.get(
        utils.TUMOR_ANTIGEN_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "svg",
            }
        )
    )
    if svg_data is None:
        subcohort_column = request.args.get(
            "subcohort_column", type=str, default="code_oncotree"
        )

        subcohort = utils.get_background_cohort_indices(
            metadata, subcohort_column, patient, background_cohort=background_cohort
        )
        fp = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=common_utils.IntensityUnit.Z_SCORE
        )

        genes = fp.index.intersection(antigens)
        pr = utils.PatientReport(cohort_index, patient, background_cohort)
        pr.setup_swarm_df(fp.loc[genes].reset_index(), subcohort)
        pr.generate_swarm_plot(
            "",
            "Protein abundance (z-score)",
            f"{patient} tumor antigens",
        )
        svg_data = pr.output_format(pr.get_antigens_cache_id("svg"), "svg")
        pr.output_format(pr.get_antigens_cache_id("png"), "png")

        pr.close_fig()

    return Response(svg_data, mimetype="image/svg+xml")


@patient_report_page.route(PatientReportApiRoutes.RTKS_SWARM_PLOT.path)
def get_rtk_swarm_plot(cohort_index: int, patient: str):
    if len(patient.split(";")) > 1:
        return "Can only handle 1 patient at a time", 400

    subcohort_column = request.args.get(
        "subcohort_column", type=str, default="code_oncotree"
    )
    background_cohort = request.args.get("background_cohort", default="", type=str)
    metadata = cohorts_db.get_patient_metadata_df(cohort_index)
    metadata = metadata.set_index("Sample name")
    background_cohort = utils.get_background_cohort(
        metadata, background_cohort, patient
    )

    subcohort = utils.get_background_cohort_indices(
        metadata, subcohort_column, patient, background_cohort=background_cohort
    )

    svg_data = cache.get(
        utils.TOPAS_RTK_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "svg",
            }
        )
    )

    if svg_data is None:
        rtk = cohorts_db.get_topas_rtk_scores_df(
            cohort_index, intensity_unit=common_utils.IntensityUnit.Z_SCORE
        )
        pr = utils.PatientReport(cohort_index, patient, background_cohort)
        pr.setup_swarm_df(rtk.rename_axis("Gene names").reset_index(), subcohort)
        pr.generate_swarm_plot(
            "",
            "RTK-TOPAS (z-score)",
            f"{patient} RTK",
            y_thresh_main=2,
            y_thresh_sec=1.5,
            ymin=0,
            y_outlier_above=4,
        )
        svg_data = pr.output_format(pr.get_topas_rtk_cache_id("svg"), "svg")
        pr.output_format(pr.get_topas_rtk_cache_id("png"), "png")
        pr.close_fig()

    return Response(svg_data, mimetype="image/svg+xml")


@patient_report_page.route(PatientReportApiRoutes.CKS_NKS_SWARM_PLOT.path)
def get_ck_nk_swarm_plot(cohort_index: int, patient: str):
    if len(patient.split(";")) > 1:
        return "Can only handle 1 patient at a time", 400

    subcohort_column = request.args.get(
        "subcohort_column", type=str, default="code_oncotree"
    )
    background_cohort = request.args.get("background_cohort", default="", type=str)

    metadata = cohorts_db.get_patient_metadata_df(cohort_index)
    metadata = metadata.set_index("Sample name")
    background_cohort = utils.get_background_cohort(
        metadata, background_cohort, patient
    )

    subcohort = utils.get_background_cohort_indices(
        metadata, subcohort_column, patient, background_cohort=background_cohort
    )

    svg_data = cache.get(
        utils.TOPAS_CK_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "svg",
            }
        )
    )
    if svg_data is None:
        ck_nk = cohorts_db.get_topas_ck_scores_df(
            cohort_index, intensity_unit=common_utils.IntensityUnit.Z_SCORE
        )

        pr = utils.PatientReport(cohort_index, patient, background_cohort)
        pr.setup_swarm_df(ck_nk.rename_axis("Gene names").reset_index(), subcohort)
        pr.generate_swarm_plot(
            "",
            "CK/NK-TOPAS (z-score)",
            f"{patient} CK/NK",
            y_thresh_main=2,
            y_thresh_sec=1.5,
        )
        svg_data = pr.output_format(pr.get_topas_ck_cache_id("svg"), "svg")
        pr.output_format(pr.get_topas_ck_cache_id("png"), "png")
        pr.close_fig()

    return Response(svg_data, mimetype="image/svg+xml")


@patient_report_page.route(PatientReportApiRoutes.IMMUNE_STATUS_HEATMAP.path)
def get_immune_status_heatmap(cohort_index: int, patient: str):
    svg_data = cache.get(
        utils.IMMUNE_HEATMAP_CACHE_ID_TEMPLATE.format_map(
            {"sample": patient, "cohort": cohort_index, "ext": "svg"}
        )
    )
    if svg_data is None:
        if len(patient.split(";")) > 1:
            return "Can only handle 1 patient at a time", 400

        fp = cohorts_db.get_protein_abundance_df(
            cohort_index, intensity_unit=common_utils.IntensityUnit.Z_SCORE
        )

        pr = utils.PatientReport(cohort_index, patient)
        pr.setup_immune_status_df(fp.loc[fp.index.intersection(immune_status_genes)].T)
        pr.generate_immune_status_heatmap(f"{patient} immune status")
        svg_data = pr.output_format(pr.get_immune_heatmap_cache_id("svg"), "svg")
        pr.output_format(pr.get_immune_heatmap_cache_id("png"), "png")
        pr.close_fig()

    return Response(svg_data, mimetype="image/svg+xml")


@patient_report_page.route(PatientReportApiRoutes.PRODICT_PATIENT_PROBABILITES.path)
# http://localhost:3832/cohort_index/patients/patient_id/prodict/score"
def get_probabilities(cohort_index: int, patient: str):
    """Returns entity scores for a given patient"""
    svg_data = cache.get(
        utils.PRODICT_PROB_CACHE_ID_TEMPLATE.format_map(
            {"sample": patient, "ext": "svg"}
        )
    )

    if svg_data is None:
        try:
            models = utils.load_sklearn_models(config.get_models_folder())
            data_clean = utils.get_imputed_df(cohort_index)
            patient_input_data = pd.DataFrame(data_clean.loc[patient]).T

            predictions = utils.probabilities_calculator(models, patient_input_data)
            pr = utils.PatientReport(cohort_index, patient)
            pr.setup_prodict_scores(predictions)
            pr.generate_prodict_lollipop(f"PROdict Classification - {patient}")
            svg_data = pr.output_format(pr.get_prodict_prob_cache_id("svg"), "svg")
            pr.output_format(pr.get_prodict_prob_cache_id("png"), "png")

            pr.close_fig()

        except Exception as e:
            return jsonify({"error during prediction": str(e)}), 500

    return Response(svg_data, mimetype="image/svg+xml")


@patient_report_page.route(PatientReportApiRoutes.PRODICT_PATIENT_UMAP.path)
def get_patient_umap(cohort_index: int, patient: str):
    """
    Generate UMAP visualization for a specific patient in its entity context.
    """
    background_cohort = request.args.get("background_cohort", default="", type=str)

    metadata = cohorts_db.get_patient_metadata_df(cohort_index)
    metadata = metadata.set_index("Sample name")
    background_cohort = utils.get_background_cohort(
        metadata, background_cohort, patient
    )

    svg_data = cache.get(
        utils.PRODICT_UMAP_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "svg",
            }
        )
    )

    if svg_data is None:
        try:
            # Loading necessary data. Intensity, metadata and signatures
            signatures_dict = utils.load_signatures_from_folder(
                config.get_signatures_folder()
            )

            # Loading imputed intensities
            data_clean = utils.get_imputed_df(cohort_index)
            data_clean["code_oncotree"] = metadata.get("code_oncotree")

            pr = utils.PatientReport(cohort_index, patient, background_cohort)
            pr.setup_prodict_umap_df(data_clean, signatures_dict)

            # Generate UMAP figure
            pr.generate_umap(
                n_neighbors=10, min_dist=0.1, title=f"UMAP Visualization - {patient}"
            )
            svg_data = pr.output_format(pr.get_prodict_umap_cache_id("svg"), "svg")
            pr.output_format(pr.get_prodict_umap_cache_id("png"), "png")

            pr.close_fig()

        except KeyError as e:
            return {
                "error": f"Missing required parameter: {str(e)}",
                "traceback": traceback.format_exc(),
            }, 400

        except Exception as e:
            return {"error": str(e), "traceback": traceback.format_exc()}, 500
    return Response(svg_data, mimetype="image/svg+xml")


@patient_report_page.route(PatientReportApiRoutes.PATIENT_REPORT_PPTX.path)
def get_patient_report_pptx(cohort_index: int, patient: str):
    background_cohort = request.args.get("background_cohort", default="", type=str)

    metadata = cohorts_db.get_patient_metadata_df(cohort_index)
    metadata = metadata.set_index("Sample name")
    background_cohort = utils.get_background_cohort(
        metadata, background_cohort, patient
    )

    prodict_umap_png = cache.get(
        utils.PRODICT_PROB_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "png",
            }
        )
    )
    prodict_prob_png = cache.get(
        utils.PRODICT_PROB_CACHE_ID_TEMPLATE.format_map(
            {"sample": patient, "ext": "png"}
        )
    )

    immune_heatmap_png = cache.get(
        utils.IMMUNE_HEATMAP_CACHE_ID_TEMPLATE.format_map(
            {"sample": patient, "cohort": cohort_index, "ext": "png"}
        )
    )

    tumor_antigen_png = cache.get(
        utils.TUMOR_ANTIGEN_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "png",
            }
        )
    )
    topas_rtk_png = cache.get(
        utils.TOPAS_RTK_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "png",
            }
        )
    )
    topas_ck_png = cache.get(
        utils.TOPAS_CK_CACHE_ID_TEMPLATE.format_map(
            {
                "sample": patient,
                "cohort": cohort_index,
                "background_cohort": (
                    background_cohort if background_cohort else "default"
                ),
                "ext": "png",
            }
        )
    )

    if (
        not prodict_umap_png
        or not prodict_prob_png
        or not tumor_antigen_png
        or not immune_heatmap_png
        or not topas_ck_png
        or not topas_rtk_png
    ):
        return "Images not available yet. Please generate them in cache first.", 400

    metadata = cohorts_db.get_patient_metadata_df(cohort_index)
    metadata = metadata.set_index("Sample name")

    prs = Presentation(config.get_report_template_pptx())
    slide = prs.slides[0]
    metadata_row = metadata.loc[patient]
    val_pp = metadata_row.get("Tumor cell content")
    val_bp = metadata_row.get("TCC_Bioinfo")

    na_tcc_values = [None, "", "missing", "NA", ""]
    for shape in slide.shapes:
        if shape.has_text_frame:
            for i, paragraph in enumerate(shape.text_frame.paragraphs):
                for run in paragraph.runs:
                    run.text = re.sub(r"\[SAMPLE\]", patient, run.text)
                    run.text = re.sub(
                        r"\[ENT\]",
                        str(metadata_row.get("code_oncotree", "NA")),
                        run.text,
                    )
                    run.text = re.sub(
                        r"\[TOP\]",
                        str(metadata_row.get("tissue_topology", "NA")),
                        run.text,
                    )
                    run.text = re.sub(
                        r"\[PP\]",
                        f"{int(val_pp)}%" if utils.can_be_int(val_pp) else "NA",
                        run.text,
                    )
                    run.text = re.sub(
                        r"\[BP\]",
                        f"{int(val_bp)}%" if utils.can_be_int(val_pp) else "NA",
                        run.text,
                    )

    slide.shapes.add_picture(
        BytesIO(tumor_antigen_png),
        left=Inches(4.47),
        top=Inches(0.55),
        height=Inches(1.89),
    )
    slide.shapes.add_picture(
        BytesIO(immune_heatmap_png),
        left=Inches(4.14),
        top=Inches(2.49),
        height=Inches(0.86),
    )
    slide.shapes.add_picture(
        BytesIO(prodict_prob_png),
        left=Inches(0.02),
        top=Inches(1.44),
        height=Inches(1.90),
    )
    slide.shapes.add_picture(
        BytesIO(prodict_umap_png),
        left=Inches(1.52),
        top=Inches(1.42),
        height=Inches(1.90),
    )
    slide.shapes.add_picture(
        BytesIO(topas_rtk_png), left=Inches(0.01), top=Inches(3.95), height=Inches(1.73)
    )
    slide.shapes.add_picture(
        BytesIO(topas_ck_png), left=Inches(0.01), top=Inches(5.74), height=Inches(1.73)
    )

    ppt_io = BytesIO()
    prs.save(ppt_io)
    ppt_io.seek(0)

    return send_file(
        ppt_io,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        as_attachment=True,
        download_name=f"{patient}.pptx",
    )
