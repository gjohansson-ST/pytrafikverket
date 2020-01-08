"""Module for communication with Trafikverket official API."""
import typing
from abc import ABCMeta, abstractmethod
from datetime import datetime
from enum import Enum

import aiohttp
from lxml import etree


class FilterOperation(Enum):
    """Contains all field filter operations."""

    equal = "EQ"
    exists = "EXISTS"
    greater_than = "GT"
    greater_than_equal = "GTE"
    less_than = "LT"
    less_than_equal = "LTE"
    not_equal = "NE"
    like = "LIKE"
    not_like = "NOTLIKE"
    #    in = "IN"
    not_in = "NOTIN"
    with_in = "WITHIN"


class SortOrder(Enum):
    """Specifies how rows of data are sorted."""

    ascending = "asc"
    decending = "desc"


class FieldSort:
    """What field and how to sort on it."""

    def __init__(self, field: str, sort_order: SortOrder):
        """Initialize the class."""
        self._field = field
        self._sort_order = sort_order

    def to_string(self):
        """Sort_order as string."""
        return self._field + " " + self._sort_order.value


class Filter:
    """Base class for all filters."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_node(self, parent_node):
        """Generate node."""
        pass


class FieldFilter(Filter):
    """Used to filter on one field."""

    def __init__(self, operation: FilterOperation, name, value):
        """Initialize the class."""
        self.operation = operation
        self.name = name
        self.value = value

    def generate_node(self, parent_node):
        """Return element node for field filter."""
        filter_node = etree.SubElement(parent_node, self.operation.value)
        filter_node.attrib["name"] = self.name
        filter_node.attrib["value"] = self.value
        return filter_node


class OrFilter(Filter):
    """Used to create a Or filter."""

    def __init__(self, filters: typing.List[Filter]):
        """Initialize the class."""
        self.filters = filters

    def generate_node(self, parent_node):
        """Return element node for filter."""
        or_node = etree.SubElement(parent_node, "OR")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node


class AndFilter(Filter):
    """Used to create a And filter."""

    def __init__(self, filters: typing.List[Filter]):
        """Initialize the class."""
        self.filters = filters

    def generate_node(self, parent_node):
        """Return element node for filter."""
        or_node = etree.SubElement(parent_node, "AND")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node


class Trafikverket(object):
    """Class used to communicate with trafikverket api."""

    _api_url = "http://api.trafikinfo.trafikverket.se/v1.2/data.xml"
    date_time_format = "%Y-%m-%dT%H:%M:%S"
    date_time_format_for_modified = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str):
        """Initialize TrafikInfo object."""
        self._client_session = client_session
        self._api_key = api_key

    def _generate_request_data(
        self,
        objecttype: str,
        includes: typing.List[str],
        filters: typing.List[Filter],
        limit: int = None,
        sorting: typing.List[FieldSort] = None,
    ):
        root_node = etree.Element("REQUEST")
        login_node = etree.SubElement(root_node, "LOGIN")
        login_node.attrib["authenticationkey"] = self._api_key
        query_node = etree.SubElement(root_node, "QUERY")
        query_node.attrib["objecttype"] = objecttype
        if limit is not None:
            query_node.attrib["limit"] = str(limit)
        if sorting is not None and len(sorting) > 0:
            query_node.attrib["orderby"] = ", ".join([fs.to_string() for fs in sorting])
        for include in includes:
            include_node = etree.SubElement(query_node, "INCLUDE")
            include_node.text = include
        filters_node = etree.SubElement(query_node, "FILTER")
        for filter in filters:
            filter.generate_node(filters_node)

        return root_node

    async def async_make_request(
        self,
        objecttype: str,
        includes: typing.List[str],
        filters: typing.List[Filter],
        limit: int = None,
        sorting: typing.List[FieldSort] = None,
    ):
        """Send request to trafikverket api and return a element node."""
        request_data = self._generate_request_data(
            objecttype, includes, filters, limit, sorting
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
                raise ValueError("Source: " + source + ", message: " + message)

            return etree.fromstring(content).xpath("/RESPONSE/RESULT/" + objecttype)


class NodeHelper(object):
    """Helper class to get node content."""

    def __init__(self, node):
        """Initialize the class."""
        self._node = node

    def get_text(self, field):
        """Return the text in 'field' from the node or None if not found."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return nodes[0].text

    def get_texts(self, field):
        """Return a list of texts from the node selected by 'field' or None."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        result = [str] * 0
        for line in nodes:
            result.append(line.text)
        return result

    def get_datetime_for_modified(self, field):
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

    def get_datetime(self, field):
        """Return a datetime object from node, selected by 'field'."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return datetime.strptime(nodes[0].text, Trafikverket.date_time_format)

    def get_bool(self, field):
        """Return True if value selected by field is 'true' else returns False."""
        nodes = self._node.xpath(field)
        if nodes is None:
            return False
        if len(nodes) == 0:
            return False
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return nodes[0].text.lower() == "true"
