"""Enables retrieval of train departure information from Trafikverket API."""

from __future__ import annotations

from datetime import datetime

from .const import (
    DATE_TIME_FORMAT,
    TRAIN_STOP_REQUIRED_FIELDS,
)
from .exceptions import (
    MultipleTrainStationsFound,
    NoTrainAnnouncementFound,
    NoTrainStationFound,
)
from .filters import FieldFilter, FieldSort, FilterOperation, OrFilter, SortOrder
from .helpers import (
    station_from_xml_node,
    train_stop_from_xml_node,
)
from .models import StationInfoModel, TrainStopModel
from .trafikverket import (
    TrafikverketBase,
)


class TrafikverketTrain(TrafikverketBase):
    """Class used to communicate with trafikverket's train api."""

    version = "1.9"

    async def async_get_train_station_from_signature(
        self, signature: str
    ) -> StationInfoModel:
        """Retrieve train station based on signature."""
        train_stations = await self._api.async_make_request(
            "TrainStation",
            "1.5",
            "rail.infrastructure",
            ["AdvertisedLocationName", "LocationSignature", "Advertised", "Deleted"],
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
            ["AdvertisedLocationName", "LocationSignature", "Advertised", "Deleted"],
            [
                FieldFilter(
                    FilterOperation.LIKE, "AdvertisedLocationName", location_name
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

        filters = [
            FieldFilter(FilterOperation.EQUAL, "ActivityType", "Avgang"),
            FieldFilter(
                FilterOperation.EQUAL, "LocationSignature", from_station.signature
            ),
            FieldFilter(
                FilterOperation.EQUAL, "AdvertisedTimeAtLocation", date_as_text
            ),
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

        train_announcements = await self._api.async_make_request(
            "TrainAnnouncement",
            self.version,
            None,
            TRAIN_STOP_REQUIRED_FIELDS,
            filters,
            1,
        )

        if len(train_announcements) == 0:
            raise NoTrainAnnouncementFound("No TrainAnnouncement found")

        train_announcement = train_announcements[0]
        return await train_stop_from_xml_node(train_announcement)

    async def async_get_next_train_stops(
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

        filters = [
            FieldFilter(FilterOperation.EQUAL, "ActivityType", "Avgang"),
            FieldFilter(
                FilterOperation.EQUAL, "LocationSignature", from_station.signature
            ),
            FieldFilter(
                FilterOperation.GREATER_THAN_EQUAL,
                "AdvertisedTimeAtLocation",
                date_as_text,
            ),
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

        sorting = [FieldSort("AdvertisedTimeAtLocation", SortOrder.ASCENDING)]
        train_announcements = await self._api.async_make_request(
            "TrainAnnouncement",
            self.version,
            None,
            TRAIN_STOP_REQUIRED_FIELDS,
            filters,
            number_of_stops,
            sorting,
        )

        if len(train_announcements) == 0:
            raise NoTrainAnnouncementFound("No TrainAnnouncement found")

        stops = []
        for announcement in train_announcements:
            stops.append(await train_stop_from_xml_node(announcement))
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
