"""Enables retreival of train departure information from Trafikverket API."""
import typing
from datetime import datetime, timedelta
from enum import Enum

import aiohttp
from pytrafikverket.trafikverket import (
    FieldFilter,
    FieldSort,
    FilterOperation,
    NodeHelper,
    OrFilter,
    SortOrder,
    Trafikverket,
)


class StationInfo(object):
    """Contains information about a train station."""

    _required_fields = ["LocationSignature", "AdvertisedLocationName"]

    def __init__(self, signature: str, name: str, advertised: str):
        """Initialize StationInfo class."""
        self.signature = signature
        self.name = name
        self.advertised = advertised

    @classmethod
    def from_xml_node(cls, node):
        """Map station information in XML data."""
        node_helper = NodeHelper(node)
        location_signature = node_helper.get_text("LocationSignature")
        advertised_location_name = node_helper.get_text("AdvertisedLocationName")
        location_advertised = node_helper.get_text("Advertised")
        return cls(location_signature, advertised_location_name, location_advertised)


class TrainStopStatus(Enum):
    """Contain the different train stop statuses."""

    on_time = "scheduled to arrive on schedule"
    delayed = "delayed"
    canceled = "canceled"


class TrainStop(object):
    """Contain information about a train stop."""

    _required_fields = [
        "ActivityId",
        "Canceled",
        "AdvertisedTimeAtLocation",
        "EstimatedTimeAtLocation",
        "TimeAtLocation",
        "OtherInformation",
        "Deviation",
        "ModifiedTime",
        "ProductInformation",
    ]

    def __init__(
        self,
        id,
        canceled: bool,
        advertised_time_at_location: datetime,
        estimated_time_at_location: datetime,
        time_at_location: datetime,
        other_information: typing.List[str],
        deviations: typing.List[str],
        modified_time: datetime,
        product_description: str,
    ):
        """Initialize TrainStop."""
        self.id = id
        self.canceled = canceled
        self.advertised_time_at_location = advertised_time_at_location
        self.estimated_time_at_location = estimated_time_at_location
        self.time_at_location = time_at_location
        self.other_information = other_information
        self.deviations = deviations
        self.modified_time = modified_time
        self.product_description = product_description

    def get_state(self) -> TrainStopStatus:
        """Retrieve the state of the departure."""
        if self.canceled:
            return TrainStopStatus.canceled
        if (
            self.advertised_time_at_location is not None
            and self.time_at_location is not None
            and self.advertised_time_at_location != self.time_at_location
        ):
            return TrainStopStatus.delayed
        if (
            self.advertised_time_at_location is not None
            and self.estimated_time_at_location is not None
            and self.advertised_time_at_location != self.estimated_time_at_location
        ):
            return TrainStopStatus.delayed
        return TrainStopStatus.on_time

    def get_delay_time(self) -> timedelta:
        """Calculate the delay of a departure."""
        if self.canceled:
            return None
        if (
            self.advertised_time_at_location is not None
            and self.time_at_location is not None
            and self.advertised_time_at_location != self.time_at_location
        ):
            return self.time_at_location - self.advertised_time_at_location
        if (
            self.advertised_time_at_location is not None
            and self.estimated_time_at_location is not None
            and self.advertised_time_at_location != self.estimated_time_at_location
        ):
            return self.estimated_time_at_location - self.advertised_time_at_location
        return None

    @classmethod
    def from_xml_node(cls, node):
        """Map the path in the return XML data."""
        node_helper = NodeHelper(node)
        activity_id = node_helper.get_text("ActivityId")
        canceled = node_helper.get_bool("Canceled")
        advertised_time_at_location = node_helper.get_datetime(
            "AdvertisedTimeAtLocation"
        )
        estimated_time_at_location = node_helper.get_datetime("EstimatedTimeAtLocation")
        time_at_location = node_helper.get_datetime("TimeAtLocation")
        other_information = node_helper.get_texts("OtherInformation/Description")
        deviations = node_helper.get_texts("Deviation/Description")
        modified_time = node_helper.get_datetime_for_modified("ModifiedTime")
        product_description = node_helper.get_texts("ProductInformation/Description")
        return cls(
            activity_id,
            canceled,
            advertised_time_at_location,
            estimated_time_at_location,
            time_at_location,
            other_information,
            deviations,
            modified_time,
            product_description,
        )


class TrafikverketTrain(object):
    """Class used to communicate with trafikverket's train api."""

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str):
        """Initialize TrainInfo object."""
        self._api = Trafikverket(client_session, api_key)

    async def async_get_train_station(self, location_name: str) -> StationInfo:
        """Retreive train station id based on name."""
        train_stations = await self._api.async_make_request(
            "TrainStation",
            "1.4",
            StationInfo._required_fields,
            [
                FieldFilter(
                    FilterOperation.equal, "AdvertisedLocationName", location_name
                ),
                FieldFilter(FilterOperation.equal, "Advertised", "true"),
            ],
        )
        if len(train_stations) == 0:
            raise ValueError("Could not find a station with the specified name")
        if len(train_stations) > 1:
            raise ValueError("Found multiple stations with the specified name")

        return StationInfo.from_xml_node(train_stations[0])

    async def async_search_train_stations(
        self, location_name: str
    ) -> typing.List[StationInfo]:
        """Search for train stations."""
        train_stations = await self._api.async_make_request(
            "TrainStation",
            "1.4",
            ["AdvertisedLocationName", "LocationSignature", "Advertised", "Deleted"],
            [
                FieldFilter(
                    FilterOperation.like, "AdvertisedLocationName", location_name
                ),
                FieldFilter(FilterOperation.equal, "Advertised", "true"),
            ],
        )
        if len(train_stations) == 0:
            raise ValueError("Could not find a station with the specified name")

        result = [StationInfo] * 0

        for train_station in train_stations:
            result.append(StationInfo.from_xml_node(train_station))

        return result

    async def async_get_train_stop(
        self,
        from_station: StationInfo,
        to_station: StationInfo,
        time_at_location: datetime,
        product_description: typing.Optional[str] = None,
        exclude_canceled: bool = False,
    ) -> TrainStop:
        """Retrieve the train stop."""
        date_as_text = time_at_location.strftime(Trafikverket.date_time_format)

        filters = [
            FieldFilter(FilterOperation.equal, "ActivityType", "Avgang"),
            FieldFilter(
                FilterOperation.equal, "LocationSignature", from_station.signature
            ),
            FieldFilter(
                FilterOperation.equal, "AdvertisedTimeAtLocation", date_as_text
            ),
            OrFilter(
                [
                    FieldFilter(
                        FilterOperation.equal,
                        "ViaToLocation.LocationName",
                        to_station.signature,
                    ),
                    FieldFilter(
                        FilterOperation.equal,
                        "ToLocation.LocationName",
                        to_station.signature,
                    ),
                ]
            ),
        ]

        if product_description:
            filters.append(
                FieldFilter(
                    FilterOperation.equal,
                    "ProductInformation.Description",
                    product_description,
                )
            )

        if exclude_canceled:
            filters.append(
                FieldFilter(
                    FilterOperation.equal,
                    "Canceled",
                    "false"
                )
            )

        train_announcements = await self._api.async_make_request(
            "TrainAnnouncement", "1.6", TrainStop._required_fields, filters
        )

        if len(train_announcements) == 0:
            raise ValueError("No TrainAnnouncement found")

        if len(train_announcements) > 1:
            raise ValueError("Multiple TrainAnnouncements found")

        train_announcement = train_announcements[0]
        return TrainStop.from_xml_node(train_announcement)

    async def async_get_next_train_stop(
        self,
        from_station: StationInfo,
        to_station: StationInfo,
        after_time: datetime,
        product_description: typing.Optional[str] = None,
        exclude_canceled: bool = False,
    ) -> TrainStop:
        """Enable retreival of next departure."""
        date_as_text = after_time.strftime(Trafikverket.date_time_format)

        filters = [
            FieldFilter(FilterOperation.equal, "ActivityType", "Avgang"),
            FieldFilter(
                FilterOperation.equal, "LocationSignature", from_station.signature
            ),
            FieldFilter(
                FilterOperation.greater_than_equal,
                "AdvertisedTimeAtLocation",
                date_as_text,
            ),
            OrFilter(
                [
                    FieldFilter(
                        FilterOperation.equal,
                        "ViaToLocation.LocationName",
                        to_station.signature,
                    ),
                    FieldFilter(
                        FilterOperation.equal,
                        "ToLocation.LocationName",
                        to_station.signature,
                    ),
                ]
            ),
        ]

        if product_description:
            filters.append(
                FieldFilter(
                    FilterOperation.equal,
                    "ProductInformation.Description",
                    product_description,
                )
            )

        if exclude_canceled:
            filters.append(
                FieldFilter(
                    FilterOperation.equal,
                    "Canceled",
                    "false"
                )
            )

        sorting = [FieldSort("AdvertisedTimeAtLocation", SortOrder.ascending)]
        train_announcements = await self._api.async_make_request(
            "TrainAnnouncement", "1.6", TrainStop._required_fields, filters, 1, sorting
        )

        if len(train_announcements) == 0:
            raise ValueError("No TrainAnnouncement found")

        if len(train_announcements) > 1:
            raise ValueError("Multiple TrainAnnouncements found")

        train_announcement = train_announcements[0]

        return TrainStop.from_xml_node(train_announcement)
