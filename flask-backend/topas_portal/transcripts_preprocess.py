# needed to prevent circular import of db.CohortDataAPI
from __future__ import annotations

from typing import TYPE_CHECKING

import topas_portal.utils as utils

if TYPE_CHECKING:
    import topas_portal.data_api.data_api as data_api


def get_density_calc_fpkm(
    cohorts_db: data_api.CohortDataAPI,
    identifier: str,
    intensity_unit: utils.IntensityUnit,
):
    """
    Computes density estimates for FPKM (Fragments Per Kilobase of transcript per Million mapped reads) data.

    This function retrieves the FPKM data matrix from the cohort database, processes it to calculate
    density estimates for a given identifier, and returns the resulting data in JSON format.

    Args:
        cohorts_db (data_api.CohortDataAPI): The database interface for retrieving FPKM data.
        identifier (str): The specific gene or transcript identifier for which density calculations 
                          should be performed.
        intensity_unit (utils.IntensityUnit): The unit of intensity measurement to be used 
                                              when fetching FPKM data.

    Returns:
        dict: A JSON-compatible dictionary representation of the density plot data.

    Notes:
        - The function first retrieves the FPKM data matrix from `cohorts_db`.
        - The data is then transformed into a density plot-friendly format using `count_df_to_density_plot_df`.
        - The processed data is converted to JSON format before being returned.
    """
    fpkm_df = cohorts_db.get_fpkm_df(intensity_unit=intensity_unit)
    count_df_fpkm = utils.count_df_to_density_plot_df(fpkm_df, identifier,list(fpkm_df.columns))
    return utils.df_to_json(count_df_fpkm)
