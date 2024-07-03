"""Data classes for Trafikverket."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum


@dataclass
class CameraInfoModel:
    """Dataclass for Trafikverket Camera."""

    camera_name: str
    camera_id: str
    active: bool | None
    deleted: bool | None
    description: str | None
    direction: str | None
    fullsizephoto: bool | None
    location: str | None
    modified: datetime | None
    phototime: datetime | None
    photourl: str | None
    status: str | None
    camera_type: str | None


@dataclass
class FerryRouteInfoModel:
    """Dataclass for Trafikverket Ferry route info."""

    ferry_route_id: str
    ferry_route_name: str
    short_name: str | None
    route_type: str | None


@dataclass
class DeviationInfoModel:
    """Dataclass for Trafikverket Ferry deviations."""

    deviation_id: str
    header: str | None
    message: str | None
    start_time: datetime | None
    end_time: datetime | None
    icon_id: str | None
    location_desc: str | None


@dataclass
class FerryStopModel:
    """Dataclass for Trafikverket Ferry stop."""

    ferry_stop_id: str
    ferry_stop_name: str | None
    short_name: str | None
    deleted: bool | None
    departure_time: datetime | None
    other_information: list[str] | None
    deviation_id: list[str] | None
    modified_time: datetime | None
    from_harbor_name: str | None
    to_harbor_name: str | None
    type_name: str | None

    def get_state(self) -> FerryStopStatus:
        """Retrieve the state of the departure."""
        if self.deleted:
            return FerryStopStatus.DELETED
        return FerryStopStatus.ON_TIME


class FerryStopStatus(StrEnum):
    """Contain the different ferry stop statuses."""

    ON_TIME = "on_time"
    CANCELED = "canceled"
    DELETED = "deleted"


@dataclass
class StationInfoModel:
    """Dataclass for Trafikverket Train Station info."""

    signature: str
    station_name: str
    advertised: str | None


class TrainStopStatus(StrEnum):
    """Contain the different train stop statuses."""

    ON_TIME = "on_time"
    DELAYED = "delayed"
    CANCELED = "canceled"


@dataclass
class TrainStopModel:
    """Dataclass for Trafikverket Train stop."""

    train_stop_id: str
    canceled: bool | None
    advertised_time_at_location: datetime | None
    estimated_time_at_location: datetime | None
    time_at_location: datetime | None
    other_information: list[str] | None
    deviations: list[str] | None
    modified_time: datetime | None
    product_description: list[str] | None

    def get_state(self) -> TrainStopStatus:
        """Retrieve the state of the departure."""
        if self.canceled:
            return TrainStopStatus.CANCELED
        if (
            self.advertised_time_at_location is not None
            and self.time_at_location is not None
            and self.advertised_time_at_location != self.time_at_location
        ):
            return TrainStopStatus.DELAYED
        if (
            self.advertised_time_at_location is not None
            and self.estimated_time_at_location is not None
            and self.advertised_time_at_location != self.estimated_time_at_location
        ):
            return TrainStopStatus.DELAYED
        return TrainStopStatus.ON_TIME

    def get_delay_time(self) -> timedelta | None:
        """Calculate the delay of a departure."""
        if self.canceled:
            return None
        if (
            self.advertised_time_at_location is not None
            and self.time_at_location is not None
            and self.advertised_time_at_location != self.time_at_location
        ):
            return self.time_at_location - self.advertised_time_at_location
        if (
            self.advertised_time_at_location is not None
            and self.estimated_time_at_location is not None
            and self.advertised_time_at_location != self.estimated_time_at_location
        ):
            return self.estimated_time_at_location - self.advertised_time_at_location
        return None


@dataclass
class WeatherStationInfoModel:
    """Dataclass for Trafikverket Weather info."""

    station_name: str
    station_id: str
    road_temp: float | None  # celsius
    air_temp: float | None  # celsius
    dew_point: float | None  # celsius
    humidity: float | None  # %
    visible_distance: float | None  # meter
    precipitationtype: str | None
    raining: bool | None
    snowing: bool | None
    road_ice: bool | None
    road_ice_depth: float | None  # mm
    road_snow: bool | None
    road_snow_depth: float | None  # mm
    road_water: bool | None
    road_water_depth: float | None  # mm
    road_water_equivalent_depth: float | None  # mm
    winddirection: str | None  # degrees
    wind_height: float | None  # m
    windforce: float | None  # m/s
    windforcemax: float | None  # m/s
    measure_time: datetime | None
    precipitation_amount: float | None  # mm/30min translated to mm/h
    modified_time: datetime | None
