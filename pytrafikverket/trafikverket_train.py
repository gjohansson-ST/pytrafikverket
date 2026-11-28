"""Enables retrieval of train departure information from Trafikverket API."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from .const import (
    DATE_TIME_FORMAT,
    TRAIN_STOP_REQUIRED_FIELDS,
)
from .exceptions import (
    MultipleTrainStationsFound,
    NoTrainAnnouncementFound,
    NoTrainStationFound,
)
from .filters import (
    FieldFilter,
    FieldSort,
    Filter,
    FilterOperation,
    OrFilter,
    SortOrder,
)
from .helpers import (
    NodeHelper,
    station_from_xml_node,
    train_stop_from_xml_node,
)
from .models import StationInfoModel, TrainStopModel
from .trafikverket import (
    TrafikverketBase,
)

if TYPE_CHECKING:
    from lxml import etree

ARRIVAL_LOOKUP_LIMIT = 50
TRAIN_RUN_FIELDS = [
    "AdvertisedTrainIdent",
    "ScheduledDepartureDateTime",
    "ToLocation",
    "ViaToLocation",
]


def _train_run(node: etree._ElementTree) -> tuple[str, str] | None:
    """Return the train ident and scheduled departure date of a train run."""
    helper = NodeHelper(node)
    ident = helper.get_text("AdvertisedTrainIdent")
    scheduled_departure = helper.get_text("ScheduledDepartureDateTime")
    if ident is None or scheduled_departure is None:
        return None
    return (ident, scheduled_departure)


def _stops_at_destination(
    departure: etree._ElementTree,
    to_station: StationInfoModel,
    arrival_runs: dict[tuple[str, str], datetime],
) -> bool:
    """Return if the train departing also stops at the destination afterwards."""
    helper = NodeHelper(departure)
    destinations = helper.get_texts("ToLocation/LocationName") or []
    destinations += helper.get_texts("ViaToLocation/LocationName") or []
    if to_station.signature in destinations:
        return True
    if (run := _train_run(departure)) is None or run not in arrival_runs:
        return False
    departure_time = helper.get_datetime("AdvertisedTimeAtLocation")
    return departure_time is not None and departure_time < arrival_runs[run]


class TrafikverketTrain(TrafikverketBase):
    """Class used to communicate with trafikverket's train api."""

    version = "2.0"
    namespace = "rail.trafficinfo"

    async def async_get_train_station_from_signature(
        self, signature: str
    ) -> StationInfoModel:
        """Retrieve train station based on signature."""
        train_stations = await self._api.async_make_request(
            "TrainStation",
            "1.5",
            "rail.infrastructure",
            [
                "AdvertisedLocationName",
                "LocationSignature",
                "Advertised",
                "Deleted",
                "OfficialLocationName",
            ],
            [
                FieldFilter(FilterOperation.EQUAL, "LocationSignature", signature),
            ],
        )
        if len(train_stations) == 0:
            raise NoTrainStationFound(
                "Could not find a station with the specified name"
            )
        return await station_from_xml_node(train_stations[0])

    async def async_search_train_station(self, location_name: str) -> StationInfoModel:
        """Retrieve train station id based on name."""
        train_stations = await self.async_search_train_stations(location_name)

        if len(train_stations) == 0:
            raise NoTrainStationFound(
                "Could not find a station with the specified name"
            )
        if len(train_stations) > 1:
            raise MultipleTrainStationsFound(
                "Found multiple stations with the specified name"
            )

        return train_stations[0]

    async def async_search_train_stations(
        self, location_name: str
    ) -> list[StationInfoModel]:
        """Search for train stations."""
        train_stations = await self._api.async_make_request(
            "TrainStation",
            "1.5",
            "rail.infrastructure",
            [
                "AdvertisedLocationName",
                "LocationSignature",
                "Advertised",
                "Deleted",
                "OfficialLocationName",
            ],
            [
                OrFilter(
                    [
                        FieldFilter(
                            FilterOperation.LIKE,
                            "AdvertisedLocationName",
                            location_name,
                        ),
                        FieldFilter(
                            FilterOperation.LIKE,
                            "OfficialLocationName",
                            location_name,
                        ),
                    ]
                ),
                FieldFilter(FilterOperation.EQUAL, "Advertised", "true"),
            ],
        )
        if len(train_stations) == 0:
            raise NoTrainStationFound(
                "Could not find a station with the specified name"
            )

        result = []

        for train_station in train_stations:
            result.append(await station_from_xml_node(train_station))

        return result

    async def async_get_train_stop(
        self,
        from_station: StationInfoModel,
        to_station: StationInfoModel,
        time_at_location: datetime,
        product_description: str | None = None,
        exclude_canceled: bool = False,
    ) -> TrainStopModel:
        """Retrieve the train stop."""
        date_as_text = time_at_location.strftime(DATE_TIME_FORMAT)
        stops = await self._async_get_departures(
            from_station,
            to_station,
            FieldFilter(
                FilterOperation.EQUAL, "AdvertisedTimeAtLocation", date_as_text
            ),
            date_as_text,
            product_description,
            exclude_canceled,
            1,
        )
        return stops[0]

    async def async_get_next_train_stops(  # noqa: PLR0917
        self,
        from_station: StationInfoModel,
        to_station: StationInfoModel,
        after_time: datetime,
        product_description: str | None = None,
        exclude_canceled: bool = False,
        number_of_stops: int = 1,
    ) -> list[TrainStopModel]:
        """Enable retrieval of next departures."""
        date_as_text = after_time.strftime(DATE_TIME_FORMAT)
        return await self._async_get_departures(
            from_station,
            to_station,
            FieldFilter(
                FilterOperation.GREATER_THAN_EQUAL,
                "AdvertisedTimeAtLocation",
                date_as_text,
            ),
            date_as_text,
            product_description,
            exclude_canceled,
            number_of_stops,
        )

    async def _async_get_arrival_runs(
        self, to_station: StationInfoModel, after_time_as_text: str
    ) -> dict[tuple[str, str], datetime]:
        """Return the next train runs arriving at a station.

        The key is the advertised train ident and the scheduled departure date
        of the train run, the value is the advertised arrival time.
        """
        arrivals = await self._api.async_make_request(
            "TrainAnnouncement",
            self.version,
            self.namespace,
            [
                "AdvertisedTrainIdent",
                "ScheduledDepartureDateTime",
                "AdvertisedTimeAtLocation",
            ],
            [
                FieldFilter(FilterOperation.EQUAL, "ActivityType", "Ankomst"),
                FieldFilter(
                    FilterOperation.EQUAL, "LocationSignature", to_station.signature
                ),
                FieldFilter(
                    FilterOperation.GREATER_THAN_EQUAL,
                    "AdvertisedTimeAtLocation",
                    after_time_as_text,
                ),
            ],
            ARRIVAL_LOOKUP_LIMIT,
            [FieldSort("AdvertisedTimeAtLocation", SortOrder.ASCENDING)],
        )
        runs: dict[tuple[str, str], datetime] = {}
        for arrival in arrivals:
            if (run := _train_run(arrival)) is None:
                continue
            arrival_time = NodeHelper(arrival).get_datetime("AdvertisedTimeAtLocation")
            if arrival_time is not None:
                runs.setdefault(run, arrival_time)
        return runs

    async def _async_get_departures(  # noqa: PLR0917
        self,
        from_station: StationInfoModel,
        to_station: StationInfoModel,
        time_filter: FieldFilter,
        after_time_as_text: str,
        product_description: str | None,
        exclude_canceled: bool,
        number_of_stops: int,
    ) -> list[TrainStopModel]:
        """Retrieve departures from a station for trains that stop at another.

        Trafikverket only lists the final destination and a few major stations
        in ToLocation and ViaToLocation. To also find trains that stop at
        smaller intermediate stations, the departures are matched against the
        train runs arriving at the destination station.
        """
        arrival_runs = await self._async_get_arrival_runs(
            to_station, after_time_as_text
        )
        train_idents = sorted({ident for ident, _ in arrival_runs})

        filters: list[Filter] = [
            FieldFilter(FilterOperation.EQUAL, "ActivityType", "Avgang"),
            FieldFilter(
                FilterOperation.EQUAL, "LocationSignature", from_station.signature
            ),
            time_filter,
            OrFilter(
                [
                    FieldFilter(
                        FilterOperation.EQUAL,
                        "ViaToLocation.LocationName",
                        to_station.signature,
                    ),
                    FieldFilter(
                        FilterOperation.EQUAL,
                        "ToLocation.LocationName",
                        to_station.signature,
                    ),
                    *(
                        FieldFilter(
                            FilterOperation.EQUAL, "AdvertisedTrainIdent", ident
                        )
                        for ident in train_idents
                    ),
                ]
            ),
        ]

        if product_description:
            filters.append(
                FieldFilter(
                    FilterOperation.LIKE,
                    "ProductInformation.Description",
                    product_description,
                )
            )

        if exclude_canceled:
            filters.append(FieldFilter(FilterOperation.EQUAL, "Canceled", "false"))

        # Departures matched only on train ident can belong to a train run going
        # in the other direction, so fetch enough to filter those out afterwards.
        train_announcements = await self._api.async_make_request(
            "TrainAnnouncement",
            self.version,
            self.namespace,
            [*TRAIN_STOP_REQUIRED_FIELDS, *TRAIN_RUN_FIELDS],
            filters,
            number_of_stops + len(arrival_runs),
            [FieldSort("AdvertisedTimeAtLocation", SortOrder.ASCENDING)],
        )

        stops = []
        for announcement in train_announcements:
            if not _stops_at_destination(announcement, to_station, arrival_runs):
                continue
            stops.append(await train_stop_from_xml_node(announcement))
            if len(stops) == number_of_stops:
                break

        if not stops:
            raise NoTrainAnnouncementFound("No TrainAnnouncement found")
        return stops

    async def async_get_next_train_stop(
        self,
        from_station: StationInfoModel,
        to_station: StationInfoModel,
        after_time: datetime,
        product_description: str | None = None,
        exclude_canceled: bool = False,
    ) -> TrainStopModel:
        """Enable retrieval of next departure."""

        stops = await self.async_get_next_train_stops(
            from_station,
            to_station,
            after_time,
            product_description,
            exclude_canceled,
            1,
        )
        return stops[0]
