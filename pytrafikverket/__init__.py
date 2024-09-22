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
    "FieldFilter",
    "FieldSort",
    "Filter",
    "FilterOperation",
    "OrFilter",
    "SortOrder",
    "NodeHelper",
    "CameraInfoModel",
    "DeviationInfoModel",
    "FerryRouteInfoModel",
    "FerryStopModel",
    "FerryStopStatus",
    "StationInfoModel",
    "TrainStopModel",
    "TrainStopStatus",
    "WeatherStationInfoModel",
    "Trafikverket",
    "TrafikverketCamera",
    "TrafikverketFerry",
    "TrafikverketTrain",
    "TrafikverketWeather",
    "NoCameraFound",
    "MultipleCamerasFound",
    "NoRouteFound",
    "MultipleRoutesFound",
    "NoFerryFound",
    "NoDeviationFound",
    "MultipleDeviationsFound",
    "NoWeatherStationFound",
    "MultipleWeatherStationsFound",
    "NoTrainStationFound",
    "MultipleTrainStationsFound",
    "NoTrainAnnouncementFound",
    "InvalidAuthentication",
    "UnknownError",
]


def run() -> None:
    main()
