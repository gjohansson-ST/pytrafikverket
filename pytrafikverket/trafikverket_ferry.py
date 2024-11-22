"""Enables retrieval of ferry departure information from Trafikverket API."""

from __future__ import annotations

from datetime import datetime

from .const import (
    DATE_TIME_FORMAT,
    DEVIATION_INFO_REQUIRED_FIELDS,
    FERRY_STOP_REQUIRED_FIELDS,
    ROUTE_INFO_REQUIRED_FIELDS,
)
from .exceptions import (
    MultipleDeviationsFound,
    MultipleRoutesFound,
    NoDeviationFound,
    NoFerryFound,
    NoRouteFound,
)
from .filters import FieldFilter, FieldSort, Filter, FilterOperation, SortOrder
from .helpers import (
    deviation_from_xml_node,
    ferry_route_from_xml_node,
    ferry_stop_from_xml_node,
)
from .models import (
    DeviationInfoModel,
    FerryRouteInfoModel,
    FerryStopModel,
)
from .trafikverket import (
    TrafikverketBase,
)


class TrafikverketFerry(TrafikverketBase):
    """Class used to communicate with trafikverket's ferry route api."""

    version = "1.2"

    async def async_get_ferry_route(self, route_name: str) -> FerryRouteInfoModel:
        """Retrieve ferry route id based on name."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            self.version,
            None,
            ROUTE_INFO_REQUIRED_FIELDS,
            [FieldFilter(FilterOperation.EQUAL, "Name", route_name)],
        )
        if len(routes) == 0:
            raise NoRouteFound("Could not find a route with the specified name")
        if len(routes) > 1:
            raise MultipleRoutesFound("Found multiple routes with the specified name")

        return await ferry_route_from_xml_node(routes[0])

    async def async_get_ferry_route_id(self, route_id: int) -> FerryRouteInfoModel:
        """Retrieve ferry route id based on routeId."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            self.version,
            None,
            ROUTE_INFO_REQUIRED_FIELDS,
            [FieldFilter(FilterOperation.EQUAL, "Id", str(route_id))],
        )
        if len(routes) == 0:
            raise NoRouteFound("Could not find a route with the specified name")
        if len(routes) > 1:
            raise MultipleRoutesFound("Found multiple routes with the specified name")

        return await ferry_route_from_xml_node(routes[0])

    async def async_search_ferry_routes(self, name: str) -> list[FerryRouteInfoModel]:
        """Search for ferry routes based on the route name."""
        routes = await self._api.async_make_request(
            "FerryRoute",
            self.version,
            None,
            ROUTE_INFO_REQUIRED_FIELDS,
            [FieldFilter(FilterOperation.LIKE, "Name", name)],
        )
        if len(routes) == 0:
            raise NoRouteFound("Could not find a ferry route with the specified name")

        result = []

        for route in routes:
            result.append(await ferry_route_from_xml_node(route))

        return result

    async def async_get_next_ferry_stops(
        self,
        from_harbor_name: str,
        to_harnbor_name: str = "",
        after_time: datetime = datetime.now(),
        number_of_stops: int = 1,
    ) -> list[FerryStopModel]:
        """Enable retrieval of next departures."""
        date_as_text = after_time.strftime(DATE_TIME_FORMAT)

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
            self.version,
            None,
            FERRY_STOP_REQUIRED_FIELDS,
            filters,
            number_of_stops,
            sorting,
        )

        if len(ferry_announcements) == 0:
            raise NoFerryFound("No FerryAnnouncement found")

        stops = []
        for announcement in ferry_announcements:
            stops.append(await ferry_stop_from_xml_node(announcement))
        return stops

    async def async_get_next_ferry_stop(
        self,
        from_harbor_name: str,
        to_harnbor_name: str = "",
        after_time: datetime = datetime.now(),
    ) -> FerryStopModel:
        """Enable retrieval of next departure."""
        stops = await self.async_get_next_ferry_stops(
            from_harbor_name, to_harnbor_name, after_time, 1
        )
        return stops[0]

    async def async_get_deviation(self, id: str) -> DeviationInfoModel:
        """Retrieve deviation info from Deviation Id."""
        filters: list[FieldFilter | Filter] = [
            FieldFilter(FilterOperation.EQUAL, "Deviation.Id", id)
        ]
        deviations = await self._api.async_make_request(
            "Situation",
            "1.5",
            None,
            DEVIATION_INFO_REQUIRED_FIELDS,
            filters,
        )

        if len(deviations) == 0:
            raise NoDeviationFound("No Deviation found")
        if len(deviations) > 1:
            raise MultipleDeviationsFound("Multiple Deviations found")

        deviation = deviations[0]
        return await deviation_from_xml_node(deviation)
