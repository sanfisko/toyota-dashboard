"""Need for pytest or else it will cause an import error in pytest."""

from pathlib import Path

import pytest

from pytoyoda.controller.Controller import _TOKEN_CACHE

TEST_USER = "user@email.info"
TEST_PASSWORD = "password"
TEST_TOKEN = "eyJ0eXAiOiJKV1QiLCJraWQiOiJZeVZ2SEU5d0xKNDBWVEpyc3pBNDJ6eTNyWjg9IiwiYWxnIjoiUlMyNTYifQ"  # noqa: E501
TEST_UUID = "12345678-1234-1234-1234-123456789012"


@pytest.fixture(scope="module")
def data_folder(request) -> str:
    """Return the folder containing test files."""
    return str(Path(request.module.__file__).parent / "data")


@pytest.fixture(scope="function")
def remove_cache() -> None:
    """Remove the credentials cache if it exists."""
    _TOKEN_CACHE.clear()
