"""Utilities for manipulating or extending pydantic models."""

from typing import Any, Dict

from pydantic import ConfigDict, model_validator
from pydantic.v1 import BaseModel, ValidationError


class CustomBaseModel(BaseModel):
    """Enhanced BaseModel that automatically sets invalid values to None.

    This model extends Pydantic's BaseModel to provide more graceful handling
    of invalid data by converting fields that fail validation to None instead
    of raising exceptions.

    Example:
        >>> class User(CustomBaseModel):
        ...     name: str
        ...     age: int
        >>> # This won't raise an error, age will be None
        >>> user = User(name="John", age="not-a-number")
        >>> print(user.age)
        None

    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, validate_assignment=True, extra="ignore"
    )

    @model_validator(mode="before")
    @classmethod
    def invalid_to_none(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Convert invalid values to None during validation.

        For each field in the model, attempt validation. If validation fails,
        set the field value to None instead of raising an exception.

        Args:
            values: Dictionary of field values to validate

        Returns:
            Dictionary with invalid values replaced by None

        """
        validated_values: Dict[str, Any] = {}

        for name, value in values.items():
            # Skip fields not defined in the model
            field = cls.__fields__.get(name)
            if field is None:
                continue

            # Try to validate the field
            try:
                validated_value, _ = field.validate(
                    value,
                    validated_values,
                    loc="__root__",
                    cls=cls,  # type: ignore[arg-type]
                )
                validated_values[name] = validated_value
            except ValidationError:
                # If validation fails, set to None
                values[name] = None
                validated_values[name] = None

        return values
