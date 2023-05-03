"""Enables retreival of ferry departure information from Trafikverket API."""
from __future__ import annotations

from typing import Any

from datetime import datetime
from enum import Enum

import aiohttp
from pytrafikverket.trafikverket import (
    Filter,
    FieldFilter,
    FieldSort,
    FilterOperation,
    NodeHelper,
    SortOrder,
    Trafikverket,
)

from .exceptions import (
    NoRouteFound,
    MultipleRoutesFound,
    NoFerryFound,
    NoDeviationFound,
    MultipleDeviationsFound,
)

# pylint: disable=W0622, C0103


class RouteInfo:
    """Contains information about a FerryRoute."""

    _required_fields = ["Id", "Name", "Shortname", "Type.Name"]

    def __init__(
        self,
        id: str | None,
        name: str | None,
        short_name: str | None,
        route_type: str | None,
    ) -> None:
        """Initialize RouteInfo class."""
        self.id = id
        self.name = name
        self.short_name = short_name
        self.route_type = route_type

    @classmethod
    def from_xml_node(cls, node: Any) -> RouteInfo:
        """Map route information in XML data."""
        node_helper = NodeHelper(node)
        id = node_helper.get_text("Id")
        name = node_helper.get_text("Name")
        short_name = node_helper.get_text("Shortname")
        route_type = node_helper.get_text("Type/Name")

        return cls(id, name, short_name, route_type)


class DeviationInfo:
    """Contains information about a Situation/Deviation."""

    _required_fields = [
        "Deviation.Id",
        "Deviation.Header",
        "Deviation.EndTime",
        "Deviation.StartTime",
        "Deviation.Message",
        "Deviation.IconId",
        "Deviation.LocationDescriptor",
    ]

    def __init__(
        self,
        id: str | None,
        header: str | None,
        message: str | None,
        start_time: datetime | None,
        end_time: datetime | None,
        icon_id: str | None,
        location_desc: str | None,
    ) -> None:
        """Initialize DeviationInfo class."""
        self.id = id
        self.header = header
        self.message = message
        self.start_time = start_time
        self.end_time = end_time
        self.icon_id = icon_id
        self.location_desc = location_desc

    @classmethod
    def from_xml_node(cls, node: Any) -> DeviationInfo:
        """Map deviation information in XML data."""
        node_helper = NodeHelper(node)
        id = node_helper.get_text("Deviation/Id")
        header = node_helper.get_text("Deviation/Header")
        message = node_helper.get_text("Deviation/Message")
        start_time = node_helper.get_datetime("Deviation/StartTime")
        end_time = node_helper.get_datetime("Deviation/EndTime")
        icon_id = node_helper.get_text("Deviation/IconId")
        location_desc = node_helper.get_text("Deviation/LocationDescriptor")
        return cls(id, header, message, start_time, end_time, icon_id, location_desc)


class FerryStopStatus(Enum):
    """Contain the different ferry stop statuses."""

    ON_TIME = "on_time"
    CANCELED = "canceled"
    DELETED = "deleted"


class FerryStop:
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
        id: str | None,
        deleted: bool,
        departure_time: datetime | None,
        other_information: list[str] | None,
        deviation_id: list[str] | None,
        modified_time: datetime | None,
        from_harbor_name: str | None,
        to_harbor_name: str | None,
    ) -> None:
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
        if self.deleted:
            return FerryStopStatus.DELETED
        return FerryStopStatus.ON_TIME

    @classmethod
    def from_xml_node(cls, node: Any) -> FerryStop:
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
            id,
            deleted,
            departure_time,
            other_information,
            deviation_id,
            modified_time,
            from_harbor_name,
            to_harbor_name,
        )


class TrafikverketFerry:
    """Class used to communicate with trafikverket's ferry route api."""

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize FerryInfo object."""
        self._api = Trafikverket(client_session, api_key)

    async def async_get_ferry_route(self, route_name: str) -> RouteInfo:
        """Retreive ferry route id based on name."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            "1.2",
            RouteInfo._required_fields,  # pylint: disable=protected-access
            [FieldFilter(FilterOperation.EQUAL, "Name", route_name)],
        )
        if len(routes) == 0:
            raise NoRouteFound("Could not find a route with the specified name")
        if len(routes) > 1:
            raise MultipleRoutesFound("Found multiple routes with the specified name")

        return RouteInfo.from_xml_node(routes[0])

    async def async_get_ferry_route_id(self, route_id: int) -> RouteInfo:
        """Retreive ferry route id based on routeId."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            "1.2",
            RouteInfo._required_fields,  # pylint: disable=protected-access
            [FieldFilter(FilterOperation.EQUAL, "Id", str(route_id))],
        )
        if len(routes) == 0:
            raise NoRouteFound("Could not find a route with the specified name")
        if len(routes) > 1:
            raise MultipleRoutesFound("Found multiple routes with the specified name")

        return RouteInfo.from_xml_node(routes[0])

    async def async_search_ferry_routes(self, name: str) -> list[RouteInfo]:
        """Search for ferry routes based on the route name."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            "1.2",
            RouteInfo._required_fields,  # pylint: disable=protected-access
            [FieldFilter(FilterOperation.LIKE, "Name", name)],
        )
        if len(routes) == 0:
            raise NoRouteFound("Could not find a ferry route with the specified name")

        result = []

        for route in routes:
            result.append(RouteInfo.from_xml_node(route))

        return result

    async def async_get_next_ferry_stops(
        self,
        from_harbor_name: str,
        to_harnbor_name: str = "",
        after_time: datetime = datetime.now(),
        number_of_stops: int = 1,
    ) -> list[FerryStop]:
        """Enable retreival of next departures."""
        date_as_text = after_time.strftime(Trafikverket.date_time_format)

        filters: list[FieldFilter | Filter] = [
            FieldFilter(FilterOperation.EQUAL, "FromHarbor.Name", from_harbor_name),
            FieldFilter(
                FilterOperation.GREATER_THAN_EQUAL, "DepartureTime", date_as_text
            ),
        ]
        if to_harnbor_name:
            filters.append(
                FieldFilter(FilterOperation.EQUAL, "ToHarbor.Name", to_harnbor_name)
            )

        sorting = [FieldSort("DepartureTime", SortOrder.ASCENDING)]
        ferry_announcements = await self._api.async_make_request(
            "FerryAnnouncement",
            "1.2",
            FerryStop._required_fields,  # pylint: disable=protected-access
            filters,
            number_of_stops,
            sorting,
        )

        if len(ferry_announcements) == 0:
            raise NoFerryFound("No FerryAnnouncement found")

        stops = []
        for announcement in ferry_announcements:
            stops.append(FerryStop.from_xml_node(announcement))
        return stops

    async def async_get_next_ferry_stop(
        self,
        from_harbor_name: str,
        to_harnbor_name: str = "",
        after_time: datetime = datetime.now(),
    ) -> FerryStop:
        """Enable retreival of next departure."""
        stops = await self.async_get_next_ferry_stops(
            from_harbor_name, to_harnbor_name, after_time, 1
        )
        return stops[0]

    async def async_get_deviation(self, id: str) -> DeviationInfo:
        """Retreive deviation info from Deviation Id."""
        filters: list[FieldFilter | Filter] = [
            FieldFilter(FilterOperation.EQUAL, "Deviation.Id", id)
        ]
        deviations = await self._api.async_make_request(
            "Situation",
            "1.5",
            DeviationInfo._required_fields,  # pylint: disable=protected-access
            filters,
        )

        if len(deviations) == 0:
            raise NoDeviationFound("No Deviation found")
        if len(deviations) > 1:
            raise MultipleDeviationsFound("Multiple Deviations found")

        deviation = deviations[0]
        return DeviationInfo.from_xml_node(deviation)
