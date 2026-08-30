"""Tests for Trafikverket Camera."""

import aiofiles
import aiohttp
import pytest
from aiointercept import aiointercept
from syrupy.assertion import SnapshotAssertion

from pytrafikverket.const import API_URL
from pytrafikverket.trafikverket_camera import TrafikverketCamera


@pytest.fixture(name="mock_data")
async def get_mock_data() -> str:
    """Mock web response."""
    async with aiofiles.open("tests/camera_response_single.xml") as f:
        content: str = await f.read()
        return content


@pytest.mark.allow_hosts(["127.0.0.1"])
async def test_api(
    mock_data: str,
    mock_http: aiointercept,
    snapshot: SnapshotAssertion,
) -> None:
    """Test api."""
    mock_http.post(API_URL, body=mock_data, status=200, repeat=True)

    async with aiohttp.ClientSession() as session:
        camera_api = TrafikverketCamera(session, "test_api_key")
        assert camera_api
        camera = await camera_api.async_get_camera("Tpl Nybygget")
        assert camera == snapshot(name="single camera")
