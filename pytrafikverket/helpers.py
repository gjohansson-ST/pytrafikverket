"""Helpers for creating dataclasses."""

from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

import aiozoneinfo
from lxml import etree

from .const import DATE_TIME_FORMAT, DATE_TIME_FORMAT_FOR_MODIFIED, SWEDEN_TIMEZONE
from .models import (
    CameraInfoModel,
    DeviationInfoModel,
    FerryRouteInfoModel,
    FerryStopModel,
    StationInfoModel,
    TrainStopModel,
    WeatherStationInfoModel,
)

LOGGER = logging.getLogger(__name__)


class NodeHelper:
    """Helper class to get node content."""

    def __init__(self, node: etree._ElementTree) -> None:
        """Initialize the class."""
        self._node = node

    def get_text(self, field: str) -> str | None:
        """Return the text in 'field' from the node or None if not found."""
        nodes: list[etree._Element] | None = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        LOGGER.debug("Return text value %s", nodes[0].text)
        value: str | None = nodes[0].text
        return value

    def get_number(self, field: str) -> float | None:
        """Return the number in 'field' from the node or None if not found."""
        nodes: list[etree._Element] | None = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        LOGGER.debug("Return number value %s", nodes[0].text)
        if TYPE_CHECKING:
            assert nodes[0].text is not None
        try:
            value = float(nodes[0].text)
        except ValueError:
            return None
        return value

    def get_texts(self, field: str) -> list[str] | None:
        """Return a list of texts from the node selected by 'field' or None."""
        nodes: list[etree._Element] | None = self._node.xpath(field)
        if nodes is None:
            return None
        result: list[str] = []
        for line in nodes:
            if TYPE_CHECKING:
                assert line.text is not None
            result.append(line.text)
        LOGGER.debug("Return texts value %s", result)
        return result

    def get_datetime_for_modified(self, field: str) -> datetime.datetime | None:
        """Return datetime object from node, selected by 'field'.

        Format of the text is expected to be modifiedTime-format.
        """
        nodes: list[etree._Element] | None = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        LOGGER.debug("Return modified value %s", nodes[0].text)
        if TYPE_CHECKING:
            assert nodes[0].text is not None
        return datetime.datetime.strptime(nodes[0].text, DATE_TIME_FORMAT_FOR_MODIFIED)

    def get_datetime(self, field: str) -> datetime.datetime | None:
        """Return a datetime object from node, selected by 'field'."""
        nodes: list[etree._Element] | None = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        LOGGER.debug("Return datetime value %s", nodes[0].text)
        if TYPE_CHECKING:
            assert nodes[0].text is not None
        return datetime.datetime.strptime(nodes[0].text, DATE_TIME_FORMAT)

    def get_bool(self, field: str) -> bool | None:
        """Return True if value selected by field is 'true' else returns False."""
        nodes: list[etree._Element] | None = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        LOGGER.debug("Return bool value %s", nodes[0].text)
        if TYPE_CHECKING:
            assert nodes[0].text is not None
        value: bool = nodes[0].text.lower() == "true"
        return value


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


async def ferry_stop_from_xml_node(node: etree._ElementTree) -> FerryStopModel:
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

    zoneinfo = await aiozoneinfo.async_get_time_zone(SWEDEN_TIMEZONE)
    if departure_time:
        departure_time = departure_time.replace(tzinfo=zoneinfo)
    if modified_time:
        modified_time = modified_time.replace(tzinfo=datetime.UTC)

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


async def deviation_from_xml_node(node: etree._ElementTree) -> DeviationInfoModel:
    """Map deviation information in XML data."""
    node_helper = NodeHelper(node)
    id = node_helper.get_text("Deviation/Id")
    header = node_helper.get_text("Deviation/Header")
    message = node_helper.get_text("Deviation/Message")
    start_time = node_helper.get_datetime("Deviation/StartTime")
    end_time = node_helper.get_datetime("Deviation/EndTime")
    icon_id = node_helper.get_text("Deviation/IconId")
    location_desc = node_helper.get_text("Deviation/LocationDescriptor")

    zoneinfo = await aiozoneinfo.async_get_time_zone(SWEDEN_TIMEZONE)
    if start_time:
        start_time = start_time.replace(tzinfo=zoneinfo)
    if end_time:
        end_time = end_time.replace(tzinfo=zoneinfo)

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


async def ferry_route_from_xml_node(node: etree._ElementTree) -> FerryRouteInfoModel:
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


async def station_from_xml_node(node: etree._ElementTree) -> StationInfoModel:
    """Map station information in XML data."""
    node_helper = NodeHelper(node)
    location_signature = node_helper.get_text("LocationSignature")
    advertised_location_name = node_helper.get_text("AdvertisedLocationName")
    location_advertised = node_helper.get_text("Advertised")

    if TYPE_CHECKING:
        assert location_signature
        assert advertised_location_name

    return StationInfoModel(
        signature=location_signature,
        station_name=advertised_location_name,
        advertised=location_advertised,
    )


async def train_stop_from_xml_node(node: etree._ElementTree) -> TrainStopModel:
    """Map the path in the return XML data."""
    node_helper = NodeHelper(node)
    activity_id = node_helper.get_text("ActivityId")
    canceled = node_helper.get_bool("Canceled")
    advertised_time_at_location = node_helper.get_datetime("AdvertisedTimeAtLocation")
    estimated_time_at_location = node_helper.get_datetime("EstimatedTimeAtLocation")
    time_at_location = node_helper.get_datetime("TimeAtLocation")
    other_information = node_helper.get_texts("OtherInformation/Description")
    deviations = node_helper.get_texts("Deviation/Description")
    modified_time = node_helper.get_datetime_for_modified("ModifiedTime")
    product_description = node_helper.get_texts("ProductInformation/Description")

    zoneinfo = await aiozoneinfo.async_get_time_zone(SWEDEN_TIMEZONE)
    if advertised_time_at_location:
        advertised_time_at_location = advertised_time_at_location.replace(
            tzinfo=zoneinfo
        )
    if estimated_time_at_location:
        estimated_time_at_location = estimated_time_at_location.replace(tzinfo=zoneinfo)
    if time_at_location:
        time_at_location = time_at_location.replace(tzinfo=zoneinfo)
    if modified_time:
        modified_time = modified_time.replace(tzinfo=datetime.UTC)

    if TYPE_CHECKING:
        assert activity_id

    return TrainStopModel(
        train_stop_id=activity_id,
        canceled=canceled,
        advertised_time_at_location=advertised_time_at_location,
        estimated_time_at_location=estimated_time_at_location,
        time_at_location=time_at_location,
        other_information=other_information,
        deviations=deviations,
        modified_time=modified_time,
        product_description=product_description,
    )
