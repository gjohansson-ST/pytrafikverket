"""Tests for Trafikverket Train stops at intermediate stations."""

from datetime import datetime
from zoneinfo import ZoneInfo

import aiofiles
import aiohttp
import pytest
from aiointercept import aiointercept

from pytrafikverket.const import API_URL
from pytrafikverket.exceptions import NoTrainAnnouncementFound
from pytrafikverket.models import StationInfoModel
from pytrafikverket.trafikverket_train import TrafikverketTrain

FROM_STATION = StationInfoModel(
    signature="Cst", station_name="Stockholm C", advertised=None
)
TO_STATION = StationInfoModel(signature="Lg", station_name="Läggesta", advertised=None)
AFTER_TIME = datetime(2026, 11, 27, 17, 0, tzinfo=ZoneInfo("Europe/Stockholm"))


async def _read(name: str) -> str:
    async with aiofiles.open(f"tests/{name}.xml", encoding="utf-8") as f:
        return await f.read()


async def _register(mock_http: aiointercept, arrivals: str, departures: str) -> None:
    """Register the arrival response followed by the departure response."""
    mock_http.post(API_URL, body=await _read(arrivals), status=200)
    mock_http.post(API_URL, body=await _read(departures), status=200)


def _request_body(mock_http: aiointercept, index: int) -> str:
    captured = mock_http.ordered_requests[index][1].captured_body
    assert captured is not None
    return captured.decode()


@pytest.mark.allow_hosts(["127.0.0.1"])
async def test_intermediate_station_found(mock_http: aiointercept) -> None:
    """Train with a later arrival at the destination is returned."""
    await _register(
        mock_http, "train_arrivals_intermediate", "train_departures_intermediate"
    )
    async with aiohttp.ClientSession() as session:
        api = TrafikverketTrain(session, "test_api_key")
        stops = await api.async_get_next_train_stops(
            FROM_STATION, TO_STATION, AFTER_TIME
        )

    assert [stop.train_stop_id for stop in stops] == ["a1"]
    assert mock_http.call_count == 2


@pytest.mark.parametrize(
    ("arrivals", "departures"),
    [
        pytest.param(
            "train_arrivals_wrong_direction",
            "train_departures_wrong_direction",
            id="arrives_before_departure",
        ),
        pytest.param(
            "train_arrivals_other_day",
            "train_departures_intermediate",
            id="different_scheduled_departure",
        ),
    ],
)
@pytest.mark.allow_hosts(["127.0.0.1"])
async def test_departure_not_stopping_afterwards_filtered(
    mock_http: aiointercept, arrivals: str, departures: str
) -> None:
    """Departures whose run does not arrive later at the destination are dropped."""
    await _register(mock_http, arrivals, departures)
    async with aiohttp.ClientSession() as session:
        api = TrafikverketTrain(session, "test_api_key")
        with pytest.raises(NoTrainAnnouncementFound):
            await api.async_get_next_train_stops(FROM_STATION, TO_STATION, AFTER_TIME)


@pytest.mark.allow_hosts(["127.0.0.1"])
async def test_destination_in_to_location_without_arrivals(
    mock_http: aiointercept,
) -> None:
    """Regression: ToLocation equal to destination works with no arrivals."""
    await _register(
        mock_http, "train_arrivals_empty", "train_departures_to_destination"
    )
    async with aiohttp.ClientSession() as session:
        api = TrafikverketTrain(session, "test_api_key")
        stops = await api.async_get_next_train_stops(
            FROM_STATION, TO_STATION, AFTER_TIME
        )

    assert [stop.train_stop_id for stop in stops] == ["a2"]


@pytest.mark.parametrize(
    ("number_of_stops", "expected_ids"),
    [
        pytest.param(1, ["a1"], id="one"),
        pytest.param(2, ["a1", "a2"], id="two"),
        pytest.param(3, ["a1", "a2", "a3"], id="all"),
    ],
)
@pytest.mark.allow_hosts(["127.0.0.1"])
async def test_number_of_stops_caps_result(
    mock_http: aiointercept, number_of_stops: int, expected_ids: list[str]
) -> None:
    """The number of stops limits the result even if more match."""
    await _register(mock_http, "train_arrivals_multiple", "train_departures_multiple")
    async with aiohttp.ClientSession() as session:
        api = TrafikverketTrain(session, "test_api_key")
        stops = await api.async_get_next_train_stops(
            FROM_STATION, TO_STATION, AFTER_TIME, number_of_stops=number_of_stops
        )

    assert [stop.train_stop_id for stop in stops] == expected_ids


@pytest.mark.allow_hosts(["127.0.0.1"])
async def test_get_train_stop(mock_http: aiointercept) -> None:
    """async_get_train_stop returns the matching stop."""
    await _register(
        mock_http, "train_arrivals_intermediate", "train_departures_intermediate"
    )
    async with aiohttp.ClientSession() as session:
        api = TrafikverketTrain(session, "test_api_key")
        stop = await api.async_get_train_stop(FROM_STATION, TO_STATION, AFTER_TIME)

    assert stop.train_stop_id == "a1"
    assert stop.product_description == ["Pendeltåg"]


@pytest.mark.allow_hosts(["127.0.0.1"])
async def test_request_bodies(mock_http: aiointercept) -> None:
    """The arrival lookup and the departure query are built as expected."""
    await _register(mock_http, "train_arrivals_multiple", "train_departures_multiple")
    async with aiohttp.ClientSession() as session:
        api = TrafikverketTrain(session, "test_api_key")
        await api.async_get_next_train_stops(FROM_STATION, TO_STATION, AFTER_TIME)

    arrival_body = _request_body(mock_http, 0)
    assert 'name="ActivityType" value="Ankomst"' in arrival_body
    assert 'name="LocationSignature" value="Lg"' in arrival_body
    assert 'limit="50"' in arrival_body

    departure_body = _request_body(mock_http, 1)
    assert 'name="ActivityType" value="Avgang"' in departure_body
    assert 'name="LocationSignature" value="Cst"' in departure_body
    for ident in ("2528", "2530", "2532"):
        assert f'EQ name="AdvertisedTrainIdent" value="{ident}"' in departure_body
    assert 'EQ name="ToLocation.LocationName" value="Lg"' in departure_body
    assert 'EQ name="ViaToLocation.LocationName" value="Lg"' in departure_body
