"""Models for vehicle location."""

from datetime import datetime
from typing import Optional

from pydantic import computed_field

from pytoyoda.models.endpoints.location import LocationResponseModel
from pytoyoda.utils.models import CustomAPIBaseModel


class Location(CustomAPIBaseModel[LocationResponseModel]):
    """Latest Location of car."""

    def __init__(self, location: LocationResponseModel, **kwargs):
        """Initialize Location model.

        Args:
            location (LocationResponseModel): Contains information about
                vehicle location
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(
            data=location.payload.vehicle_location
            if location and location.payload
            else None,
            **kwargs,
        )

    @computed_field
    @property
    def latitude(self) -> Optional[float]:
        """Latitude.

        Returns:
            float: Latest latitude or None. _Not always available_.

        """
        return self._data.latitude if self._data else None

    @computed_field
    @property
    def longitude(self) -> Optional[float]:
        """Longitude.

        Returns:
            float: Latest longitude or None. _Not always available_.

        """
        return self._data.longitude if self._data else None

    @computed_field
    @property
    def timestamp(self) -> Optional[datetime]:
        """Timestamp.

        Returns:
            datetime: Position aquired timestamp or None.
                _Not always available_.

        """
        return self._data.location_acquisition_datetime if self._data else None

    @computed_field
    @property
    def state(self) -> str:
        """State.

        Returns:
            str: The state of the position or None. _Not always available_.

        """
        return self._data.display_name if self._data else None
