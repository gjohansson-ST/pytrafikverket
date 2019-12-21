"""Enables retreival of ferry departure information from Trafikverket API."""
import typing
from datetime import datetime
from enum import Enum
from typing import List

import aiohttp
from pytrafikverket.trafikverket import (
    FieldFilter,
    FieldSort,
    FilterOperation,
    NodeHelper,
    SortOrder,
    Trafikverket,
    mindebug
)


class RouteInfo(object):
    """Contains information about a Ferryroute. """

    _required_fields = ["Id", "Name"]

    def __init__(self, id: str, name: str):
        """Initialize RouteInfo class."""
        self.id = id
        self.name = name

    @classmethod
    def from_xml_node(cls, node):
        """Map route information in XML data."""
        node_helper = NodeHelper(node)
        id = node_helper.get_text("Id")
        name = node_helper.get_text("Name")
        return cls(id, name)

class DeviationInfo(object):
    """Contains information about a deviation situation."""
    _required_fields = ["Deviation.Id", "Deviation.Header", "Deviation.EndTime", "Deviation.StartTime",
                        "Deviation.Message", "Deviation.IconId", "Deviation.LocationDescriptor"]

    def __init__(self, id: str, header: str, message: str):
        """Initialize DeviationInfo class."""
        self.id = id
        self.header = header
        self.message = message

    @classmethod
    def from_xml_node(cls, node):
        """Map route information in XML data."""
        node_helper = NodeHelper(node)
        id = node_helper.get_text("Deviation/Id")
        header = node_helper.get_text("Deviation/Header")
        message = node_helper.get_text("Deviation/Message")
        return cls(id, header, message)


class FerryStopStatus(Enum):
    """Contain the different ferry stop statuses."""

    on_time = "scheduled to arrive on schedule"
    delayed = "delayed"
    canceled = "canceled"


class FerryStop(object):
    """Contain information about a ferry departure."""

    _required_fields = [
        "Id",
        "Deleted",
        "DepartureTime",
        "Route.Name",
        "DeviationId",
        "ModifiedTime",
        "FromHarbor",
        "ToHarbor",
        "Info",
    ]

    def __init__(
        self,
        id,
        deleted: bool,
        departure_time: datetime,
        other_information: typing.List[str],
        deviation_id: int,
        modified_time: datetime,
        from_harbor_name: str,
        to_harbor_name: str
    ):
        """Initialize FerryStop."""
        self.id = id
        self.deleted = deleted
        self.departure_time = departure_time
        self.other_information = other_information
        self.deviation_id = deviation_id
        self.modified_time = modified_time
        self.from_harbor_name = from_harbor_name
        self.to_harbor_name = to_harbor_name

    def get_state(self) -> FerryStopStatus:
        """Retrieve the state of the departure."""
        if self.deleted:  # Ferrys got no canceled-key, but a deleted
            return FerryStopStatus.deleted
        return FerryStopStatus.on_time

    @classmethod
    def from_xml_node(cls, node):
        """Map the path in the return XML data."""
        node_helper = NodeHelper(node)
        id = node_helper.get_text("Id")
        deleted = node_helper.get_bool("Deleted")
        departure_time = node_helper.get_datetime("DepartureTime")
        other_information = node_helper.get_texts("Info")
        deviation_id = node_helper.get_texts("DeviationId")
        modified_time = node_helper.get_datetime_for_modified("ModifiedTime")
        from_harbor_name = node_helper.get_text("FromHarbor/Name")
        to_harbor_name = node_helper.get_text("ToHarbor/Name")

        return cls(
            id, deleted, departure_time, other_information, deviation_id,
            modified_time, from_harbor_name, to_harbor_name)

    def print(self):
        """Prints some class variables"""
        print(f"time: {self.departure_time}")
        print(f"from: {self.from_harbor_name}")
        print(f"to: {self.to_harbor_name}")


class TrafikverketFerry(object):
    """Class used to communicate with trafikverket's ferry route api."""

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str):
        """Initialize FerryInfo object."""
        self._api = Trafikverket(client_session, api_key)

    async def async_get_route(self, route_name: str) -> RouteInfo:
        """Retreive ferry route id based on name."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            RouteInfo._required_fields,
            [FieldFilter(FilterOperation.equal, "Name", route_name)],
        )
        if len(routes) == 0:
            raise ValueError("Could not find a route with the specified name")
        if len(routes) > 1:
            raise ValueError("Found multiple routes with the specified name")

        return RouteInfo.from_xml_node(routes[0])

    async def async_search_routes(self, name: str) -> typing.List[RouteInfo]:
        """Search for ferry routes."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            ["Name", "Id"],
            [FieldFilter(FilterOperation.like, "Name", name)],
        )
        if len(routes) == 0:
            raise ValueError("Could not find a ferry route with the specified name")

        result = [RouteInfo] * 0

        for route in routes:
            result.append(RouteInfo.from_xml_node(route))

        return result

    async def async_get_next_ferry_stops(
        self,
        from_harbor_name: str,
        to_harnbor_name: str = "",
        number_of_stops: int = 1,
        after_time: datetime = datetime.now(),
    ) -> List[FerryStop]:
        """Enable retreival of next departures."""
        # ferry_announcements = self.async_get_next_ferry_stops(
        #     1, from_harbor_name, to_harnbor_name,
        #     after_time)

        date_as_text = after_time.strftime(Trafikverket.date_time_format)

        filters = [
            FieldFilter(FilterOperation.equal,
                        "FromHarbor.Name", from_harbor_name),
            FieldFilter(FilterOperation.greater_than_equal,
                        "DepartureTime", date_as_text),
        ]
        if to_harnbor_name:
            filters.append(FieldFilter(FilterOperation.equal,
                           "ToHarbor.Name", to_harnbor_name))

        sorting = [FieldSort("DepartureTime", SortOrder.ascending)]
        ferry_announcements = await self._api.async_make_request(
            "FerryAnnouncement", FerryStop._required_fields, filters, number_of_stops, sorting)

        if len(ferry_announcements) == 0:
            raise ValueError("No FerryAnnouncement found")

        stops = []
        for announcement in ferry_announcements:
            stops.append(FerryStop.from_xml_node(announcement))
        return stops

    async def async_get_next_ferry_stop(
            self,
            from_harbor_name: str,
            to_harnbor_name: str = "",
            after_time: datetime = datetime.now()) -> FerryStop:
        """Enable retreival of next departure."""
        date_as_text = after_time.strftime(Trafikverket.date_time_format)

        filters = [
            FieldFilter(FilterOperation.equal,
                        "FromHarbor.Name", from_harbor_name),
            FieldFilter(FilterOperation.greater_than_equal,
                        "DepartureTime", date_as_text),
        ]
        if to_harnbor_name:
            filters.append(FieldFilter(FilterOperation.equal,
                           "ToHarbor.Name", to_harnbor_name))

        sorting = [FieldSort("DepartureTime", SortOrder.ascending)]

        ferry_announcements = await self._api.async_make_request(
                                "FerryAnnouncement",
                                FerryStop._required_fields,
                                filters,
                                1, sorting)

        if len(ferry_announcements) == 0:
            raise ValueError("No FerryAnnouncement found")

        if len(ferry_announcements) > 1:
            raise ValueError("Multiple FerryAnnouncements found")

        ferry_announcement = ferry_announcements[0]

        return FerryStop.from_xml_node(ferry_announcement)

    async def async_get_deviation(self, id: str) -> DeviationInfo:
        mindebug(f"Call get_deviation. {str}")
        filters = [
            FieldFilter(FilterOperation.equal,
                        "Deviation.Id", id)
        ]

        deviations = await self._api.async_make_request(
            "Situation", DeviationInfo._required_fields, filters)

        # if len(deviations) == 0:
        #     raise ValueError("No Deviation found")

        deviation = deviations[0]

        return DeviationInfo.from_xml_node(deviation)

    # async def async_get_deviation(self, id: str) -> DeviationInfo:
    #     """Retreive deviation info from Deviation.Id."""
    #     deviation = await self._api.async_make_request(
    #         "Situation",
    #         DeviationInfo._required_fields,
    #         [FieldFilter(FilterOperation.equal, "Deviation.Id", id)]
    #     )
    #     if len(deviation) == 0:
    #         raise ValueError("Could not find a route with the specified name")

    #     return DeviationInfo.from_xml_node(deviation[0])
