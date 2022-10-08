"""Retrieve camera data from Trafikverket API."""

from datetime import datetime
import aiohttp
from pytrafikverket.trafikverket import (
    FieldFilter,
    FilterOperation,
    NodeHelper,
    Trafikverket,
)


class CameraInfo:
    """Fetch Camera data."""

    _required_fields = [
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

    def __init__(
        self,
        camera_name: str,
        camera_id: str,
        active: bool,
        deleted: bool,
        description: str,
        direction: str,
        fullsizephoto: bool,
        location: str,
        modified: datetime,
        phototime: datetime,
        photourl: str,
        status: str,
        camera_type: str,
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
    def from_xml_node(cls, node):
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
            CameraInfo._required_fields,  # pylint: disable=protected-access
            [FieldFilter(FilterOperation.equal, "Name", location_name)],
        )
        if len(cameras) == 0:
            raise ValueError("Could not find a camera with the specified name")
        if len(cameras) > 1:
            raise ValueError("Found multiple camera with the specified name")

        return CameraInfo.from_xml_node(cameras[0])
