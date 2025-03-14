"""Utilities for validating locale strings."""

import contextlib
from typing import Optional

from langcodes import Language
from langcodes.tag_parser import LanguageTagError


def is_valid_locale(locale: Optional[str]) -> bool:
    """Check if the provided locale string is valid according to language standards.

    Args:
        locale: A string representing a locale (e.g., 'en-US', 'de-DE', 'fr')

    Returns:
        bool: True if the locale is valid, False otherwise.
              Returns False for None or empty strings.

    Examples:
        >>> is_valid_locale("en-US")
        True
        >>> is_valid_locale("xyz")
        False
        >>> is_valid_locale(None)
        False

    """
    if not locale:
        return False
    with contextlib.suppress(LanguageTagError):
        return Language.get(locale).is_valid()
    return False
