"""Need for pytest or else it will cause an import error in pytest."""

from pathlib import Path

import pytest

from pytoyoda.controller import _TOKEN_CACHE


@pytest.fixture(scope="module")
def data_folder(request) -> str:
    """Return the folder containing test files."""
    return str(Path(request.module.__file__).parent / "data")


@pytest.fixture(scope="function")
def remove_cache() -> None:
    """Remove the credentials cache file if it exists."""
    # Remove cache file if exists
    _TOKEN_CACHE.clear()
