"""Exceptions for Trafikverket."""

from typing import Any


class NoCameraFound(Exception):
    """Error from Sensibo api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)


class MultipleCamerasFound(Exception):
    """Authentication issue from Sensibo api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)


class NoRouteFound(Exception):
    """Error from Sensibo api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)


class MultipleRoutesFound(Exception):
    """Authentication issue from Sensibo api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)


class NoFerryFound(Exception):
    """Error from Sensibo api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)


class NoDeviationFound(Exception):
    """Error from Sensibo api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)


class MultipleDeviationsFound(Exception):
    """Authentication issue from Sensibo api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)
