"""Retrieve camera data from Trafikverket API."""
from __future__ import annotations

from datetime import datetime

import aiohttp
from lxml import etree

from .exceptions import MultipleCamerasFound, NoCameraFound
from .trafikverket import (
    FieldFilter,
    FilterOperation,
    NodeHelper,
    OrFilter,
    Trafikverket,
)

CAMERA_INFO_REQUIRED_FIELDS = [
    "Name",
    "Id",
    "Active",
    "Deleted",
    "Description",
    "Direction",
    "HasFullSizePhoto",
    "Location",
    "ModifiedTime",
    "PhotoTime",
    "PhotoUrl",
    "Status",
    "Type",
]


class CameraInfo:  # pylint: disable=R0902
    """Fetch Camera data."""

    def __init__(  # pylint: disable=R0913
        self,
        camera_name: str | None,
        camera_id: str | None,
        active: bool,
        deleted: bool,
        description: str | None,
        direction: str | None,
        fullsizephoto: bool,
        location: str | None,
        modified: datetime | None,
        phototime: datetime | None,
        photourl: str | None,
        status: str | None,
        camera_type: str | None,
    ) -> None:
        """Initialize the class."""
        self.camera_name = camera_name
        self.camera_id = camera_id
        self.active = active
        self.deleted = deleted
        self.description = description
        self.direction = direction
        self.fullsizephoto = fullsizephoto
        self.location = location
        self.modified = modified
        self.phototime = phototime
        self.photourl = photourl
        self.status = status
        self.camera_type = camera_type

    @classmethod
    def from_xml_node(
        cls, node: etree._ElementTree
    ) -> CameraInfo:  # pylint: disable=too-many-locals
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
        return cls(
            camera_name,
            camera_id,
            active,
            deleted,
            description,
            direction,
            fullsizephoto,
            location,
            modified,
            phototime,
            photourl,
            status,
            camera_type,
        )


class TrafikverketCamera:
    """Class used to communicate with trafikverket's camera api."""

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize Camera object."""
        self._api = Trafikverket(client_session, api_key)

    async def async_get_camera(self, location_name: str) -> CameraInfo:
        """Retrieve camera from API."""
        cameras = await self._api.async_make_request(
            "Camera",
            "1.0",
            CAMERA_INFO_REQUIRED_FIELDS,
            [
                OrFilter(
                    [
                        FieldFilter(FilterOperation.LIKE, "Name", location_name),
                        FieldFilter(FilterOperation.LIKE, "Location", location_name),
                        FieldFilter(FilterOperation.EQUAL, "Id", location_name),
                    ]
                )
            ],
        )
        if len(cameras) == 0:
            raise NoCameraFound("Could not find a camera with the specified name")
        if len(cameras) > 1:
            raise MultipleCamerasFound("Found multiple camera with the specified name")

        return CameraInfo.from_xml_node(cameras[0])

    async def async_get_cameras(self, location_name: str) -> CameraInfo:
        """Retrieve camera from API."""
        cameras = await self._api.async_make_request(
            "Camera",
            "1.0",
            CAMERA_INFO_REQUIRED_FIELDS,
            [
                OrFilter(
                    [
                        FieldFilter(FilterOperation.LIKE, "Name", location_name),
                        FieldFilter(FilterOperation.LIKE, "Location", location_name),
                        FieldFilter(FilterOperation.EQUAL, "Id", location_name),
                    ]
                )
            ],
        )
        if len(cameras) == 0:
            raise NoCameraFound("Could not find a camera with the specified name")

        camera_list = []
        for camera in cameras:
            camera_list.append(CameraInfo.from_xml_node(camera))
        return camera_list
