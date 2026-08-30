"""Fixtures for tests."""

from collections.abc import AsyncGenerator

import pytest
from aiointercept import aiointercept


@pytest.fixture
async def mock_http() -> AsyncGenerator[aiointercept, None]:
    """Mock http calls."""
    async with aiointercept(mock_external_urls=True) as m:
        yield m
