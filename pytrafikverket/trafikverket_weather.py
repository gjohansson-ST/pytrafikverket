import asyncio
import aiohttp
from pytrafikverket.trafikverket import Trafikverket, FieldFilter, \
                                        FilterOperation, NodeHelper

class WeatherStationInfo(object):
    """Fetch Weather data from specified weather station"""

    required_fields = ["Name", "Id", "Measurement.Road.Temp", "Measurement.Air.Temp", 
                       "Measurement.Air.RelativeHumidity", "Measurement.Precipitation.Type", 
                       "Measurement.Wind.Direction", "Measurement.Wind.DirectionText", "Measurement.Wind.Force" ]

    def __init__(self, station_name: str, station_id: str, road_temp: float, air_temp: float, 
                 humidity: float, precipitationtype: str, winddirection: float, 
                 winddirectiontext: str, windforce: float):
        self.station_name = station_name
        self.station_id = station_id
        self.road_temp = road_temp
        self.air_temp = air_temp
        self.humidity = humidity
        self.precipitationtype = precipitationtype
        self.winddirection = winddirection
        self.winddirectiontext = winddirectiontext
        self.windforce = windforce

    @classmethod
    def from_xml_node(cls, node):
        node_helper = NodeHelper(node)
        station_name = node_helper.get_text("Name")
        station_id = node_helper.get_text("Id")
        road_temp = node_helper.get_text("Measurement/Air/Temp")
        air_temp = node_helper.get_text("Measurement/Road/Temp")
        humidity = node_helper.get_text("Measurement/Air/RelativeHumidity")
        precipitationtype = node_helper.get_text("Measurement/Precipitation/Type")
        winddirection = node_helper.get_text("Measurement/Wind/Direction")
        winddirectiontext = node_helper.get_text("Measurement/Wind/DirectionText")
        windforce = node_helper.get_text("Measurement/Wind/Force")
        return cls(station_name, station_id, road_temp, air_temp, humidity, 
                   precipitationtype, winddirection, winddirectiontext, windforce)


class TrafikverketWeather(object):
    """class used to communicate with trafikverket's weather api"""

    def __init__(self, client_session:aiohttp.ClientSession, api_key:str):
        """Initialize Weather object"""
        self._api = Trafikverket(client_session, api_key)
    
    async def async_get_weather(self, location_name: str) -> WeatherStationInfo:
        weather_stations = await self._api.async_make_request("WeatherStation",
                                                      WeatherStationInfo.required_fields,
                                                      [FieldFilter(FilterOperation.equal,
                                                                   "Name",
                                                                   location_name)])
        if len(weather_stations) == 0:
            raise ValueError("Could not find a weather station with the specified name")
        if len(weather_stations) > 1:
            raise ValueError("Found multiple weather stations with the specified name")

        return WeatherStationInfo.from_xml_node(weather_stations[0])