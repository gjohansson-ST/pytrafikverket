"""Exceptions for Trafikverket."""
from __future__ import annotations


class NoCameraFound(Exception):
    """Error found no camera."""


class MultipleCamerasFound(Exception):
    """Error found multiple cameras."""


class NoRouteFound(Exception):
    """Error found no ferry route."""


class MultipleRoutesFound(Exception):
    """Error found multiple ferry routes."""


class NoFerryFound(Exception):
    """Error found no ferry."""


class NoDeviationFound(Exception):
    """Error found no deviation."""


class MultipleDeviationsFound(Exception):
    """Error found multiple deviations."""


class NoWeatherStationFound(Exception):
    """Error found no weather station."""


class MultipleWeatherStationsFound(Exception):
    """Error found multiple weather stations."""


class NoTrainStationFound(Exception):
    """Error found no train station."""


class MultipleTrainStationsFound(Exception):
    """Error found multiple train stations."""


class NoTrainAnnouncementFound(Exception):
    """Error found no train announcement."""


class MultipleTrainAnnouncementFound(Exception):
    """Error found multiple train announcements."""


class InvalidAuthentication(Exception):
    """Error found multiple train announcements."""


class UnknownError(Exception):
    """Error found multiple train announcements."""
