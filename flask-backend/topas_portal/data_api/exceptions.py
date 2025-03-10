from .. import utils


class CohortDataNotLoadedError(Exception):
    """Exception raised when cohort data is not loaded."""

    def __init__(self, message="Try reloading the data for the current cohort."):
        self.message = message
        super().__init__(self.message)


class DataLayerUnavailableError(Exception):
    """Exception raised when specific data layer is unavailable for a cohort."""

    def __init__(self, data_layer: utils.DataType):
        self.message = (
            f"Try reloading the data layer '{data_layer}' for the current cohort."
        )
        super().__init__(self.message)


class IntensityUnitUnavailableError(Exception):
    """Exception raised when specific intensity unit is unavailable for a cohort."""

    def __init__(self, intensity_unit: utils.IntensityUnit):
        self.message = f"Make sure intensity unit '{intensity_unit}' is available for your data layer for the current cohort."
        super().__init__(self.message)
