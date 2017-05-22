from abc import ABCMeta, abstractmethod
import typing
from enum import Enum
from datetime import datetime
import aiohttp
from lxml import etree

class FilterOperation(Enum):
    """Contains all field filter operations"""
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

class Filter:
    """Base class for all filters"""
    __metaclass__ = ABCMeta

    @abstractmethod
    def generate_node(self, parent_node):
        pass

class FieldFilter(Filter):
    """Used to filter on one field"""
    def __init__(self, operation:FilterOperation, name, value):
        self.operation = operation
        self.name = name
        self.value = value

    def generate_node(self, parent_node):
        filter_node = etree.SubElement(parent_node, self.operation.value)
        filter_node.attrib["name"] = self.name
        filter_node.attrib["value"] = self.value
        return filter_node

class OrFilter(Filter):
    """Used to create a Or filter"""
    def __init__(self, filters: typing.List[Filter]):
        self.filters = filters

    def generate_node(self, parent_node):
        or_node = etree.SubElement(parent_node, "OR")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node

class AndFilter(Filter):
    """Used to create a And filter"""
    def __init__(self, filters: typing.List[Filter]):
        self.filters = filters

    def generate_node(self, parent_node):
        or_node = etree.SubElement(parent_node, "AND")
        for sub_filter in self.filters:
            sub_filter.generate_node(or_node)
        return or_node

class Trafikverket(object):
    """Class used to communicate with trafikverket api"""

    _api_url = "http://api.trafikinfo.trafikverket.se/v1.1/data.xml"
    date_time_format = "%Y-%m-%dT%H:%M:%S"
    date_time_format_for_modified = "%Y-%m-%dT%H:%M:%S.%fZ"

    def __init__(self, client_session:aiohttp.ClientSession, api_key:str):
        """Initialize TrafikInfo object"""
        self._client_session = client_session
        self._api_key = api_key

    def _generate_request_data(self, objecttype:str,
                               includes: typing.List[str],
                               filters: typing.List[Filter]):
        root_node = etree.Element("REQUEST")
        login_node = etree.SubElement(root_node, "LOGIN")
        login_node.attrib["authenticationkey"] = self._api_key
        query_node = etree.SubElement(root_node, "QUERY")
        query_node.attrib["objecttype"] = objecttype
        for include in includes:
            include_node = etree.SubElement(query_node, "INCLUDE")
            include_node.text = include
        filters_node = etree.SubElement(query_node, "FILTER")
        for filter in filters:
            filter.generate_node(filters_node)
        return root_node

    async def make_request(self, objecttype:str,
                           includes: typing.List[str],
                           filters: typing.List[Filter]):
        request_data = self._generate_request_data(objecttype, includes, filters)
        request_data_text = etree.tostring(request_data, pretty_print=False)
        headers = {"content-type": "text/xml"}
        async with self._client_session.post(Trafikverket._api_url,
                                             data=request_data_text,
                                             headers=headers) as response:
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
    """Helper class to get node content"""
    def __init__(self, node):
        self._node = node

    def get_text(self, field):
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return nodes[0].text

    def get_texts(self, field):
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        result = [str] * 0
        for line in nodes:
            result.append(line.text)
        return result

    def get_datetime_for_modified(self, field):
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return datetime.strptime(nodes[0].text, Trafikverket.date_time_format_for_modified)

    def get_datetime(self, field):
        nodes = self._node.xpath(field)
        if nodes is None:
            return None
        if len(nodes) == 0:
            return None
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return datetime.strptime(nodes[0].text, Trafikverket.date_time_format)

    def get_bool(self, field):
        nodes = self._node.xpath(field)
        if nodes is None:
            return False
        if len(nodes) == 0:
            return False
        if len(nodes) > 1:
            raise ValueError("Found multiple nodes should only 0 or 1 is allowed")
        return nodes[0].text.lower() == "true"
