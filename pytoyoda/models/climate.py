"""Climate Settings Models."""

from datetime import datetime, timedelta
from typing import Any, List, Optional

from pydantic import computed_field

from pytoyoda.models.endpoints.climate import (
    ACOperations,
    ACParameters,
    ClimateOptions,
    ClimateSettingsModel,
    ClimateStatusModel,
)
from pytoyoda.utils.models import CustomAPIBaseModel, Temperature


class ClimateOptionStatus(CustomAPIBaseModel[ClimateOptions]):
    """Climate option status."""

    def __init__(self, options: ClimateOptions, **kwargs):
        """Initialize climate option status.

        Args:
            options (ClimateOptions): Contains all additional options for climate
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=options, **kwargs)

    @computed_field
    @property
    def front_defogger(self) -> bool:
        """The front defogger status.

        Returns:
            bool: The status of front defogger

        """
        return self._data.front_defogger

    @computed_field
    @property
    def rear_defogger(self) -> bool:
        """The rear defogger status.

        Returns:
            bool: The status of rear defogger

        """
        return self._data.rear_defogger


class ClimateStatus(CustomAPIBaseModel[ClimateStatusModel]):
    """Climate status."""

    def __init__(self, climate_status: ClimateStatusModel, **kwargs):
        """Initialize climate status.

        Args:
            climate_status (ClimateStatusModel): Contains all information
              regarding the climate status
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=climate_status.payload, **kwargs)

    @computed_field
    @property
    def type(self) -> str:
        """The type.

        Returns:
            str: The type

        """
        return self._data.type

    @computed_field
    @property
    def status(self) -> bool:
        """The status.

        Returns:
            bool: The status

        """
        return self._data.status

    @computed_field
    @property
    def start_time(self) -> Optional[datetime]:
        """Start time.

        Returns:
            datetime: Start time

        """
        return self._data.started_at

    @computed_field
    @property
    def duration(self) -> Optional[timedelta]:
        """The duration.

        Returns:
            timedelta: The duration

        """
        if self._data.duration is None:
            return None

        return timedelta(seconds=self._data.duration)

    @computed_field
    @property
    def current_temperature(self) -> Optional[Temperature]:
        """The current temperature.

        Returns:
            Temperature: The current temperature with unit

        """
        if self._data.current_temperature is None:
            return None

        return Temperature(
            value=self._data.current_temperature.value,
            unit=self._data.current_temperature.unit,
        )

    @computed_field
    @property
    def target_temperature(self) -> Optional[Temperature]:
        """The target temperature.

        Returns:
            Temperature: The target temperature with unit

        """
        if self._data.target_temperature is None:
            return None

        return Temperature(
            value=self._data.target_temperature.value,
            unit=self._data.target_temperature.unit,
        )

    @computed_field
    @property
    def options(self) -> Optional[ClimateOptionStatus]:
        """The status of climate options.

        Returns:
            ClimateOptionsStatus: The statuses of climate options

        """
        if self._data.options is None:
            return None

        return ClimateOptionStatus(options=self._data.options)


class ClimateSettingsParameter(CustomAPIBaseModel[ACParameters]):
    """Climate settings parameter."""

    def __init__(self, parameter: ACParameters, **kwargs):
        """Initialize climate settings parameter.

        Args:
            parameter (ACParameters): Contains all parameters
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=parameter, **kwargs)

    @computed_field
    @property
    def available(self) -> Optional[bool]:
        """The parameter availability.

        Returns:
            bool: The parameter availability value

        """
        return self._data.available

    @computed_field
    @property
    def enabled(self) -> bool:
        """The parameter enable.

        Returns:
            bool: The parameter enable value

        """
        return self._data.enabled

    @computed_field
    @property
    def display_name(self) -> Optional[str]:
        """The parameter display name.

        Returns:
            str: The parameter display name

        """
        return self._data.display_name

    @computed_field
    @property
    def name(self) -> str:
        """The parameter name.

        Returns:
            str: The parameter name

        """
        return self._data.name

    @computed_field
    @property
    def icon_url(self) -> Optional[str]:
        """The parameter icon url.

        Returns:
            str: The parameter icon url

        """
        return self._data.icon_url


class ClimateSettingsOperation(CustomAPIBaseModel[ACOperations]):
    """Climate settings operation."""

    def __init__(self, operations: ACOperations, **kwargs):
        """Initialize climate settings operation.

        Args:
            operations (ACOperations): Contains all options for climate
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=operations, **kwargs)

    @computed_field
    @property
    def available(self) -> Optional[bool]:
        """The operation availability.

        Returns:
            bool: The operation availability value

        """
        return self._data.available

    @computed_field
    @property
    def category_name(self) -> str:
        """The operation category name.

        Returns:
            str: The operation category name

        """
        return self._data.category_name

    @computed_field
    @property
    def category_display_name(self) -> Optional[str]:
        """The operation category display name.

        Returns:
            str: The operation category display name

        """
        return self._data.category_display_name

    @computed_field
    @property
    def parameters(self) -> Optional[List[ClimateSettingsParameter]]:
        """The operation parameter.

        Returns:
            List[ClimateSettingsParameter]: The operation parameter

        """
        if self._data.ac_parameters is None:
            return None

        return [ClimateSettingsParameter(parameter=p) for p in self._data.ac_parameters]


class ClimateSettings(CustomAPIBaseModel[Any]):
    """Climate settings."""

    def __init__(self, climate_settings: ClimateSettingsModel, **kwargs):
        """Initialize climate settings.

        Args:
            climate_settings (ClimateSettingsModel): Contains all information
                regarding the climate settings
            **kwargs: Additional keyword arguments passed to the parent class

        """
        super().__init__(data=climate_settings.payload, **kwargs)

    @computed_field
    @property
    def settings_on(self) -> bool:
        """The settings on value.

        Returns:
            bool: The value of settings on

        """
        return self._data.settings_on

    @computed_field
    @property
    def temp_interval(self) -> Optional[float]:
        """The temperature interval.

        Returns:
            float: The value of temperature interval

        """
        return self._data.temp_interval

    @computed_field
    @property
    def min_temp(self) -> Optional[float]:
        """The min temperature.

        Returns:
            float: The value of min temperature

        """
        return self._data.min_temp

    @computed_field
    @property
    def max_temp(self) -> Optional[float]:
        """The max temperature.

        Returns:
            float: The value of max temperature

        """
        return self._data.max_temp

    @computed_field
    @property
    def temperature(self) -> Temperature:
        """The temperature.

        Returns:
            Temperature: The temperature with unit

        """
        return Temperature(
            value=self._data.temperature,
            unit=self._data.temperature_unit,
        )

    @computed_field
    @property
    def operations(self) -> Optional[List[ClimateSettingsOperation]]:
        """The climate operation settings.

        Returns:
            List[ClimateSettingsOperation]: The settings of climate operation

        """
        if self._data.ac_operations is None:
            return None

        return [ClimateSettingsOperation(operation=p) for p in self._data.ac_operations]
