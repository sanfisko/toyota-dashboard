"""Utilities for manipulating or extending pydantic models."""

from collections.abc import Callable
from typing import Annotated, Any, get_args, get_origin

from pydantic import BaseModel, ValidationError, WrapValidator


def invalid_to_none(v: Any, handler: Callable[[Any], Any]) -> Any:
    """Return None for failed validations otherwise original value.

    Args:
        v: Value to validate
        handler: Original validation handler

    Returns:
        Validated value or None if validation fails

    """
    try:
        return handler(v)
    except ValidationError:
        return None


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

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Automatically add validation wrapper to all fields of subclasses.

        This method is called when a subclass of CustomBaseModel is created.
        It adds the invalid_to_none validator to each field annotation.
        """
        for name, annotation in cls.__annotations__.items():
            # Skip private/protected attributes
            if name.startswith("_"):
                continue

            # Apply the validator wrapper
            validator = WrapValidator(invalid_to_none)

            # Handle already Annotated fields
            if get_origin(annotation) is Annotated:
                base_type = get_args(annotation)[0]
                existing_metadata = get_args(annotation)[1:]
                cls.__annotations__[name] = Annotated[
                    base_type, validator, *existing_metadata
                ]
            else:
                cls.__annotations__[name] = Annotated[annotation, validator]
