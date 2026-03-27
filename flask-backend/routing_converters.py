from werkzeug.routing import BaseConverter
from topas_portal.data_type import DataType
from topas_portal.constants import (
    IntensityUnit,
    SampleFilter,
)



class DataTypeConverter(BaseConverter):
    def to_python(self, value):
        """Convert matched string to a DataType."""
        return DataType(value)

    def to_url(self, value):
        """Convert DataType object back to string for URL generation."""
        return str(value)


class IntensityUnitConverter(BaseConverter):
    def to_python(self, value):
        """Convert matched string to a IntensityUnit."""
        return IntensityUnit(value)

    def to_url(self, value):
        """Convert IntensityUnit object back to string for URL generation."""
        return str(value)


class IncludeRefConverter(BaseConverter):
    def to_python(self, value):
        """Convert matched string to a IntensityUnit."""
        return SampleFilter(value)

    def to_url(self, value):
        """Convert IntensityUnit object back to string for URL generation."""
        return str(value)