"""Helpers for creating dataclasses."""

import datetime
from typing import TYPE_CHECKING

import aiozoneinfo
from lxml import etree

from .models import WeatherStationInfoModel
from .trafikverket import NodeHelper

SWEDEN_TIMEZONE = "Europe/Stockholm"


async def weather_from_xml_node(node: etree._ElementTree) -> WeatherStationInfoModel:
    """Map XML path for values."""
    node_helper = NodeHelper(node)
    station_name = node_helper.get_text("Name")
    station_id = node_helper.get_text("Id")
    air_temp = node_helper.get_number("Observation/Air/Temperature/Value")
    road_temp = node_helper.get_number("Observation/Surface/Temperature/Value")
    dew_point = node_helper.get_number("Observation/Air/Dewpoint/Value")
    humidity = node_helper.get_number("Observation/Air/RelativeHumidity/Value")
    visible_distance = node_helper.get_number("Observation/Air/VisibleDistance/Value")
    precipitationtype = node_helper.get_text("Observation/Weather/Precipitation")
    raining = node_helper.get_bool("Observation/Aggregated30minutes/Precipitation/Rain")
    snowing = node_helper.get_bool("Observation/Aggregated30minutes/Precipitation/Snow")
    road_ice = node_helper.get_bool("Observation/Surface/Ice")
    road_ice_depth = node_helper.get_number("Observation/Surface/IceDepth/Value")
    road_snow = node_helper.get_bool("Observation/Surface/Snow")
    road_snow_depth = node_helper.get_number(
        "Observation/Surface/SnowDepth.Solid/Value"
    )
    road_water = node_helper.get_bool("Observation/Surface/Water")
    road_water_depth = node_helper.get_number("Observation/Surface/WaterDepth/Value")
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

    zoneinfo = await aiozoneinfo.async_get_time_zone(SWEDEN_TIMEZONE)
    if measure_time:
        measure_time = measure_time.replace(tzinfo=zoneinfo)
    if modified_time:
        modified_time = modified_time.replace(tzinfo=datetime.UTC)

    if TYPE_CHECKING:
        assert station_name
        assert station_id

    return WeatherStationInfoModel(
        station_name=station_name,
        station_id=station_id,
        road_temp=road_temp,
        air_temp=air_temp,
        dew_point=dew_point,
        humidity=humidity,
        visible_distance=visible_distance,
        precipitationtype=precipitationtype,
        raining=raining,
        snowing=snowing,
        road_ice=road_ice,
        road_ice_depth=road_ice_depth,
        road_snow=road_snow,
        road_snow_depth=road_snow_depth,
        road_water=road_water,
        road_water_depth=road_water_depth,
        road_water_equivalent_depth=road_water_equivalent_depth,
        winddirection=winddirection,
        wind_height=wind_height,
        windforce=windforce,
        windforcemax=windforcemax,
        measure_time=measure_time,
        precipitation_amount=precipitation_amount,
        modified_time=modified_time,
    )
