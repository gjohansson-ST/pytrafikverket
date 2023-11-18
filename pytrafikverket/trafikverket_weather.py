"""Retrieve weather station data from Trafikverket API."""
from __future__ import annotations

from datetime import datetime

import aiohttp
from lxml import etree

from .exceptions import MultipleWeatherStationsFound, NoWeatherStationFound
from .trafikverket import FieldFilter, FilterOperation, NodeHelper, Trafikverket

WEATHER_REQUIRED_FIELDS = [
    "Name",  # string, replaced
    "Id",  # string, replaced
    "ModifiedTime",  # datetime, new, Tidpunkt då dataposten ändrades i cachen
    "Observation.Sample",  # datetime, replaced, Tidpunkt som observationen avser, inklusive tidzon för att hantera sommartid och normaltid.
    "Observation.Air.Temperature.Value",  # float, replaced, Lufttemperatur. Value [C]
    "Observation.Air.RelativeHumidity.Value",  # float, replaced, Relativ luftfuktighet. Andel av den fukt som luften kan bära. Vid 100% är luften mättad. Value [%]
    "Observation.Air.Dewpoint.Value",  # float, new, Daggpunkt, den temperatur där vatten kondenserar. Value [C]
    "Observation.Air.VisibleDistance.Value",  # float, new, Den sträcka det finns sikt. Value [m]
    "Observation.Wind.Direction.Value",  # int, replaced, Mått på vindriktning vid en viss tidpunkt. Medelvärde över tiominutersperiod t.o.m. tidpunkten. Value [grader]
    "Observation.Wind.Height",  # int, new, Vindsensorns höjdplacering [m]
    "Observation.Wind.Speed.Value",  # float, replaced, Mått på vindhastighet vid en viss tidpunkt. Medelvärde över tiominutersperiod t.o.m. tidpunkten. Value [m/s]
    "Observation.Aggregated30minutes.Wind.SpeedMax.Value",  # float, replaced, Högst uppmätt 3-sekundersmedelvärde under perioden. Value [m/s]
    "Observation.Weather.Precipitation",  # string, replaced, Vilken typ av nederbörd som detekterats
    "Observation.Aggregated30minutes.Precipitation.TotalWaterEquivalent.Value",  # float, replaced, Mängd vatten som nederbörden under perioden motsvarar. Value [mm]
    "Observation.Aggregated30minutes.Precipitation.Rain",  # bool, new, Förekomst av regn.
    "Observation.Aggregated30minutes.Precipitation.Snow",  # bool, new, Förekomst av snö.
    "Observation.Surface.Temperature.Value",  # float, replaced, Vägytans temperatur. Value [C]
    "Observation.Surface.Ice",  # bool, new, Förekomst av is på vägytan.
    "Observation.Surface.IceDepth.Value",  # float, new, Isdjup på vägytan. Value [mm]
    "Observation.Surface.Snow",  # bool, new, Förekomst av snö på vägytan.
    "Observation.Surface.SnowDepth.Solid.Value",  # float, new, Mängd snö. Value [mm]
    "Observation.Surface.SnowDepth.WaterEquivalent.Value",  # float, new, Mängd vatten som snön motsvarar i smält form. Value [mm]
    "Observation.Surface.Water",  # bool, new, Förekomst av vatten på vägytan.
    "Observation.Surface.WaterDepth.Value",  # float, new, Vattendjup på vägytan. Value [mm]
]
"""
Precipitation possible values are:
  no
  rain
  freezing_rain
  snow
  sleet
  yes
"""


class WeatherStationInfo:  # pylint: disable=R0902
    """Fetch Weather data from specified weather station."""

    def __init__(  # pylint: disable=R0914, R0913
        self,
        station_name: str,
        station_id: str,
        road_temp: float | None,  # celsius
        air_temp: float | None,  # celsius
        dew_point: float | None,  # celsius
        humidity: float | None,  # %
        visible_distance: float | None,  # meter
        precipitationtype: str | None,
        raining: bool,
        snowing: bool,
        road_ice: bool,
        road_ice_depth: float | None,  # mm
        road_snow: bool,
        road_snow_depth: float | None,  # mm
        road_water: bool,
        road_water_depth: float | None,  # mm
        road_water_equivalent_depth: float | None,  # mm
        winddirection: str | None,  # degrees
        wind_height: int | None,  # m
        windforce: float | None,  # m/s
        windforcemax: float | None,  # m/s
        measure_time: datetime | None,
        precipitation_amount: float | None,  # mm/30min translated to mm/h
        modified_time: datetime | None,
    ) -> None:
        """Initialize the class."""
        self.station_name = station_name
        self.station_id = station_id
        self.road_temp = road_temp
        self.air_temp = air_temp
        self.dew_point = dew_point
        self.humidity = humidity
        self.visible_distance = visible_distance
        self.precipitationtype = precipitationtype
        self.raining = raining
        self.snowing = snowing
        self.road_ice = road_ice
        self.road_ice_depth = road_ice_depth
        self.road_snow = road_snow
        self.road_snow_depth = road_snow_depth
        self.road_water = road_water
        self.road_water_depth = road_water_depth
        self.road_water_equivalent_depth = road_water_equivalent_depth
        self.winddirection = winddirection
        self.wind_height = wind_height
        self.windforce = windforce
        self.windforcemax = windforcemax
        self.measure_time = measure_time
        self.precipitation_amount = precipitation_amount
        self.modified_time = modified_time

    @classmethod
    def from_xml_node(
        cls, node: etree._ElementTree
    ) -> WeatherStationInfo:  # pylint: disable=R0914
        """Map XML path for values."""
        node_helper = NodeHelper(node)
        station_name = node_helper.get_text("Name")
        station_id = node_helper.get_text("Id")
        air_temp = node_helper.get_number("Observation/Air/Temperature/Value")
        road_temp = node_helper.get_number("Observation/Surface/Temperature/Value")
        dew_point = node_helper.get_number("Observation/Air/Dewpoint/Value")
        humidity = node_helper.get_number("Observation/Air/RelativeHumidity/Value")
        visible_distance = node_helper.get_number(
            "Observation/Air/VisibleDistance/Value"
        )
        precipitationtype = node_helper.get_text("Observation/Weather/Precipitation")
        raining = node_helper.get_bool(
            "Observation/Aggregated30minutes/Precipitation/Rain"
        )
        snowing = node_helper.get_bool(
            "Observation/Aggregated30minutes/Precipitation/Snow"
        )
        road_ice = node_helper.get_bool("Observation/Surface/Ice")
        road_ice_depth = node_helper.get_number("Observation/Surface/IceDepth/Value")
        road_snow = node_helper.get_bool("Observation/Surface/Snow")
        road_snow_depth = node_helper.get_number(
            "Observation/Surface/SnowDepth.Solid/Value"
        )
        road_water = node_helper.get_bool("Observation/Surface/Water")
        road_water_depth = node_helper.get_number(
            "Observation/Surface/WaterDepth/Value"
        )
        road_water_equivalent_depth = node_helper.get_number(
            "Observation/Surface/SnowDepth/WaterEquivalent/Value"
        )
        winddirection = node_helper.get_text("Observation/Wind/Direction/Value")
        wind_height = node_helper.get_number("Observation/Wind/Height")
        windforce = node_helper.get_number("Observation/Wind/Speed/Value")
        windforcemax = node_helper.get_number(
            "Observation/Aggregated30minutes/Wind/SpeedMax/Value"
        )
        measure_time = node_helper.get_datetime("Observation/Sample")
        precipitation_amount = node_helper.get_number(
            "Observation/Aggregated30minutes/Precipitation/TotalWaterEquivalent/Value"
        )
        if precipitation_amount:
            precipitation_amount = precipitation_amount * 2  # mm/30min to mm/h
        modified_time = node_helper.get_datetime_for_modified("ModifiedTime")
        return cls(
            station_name,
            station_id,
            road_temp,
            air_temp,
            dew_point,
            humidity,
            visible_distance,
            precipitationtype,
            raining,
            snowing,
            road_ice,
            road_ice_depth,
            road_snow,
            road_snow_depth,
            road_water,
            road_water_depth,
            road_water_equivalent_depth,
            winddirection,
            wind_height,
            windforce,
            windforcemax,
            measure_time,
            precipitation_amount,
            modified_time,
        )


class TrafikverketWeather:
    """Class used to communicate with trafikverket's weather api."""

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize Weather object."""
        self._api = Trafikverket(client_session, api_key)

    async def async_get_weather(self, location_name: str) -> WeatherStationInfo:
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

        return WeatherStationInfo.from_xml_node(weather_stations[0])
