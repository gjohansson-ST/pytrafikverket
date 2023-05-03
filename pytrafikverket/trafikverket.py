"""Module for communication with Trafikverket official API."""
from __future__ import annotations

from typing import Any, cast
from abc import ABCMeta, abstractmethod
from datetime import datetime
from enum import Enum

import aiohttp
from lxml import etree

from .exceptions import InvalidAuthentication, UnknownError

class FilterOperation(Enum):
    """Contains all field filter operations."""

    EQUAL = "EQ"
    EXISTS = "EXISTS"
    GREATER_THAN = "GT"
    GREATER_THAN_EQUAL = "GTE"
    LESS_THAN = "LT"
    LESS_THAN_EQUAL = "LTE"
    NOT_EQUAL = "NE"
    LIKE = "LIKE"
    NOT_LIKE = "NOTLIKE"
    #    IN = "IN"
    NOT_IN = "NOTIN"
    WITH_IN = "WITHIN"


class SortOrder(Enum):
    """Specifies how rows of data are sorted."""

    ASCENDING = "asc"
    DECENDING = "desc"


class FieldSort:
    """What field and how to sort on it."""

    def __init__(self, field: str, sort_order: SortOrder) -> None:
        """Initialize the class."""
        self._field = field
        self._sort_order = sort_order

    def to_string(self) -> str:
        """Sort_order as string."""
        return self._field + " " + self._sort_order.value


class Filter:
    """Base class for all filters."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_node(self, parent_node: Any) -> Any:
        """Generate node."""


class FieldFilter(Filter):
    """Used to filter on one field."""

    def __init__(self, operation: FilterOperation, name: str, value: Any) -> None:
        """Initialize the class."""
        self.operation = operation
        self.name = name
        self.value = value

    def generate_node(self, parent_node: Any) -> Any:
        """Return element node for field filter."""
        filter_node = etree.SubElement(parent_node, self.operation.value)
        filter_node.attrib["name"] = self.name
        filter_node.attrib["value"] = self.value
        return filter_node


class OrFilter(Filter):
    """Used to create a Or filter."""

    def __init__(self, filters: list[Filter]) -> None:
        """Initialize the class."""
        self.filters = filters

    def generate_node(self, parent_node: Any) -> Any:
        """Return element node for filter."""
        or_node = etree.SubElement(parent_node, "OR")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node


class AndFilter(Filter):
    """Used to create a And filter."""

    def __init__(self, filters: list[Filter]) -> None:
        """Initialize the class."""
        self.filters = filters

    def generate_node(self, parent_node: Any) -> Any:
        """Return element node for filter."""
        or_node = etree.SubElement(parent_node, "AND")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node


class Trafikverket:
    """Class used to communicate with trafikverket api."""

    _api_url = "https://api.trafikinfo.trafikverket.se/v2/data.xml"
    date_time_format = "%Y-%m-%dT%H:%M:%S.%f%z"
    date_time_format_for_modified = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize TrafikInfo object."""
        self._client_session = client_session
        self._api_key = api_key

    def _generate_request_data(
        self,
        objecttype: str,
        schemaversion: str,
        includes: list[str],
        filters: list[Filter],
        limit: int | None = None,
        sorting: list[FieldSort] | None = None,
    ) -> Any:
        root_node = etree.Element("REQUEST")
        login_node = etree.SubElement(root_node, "LOGIN")
        login_node.attrib["authenticationkey"] = self._api_key
        query_node = etree.SubElement(root_node, "QUERY")
        query_node.attrib["objecttype"] = objecttype
        query_node.attrib["schemaversion"] = schemaversion
        if limit is not None:
            query_node.attrib["limit"] = str(limit)
        if sorting is not None and len(sorting) > 0:
            query_node.attrib["orderby"] = ", ".join([fs.to_string() for fs in sorting])
        for include in includes:
            include_node = etree.SubElement(query_node, "INCLUDE")
            include_node.text = include
        filters_node = etree.SubElement(query_node, "FILTER")
        for _filter in filters:
            _filter.generate_node(filters_node)

        return root_node

    async def async_make_request(
        self,
        objecttype: str,
        schemaversion: str,
        includes: list[str],
        filters: list[Filter | FieldFilter],
        limit: int | None = None,
        sorting: list[FieldSort] | None = None,
    ) -> Any:
        """Send request to trafikverket api and return a element node."""
        request_data = self._generate_request_data(
            objecttype, schemaversion, includes, filters, limit, sorting
        )
        request_data_text = etree.tostring(request_data, pretty_print=False)
        headers = {"content-type": "text/xml"}
        async with self._client_session.post(
            Trafikverket._api_url, data=request_data_text, headers=headers
        ) as response:
            content = await response.text()
            error_nodes = etree.fromstring(content).xpath("/RESPONSE/RESULT/ERROR")
            if len(error_nodes) > 0:
                error_node = error_nodes[0]
                helper = NodeHelper(error_node)
                source = helper.get_text("SOURCE")
                message = helper.get_text("MESSAGE")
                if response.status == 401:
                    raise InvalidAuthentication(f"Source: {source}, message: {message}, status: {response.status}")
                raise UnknownError(f"Source: {source}, message: {message}, status: {response.status}")

            return etree.fromstring(content).xpath("/RESPONSE/RESULT/" + objecttype)


class NodeHelper:
    """Helper class to get node content."""

    def __init__(self, node: Any) -> None:
        """Initialize the class."""
        self._node = node

    def get_text(self, field: str) -> str | None:
        """Return the text in 'field' from the node or None if not found."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        value = nodes[0].text
        return cast(str, value)

    def get_number(self, field: str) -> float | None:
        """Return the number in 'field' from the node or None if not found."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        value = nodes[0].text
        return cast(float, value)

    def get_texts(self, field: str) -> list[str] | None:
        """Return a list of texts from the node selected by 'field' or None."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        result = []
        for line in nodes:
            result.append(line.text)
        return result

    def get_datetime_for_modified(self, field: str) -> datetime | None:
        """Return datetime object from node, selected by 'field'.

        Format of the text is expected to be modifiedTime-format.
        """
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return datetime.strptime(
            nodes[0].text, Trafikverket.date_time_format_for_modified
        )

    def get_datetime(self, field: str) -> datetime | None:
        """Return a datetime object from node, selected by 'field'."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return datetime.strptime(nodes[0].text, Trafikverket.date_time_format)

    def get_bool(self, field: str) -> bool:
        """Return True if value selected by field is 'true' else returns False."""
        nodes: etree.XPath = self._node.xpath(field)
        if nodes is None:
            return False
        if len(nodes) == 0:
            return False
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        value = nodes[0].text.lower() == "true"
        return cast(bool, value)
