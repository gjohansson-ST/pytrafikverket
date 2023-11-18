"""Data classes for Trafikverket."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class CameraInfoModel:  # pylint: disable=R0902
    """Dataclass for Trafikverket Camera."""

    camera_name: str | None
    camera_id: str | None
    active: bool
    deleted: bool
    description: str | None
    direction: str | None
    fullsizephoto: bool
    location: str | None
    modified: datetime | None
    phototime: datetime | None
    photourl: str | None
    status: str | None
    camera_type: str | None


@dataclass
class FerryRouteInfoModel:  # pylint: disable=R0902
    """Dataclass for Trafikverket Ferry route info."""

    ferry_route_id: str | None
    name: str | None
    short_name: str | None
    route_type: str | None


@dataclass
class DeviationInfoModel:  # pylint: disable=R0902
    """Dataclass for Trafikverket Ferry deviations."""

    deviation_id: str | None
    header: str | None
    message: str | None
    start_time: datetime | None
    end_time: datetime | None
    icon_id: str | None
    location_desc: str | None


@dataclass
class FerryStopModel:  # pylint: disable=R0902
    """Dataclass for Trafikverket Ferry stop."""

    ferry_stop_id: str | None
    deleted: bool
    departure_time: datetime | None
    other_information: list[str] | None
    deviation_id: list[str] | None
    modified_time: datetime | None
    from_harbor_name: str | None
    to_harbor_name: str | None


@dataclass
class StationInfoModel:  # pylint: disable=R0902
    """Dataclass for Trafikverket Train Station info."""

    signature: str | None
    name: str | None
    advertised: str | None


@dataclass
class TrainStopModel:  # pylint: disable=R0902
    """Dataclass for Trafikverket Train stop."""

    train_stop_id: str | None
    canceled: bool
    advertised_time_at_location: datetime | None
    estimated_time_at_location: datetime | None
    time_at_location: datetime | None
    other_information: list[str] | None
    deviations: list[str] | None
    modified_time: datetime | None
    product_description: list[str] | None


@dataclass
class WeatherStationInfoModel:  # pylint: disable=R0902
    """Dataclass for Trafikverket Weather info."""

    weather_station_id: str
    station_name: str
    road_temp: float | None  # celsius
    air_temp: float | None  # celsius
    dew_point: float | None  # celsius
    humidity: float | None  # %
    visible_distance: float | None  # meter
    precipitationtype: str | None
    raining: bool
    snowing: bool
    road_ice: bool
    road_ice_depth: float | None  # mm
    road_snow: bool
    road_snow_depth: float | None  # mm
    road_water: bool
    road_water_depth: float | None  # mm
    road_water_equivalent_depth: float | None  # mm
    winddirection: str | None  # degrees
    wind_height: int | None  # m
    windforce: float | None  # m/s
    windforcemax: float | None  # m/s
    measure_time: datetime | None
    precipitation_amount: float | None  # mm/30min translated to mm/h
    modified_time: datetime | None
