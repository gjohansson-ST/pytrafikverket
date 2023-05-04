"""Retrieve weather station data from Trafikverket API."""
from __future__ import annotations

from typing import Any
from datetime import datetime

import aiohttp
from pytrafikverket.trafikverket import (
    FieldFilter,
    FilterOperation,
    NodeHelper,
    Trafikverket,
)

from .exceptions import NoWeatherStationFound, MultipleWeatherStationsFound

WIND_DIRECTION_TRANSLATION = {
    "Öst": "east",
    "Nordöst": "north_east",
    "Östsydöst": "east_south_east",
    "Norr": "north",
    "Nordnordöst": "north_north_east",
    "Nordnordväst": "north_north_west",
    "Nordväst": "north_west",
    "Söder": "south",
    "Sydöst": "south_east",
    "Sydsydväst": "south_south_west",
    "Sydväst": "south_west",
    "Väst": "west",
}
PRECIPITATION_AMOUNTNAME_TRANSLATION = {
    "Givare saknas/Fel på givare": "error",
    "Lätt regn": "mild_rain",
    "Måttligt regn": "moderate_rain",
    "Kraftigt regn": "heavy_rain",
    "Lätt snöblandat regn": "mild_snow_rain",
    "Måttligt snöblandat regn": "moderate_snow_rain",
    "Kraftigt snöblandat regn": "heavy_snow_rain",
    "Lätt snöfall": "mild_snow",
    "Måttligt snöfall": "moderate_snow",
    "Kraftigt snöfall": "heavy_snow",
    "Annan nederbördstyp": "other",
    "Ingen nederbörd": "none",
    "Okänd nederbördstyp": "error",
}
PRECIPITATION_TYPE_TRANSLATION = {
    "Duggregn": "drizzle",
    "Hagel": "hail",
    "Ingen nederbörd": "none",
    "Regn": "rain",
    "Snö": "snow",
    "Snöblandat regn": "rain_snow_mixed",
    "Underkylt regn": "freezing_rain",
}


class WeatherStationInfo:
    """Fetch Weather data from specified weather station."""

    _required_fields = [
        "Name",
        "Id",
        "Measurement.Road.Temp",
        "Measurement.Air.Temp",
        "Measurement.Air.RelativeHumidity",
        "Measurement.Precipitation.Type",
        "Measurement.Wind.Direction",
        "Measurement.Wind.DirectionText",
        "Measurement.Wind.Force",
        "Measurement.Wind.ForceMax",
        "Active",
        "Measurement.MeasureTime",
        "Measurement.Precipitation.Amount",
        "Measurement.Precipitation.AmountName",
    ]

    def __init__(
        self,
        station_name: str | None,
        station_id: str | None,
        road_temp: float | None,
        air_temp: float | None,
        humidity: float | None,
        precipitationtype: str | None,
        precipitationtype_translated: str | None,
        winddirection: str | None,
        winddirectiontext: str | None,
        winddirectiontext_translated: str | None,
        windforce: float | None,
        windforcemax: float | None,
        active: bool,
        measure_time: datetime | None,
        precipitation_amount: float | None,
        precipitation_amountname: str | None,
        precipitation_amountname_translated: str | None,
        modified_time: datetime | None,
    ) -> None:
        """Initialize the class."""
        self.station_name = station_name
        self.station_id = station_id
        self.road_temp = road_temp
        self.air_temp = air_temp
        self.humidity = humidity
        self.precipitationtype = precipitationtype
        self.precipitationtype_translated = precipitationtype_translated
        self.winddirection = winddirection
        self.winddirectiontext = winddirectiontext
        self.winddirectiontext_translated = winddirectiontext_translated
        self.windforce = windforce
        self.windforcemax = windforcemax
        self.active = active
        self.measure_time = measure_time
        self.precipitation_amount = precipitation_amount
        self.precipitation_amountname = precipitation_amountname
        self.precipitation_amountname_translated = precipitation_amountname_translated
        self.modified_time = modified_time

    @classmethod
    def from_xml_node(cls, node: Any) -> WeatherStationInfo:
        """Map XML path for values."""
        node_helper = NodeHelper(node)
        station_name = node_helper.get_text("Name")
        station_id = node_helper.get_text("Id")
        air_temp = node_helper.get_number("Measurement/Air/Temp")
        road_temp = node_helper.get_number("Measurement/Road/Temp")
        humidity = node_helper.get_number("Measurement/Air/RelativeHumidity")
        precipitationtype_translated = None
        if precipitationtype := node_helper.get_text("Measurement/Precipitation/Type"):
            precipitationtype_translated = PRECIPITATION_TYPE_TRANSLATION.get(
                precipitationtype
            )
        winddirection = node_helper.get_text("Measurement/Wind/Direction")
        winddirectiontext_translated = None
        if winddirectiontext := node_helper.get_text("Measurement/Wind/DirectionText"):
            winddirectiontext_translated = WIND_DIRECTION_TRANSLATION.get(
                winddirectiontext
            )
        windforce = node_helper.get_number("Measurement/Wind/Force")
        windforcemax = node_helper.get_number("Measurement/Wind/ForceMax")
        active = node_helper.get_bool("Active")
        measure_time = node_helper.get_datetime("Measurement/MeasureTime")
        precipitation_amount = node_helper.get_number(
            "Measurement/Precipitation/Amount"
        )
        precipitation_amountname_translated = None
        if precipitation_amountname := node_helper.get_text(
            "Measurement/Precipitation/AmountName"
        ):
            precipitation_amountname_translated = (
                PRECIPITATION_AMOUNTNAME_TRANSLATION.get(precipitation_amountname)
            )
        modified_time = node_helper.get_datetime_for_modified("ModifiedTime")
        return cls(
            station_name,
            station_id,
            road_temp,
            air_temp,
            humidity,
            precipitationtype,
            precipitationtype_translated,
            winddirection,
            winddirectiontext,
            winddirectiontext_translated,
            windforce,
            windforcemax,
            active,
            measure_time,
            precipitation_amount,
            precipitation_amountname,
            precipitation_amountname_translated,
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
            "WeatherStation",
            "1.0",
            WeatherStationInfo._required_fields,  # pylint: disable=protected-access
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
