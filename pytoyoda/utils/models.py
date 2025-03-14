"""Utilities for manipulating or extending pydantic models."""

from collections.abc import Callable
from typing import Annotated, Any, get_args, get_origin

from pydantic import BaseModel, ValidationError, WrapValidator


def invalid_to_none(v: Any, handler: Callable[[Any], Any]) -> Any:  # noqa: D103
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

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: D105
        for name, annotation in cls.__annotations__.items():
            if name.startswith("_"):  # exclude protected/private attributes
                continue
            validator = WrapValidator(invalid_to_none)
            if get_origin(annotation) is Annotated:
                cls.__annotations__[name] = Annotated[
                    *get_args(annotation),
                    validator,
                ]
            else:
                cls.__annotations__[name] = Annotated[annotation, validator]
