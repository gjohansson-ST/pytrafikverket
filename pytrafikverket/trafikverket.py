"""Module for communication with Trafikverket official API."""

from __future__ import annotations

import logging

import aiohttp
from lxml import etree

from .const import API_URL
from .exceptions import InvalidAuthentication, UnknownError
from .filters import FieldFilter, FieldSort, Filter
from .helpers import NodeHelper

LOGGER = logging.getLogger(__name__)


class Trafikverket:
    """Class used to communicate with trafikverket api."""

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize TrafikInfo object."""
        self._client_session = client_session
        self._api_key = api_key

    def _generate_request_data(
        self,
        objecttype: str,
        schemaversion: str,
        namespace: str | None,
        includes: list[str],
        filters: list[Filter],
        limit: int | None = None,
        sorting: list[FieldSort] | None = None,
    ) -> etree._Element:
        root_node = etree.Element("REQUEST")
        login_node = etree.SubElement(root_node, "LOGIN")
        login_node.attrib["authenticationkey"] = self._api_key
        query_node = etree.SubElement(root_node, "QUERY")
        query_node.attrib["objecttype"] = objecttype
        query_node.attrib["schemaversion"] = schemaversion
        if namespace is not None:
            # Only used in some queries
            query_node.attrib["namespace"] = namespace
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
        namespace: str | None,
        includes: list[str],
        filters: list[Filter | FieldFilter],
        limit: int | None = None,
        sorting: list[FieldSort] | None = None,
    ) -> list[etree._ElementTree]:
        """Send request to trafikverket api and return a element node."""
        request_data = self._generate_request_data(
            objecttype, schemaversion, namespace, includes, filters, limit, sorting
        )
        request_data_text = etree.tostring(request_data, pretty_print=False)
        LOGGER.debug("Sending query with: %s", request_data_text)
        headers = {"content-type": "text/xml"}
        async with self._client_session.post(
            API_URL, data=request_data_text, headers=headers
        ) as response:
            content = await response.text()
            LOGGER.debug("Response received with: %s", content)
            error_nodes = etree.fromstring(content).xpath("/RESPONSE/RESULT/ERROR")
            if len(error_nodes) > 0:
                error_node = error_nodes[0]
                helper = NodeHelper(error_node)
                source = helper.get_text("SOURCE")
                message = helper.get_text("MESSAGE")
                if response.status == 401:
                    raise InvalidAuthentication(
                        f"Source: {source}, message: {message}"
                        ", status: {response.status}"
                    )
                raise UnknownError(
                    f"Source: {source}, message: {message}"
                    ", status: {response.status}"
                )

            result: list[etree._ElementTree] = etree.fromstring(content).xpath(
                "/RESPONSE/RESULT/" + objecttype
            )
            return result


class TrafikverketBase:
    """Base class used to communicate with trafikverket's api."""

    version = "1.0"

    def __init__(self, client_session: aiohttp.ClientSession, api_key: str) -> None:
        """Initialize Trafikverket Base."""
        self._api = Trafikverket(client_session, api_key)
