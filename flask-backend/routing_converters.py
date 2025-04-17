from werkzeug.routing import BaseConverter
from topas_portal import utils


class DataTypeConverter(BaseConverter):
    def to_python(self, value):
        """Convert matched string to a DataType."""
        return utils.DataType(value)

    def to_url(self, value):
        """Convert DataType object back to string for URL generation."""
        return str(value)


class IntensityUnitConverter(BaseConverter):
    def to_python(self, value):
        """Convert matched string to a IntensityUnit."""
        return utils.IntensityUnit(value)

    def to_url(self, value):
        """Convert IntensityUnit object back to string for URL generation."""
        return str(value)