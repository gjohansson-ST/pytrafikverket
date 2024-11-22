"""Retrieve weather station data from Trafikverket API."""

from __future__ import annotations

from .const import WEATHER_REQUIRED_FIELDS
from .exceptions import MultipleWeatherStationsFound, NoWeatherStationFound
from .filters import FieldFilter, FilterOperation
from .helpers import weather_from_xml_node
from .models import WeatherStationInfoModel
from .trafikverket import TrafikverketBase


class TrafikverketWeather(TrafikverketBase):
    """Class used to communicate with trafikverket's weather api."""

    version = "2.1"

    async def async_get_weather(self, location_name: str) -> WeatherStationInfoModel:
        """Retrieve weather from API."""
        weather_stations = await self._api.async_make_request(
            "WeatherMeasurepoint",
            self.version,
            None,
            WEATHER_REQUIRED_FIELDS,
            [FieldFilter(FilterOperation.EQUAL, "Name", location_name)],
        )
        if len(weather_stations) == 0:
            raise NoWeatherStationFound(
                "Could not find a weather station with the specified name"
            )
        if len(weather_stations) > 1:
            raise MultipleWeatherStationsFound(
                "Found multiple weather stations with the specified name"
            )

        return await weather_from_xml_node(weather_stations[0])

    async def async_search_weather_stations(
        self, location_name: str
    ) -> list[WeatherStationInfoModel]:
        """Retrieve weather from API."""
        weather_stations = await self._api.async_make_request(
            "WeatherMeasurepoint",
            self.version,
            None,
            ["Name" "Id"],
            [
                FieldFilter(FilterOperation.LIKE, "Name", location_name),
                FieldFilter(FilterOperation.EQUAL, "Deleted", False),
            ],
        )
        if len(weather_stations) == 0:
            raise NoWeatherStationFound(
                "Could not find a weather station with the specified name"
            )

        result = []
        for weather_station in weather_stations:
            result.append(await weather_from_xml_node(weather_station))
        return result
