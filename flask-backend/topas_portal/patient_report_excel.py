from __future__ import annotations

from typing import TYPE_CHECKING
from enum import Enum

import pandas as pd
import xlsxwriter

from topas_portal import utils
from . import patient_report

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


class ColumnFormats(Enum):
    STRING = {}
    INTEGER = {"num_format": "#,##0"}
    TWO_DECIMALS = {"num_format": "#,##0.00"}


# Output columns with formats and column widths
SHEET_COLUMN_FORMATS = {
    utils.DataType.REPORT_SUMMARY: {
        "Topas_id": (ColumnFormats.STRING, 15),
        "Score type": (ColumnFormats.STRING, 45),
        "Z-score": (ColumnFormats.TWO_DECIMALS, 8),
    },
    utils.DataType.FULL_PROTEOME: {
        "Gene names": (ColumnFormats.STRING, 12),
        "Rank": (ColumnFormats.INTEGER, 6),
        "Occurrence": (ColumnFormats.INTEGER, 12),
        "Z-score": (ColumnFormats.TWO_DECIMALS, 8),
        "FC": (ColumnFormats.TWO_DECIMALS, 8),
        "BatchRank": (ColumnFormats.INTEGER, 10),
        "Intensity": (ColumnFormats.TWO_DECIMALS, 10),
        "Identification metadata": (ColumnFormats.STRING, 30),
        "POI_REPORT": (ColumnFormats.STRING, 15),
        "POI_EXPLORATORY": (ColumnFormats.STRING, 17),
        "POI_PRODICT": (ColumnFormats.STRING, 15),
    },
    utils.DataType.PHOSPHO_PROTEOME: {
        "Modified sequence representative": (ColumnFormats.STRING, 40),
        "Gene names": (ColumnFormats.STRING, 12),
        "Site positions (MQ identified - PSP)": (ColumnFormats.STRING, 32),
        "Rank": (ColumnFormats.INTEGER, 6),
        "Occurrence": (ColumnFormats.INTEGER, 12),
        "Z-score": (ColumnFormats.TWO_DECIMALS, 8),
        "FC": (ColumnFormats.TWO_DECIMALS, 8),
        "BatchRank": (ColumnFormats.INTEGER, 10),
        "Intensity": (ColumnFormats.TWO_DECIMALS, 10),
        "Identification metadata": (ColumnFormats.STRING, 25),
        "Site positions (PSP)": (ColumnFormats.STRING, 25),
        "Kinases (TOPAS)": (ColumnFormats.STRING, 15),
        "Kinases (PSP)": (ColumnFormats.STRING, 15),
        "POI_REPORT": (ColumnFormats.STRING, 15),
        "POI_EXPLORATORY": (ColumnFormats.STRING, 17),
        "POI_PRODICT": (ColumnFormats.STRING, 15),
        "Effects on Modified Protein (PSP)": (ColumnFormats.STRING, 15),
        "Effects on Biological Process (PSP)": (ColumnFormats.STRING, 15),
        "Induce interaction with protein (PSP)": (ColumnFormats.STRING, 15),
        "Induce interaction with other (PSP)": (ColumnFormats.STRING, 15),
        "Low throughput studies (PSP)": (ColumnFormats.STRING, 15),
        "High throughput studies (PSP)": (ColumnFormats.STRING, 15),
        "Modified sequence group": (ColumnFormats.STRING, 40),
    },
    utils.DataType.PHOSPHO_SCORE: {
        "Gene names": (ColumnFormats.STRING, 12),
        "Rank": (ColumnFormats.INTEGER, 6),
        "Occurrence": (ColumnFormats.INTEGER, 12),
        "Z-score": (ColumnFormats.TWO_DECIMALS, 8),
        "BatchRank": (ColumnFormats.INTEGER, 10),
        "POI_REPORT": (ColumnFormats.STRING, 15),
        "POI_EXPLORATORY": (ColumnFormats.STRING, 17),
    },
}


def generate_patient_report(
    cohorts_db: data_api.CohortDataAPI,
    cohort_index: int,
    patient: str,
    report_path: str,
):
    sheet_names = {
        utils.DataType.REPORT_SUMMARY: "Summary",
        utils.DataType.FULL_PROTEOME: "Proteome",
        utils.DataType.PHOSPHO_PROTEOME: "Phosphoproteome",
        utils.DataType.PHOSPHO_SCORE: "Protein phosphorylation score",
    }
    with pd.ExcelWriter(report_path, engine="xlsxwriter") as writer:
        for data_type, sheet_name in sheet_names.items():
            print(f"Preparing {sheet_name} sheet for {patient}")
            df = patient_report.get_reports_per_patient(
                cohorts_db,
                data_type,
                cohort_index,
                patient,
            )

            # put columns in the correct order
            df = df[SHEET_COLUMN_FORMATS[data_type].keys()]
            df = df.set_index(df.columns[0])

            print(f"Writing {sheet_name} sheet for {patient}")
            # Get the xlsxwriter workbook and worksheet objects
            worksheet, workbook = create_workbook(
                df, writer, sheet_name, use_index=True
            )

            # Add cell formats
            formats = {}
            for format in ColumnFormats:
                formats[format] = workbook.add_format(format.value)

            for idx, (_, (format, width)) in enumerate(
                SHEET_COLUMN_FORMATS[data_type].items()
            ):
                worksheet.set_column(idx, idx, width, formats[format])


def create_workbook(
    df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str, use_index: bool = True
) -> tuple[xlsxwriter.Worksheet, xlsxwriter.Workbook]:
    df.to_excel(
        writer, sheet_name=sheet_name, index=use_index, merge_cells=False
    )  # this is the slow part...
    workbook, worksheet = writer.book, writer.sheets[sheet_name]
    return worksheet, workbook
