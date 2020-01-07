"""Retrieve weather station data from Trafikverket API."""

import aiohttp
from pytrafikverket.trafikverket import (FieldFilter, FilterOperation,
                                         NodeHelper, Trafikverket)


class WeatherStationInfo(object):
    """Fetch Weather data from specified weather station."""

    _required_fields = ["Name",
                        "Id",
                        "Measurement.Road.Temp",
                        "Measurement.Air.Temp",
                        "Measurement.Air.RelativeHumidity",
                        "Measurement.Precipitation.Type",
                        "Measurement.Wind.Direction",
                        "Measurement.Wind.DirectionText",
                        "Measurement.Wind.Force",
                        "Active",
                        "Measurement.MeasureTime",
                        "Measurement.Precipitation.Amount",
                        "Measurement.Precipitation.AmountName"]

    def __init__(self, station_name: str, station_id: str, road_temp: float,
                 air_temp: float, humidity: float, precipitationtype: str,
                 winddirection: float, winddirectiontext: str,
                 windforce: float, active: bool, measure_time: str,
                 precipitation_amount: float, precipitation_amountname: str, ):
        """Initialize the class."""
        self.station_name = station_name
        self.station_id = station_id
        self.road_temp = road_temp
        self.air_temp = air_temp
        self.humidity = humidity
        self.precipitationtype = precipitationtype
        self.winddirection = winddirection
        self.winddirectiontext = winddirectiontext
        self.windforce = windforce
        self.active = active
        self.measure_time = measure_time
        self.precipitation_amount = precipitation_amount
        self.precipitation_amountname = precipitation_amountname

    @classmethod
    def from_xml_node(cls, node):
        """Map XML path for values."""
        node_helper = NodeHelper(node)
        station_name = node_helper.get_text("Name")
        station_id = node_helper.get_text("Id")
        air_temp = node_helper.get_text("Measurement/Air/Temp")
        road_temp = node_helper.get_text("Measurement/Road/Temp")
        humidity = node_helper.get_text("Measurement/Air/RelativeHumidity")
        precipitationtype = node_helper.get_text(
            "Measurement/Precipitation/Type")
        winddirection = node_helper.get_text("Measurement/Wind/Direction")
        winddirectiontext = node_helper.get_text(
            "Measurement/Wind/DirectionText")
        windforce = node_helper.get_text("Measurement/Wind/Force")
        active = node_helper.get_text("Active")
        measure_time = node_helper.get_text("Measurement/MeasureTime")
        precipitation_amount = node_helper.get_text(
            "Measurement/Precipitation/Amount")
        precipitation_amountname = node_helper.get_text(
            "Measurement/Precipitation/AmountName")
        return cls(station_name, station_id, road_temp, air_temp, humidity,
                   precipitationtype, winddirection, winddirectiontext,
                   windforce, active, measure_time, precipitation_amount,
                   precipitation_amountname)


class TrafikverketWeather(object):
    """Class used to communicate with trafikverket's weather api."""

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str):
        """Initialize Weather object."""
        self._api = Trafikverket(client_session, api_key)

    async def async_get_weather(
            self, location_name: str) -> WeatherStationInfo:
        """Retrieve weather from API."""
        weather_stations = await self._api.async_make_request(
            "WeatherStation",
            WeatherStationInfo._required_fields,
            [FieldFilter(FilterOperation.equal, "Name", location_name)])
        if len(weather_stations) == 0:
            raise ValueError(
                "Could not find a weather station with the specified name")
        if len(weather_stations) > 1:
            raise ValueError(
                "Found multiple weather stations with the specified name")

        return WeatherStationInfo.from_xml_node(weather_stations[0])
