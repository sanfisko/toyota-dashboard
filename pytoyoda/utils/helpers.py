"""Helper functions for numeric operations with None handling."""

from typing import Optional, Union


def add_with_none(
    this: Optional[Union[int, float]], that: Optional[Union[int, float]]
) -> Optional[Union[int, float]]:
    """Add two items safely, handling None values.

    If either value is None, returns the other value.
    If both values are None, returns None.
    Otherwise, returns the sum of both values.

    Args:
        this: First value to add
        that: Second value to add

    Returns:
        The sum of both values, or whichever value is not None,
        or None if both values are None.

    Examples:
        >>> add_with_none(5, 3)
        8
        >>> add_with_none(None, 3)
        3
        >>> add_with_none(5, None)
        5
        >>> add_with_none(None, None)
        None

    """
    if this is None:
        return that
    if that is None:
        return this

    return this + that
