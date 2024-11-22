"""Pytrafikverket module."""

from .__main__ import main
from .exceptions import (
    InvalidAuthentication,
    MultipleCamerasFound,
    MultipleDeviationsFound,
    MultipleRoutesFound,
    MultipleTrainStationsFound,
    MultipleWeatherStationsFound,
    NoCameraFound,
    NoDeviationFound,
    NoFerryFound,
    NoRouteFound,
    NoTrainAnnouncementFound,
    NoTrainStationFound,
    NoWeatherStationFound,
    UnknownError,
)
from .filters import (
    AndFilter,
    FieldFilter,
    FieldSort,
    Filter,
    FilterOperation,
    OrFilter,
    SortOrder,
)
from .helpers import NodeHelper
from .models import (
    CameraInfoModel,
    DeviationInfoModel,
    FerryRouteInfoModel,
    FerryStopModel,
    FerryStopStatus,
    StationInfoModel,
    TrainStopModel,
    TrainStopStatus,
    WeatherStationInfoModel,
)
from .trafikverket import Trafikverket
from .trafikverket_camera import TrafikverketCamera
from .trafikverket_ferry import TrafikverketFerry
from .trafikverket_train import TrafikverketTrain
from .trafikverket_weather import TrafikverketWeather

__all__ = [
    "AndFilter",
    "CameraInfoModel",
    "DeviationInfoModel",
    "FerryRouteInfoModel",
    "FerryStopModel",
    "FerryStopStatus",
    "FieldFilter",
    "FieldSort",
    "Filter",
    "FilterOperation",
    "InvalidAuthentication",
    "MultipleCamerasFound",
    "MultipleDeviationsFound",
    "MultipleRoutesFound",
    "MultipleTrainStationsFound",
    "MultipleWeatherStationsFound",
    "NoCameraFound",
    "NoDeviationFound",
    "NoFerryFound",
    "NoRouteFound",
    "NoTrainAnnouncementFound",
    "NoTrainStationFound",
    "NoWeatherStationFound",
    "NodeHelper",
    "OrFilter",
    "SortOrder",
    "StationInfoModel",
    "Trafikverket",
    "TrafikverketCamera",
    "TrafikverketFerry",
    "TrafikverketTrain",
    "TrafikverketWeather",
    "TrainStopModel",
    "TrainStopStatus",
    "UnknownError",
    "WeatherStationInfoModel",
]


def run() -> None:
    main()
