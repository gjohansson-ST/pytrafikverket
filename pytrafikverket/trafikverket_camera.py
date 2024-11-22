"""Retrieve camera data from Trafikverket API."""

from __future__ import annotations

from pytrafikverket.helpers import camera_from_xml_node
from pytrafikverket.models import CameraInfoModel

from .const import CAMERA_INFO_REQUIRED_FIELDS
from .exceptions import MultipleCamerasFound, NoCameraFound
from .filters import FieldFilter, FilterOperation, OrFilter
from .trafikverket import (
    TrafikverketBase,
)


class TrafikverketCamera(TrafikverketBase):
    """Class used to communicate with trafikverket's camera api."""

    version = "1.0"

    async def async_get_camera(self, search_string: str) -> CameraInfoModel:
        """Retrieve camera from API."""
        cameras = await self._api.async_make_request(
            "Camera",
            self.version,
            None,
            CAMERA_INFO_REQUIRED_FIELDS,
            [
                OrFilter(
                    [
                        FieldFilter(FilterOperation.LIKE, "Name", search_string),
                        FieldFilter(FilterOperation.LIKE, "Location", search_string),
                        FieldFilter(FilterOperation.LIKE, "Id", search_string),
                    ]
                )
            ],
        )
        if len(cameras) == 0:
            raise NoCameraFound("Could not find a camera with the specified name")
        if len(cameras) > 1:
            raise MultipleCamerasFound("Found multiple camera with the specified name")

        return await camera_from_xml_node(cameras[0])

    async def async_get_cameras(self, search_string: str) -> list[CameraInfoModel]:
        """Retrieve multipple cameras from API."""
        cameras = await self._api.async_make_request(
            "Camera",
            self.version,
            None,
            CAMERA_INFO_REQUIRED_FIELDS,
            [
                OrFilter(
                    [
                        FieldFilter(FilterOperation.LIKE, "Name", search_string),
                        FieldFilter(FilterOperation.LIKE, "Location", search_string),
                        FieldFilter(FilterOperation.LIKE, "Id", search_string),
                    ]
                )
            ],
        )
        if len(cameras) == 0:
            raise NoCameraFound("Could not find a camera with the specified name")

        camera_list = []
        for camera in cameras:
            camera_list.append(await camera_from_xml_node(camera))
        return camera_list
