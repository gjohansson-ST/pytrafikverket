"""Helpers for creating dataclasses."""

import datetime
from typing import TYPE_CHECKING

import aiozoneinfo
from lxml import etree

from .models import (
    CameraInfoModel,
    DeviationInfoModel,
    FerryRouteInfoModel,
    FerryStopModel,
    WeatherStationInfoModel,
)
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


async def camera_from_xml_node(node: etree._ElementTree) -> CameraInfoModel:
    """Map XML path for values."""
    node_helper = NodeHelper(node)
    camera_name = node_helper.get_text("Name")
    camera_id = node_helper.get_text("Id")
    active = node_helper.get_bool("Active")
    deleted = node_helper.get_bool("Deleted")
    description = node_helper.get_text("Description")
    direction = node_helper.get_text("Direction")
    fullsizephoto = node_helper.get_bool("HasFullSizePhoto")
    location = node_helper.get_text("Location")
    modified = node_helper.get_datetime_for_modified("ModifiedTime")
    phototime = node_helper.get_datetime("PhotoTime")
    photourl = node_helper.get_text("PhotoUrl")
    status = node_helper.get_text("Status")
    camera_type = node_helper.get_text("Type")

    zoneinfo = await aiozoneinfo.async_get_time_zone(SWEDEN_TIMEZONE)
    if phototime:
        phototime = phototime.replace(tzinfo=zoneinfo)
    if modified:
        modified = modified.replace(tzinfo=datetime.UTC)

    if TYPE_CHECKING:
        assert camera_name
        assert camera_id

    return CameraInfoModel(
        camera_name=camera_name,
        camera_id=camera_id,
        active=active,
        deleted=deleted,
        description=description,
        direction=direction,
        fullsizephoto=fullsizephoto,
        location=location,
        modified=modified,
        phototime=phototime,
        photourl=photourl,
        status=status,
        camera_type=camera_type,
    )


def ferry_stop_from_xml_node(node: etree._ElementTree) -> FerryStopModel:
    """Map the path in the return XML data."""
    node_helper = NodeHelper(node)
    id = node_helper.get_text("Id")
    name = node_helper.get_text("Route/Name")
    short_name = node_helper.get_text("Route/Shortname")
    deleted = node_helper.get_bool("Deleted")
    departure_time = node_helper.get_datetime("DepartureTime")
    other_information = node_helper.get_texts("Info")
    deviation_id = node_helper.get_texts("DeviationId")
    modified_time = node_helper.get_datetime_for_modified("ModifiedTime")
    from_harbor_name = node_helper.get_text("FromHarbor/Name")
    to_harbor_name = node_helper.get_text("ToHarbor/Name")
    type_name = node_helper.get_text("Route/Type/Name")

    if TYPE_CHECKING:
        assert id
        assert name

    return FerryStopModel(
        ferry_stop_id=id,
        ferry_stop_name=name,
        short_name=short_name,
        deleted=deleted,
        departure_time=departure_time,
        other_information=other_information,
        deviation_id=deviation_id,
        modified_time=modified_time,
        from_harbor_name=from_harbor_name,
        to_harbor_name=to_harbor_name,
        type_name=type_name,
    )


def deviation_from_xml_node(node: etree._ElementTree) -> DeviationInfoModel:
    """Map deviation information in XML data."""
    node_helper = NodeHelper(node)
    id = node_helper.get_text("Deviation/Id")
    header = node_helper.get_text("Deviation/Header")
    message = node_helper.get_text("Deviation/Message")
    start_time = node_helper.get_datetime("Deviation/StartTime")
    end_time = node_helper.get_datetime("Deviation/EndTime")
    icon_id = node_helper.get_text("Deviation/IconId")
    location_desc = node_helper.get_text("Deviation/LocationDescriptor")

    if TYPE_CHECKING:
        assert id

    return DeviationInfoModel(
        deviation_id=id,
        header=header,
        message=message,
        start_time=start_time,
        end_time=end_time,
        icon_id=icon_id,
        location_desc=location_desc,
    )


def ferry_route_from_xml_node(node: etree._ElementTree) -> FerryRouteInfoModel:
    """Map route information in XML data."""
    node_helper = NodeHelper(node)
    id = node_helper.get_text("Id")
    name = node_helper.get_text("Name")
    short_name = node_helper.get_text("Shortname")
    route_type = node_helper.get_text("Type/Name")

    if TYPE_CHECKING:
        assert id
        assert name

    return FerryRouteInfoModel(
        ferry_route_id=id,
        ferry_route_name=name,
        short_name=short_name,
        route_type=route_type,
    )
