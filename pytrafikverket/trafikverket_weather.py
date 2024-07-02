"""Retrieve weather station data from Trafikverket API."""

from __future__ import annotations

<<<<<<< HEAD
from datetime import datetime

from lxml import etree

from .exceptions import MultipleWeatherStationsFound, NoWeatherStationFound
from .trafikverket import (
    FieldFilter,
    FilterOperation,
    NodeHelper,
    TrafikverketBase,
)
=======
import aiohttp

from pytrafikverket.helpers import weather_from_xml_node
from pytrafikverket.models import WeatherStationInfoModel

from .exceptions import MultipleWeatherStationsFound, NoWeatherStationFound
from .trafikverket import FieldFilter, FilterOperation, Trafikverket
>>>>>>> 6d88309 (Move weather to dataclass)

WEATHER_REQUIRED_FIELDS = [
    "Name",  # string, replaced
    "Id",  # string, replaced
    "ModifiedTime",  # datetime, new, Tidpunkt då dataposten ändrades i cachen
    "Observation.Sample",  # datetime, replaced, Tidpunkt som observationen avser, inklusive tidzon för att hantera sommartid och normaltid. # codespell:ignore
    "Observation.Air.Temperature.Value",  # float, replaced, Lufttemperatur. Value [C]
    "Observation.Air.RelativeHumidity.Value",  # float, replaced, Relativ luftfuktighet. Andel av den fukt som luften kan bära. Vid 100% är luften mättad. Value [%] # codespell:ignore
    "Observation.Air.Dewpoint.Value",  # float, new, Daggpunkt, den temperatur där vatten kondenserar. Value [C] # codespell:ignore
    "Observation.Air.VisibleDistance.Value",  # float, new, Den sträcka det finns sikt. Value [m]
    "Observation.Wind.Direction.Value",  # int, replaced, Mått på vindriktning vid en viss tidpunkt. Medelvärde över tiominutersperiod t.o.m. tidpunkten. Value [grader]
    "Observation.Wind.Height",  # int, new, Vindsensorns höjdplacering [m]
    "Observation.Wind.Speed.Value",  # float, replaced, Mått på vindhastighet vid en viss tidpunkt. Medelvärde över tiominutersperiod t.o.m. tidpunkten. Value [m/s]
    "Observation.Aggregated30minutes.Wind.SpeedMax.Value",  # float, replaced, Högst uppmätt 3-sekundersmedelvärde under perioden. Value [m/s]
    "Observation.Weather.Precipitation",  # string, replaced, Vilken typ av nederbörd som detekterats # codespell:ignore
    "Observation.Aggregated30minutes.Precipitation.TotalWaterEquivalent.Value",  # float, replaced, Mängd vatten som nederbörden under perioden motsvarar. Value [mm] # codespell:ignore
    "Observation.Aggregated30minutes.Precipitation.Rain",  # bool, new, Förekomst av regn.
    "Observation.Aggregated30minutes.Precipitation.Snow",  # bool, new, Förekomst av snö.
    "Observation.Surface.Temperature.Value",  # float, replaced, Vägytans temperatur. Value [C] # codespell:ignore
    "Observation.Surface.Ice",  # bool, new, Förekomst av is på vägytan.
    "Observation.Surface.IceDepth.Value",  # float, new, Isdjup på vägytan. Value [mm]
    "Observation.Surface.Snow",  # bool, new, Förekomst av snö på vägytan.
    "Observation.Surface.SnowDepth.Solid.Value",  # float, new, Mängd snö. Value [mm]
    "Observation.Surface.SnowDepth.WaterEquivalent.Value",  # float, new, Mängd vatten som snön motsvarar i smält form. Value [mm] # codespell:ignore
    "Observation.Surface.Water",  # bool, new, Förekomst av vatten på vägytan.
    "Observation.Surface.WaterDepth.Value",  # float, new, Vattendjup på vägytan. Value [mm]
]

# Precipitation possible values are: no, rain, freezing_rain, snow, sleet, yes

class TrafikverketWeather(TrafikverketBase):
    """Class used to communicate with trafikverket's weather api."""

    async def async_get_weather(self, location_name: str) -> WeatherStationInfoModel:

        """Retrieve weather from API."""
        weather_stations = await self._api.async_make_request(
            "WeatherMeasurepoint",
            "2.0",
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
